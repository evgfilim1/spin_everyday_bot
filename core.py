import pickle
from datetime import datetime

from telegram import ChatMember, ParseMode, TelegramError
from telegram import User, Update, Message, Bot
from telegram.ext.dispatcher import run_async

from config import RESET_TIME, BOT_CREATOR, LOG_CHANNEL

chat_users = {}
spin_name = {}
can_change_name = {}
results_today = {}
results_total = {}

announcement_chats = []


def _check_destination(bot_name: str, message_text: str) -> bool:
    msg = message_text.split()
    msg = msg[0].split('@')
    msg.append('')
    return msg[1] == bot_name or msg[1] == ''


def is_private(chat_id: int) -> bool:
    return chat_id > 0


def not_pm(function: callable):
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        msg = get_message(update)
        if is_private(msg.chat_id):
            msg.reply_text("Эта команда недоступна в ЛС")
            return
        function(bot, update, *args, **kwargs)

    return wrapper


def check_destination(function: callable):
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        msg = get_message(update)
        if not _check_destination(bot.username, msg.text):
            return
        function(bot, update, *args, **kwargs)

    return wrapper


def get_name(user: User) -> str:
    if bool(user.username):
        return '@' + user.username
    else:
        return user.first_name


def load(filename: str) -> dict:
    with open(filename, 'rb') as ff:
        return pickle.load(ff)


def save(obj: dict, filename: str):
    with open(filename, 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def load_all():
    global chat_users, spin_name, can_change_name, results_today, results_total
    if not __import__("os").path.exists("users.pkl"):
        return
    chat_users = load("users.pkl")
    spin_name = load("spin.pkl")
    can_change_name = load("changers.pkl")
    results_today = load("results.pkl")
    results_total = load("total.pkl")


def save_all():
    save(chat_users, "users.pkl")
    save(spin_name, "spin.pkl")
    save(can_change_name, "changers.pkl")
    save(results_today, "results.pkl")
    save(results_total, "total.pkl")


def clear_data(chat_id: int):
    chat_users.pop(chat_id)
    try:
        spin_name.pop(chat_id)
    except KeyError:
        pass

    try:
        can_change_name.pop(chat_id)
    except KeyError:
        pass

    try:
        results_today.pop(chat_id)
    except KeyError:
        pass


def migrate(from_chat: int, to_chat: int):
    chat_users.update({to_chat: chat_users.get(from_chat)})
    spin_name.update({to_chat: spin_name.get(from_chat)})
    can_change_name.update({to_chat: can_change_name.get(from_chat)})
    results_today.update({to_chat: results_today.get(from_chat)})
    clear_data(from_chat)


def is_user_left(chat_user: ChatMember) -> bool:
    return chat_user.status == ChatMember.LEFT or \
           chat_user.status == ChatMember.KICKED


def time_diff() -> float:
    t = RESET_TIME.split(':')
    now = datetime.now()
    then = datetime(2016, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def get_message(update: Update) -> Message:
    return update.message or update.edited_message


def choose_random_user(chat_id: int, bot: Bot) -> str:
    from random import choice
    user = choice(list(chat_users[chat_id].items()))    # Getting tuple (user_id, username)
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user[0])
        if is_user_left(member):
            raise TelegramError("User left the group")
    except TelegramError:
        chat_users[chat_id].pop(user[0])
        return choose_random_user(chat_id, bot)
    user = get_name(member.user)
    uid = member.user.id
    results_today.update({chat_id: user})
    chat_users[chat_id].update({uid: user})
    if chat_id not in results_total:
        results_total.update({chat_id: {}})
    results_total[chat_id].update({uid: results_total[chat_id].get(uid, 0) + 1})
    return user


def top_win(chat_id: int) -> list:
    return sorted(results_total.get(chat_id, {}).items(), key=lambda x: x[1], reverse=True)


def can_change_spin_name(chat_id: int, user_id: int) -> bool:
    return user_id in can_change_name[chat_id] or user_id == BOT_CREATOR


def log_to_channel(bot: Bot, level: str, text: str):
    bot.send_message(chat_id=LOG_CHANNEL, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


@run_async
def announce(bot: Bot, text: str, md: bool=False):
    from time import sleep
    # Sending announcement to 15 chats, then sleep
    sleep_border = 15
    announcement_chats.extend(chat_users.keys())
    text = text.replace("\\n", "\n")
    while len(announcement_chats) > 0:
        chat = announcement_chats.pop()
        try:
            if md:
                bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=chat, text=text)
            sleep_border -= 1
        except TelegramError:
            log_to_channel(bot, "WARNING", f"Chat {chat} is not reachable for messages, deleting it")
            chat_users.pop(chat)
            # pass
        if sleep_border == 0:
            sleep(5)
            sleep_border = 15


def admins_refresh(bot: Bot, chat_id: int):
    admins = bot.get_chat_administrators(chat_id=chat_id)
    can_change_name[chat_id] = []
    for admin in admins:
        can_change_name[chat_id].append(admin.user.id)


def fix_md(text: str) -> str:
    md_symbols = '*_`['
    for symbol in md_symbols:
        try:
            text = text.replace(symbol, '\\' + symbol)
        except AttributeError:
            break
    return text

load_all()

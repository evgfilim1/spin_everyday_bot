import pickle
from datetime import datetime

from telegram import ChatMember, ParseMode, TelegramError
from telegram import User, Update, Message, Bot

from config import RESET_TIME, BOT_CREATOR, LOG_CHANNEL


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


def load_all() -> (dict, dict, dict, dict):
    if not __import__("os").path.exists("users.pkl"):
        return {}, {}, {}, {}
    chat_users = load("users.pkl")
    spin_name = load("spin.pkl")
    can_change_spin_name = load("changers.pkl")
    results = load("results.pkl")
    return chat_users, spin_name, can_change_spin_name, results


def save_all(chat_users: dict, spin_name: dict, can_change_spin_name: dict, results: dict):
    save(chat_users, "users.pkl")
    save(spin_name, "spin.pkl")
    save(can_change_spin_name, "changers.pkl")
    save(results, "results.pkl")


def clear_data(chat_id: int, chat_users: dict, spin_name: dict, can_change_name: dict, results: dict):
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
        results.pop(chat_id)
    except KeyError:
        pass


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


def choose_random_user(chat_users: dict, results: dict, chat_id: int, bot: Bot) -> str:
    from random import choice
    user = choice(list(chat_users[chat_id].items()))    # Getting tuple (user_id, username)
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user[0])
        if is_user_left(member):
            raise TelegramError("User left the group")
    except TelegramError:
        chat_users[chat_id].pop(user[0])
        return choose_random_user(chat_users, results, chat_id, bot)
    user = get_name(member.user)
    results.update({chat_id: user})
    chat_users[chat_id].update({member.user.id: user})
    return user


def can_change_name(can_change_spin_name: dict, chat_id: int, user_id: int) -> bool:
    return user_id in can_change_spin_name[chat_id] or user_id == BOT_CREATOR


def log_to_channel(bot: Bot, level: str, text: str):
    bot.send_message(chat_id=LOG_CHANNEL, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


def announce(bot: Bot, chat_users: dict, text: str, md: bool=False):
    for chat in chat_users.keys():
        try:
            if md:
                bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=chat, text=text)
        except TelegramError:
            pass


def admins_refresh(can_change_spin_name: dict, bot: Bot, chat_id: int):
    admins = bot.get_chat_administrators(chat_id=chat_id)
    can_change_spin_name[chat_id] = []
    for admin in admins:
        can_change_spin_name[chat_id].append(admin.user.id)


def fix_md(text: str) -> str:
    md_symbols = '*_`['
    for symbol in md_symbols:
        try:
            text = text.replace(symbol, '\\' + symbol)
        except AttributeError:
            break
    return text


def is_admin(user: User):
    if User.id == BOT_CREATOR:
        return

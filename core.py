import pickle
from datetime import datetime

from telegram import ChatMember, ParseMode, TelegramError
from telegram import User, Update, Message, Bot

from config import resetTime, botCREATOR, logChannel

# botID = int(botTOKEN[:botTOKEN.index(":")])  # deprecated


def check_destination(bot_name: str, message_text: str) -> bool:
    msg = message_text.split()
    msg = msg[0].split('@')
    msg.append('')
    return msg[1] == bot_name or msg[1] == ''


def get_name(user: User) -> str:
    if bool(user.username):
        return '@' + user.username
    else:
        return user.first_name


def loader(filename: str) -> dict:
    with open(filename, 'rb') as ff:
        return pickle.load(ff)


def saver(obj: dict, filename: str):
    with open(filename, 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def load_all() -> (dict, dict, dict, dict):
    if not __import__("os").path.exists("users.pkl"):
        return {}, {}, {}, {}
    chat_users = loader("users.pkl")
    spin_name = loader("spin.pkl")
    can_change_spin_name = loader("changers.pkl")
    results = loader("results.pkl")
    return chat_users, spin_name, can_change_spin_name, results


def save_all(chat_users: dict, spin_name: dict, can_change_spin_name: dict, results: dict):
    saver(chat_users, "users.pkl")
    saver(spin_name, "spin.pkl")
    saver(can_change_spin_name, "changers.pkl")
    saver(results, "results.pkl")


def is_user_left(chat_user: ChatMember) -> bool:
    if chat_user.status == ChatMember.LEFT or \
                    chat_user.status == ChatMember.KICKED:
        return True
    else:
        return False


def is_private(chat_id: int, user_id: int = None) -> bool:
    if user_id is not None:
        print("WARNING: 'user_id' is deprecated, it will be removed soon")
    return chat_id > 0


def time_diff() -> float:
    t = resetTime.split(':')
    now = datetime.now()
    then = datetime(2016, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def get_message(update: Update) -> Message:
    if bool(update.edited_message):
        return update.edited_message
    else:
        return update.message


def choose_random_user(chat_users: dict, results: dict, chat_id: int) -> str:
    from random import choice
    user = choice(list(chat_users[chat_id].items()))
    user = user[1]
    results.update({chat_id: user})
    return user


def can_change_name(can_change_spin_name: dict, chat_id: int, user_id: int) -> bool:
    return user_id in can_change_spin_name[chat_id] or user_id == botCREATOR


def log_to_channel(bot: Bot, level: str, text: str):
    bot.sendMessage(chat_id=logChannel, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


def announce(bot: Bot, chat_users: dict, text: str, md: bool = False):
    for chat in chat_users.keys():
        try:
            if md:
                bot.sendMessage(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat, text=text)
        except TelegramError:
            pass


def admins_refresh(can_change_spin_name: dict, bot: Bot, chat_id: int):
    admins = bot.getChatAdministrators(chat_id=chat_id)
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

import pickle
from telegram import ChatMember, ParseMode, TelegramError
from datetime import datetime
from config import resetTime, botCREATOR, botTOKEN, logChannel

botID = int(botTOKEN[:botTOKEN.index(":")])


def get_name(user) -> str:
    if bool(user.username):
        return '@' + user.username
    else:
        return user.first_name


def loader(filename: str):
    with open(filename, 'rb') as ff:
        return pickle.load(ff)


def saver(obj, filename: str):
    with open(filename, 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def load_all():
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


def is_user_left(chat_user) -> bool:
    if chat_user.status == ChatMember.LEFT or \
                    chat_user.status == ChatMember.KICKED:
        return True
    else:
        return False


def is_private(chat_id: int, user_id: int=0) -> bool:
    if user_id != 0:
        print("WARNING: 'user_id' is deprecated, it will be removed soon")
    return chat_id > 0


def time_diff() -> float:
    t = resetTime.split(':')
    now = datetime.now()
    then = datetime(2016, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def get_message(update):
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


def log_to_channel(bot, level: str, text: str):
    bot.sendMessage(chat_id=logChannel, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


def announce(bot, chat_users: dict, text: str, md: bool=False):
    for chat in chat_users.keys():
        try:
            if md:
                bot.sendMessage(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat, text=text)
        except TelegramError:
            pass


def admins_refresh(can_change_spin_name: dict, bot, chat_id: int):
    admins = bot.getChatAdministrators(chat_id=chat_id)
    can_change_spin_name[chat_id] = []
    for admin in admins:
        can_change_spin_name[chat_id].append(admin.user.id)


def fix_md(text):
    md_symbols = '*_`['
    for symbol in md_symbols:
        try:
            text = text.replace(symbol, '\\' + symbol)
        except AttributeError:
            break
    return text

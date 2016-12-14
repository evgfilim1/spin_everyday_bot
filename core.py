import pickle
from telegram import ChatMember, ParseMode, TelegramError
from datetime import datetime
from config import resetTime, botCREATOR, botTOKEN, logChannel

botID = int(botTOKEN[:botTOKEN.index(":")])


def getuname(user) -> str:
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


def loadAll():
    if not __import__("os").path.exists("users.pkl"):
        return {}, {}, {}, {}
    chatUsers = loader("users.pkl")
    spinName = loader("spin.pkl")
    canChangeSN = loader("changers.pkl")
    results = loader("results.pkl")
    return chatUsers, spinName, canChangeSN, results


def saveAll(chatUsers: dict, spinName: dict, canChangeSN: dict, results: dict):
    saver(chatUsers, "users.pkl")
    saver(spinName, "spin.pkl")
    saver(canChangeSN, "changers.pkl")
    saver(results, "results.pkl")


def isUserLeft(chat_user) -> bool:
    if chat_user.status == ChatMember.LEFT or \
                    chat_user.status == ChatMember.KICKED:
        return True
    else:
        return False


def isPrivate(chat_id: int, user_id: int) -> bool:
    return chat_id == user_id


def timediff() -> float:
    t = resetTime.split(':')
    now = datetime.now()
    then = datetime(2016, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def getMesg(update):
    if bool(update.edited_message):
        return update.edited_message
    else:
        return update.message


def chooseRandomUser(chatUsers: dict, results: dict, chat_id: int) -> str:
    from random import choice
    user = choice(list(chatUsers[chat_id].items()))
    user = user[1]
    results.update({chat_id: user})
    return user


def ifCanChangeSN(canChangeSN: dict, chat_id: int, user_id: int) -> bool:
    return user_id in canChangeSN[chat_id] or user_id == botCREATOR


def logToChannel(bot, level: str, text: str):
    bot.sendMessage(chat_id=logChannel, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


def announce(bot, chatUsers: dict, text: str, md: bool=False):
    for chat in chatUsers.keys():
        try:
            if md:
                bot.sendMessage(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat, text=text)
        except TelegramError:
            pass


def adminsRefreshLocal(canChangeSN: dict, bot, chat_id: int):
    admins = bot.getChatAdministrators(chat_id=chat_id)
    canChangeSN[chat_id] = []
    for admin in admins:
        canChangeSN[chat_id].append(admin.user.id)


def fix_md(text):
    MARKDOWN_SYMBOLS = '*_`['
    for symbol in MARKDOWN_SYMBOLS:
        try:
            text = text.replace(symbol, '\\' + symbol)
        except AttributeError:
            break
    return text
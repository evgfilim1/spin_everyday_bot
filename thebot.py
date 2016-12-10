from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async
from datetime import datetime
import pickle
import logging

TIME_FORMAT = "%d %b, %H:%M:%S"
LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt=TIME_FORMAT)

botTOKEN = "254071256:AAEgs8r_5x0sYH24eDRL2ix-vKra2hqDAWc"
botID = int(botTOKEN[:botTOKEN.index(":")])
botCREATOR = 230130383
defaultSpinName = "победитель"
texts = ["Итак, кто же сегодня *{s} дня*?", "_Хмм, интересно..._", "*АГА!*",
         "Сегодня ты *{s} дня,* {n}"]
textAlready = "Согласно сегодняшнему розыгрышу, *{s} дня* -- `{n}`"
helpText = """*Привет!* Я бот, который делает ежедневные розыгрыши.
Для начала, _придумайте,_ что вы будете разыгрывать и _измените_ текст при помощи /setsn
Затем, _подождите,_ пока бот запомнит пользователей чата, получая от них сообщения \
(количество пользователей можно узнать при помощи команды /countsn)
И _стартуйте_ розыгрыши при помощи команды /spinsn!
------
По всем вопросам обращайтесь к @evgfilim1
Если вы не можете изменить текст розыгрыша и \
если вы являетесь админом чата, используйте /adminF5sn для ручного обновления списка админов"""

# allUsers = {}
chatUsers = {}
spinName = {}
canChangeSN = {}
results = {}


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
    global chatUsers, spinName, canChangeSN, results
    if not __import__("os").path.exists("users.pkl"):
        return
    chatUsers = loader("users.pkl")
    spinName = loader("spin.pkl")
    canChangeSN = loader("changers.pkl")
    results = loader("results.pkl")


def saveAll():
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
    t = "0:00".split(':')
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


def chooseRandomUser(chat_id: int) -> str:
    from random import choice
    user = choice(list(chatUsers[chat_id].items()))
    user = user[1]
    results.update({chat_id: user})
    return user


def ifCanChangeSN(chat_id: int, user_id: int) -> bool:
    return user_id in canChangeSN[chat_id] or user_id == botCREATOR


def logToChannel(bot, level: str, text: str):
    bot.sendMessage(chat_id=-1001090196910, text="{lvl}:\n{txt}\n\n{time}".format(
        lvl=level, txt=text, time=datetime.now()
    ), parse_mode=ParseMode.MARKDOWN)


def adminsRefreshLocal(bot, chat_id):
    admins = bot.getChatAdministrators(chat_id=chat_id)
    canChangeSN[chat_id] = []
    for admin in admins:
        canChangeSN[chat_id].append(admin.user.id)


def errorh(bot, update, error):
    logToChannel(bot, "WARNING", "The last update \
caused error!\n```\n{err}\n```".format(err=error))


def reset(bot, job):
    results.clear()
    logToChannel(bot, "INFO", "Reset done")


def autoSave(bot, job):
    saveAll()


def updateCache(bot, update):
    user = update.message.from_user
    if not isPrivate(update.message.chat_id, user.id):
        chatUsers[update.message.chat_id].update({user.id: getuname(user)})


def adminShell(bot, update, args):
    msg = getMesg(update)
    if msg.from_user.id == botCREATOR:
        try:
            cmd = args.pop(0)
        except IndexError:
            return
        if cmd == "exec":
            eval(" ".join(args))
        elif cmd == "vardump":
            bot.sendMessage(chat_id=msg.chat_id, text="```\n{}\n```".format(
                eval(" ".join(args))
            ), parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg.message_id)
        else:
            return
    else:
        return


def svcHandler(bot, update):
    chat_id = update.message.chat_id
    to_id = update.message.migrate_to_chat_id
    if update.message.group_chat_created or \
            (bool(update.message.new_chat_member) and update.message.new_chat_member.id == botID):
        chatUsers[chat_id] = {}
        adminsRefreshLocal(bot, chat_id)
    elif to_id != 0:
        chatUsers.update({to_id: chatUsers.get(chat_id)})
        chatUsers.pop(chat_id)
        spinName.update({to_id: spinName.get(chat_id)})
        spinName.pop(chat_id)
        canChangeSN.update({to_id: canChangeSN.get(chat_id)})
        canChangeSN.pop(chat_id)
        results.update({to_id: results.get(chat_id)})
        results.pop(chat_id)
    elif bool(update.message.left_chat_member) and update.message.left_chat_member.id == botID:
        chatUsers.pop(chat_id)
        spinName.pop(chat_id)
        canChangeSN.pop(chat_id)
        results.pop(chat_id)


def helper(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=helpText, parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=update.message.message_id)


def adminRefresh(bot, update):
    if isPrivate(update.message.chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    adminsRefreshLocal(bot, update.message.chat_id)
    bot.sendMessage(chat_id=update.message.chat_id, text="Список админов обновлён",
                    reply_to_message_id=update.message.message_id)


def pingas(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Ping? Pong!",
                    reply_to_message_id=update.message.message_id)


@run_async
def doTheSpin(bot, update):
    chat_id = update.message.chat_id
    if isPrivate(chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    s = spinName.get(chat_id, defaultSpinName)
    p = results.get(chat_id, 0)
    if p != 0:
        bot.sendMessage(chat_id=chat_id, text=textAlready.format(s=s, n=p),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=update.message.message_id)
    else:
        p = chooseRandomUser(chat_id)
        from time import sleep
        for t in texts:
            bot.sendMessage(chat_id=chat_id, text=t.format(s=s, n=p),
                            parse_mode=ParseMode.MARKDOWN)
            sleep(2)


def changeSpinName(bot, update, args):
    msg = getMesg(update)

    if isPrivate(msg.chat_id, msg.from_user.id):
        bot.sendMessage(chat_id=msg.chat_id, text="Я не работаю в ЛС")
        return

    if ifCanChangeSN(msg.chat_id, msg.from_user.id):
        spinName[msg.chat_id] = " ".join(args)
        bot.sendMessage(chat_id=msg.chat_id, text="Текст розыгрыша изменён!",
                        reply_to_message_id=msg.message_id)
    else:
        return


def spinCount(bot, update):
    if isPrivate(update.message.chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Кол-во людей, участвующих в розыгрыше: _{}_".format(
                        len(chatUsers[update.message.chat_id])
                    ), reply_to_message_id=update.message.message_id,
                    parse_mode=ParseMode.MARKDOWN)


updater = Updater(botTOKEN, workers=8)

jobs = updater.job_queue
jobs.put(Job(autoSave, 60.0))
jobs.put(Job(reset, 86400.0), next_t=timediff())

dp = updater.dispatcher

dp.add_handler(CommandHandler('start', helper))
dp.add_handler(CommandHandler('help', helper))
dp.add_handler(CommandHandler('adminF5sn', adminRefresh))
dp.add_handler(CommandHandler('admin', adminShell, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('pingsn', pingas))
dp.add_handler(CommandHandler('setsn', changeSpinName, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('countsn', spinCount))
dp.add_handler(CommandHandler('spinsn', doTheSpin))
dp.add_handler(MessageHandler(Filters.status_update, svcHandler))
dp.add_handler(MessageHandler(Filters.all, updateCache, allow_edited=True))

dp.add_error_handler(errorh)

loadAll()
logToChannel(updater.bot, "INFO", "Bot started")

updater.start_polling()
updater.idle()

saveAll()
logToChannel(updater.bot, "INFO", "Bot stopped")

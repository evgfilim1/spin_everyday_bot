from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async
import logging
import core
import config

TIME_FORMAT = "%d %b, %H:%M:%S"
LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt=TIME_FORMAT)

# chatUsers = {}
# spinName = {}
# canChangeSN = {}
# results = {}

chatUsers, spinName, canChangeSN, results = core.load_all()


def handle_error(bot, update, error):
    core.log_to_channel(bot, "WARNING", "The last update caused error!\n```\n{err}\n```".
                        format(err=error))


def reset(bot, job):
    results.clear()
    core.log_to_channel(bot, "INFO", "Reset done")


def auto_save(bot, job):
    core.save_all(chatUsers, spinName, canChangeSN, results)


def update_cache(bot, update):
    msg = core.get_message(update)
    user = msg.from_user
    if not core.is_private(msg.chat_id, user.id):
        chatUsers[msg.chat_id].update({user.id: core.get_name(user)})


def admin_shell(bot, update, args):
    msg = core.get_message(update)
    if msg.from_user.id == config.botCREATOR:
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


def svc_handler(bot, update):
    chat_id = update.message.chat_id
    to_id = update.message.migrate_to_chat_id
    if update.message.group_chat_created or \
            (bool(update.message.new_chat_member) and update.message.new_chat_member.id == core.botID):
        chatUsers[chat_id] = {}
        core.admins_refresh(canChangeSN, bot, chat_id)
    elif to_id != 0:
        chatUsers.update({to_id: chatUsers.get(chat_id)})
        chatUsers.pop(chat_id)
        spinName.update({to_id: spinName.get(chat_id)})
        spinName.pop(chat_id)
        canChangeSN.update({to_id: canChangeSN.get(chat_id)})
        canChangeSN.pop(chat_id)
        results.update({to_id: results.get(chat_id)})
        results.pop(chat_id)
    elif bool(update.message.left_chat_member) and update.message.left_chat_member.id == core.botID:
        chatUsers.pop(chat_id)
        spinName.pop(chat_id)
        canChangeSN.pop(chat_id)
        results.pop(chat_id)


def helper(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=config.helpText, parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=update.message.message_id)


def admin_refresh(bot, update):
    if core.is_private(update.message.chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    core.admins_refresh(canChangeSN, bot, update.message.chat_id)
    bot.sendMessage(chat_id=update.message.chat_id, text="Список админов обновлён",
                    reply_to_message_id=update.message.message_id)


def ping(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Ping? Pong!",
                    reply_to_message_id=update.message.message_id)


@run_async
def do_the_spin(bot, update):
    chat_id = update.message.chat_id
    if core.is_private(chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    s = core.fix_md(spinName.get(chat_id, config.defaultSpinName))
    p = results.get(chat_id, 0)
    if p != 0:
        bot.sendMessage(chat_id=chat_id, text=config.textAlready.format(s=s, n=p),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=update.message.message_id)
    else:
        p = core.fix_md(core.choose_random_user(chatUsers, results, chat_id))
        from time import sleep
        for t in config.texts:
            bot.sendMessage(chat_id=chat_id, text=t.format(s=s, n=p),
                            parse_mode=ParseMode.MARKDOWN)
            sleep(2)


def change_spin_name(bot, update, args):
    msg = core.get_message(update)

    if core.is_private(msg.chat_id, msg.from_user.id):
        bot.sendMessage(chat_id=msg.chat_id, text="Я не работаю в ЛС")
        return

    if core.can_change_name(canChangeSN, msg.chat_id, msg.from_user.id):
        spin_name = " ".join(args)
        if spin_name == "":
            spin_name = config.defaultSpinName
        spinName[msg.chat_id] = spin_name
        bot.sendMessage(chat_id=msg.chat_id, text="Текст розыгрыша изменён на *{} дня*".
                        format(spin_name), reply_to_message_id=msg.message_id,
                        parse_mode=ParseMode.MARKDOWN)
    else:
        return


def spin_count(bot, update):
    if core.is_private(update.message.chat_id, update.message.from_user.id):
        bot.sendMessage(chat_id=update.message.chat_id, text="Я не работаю в ЛС")
        return
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Кол-во людей, участвующих в розыгрыше: _{}_".format(
                        len(chatUsers[update.message.chat_id])
                    ), reply_to_message_id=update.message.message_id,
                    parse_mode=ParseMode.MARKDOWN)


updater = Updater(config.botTOKEN, workers=8)

jobs = updater.job_queue
jobs.put(Job(auto_save, 60.0))
jobs.put(Job(reset, 86400.0), next_t=core.time_diff())

dp = updater.dispatcher

dp.add_handler(CommandHandler('start', helper))
dp.add_handler(CommandHandler('help', helper))
dp.add_handler(CommandHandler('adminF5sn', admin_refresh))
dp.add_handler(CommandHandler('sudo', admin_shell, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('pingsn', ping))
dp.add_handler(CommandHandler('setsn', change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('countsn', spin_count))
dp.add_handler(CommandHandler('spinsn', do_the_spin))
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(MessageHandler(Filters.all, update_cache, allow_edited=True))

dp.add_error_handler(handle_error)

core.log_to_channel(updater.bot, "INFO", "Bot started")

updater.start_polling()
updater.idle()

core.save_all(chatUsers, spinName, canChangeSN, results)
core.log_to_channel(updater.bot, "INFO", "Bot stopped")

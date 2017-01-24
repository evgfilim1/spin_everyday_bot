import logging

from telegram import (Bot, Update, ParseMode, TelegramError,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import Updater, Job, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

import config
import core

TIME_FORMAT = "%d %b, %H:%M:%S"
LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt=TIME_FORMAT)

updater = Updater(config.BOT_TOKEN, workers=8)
jobs = updater.job_queue
dp = updater.dispatcher

StartKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="Написать боту", url="telegram.me/{}".format(updater.bot.username))]
])

chatUsers, spinName, canChangeSN, results = core.load_all()


def handle_error(bot: Bot, update: Update, error):
    core.log_to_channel(bot, "WARNING", f"The last update caused error!\n```\n{error}\n```")


def reset(bot: Bot, job: Job=None):
    results.clear()
    core.log_to_channel(bot, "INFO", "Reset done")


def auto_save(bot: Bot, job: Job):
    core.save_all(chatUsers, spinName, canChangeSN, results)


def update_cache(bot: Bot, update: Update):
    msg = core.get_message(update)
    user = msg.from_user
    if not core.is_private(msg.chat_id):
        chatUsers[msg.chat_id].update({user.id: core.get_name(user)})


@core.check_destination
def admin_shell(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    if msg.from_user.id == config.BOT_CREATOR:
        try:
            cmd = args.pop(0)
        except IndexError:
            return
        if cmd == "exec":
            exec(" ".join(args))
        elif cmd == "vardump":
            bot.sendMessage(chat_id=msg.chat_id, text="```\n{}\n```".format(
                eval(" ".join(args))
            ), parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg.message_id)
        else:
            return
    else:
        return


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    to_id = update.message.migrate_to_chat_id
    if update.message.group_chat_created or \
            (bool(update.message.new_chat_member) and update.message.new_chat_member.id == bot.id):
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
    elif bool(update.message.left_chat_member) and update.message.left_chat_member.id == bot.id:
        chatUsers.pop(chat_id)
        spinName.pop(chat_id)
        canChangeSN.pop(chat_id)
        results.pop(chat_id)


@core.check_destination
def helper(bot: Bot, update: Update):
    try:
        bot.sendMessage(chat_id=update.message.from_user.id, text=config.HELP_TEXT,
                        parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        bot.sendMessage(chat_id=update.message.chat_id, text=config.PM_ONLY_MESSAGE,
                        reply_markup=StartKeyboard, reply_to_message_id=update.message.message_id)


@core.not_pm
@core.check_destination
def admin_refresh(bot: Bot, update: Update):
    core.admins_refresh(canChangeSN, bot, update.message.chat_id)
    bot.sendMessage(chat_id=update.message.chat_id, text="Список админов обновлён",
                    reply_to_message_id=update.message.message_id)


@core.check_destination
def ping(bot: Bot, update: Update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Ping? Pong!",
                    reply_to_message_id=update.message.message_id)


@run_async
@core.not_pm
@core.check_destination
def do_the_spin(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    s = core.fix_md(spinName.get(chat_id, config.DEFAULT_SPIN_NAME))
    p = results.get(chat_id, 0)
    if p != 0:
        bot.sendMessage(chat_id=chat_id, text=config.TEXT_ALREADY.format(s=s, n=p),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=update.message.message_id)
    else:
        p = core.fix_md(core.choose_random_user(chatUsers, results, chat_id))
        from time import sleep
        for t in config.TEXTS:
            bot.sendMessage(chat_id=chat_id, text=t.format(s=s, n=p),
                            parse_mode=ParseMode.MARKDOWN)
            sleep(2)


@core.not_pm
@core.check_destination
def change_spin_name(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    if core.can_change_name(canChangeSN, msg.chat_id, msg.from_user.id):
        spin_name = " ".join(args)
        if spin_name == "":
            spin_name = config.DEFAULT_SPIN_NAME
        spinName[msg.chat_id] = spin_name
        bot.sendMessage(chat_id=msg.chat_id, text=f"Текст розыгрыша изменён на *{spin_name} дня*",
                        reply_to_message_id=msg.message_id, parse_mode=ParseMode.MARKDOWN)
    else:
        return


@core.not_pm
@core.check_destination
def spin_count(bot: Bot, update: Update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Кол-во людей, участвующих в розыгрыше: _{}_".format(
                        len(chatUsers[update.message.chat_id])
                    ), reply_to_message_id=update.message.message_id,
                    parse_mode=ParseMode.MARKDOWN)


jobs.put(Job(auto_save, 60.0))
jobs.put(Job(reset, 86400.0), next_t=core.time_diff())

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

updater.start_polling(clean=True)
updater.idle()

core.save_all(chatUsers, spinName, canChangeSN, results)
core.log_to_channel(updater.bot, "INFO", "Bot stopped")

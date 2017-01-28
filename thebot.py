!#/usr/bin/python3
#again depends on PM

import logging

from telegram import (Bot, Update, ParseMode, TelegramError,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import Updater, Job, CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from random import choice

import config
import core

TIME_FORMAT = "%d %b, %H:%M:%S"
LOG_FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt=TIME_FORMAT)

updater = Updater(config.BOT_TOKEN, workers=config.WORKERS)
jobs = updater.job_queue
dp = updater.dispatcher

START_KEYBOARD = InlineKeyboardMarkup([[ InlineKeyboardButton( text="Написать боту", url="telegram.me/{}".format(updater.bot.username) ) ]])

chat_users, spin_name, can_change_name, results = core.load_all()


def handle_error(bot: Bot, update: Update, error):
    core.log_to_channel(bot, "WARNING", f"The last update caused error!\n```\n{error}\n```") # n0w fud1gn' 3ng m8


def reset(bot: Bot, job: Job=None):
    results.clear()
    core.log_to_channel(bot, "INFO", "Reset done")


def auto_save(bot: Bot, job: Job):
    core.save_all(chat_users, spin_name, can_change_name, results)


def update_cache(bot: Bot, update: Update):
    msg = core.get_message(update)
    user = msg.from_user
    if not core.is_private(msg.chat_id):
        chat_users[msg.chat_id].update({user.id: core.get_name(user)})


@core.check_destination
@core.is_admin
def admin_shell(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    try:
        cmd = args.pop(0)
    except IndexError:
        return
    if cmd == "exec":
        exec(" ".join(args))
    elif cmd == "vardump":
        bot.send_message(chat_id=msg.chat_id, text="```\n{}\n```".format(eval(" ".join(args))), 
                         parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg.message_id)
    elif cmd == "reset":
        reset(bot, None)


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_member = update.message.new_chat_member
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or (bool(new_member) and new_member.id == bot.id):
        chat_users[chat_id] = {}
        core.admins_refresh(can_change_name, bot, chat_id)
    elif bool(new_member):
        if bool(new_member.username) and new_member.username[-3:] == "bot":
            return
        chat_users[chat_id].update({new_member.id: core.get_name(new_member)})
    elif migrate_to_id != 0: # function mb?
        chat_users.update({migrate_to_id: chat_users.get(chat_id)})
        spin_name.update({migrate_to_id: spin_name.get(chat_id)})
        can_change_name.update({migrate_to_id: can_change_name.get(chat_id)})
        results.update({migrate_to_id: results.get(chat_id)})
        core.clear_data(chat_id, chat_users, spin_name, can_change_name, results)
    elif bool(left_member) and left_member.id == bot.id:
        core.clear_data(chat_id, chat_users, spin_name, can_change_name, results)
    elif bool(left_member):
        chat_users[chat_id].pop(left_member.id)


@core.check_destination
def helper(bot: Bot, update: Update):
    try:
        bot.send_message(chat_id=update.message.from_user.id, text=config.HELP_TEXT,
                         parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        update.message.reply_text(text=config.PM_ONLY_MESSAGE, reply_markup=START_KEYBOARD)


@core.not_pm
@core.check_destination
def admin_refresh(bot: Bot, update: Update):
    core.admins_refresh(can_change_name, bot, update.message.chat_id)
    update.message.reply_text(text="Список админов обновлён")


@core.check_destination
def ping(bot: Bot, update: Update):
    update.message.reply_text(text="Pong! Pong! Pong! Pong! Bot in da fudgin\\' house m8!")


@run_async
@core.not_pm
@core.check_destination
def do_the_spin(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    s = core.fix_md(spin_name.get(chat_id, config.DEFAULT_SPIN_NAME))
    p = results.get(chat_id)
    if p is not None:
        bot.send_message(chat_id=chat_id, text=config.TEXT_ALREADY.format(s=s, n=p),
                         parse_mode=ParseMode.MARKDOWN)
    else:
        p = core.fix_md(core.choose_random_user(chat_users, results, chat_id, bot))
        from time import sleep
        curr_text = choice(config.TEXTS)
        for t in curr_text:
            bot.send_message(chat_id=chat_id, text=t.format(s=s, n=p),
                             parse_mode=ParseMode.MARKDOWN)
            sleep(2)


@core.not_pm
@core.check_destination
def change_spin_name(bot: Bot, update: Update, args: list):
    msg = core.get_message(update) #why fudg1n' upd4t3s m8!?
    if core.can_change_name(can_change_name, msg.chat_id, msg.from_user.id):
        spin = " ".join(args)
        if spin == None:
            spin = config.DEFAULT_SPIN_NAME
        spin_name[msg.chat_id] = spin
        msg.reply_text(text=f"Текст розыгрыша изменён на *{spin} дня*", parse_mode=ParseMode.MARKDOWN)
    else:
        return


@core.not_pm
@core.check_destination
def spin_count(bot: Bot, update: Update):
    update.message.reply_text(text="Кол-во людей, участвующих в розыгрыше: _{}_".format(len(chat_users[update.message.chat_id])),
                              parse_mode=ParseMode.MARKDOWN)


jobs.put(Job(auto_save, 60.0))
jobs.put(Job(reset, 86400.0), next_t=core.time_diff())

#handler hell
dp.add_handler(CommandHandler('start', helper))
dp.add_handler(CommandHandler('help', helper))
dp.add_handler(CommandHandler('adminF5sn', admin_refresh))
dp.add_handler(CommandHandler('sudo', admin_shell, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('pingsn', ping))
dp.add_handler(CommandHandler('setsn', change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('countsn', spin_count))
dp.add_handler(CommandHandler('spinsn', do_the_spin))
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(MessageHandler(Filters.all, update_cache, allow_edited=True), group=-1)

dp.add_error_handler(handle_error)

core.log_to_channel(updater.bot, "INFO", "Bot started")

updater.start_polling(clean=True)
updater.idle()

core.save_all(chat_users, spin_name, can_change_name, results)
core.log_to_channel(updater.bot, "INFO", "Bot stopped")

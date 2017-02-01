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

updater = Updater(config.BOT_TOKEN, workers=8)
jobs = updater.job_queue
dp = updater.dispatcher

START_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="Написать боту", url="telegram.me/{}".format(updater.bot.username))]
])

locks = []


def handle_error(bot: Bot, update: Update, error):
    core.log_to_channel(bot, "WARNING", f"The last update caused error!\n```\n{error}\n```")


def reset(bot: Bot, job: Job=None):
    core.results_today.clear()
    core.log_to_channel(bot, "INFO", "Reset done")


def auto_save(bot: Bot, job: Job):
    core.save_all()


def update_cache(bot: Bot, update: Update):
    msg = core.get_message(update)
    user = msg.from_user
    if not core.is_private(msg.chat_id):
        core.chat_users[msg.chat_id].update({user.id: core.get_name(user)})


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
            bot.send_message(chat_id=msg.chat_id, text="```\n{}\n```".format(
                eval(" ".join(args))
            ), parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg.message_id)
        elif cmd == "reset":
            reset(bot, None)
        elif cmd == "respin":
            core.results_today.pop(msg.chat_id)
            msg.reply_text("respin ok")
        elif cmd == "md_announce":
            core.announce(bot, " ".join(args), md=True)
        elif cmd == "announce":
            core.announce(bot, " ".join(args))


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_member = update.message.new_chat_member
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or (bool(new_member) and new_member.id == bot.id):
        core.chat_users[chat_id] = {}
        core.admins_refresh(bot, chat_id)
    elif bool(new_member):
        if bool(new_member.username) and new_member.username[-3:] == "bot":
            return
        core.chat_users[chat_id].update({new_member.id: core.get_name(new_member)})
    elif migrate_to_id != 0:
        core.migrate(chat_id, migrate_to_id)
    elif bool(left_member) and left_member.id == bot.id:
        core.clear_data(chat_id)
    elif bool(left_member):
        core.chat_users[chat_id].pop(left_member.id)


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
    core.admins_refresh(bot, update.message.chat_id)
    update.message.reply_text(text="Список админов обновлён")


@core.check_destination
def ping(bot: Bot, update: Update):
    update.message.reply_text(text="Ping? Pong!")


@run_async
@core.not_pm
@core.check_destination
def do_the_spin(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    s = core.fix_md(core.spin_name.get(chat_id, config.DEFAULT_SPIN_NAME))
    p = core.results_today.get(chat_id)
    if chat_id in locks:
        return
    if p is not None:
        bot.send_message(chat_id=chat_id, text=config.TEXT_ALREADY.format(s=s, n=p),
                         parse_mode=ParseMode.MARKDOWN)
    else:
        p = core.fix_md(core.choose_random_user(chat_id, bot))
        from time import sleep
        curr_text = choice(config.TEXTS)
        locks.append(chat_id)
        for t in curr_text:
            bot.send_message(chat_id=chat_id, text=t.format(s=s, n=p),
                             parse_mode=ParseMode.MARKDOWN)
            sleep(2)
        locks.pop(locks.index(chat_id))


def top(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    if chat_id in locks:
        return
    text = "Статистика пользователей в данном чате: (первые 10 человек)\n"
    for user in core.top_win(chat_id)[:10]:
        username = core.chat_users[chat_id].get(user[0], f"id{user[0]}")
        text += f"*{username}*: {user[1]} раз(а)\n"
    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN)


@core.not_pm
@core.check_destination
def change_spin_name(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    if core.can_change_name(msg.chat_id, msg.from_user.id):
        spin = " ".join(args)
        if spin == "":
            spin = core.spin_name.get(msg.chat_id, config.DEFAULT_SPIN_NAME)
            msg.reply_text(text=f"Текущее название розыгрыша: *{spin} дня*", parse_mode=ParseMode.MARKDOWN)
        else:
            core.spin_name[msg.chat_id] = spin
            msg.reply_text(text=f"Текст розыгрыша изменён на *{spin} дня*", parse_mode=ParseMode.MARKDOWN)
    else:
        return


@core.not_pm
@core.check_destination
def spin_count(bot: Bot, update: Update):
    update.message.reply_text(text="Кол-во людей, участвующих в розыгрыше: _{}_".format(
                                  len(core.chat_users[update.message.chat_id])
                              ), parse_mode=ParseMode.MARKDOWN)


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
dp.add_handler(CommandHandler('topsn', top))
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(MessageHandler(Filters.all, update_cache, allow_edited=True), group=-1)

dp.add_error_handler(handle_error)

updater.start_polling(clean=True)
core.log_to_channel(updater.bot, "INFO", "Bot started")
updater.idle()

core.save_all()
core.log_to_channel(updater.bot, "INFO", "Bot stopped")

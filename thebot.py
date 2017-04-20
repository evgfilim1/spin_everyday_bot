# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import logging

from telegram import (Bot, Update, ParseMode, TelegramError,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, Job, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters, JobQueue)
from telegram.ext.dispatcher import run_async

from random import choice

import config
import core

# Set all logging time in UTC
logging.Formatter.converter = __import__("time").gmtime

updater = Updater(config.BOT_TOKEN, workers=8)
jobs = updater.job_queue
dp = updater.dispatcher

START_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton(text="Написать боту", url="t.me/{}".format(updater.bot.username))]
])

locks = []

tg_handler = core.TelegramHandler(updater.bot)
tg_handler.setFormatter(logging.Formatter(config.LOG_TG_FORMAT, style='{'))

log = logging.getLogger('bot')
log.addHandler(core.handler)
log.addHandler(tg_handler)
log.setLevel(logging.DEBUG)

# Just configure loggers below and don't use them
tg_log = logging.getLogger('telegram.ext')
tg_log.addHandler(core.handler)
tg_log.addHandler(tg_handler)
tg_log.setLevel(logging.INFO)

sock_log = logging.getLogger('TeleSocket')
sock_log.addHandler(core.handler)
sock_log.addHandler(tg_handler)
sock_log.setLevel(logging.INFO)
del tg_handler, tg_log, sock_log


def handle_error(bot: Bot, update: Update, error):
    log.error(f"Update {update} caused error: {error}")


def reset(bot: Bot, job: Job = None):
    core.results_today.clear()
    log.debug("Reset done")


def auto_save(bot: Bot, job: Job):
    core.save_all()


def auto_spin(bot: Bot, job: Job):
    from telegram import Message, Chat, User
    u = Update(0, message=Message(0, User(0, ''), 0, Chat(job.context, ''), text='/spin'))
    if core.results_today.get(job.context) is None:
        do_the_spin(bot, u)


def update_cache(bot: Bot, update: Update):
    msg = core.get_message(update)
    user = msg.from_user
    # Also skip first update when the bot is added
    if not core.is_private(msg.chat_id) and core.chat_users.get(msg.chat_id) is not None:
        core.chat_users[msg.chat_id].update({user.id: core.get_name(user)})


def pages_handler(bot: Bot, update: Update):
    query = update.callback_query
    data = query.data.split(':')[1]
    msg = query.message

    if msg.chat_id in locks:
        query.answer("Нельзя использовать кнопки, пока идёт розыгрыш")
        return

    page_n = int(data.split('_')[1])
    text, max_pages = core.make_top(msg.chat_id, page=page_n)
    reply_keyboard = [[]]
    if page_n != 1:
        reply_keyboard[0].append(InlineKeyboardButton("<<", callback_data=f"top:page_{page_n - 1}"))
    if page_n != max_pages:
        reply_keyboard[0].append(InlineKeyboardButton(">>", callback_data=f"top:page_{page_n + 1}"))
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(reply_keyboard),
                                parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        pass


def help_button_handler(bot: Bot, update: Update):
    query = update.callback_query
    data = query.data.split(':')[1]

    keys = []
    for key in config.HELP_TEXT[data][1]:
        key = key.split('%')
        keys.append([InlineKeyboardButton(text=key[0], callback_data=f"help:{key[1]}")])
    try:
        query.edit_message_text(config.HELP_TEXT[data][0], reply_markup=InlineKeyboardMarkup(keys),
                                parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        pass


@core.check_destination
def admin_shell(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    if msg.from_user.id != config.BOT_CREATOR:
        log.warning(f"Attempted to use '{msg.text}' by {core.get_name(msg.from_user)}")
        return

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
        log.info(f"Respin done in '{msg.chat.title}' ({msg.chat_id})")
        core.results_today.pop(msg.chat_id)
        msg.reply_text("respin ok")
    elif cmd == "md_announce":
        core.announce(bot, " ".join(args), md=True)
    elif cmd == "announce":
        core.announce(bot, " ".join(args))
    elif cmd == "sendlogs":
        if config.LOG_FILE is None:
            msg.reply_text("Logging to file is not configured.")
            return
        with open(config.LOG_FILE, 'rb') as f:
            msg.reply_document(f)
    elif cmd == "help":
        msg.reply_text("Help:\nexec — execute code\nvardump — print variable's value\n"
                       "reset — reset all spins\nrespin — reset spin in this chat\n"
                       "md_announce — tell something to all chats (markdown is on)\n"
                       "announce — tell something to all chats (markdown is off)\n"
                       "sendlogs — send latest logs as document")


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_member = update.message.new_chat_member
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or (bool(new_member) and new_member.id == bot.id):
        # TODO: add admins to the list
        log.info(f"New chat! ({chat_id})")
        core.chat_users[chat_id] = {}
        core.can_change_name[chat_id] = []
    elif bool(new_member):
        if bool(new_member.username) and new_member.username[-3:].lower() == "bot":
            return
        core.chat_users[chat_id].update({new_member.id: core.get_name(new_member)})
    elif migrate_to_id != 0:
        core.migrate(chat_id, migrate_to_id)
    elif bool(left_member) and left_member.id == bot.id:
        core.clear_data(chat_id)
    elif bool(left_member):
        try:
            core.chat_users[chat_id].pop(left_member.id)
        except KeyError:
            # Passing this because of bots and unknown users
            pass


@core.check_destination
def helper(bot: Bot, update: Update):
    keys = []
    for key in config.HELP_TEXT["main"][1]:
        key = key.split('%')
        keys.append([InlineKeyboardButton(text=key[0], callback_data=f"help:{key[1]}")])

    try:
        bot.send_message(chat_id=update.message.from_user.id, text=config.HELP_TEXT["main"][0],
                         parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keys))
    except TelegramError:
        update.message.reply_text(text=config.PM_ONLY_MESSAGE, reply_markup=START_KEYBOARD)


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


@core.not_pm
@core.check_destination
def auto_spin_config(bot: Bot, update: Update, args: list, job_queue: JobQueue):
    msg = core.get_message(update)
    if len(args) == 0:
        return
    is_moder = core.can_change_spin_name(msg.chat_id, msg.from_user.id, bot)
    cmd = args.pop(0)
    if cmd == "set" and is_moder:
        try:
            time = args[0].split(':')
            time = "{:0>2}:{:0>2}".format(time[0], time[1])
            job = Job(auto_spin, 86400.0, context=msg.chat_id)
            job_queue.put(job, next_t=core.time_diff(time))
            if msg.chat_id in core.auto_spins:
                core.auto_spin_jobs[msg.chat_id].schedule_removal()
        except (ValueError, IndexError):
            msg.reply_text(f"Ошибка! Проверьте время на правильность и отредактируйте сообщение")
            return

        core.auto_spins.update({msg.chat_id: time})
        core.auto_spin_jobs.update({msg.chat_id: job})
        msg.reply_text(f"Автоматический розыгрыш установлен на {time} GMT+0\n\n"
                       f"ВНИМАНИЕ! Если розыгрыш уже был проведён до того, как запустится автоматический розыгрыш, то"
                       f" бот не напишет ничего в чат по наступлению времени розыгрыша")
    elif cmd == 'del' and is_moder:
        if msg.chat_id in core.auto_spins:
            core.auto_spin_jobs.pop(msg.chat_id).schedule_removal()
            core.auto_spins.pop(msg.chat_id)
            msg.reply_text("Теперь автоматический розыгрыш отключен в этом чате")
        else:
            msg.reply_text("Автоматический розыгрыш ещё не был включен в этом чате")
    elif cmd == 'status':
        if msg.chat_id in core.auto_spins:
            msg.reply_text(f"Автоматический розыгрыш установлен в этом чате"
                           f" на {core.auto_spins.get(msg.chat_id)} GMT+0")
        else:
            msg.reply_text("Автоматический розыгрыш отключен в этом чате")


@core.not_pm
@core.check_destination
def top(bot: Bot, update: Update, args: list):
    chat_id = update.message.chat_id
    reply_keyboard = [[]]
    if chat_id in locks:
        return
    if chat_id not in core.results_total:
        core.results_total[chat_id] = {}
    if len(args) == 1 and args[0] == "me":
        user = update.message.from_user
        username = core.get_name(user)
        stat = core.results_total[chat_id].get(user.id, 0)
        text = f"Ваша статистика:\n*{username}*: {stat} раз(а)"
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        username = core.get_name(user)
        stat = core.results_total[chat_id].get(user.id, 0)
        text = f"Статистика пользователя *{username}*: {stat} раз(а)"
    else:
        text, pages = core.make_top(chat_id, page=1)
        if pages > 1:
            reply_keyboard = [[InlineKeyboardButton(">>", callback_data="top:page_2")]]
    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=InlineKeyboardMarkup(reply_keyboard))


@core.not_pm
@core.check_destination
def change_spin_name(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    if len(args) == 0:
        spin = core.spin_name.get(msg.chat_id, config.DEFAULT_SPIN_NAME)
        msg.reply_text(text=f"Текущее название розыгрыша: *{spin} дня*", parse_mode=ParseMode.MARKDOWN)
        return
    if core.can_change_spin_name(msg.chat_id, msg.from_user.id, bot):
        if args[-1].lower() == "дня" and len(args) > 1:
            args.pop(-1)
        spin = " ".join(args)
        core.spin_name[msg.chat_id] = spin
        msg.reply_text(text=f"Текст розыгрыша изменён на *{spin} дня*", parse_mode=ParseMode.MARKDOWN)


@core.not_pm
@core.check_destination
def admin_ctrl(bot: Bot, update: Update, args: list):
    msg = core.get_message(update)
    reply = msg.reply_to_message
    admins = core.get_admins_ids(bot, msg.chat_id)
    admins.append(config.BOT_CREATOR)
    is_admin = msg.from_user.id in admins
    if len(args) == 0:
        return
    cmd = args.pop(0)
    if msg.chat_id not in core.can_change_name:
        core.can_change_name[msg.chat_id] = []
    if cmd == "add" and reply and is_admin:
        if core.can_change_spin_name(msg.chat_id, reply.from_user.id, bot):
            msg.reply_text(text="Этот пользователь *уже может* изменять название розыгрыша",
                           parse_mode=ParseMode.MARKDOWN)
        else:
            core.can_change_name[msg.chat_id].append(reply.from_user.id)
            msg.reply_text(text="Теперь этот пользователь *может* изменять название розыгрыша",
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == "del" and reply and is_admin:
        if not core.can_change_spin_name(msg.chat_id, reply.from_user.id, bot):
            msg.reply_text(text="Этот пользователь *ещё не может* изменять название розыгрыша",
                           parse_mode=ParseMode.MARKDOWN)
        else:
            index = core.can_change_name[msg.chat_id].index(reply.from_user.id)
            core.can_change_name[msg.chat_id].pop(index)
            msg.reply_text(text="Теперь этот пользователь *не может* изменять название розыгрыша",
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == "list":
        text = "Пользователи, которые *могут* изменять название розыгрыша (не считая администраторов):\n```\n"
        for user in core.can_change_name[msg.chat_id]:
            text += core.chat_users[msg.chat_id].get(user, f"id{user}") + '\n'
        text += "```"
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@core.not_pm
@core.check_destination
def spin_count(bot: Bot, update: Update):
    update.message.reply_text(text=f"Кол-во людей, участвующих в розыгрыше: "
                                   f"_{len(core.chat_users[update.message.chat_id])}_",
                              parse_mode=ParseMode.MARKDOWN)


jobs.put(Job(auto_save, 60.0))
jobs.put(Job(reset, 86400.0), next_t=core.time_diff())

dp.add_handler(CommandHandler('start', helper))
dp.add_handler(CommandHandler('help', helper))
dp.add_handler(CommandHandler('admgroup', admin_ctrl, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('sudo', admin_shell, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('ping', ping))
dp.add_handler(CommandHandler('setname', change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('count', spin_count))
dp.add_handler(CommandHandler('spin', do_the_spin))
dp.add_handler(CommandHandler('auto', auto_spin_config, pass_args=True, allow_edited=True,
                              pass_job_queue=True))
dp.add_handler(CommandHandler('stat', top, pass_args=True))
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(CallbackQueryHandler(pages_handler, pattern="^top:page_[1-9]+[0-9]*$"))
dp.add_handler(CallbackQueryHandler(help_button_handler, pattern="^help:.+$"))
dp.add_handler(MessageHandler(Filters.all, update_cache, allow_edited=True), group=-1)

dp.add_error_handler(handle_error)

core.init(bot=updater.bot, job_queue=updater.job_queue, callback=auto_spin)

if config.TELESOCKET_TOKEN:
    # TODO: clean old messages
    from TeleSocketClient import TeleSocket
    updater.bot.set_webhook()
    sock = TeleSocket()
    sock.login(config.TELESOCKET_TOKEN)
    sock.add_telegram_handler(lambda update: core.read_update(updater, update))
    webhook = sock.set_webhook(updater.bot.username)
    updater.bot.set_webhook(webhook_url=webhook.url)
    updater.job_queue.start()
    updater._init_thread(updater.dispatcher.start, "dispatcher")
    updater.running = True
else:
    updater.start_polling(clean=True)

log.info("Bot started")
updater.idle()

core.save_all()
log.info("Bot stopped")

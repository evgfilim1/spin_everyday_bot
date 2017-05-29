# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import logging

from telegram import (Bot, Update, ParseMode, TelegramError,
                      InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ReplyKeyboardRemove)
from telegram.ext import (Updater, Job, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters, JobQueue, ConversationHandler)
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

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
ALLOWED_UPDATES = ["message", "edited_message", "callback_query"]

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


def reset(bot: Bot = None, job: Job = None):
    core.results_today.clear()
    log.debug("Reset done")


def auto_save(bot: Bot = None, job: Job = None):
    core.save_all()


def auto_spin(bot: Bot, job: Job):
    from telegram import Message, Chat
    u = Update(0, message=Message(0, None, 0, Chat(job.context, '')))
    if core.results_today.get(job.context) is None:
        do_the_spin(bot, u)


def update_cache(bot: Bot, update: Update):
    user = update.effective_user
    chat_id = update.effective_message.chat_id
    # Also skip first update when the bot is added
    if not core.is_private(chat_id) and core.chat_users.get(chat_id) is not None:
        core.chat_users[chat_id].update({user.id: user.name})


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


def admin_shell(bot: Bot, update: Update, args: list):
    msg = update.effective_message
    if msg.from_user.id != config.BOT_CREATOR:
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
    elif cmd == "delete":
        if len(args) == 0:
            msg.reply_to_message.delete()
        else:
            params = args.pop(0).split('_')
            if params[0] == "current":
                params[0] = msg.chat_id
            bot.delete_message(chat_id=params[0], message_id=params[1])
    elif cmd == "count":
        msg.reply_text(f"Чатов у бота: {len(core.chat_users)}")
    elif cmd == "send" or cmd == "edit":
        params = args.pop(0)
        text = " ".join(args).replace("\\n", "\n")
        params = params.split("_")
        chat = params[0]
        if chat == "current":
            chat = msg.chat_id
        try:
            msg_id = params[1]
            assert msg_id != ""
        except (KeyError, AssertionError, IndexError):
            msg_id = None
        try:
            parse_mode = params[2]
        except (KeyError, IndexError):
            parse_mode = None
        del params
        if cmd == "send":
            new_msg = bot.send_message(chat, text, parse_mode=parse_mode, reply_to_message_id=msg_id)
            msg.reply_text(f"Sent message ID: {new_msg.message_id}")
        elif cmd == "edit":
            bot.edit_message_text(chat_id=chat, text=text, parse_mode=parse_mode, message_id=msg_id)
    elif cmd == "help":
        msg.reply_text("Help:\nexec — execute code\nvardump — print variable's value\n"
                       "delete [<chat>_<msgid>] - delete replied or specified message\n"
                       "send <chat>_<msgid>_<parsemode> - send message\n"
                       "edit <chat>_<msgid>_<parsemode> - edit message\n"
                       "reset — reset all spins\nrespin — reset spin in this chat\n"
                       "md_announce <text> — tell something to all chats (markdown is on)\n"
                       "announce <text> — tell something to all chats (markdown is off)\n"
                       "count - count known chats\nsendlogs — send latest logs as document")


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_members = update.message.new_chat_members
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or \
            (len(new_members) != 0 and any(new_member.id == bot.id for new_member in new_members)):
        # TODO: add admins to the list
        log.info(f"New chat! ({chat_id})")
        core.chat_users[chat_id] = {}
        core.can_change_name[chat_id] = []
    elif new_members:
        for new_member in new_members:
            if new_member.username and new_member.username[-3:].lower() == "bot":
                return
            core.chat_users[chat_id].update({new_member.id: new_member.name})
    elif migrate_to_id:
        core.migrate(chat_id, migrate_to_id)
    elif left_member and left_member.id == bot.id:
        core.clear_data(chat_id)
    elif left_member:
        try:
            core.chat_users[chat_id].pop(left_member.id)
        except KeyError:
            # Passing this because of bots and unknown users
            pass


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


def ping(bot: Bot, update: Update):
    update.message.reply_text(text="Ping? Pong!")


@run_async
@core.not_pm
def do_the_spin(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    s = escape_markdown(core.spin_name.get(chat_id, config.DEFAULT_SPIN_NAME))
    p = core.results_today.get(chat_id)
    if chat_id in locks:
        return
    if p is not None:
        bot.send_message(chat_id=chat_id, text=config.TEXT_ALREADY.format(s=s, n=p),
                         parse_mode=ParseMode.MARKDOWN)
    else:
        p = escape_markdown(core.choose_random_user(chat_id, bot))
        from time import sleep
        curr_text = choice(config.TEXTS)
        locks.append(chat_id)
        for t in curr_text:
            bot.send_message(chat_id=chat_id, text=t.format(s=s, n=p),
                             parse_mode=ParseMode.MARKDOWN)
            sleep(2)
        locks.pop(locks.index(chat_id))


@core.not_pm
def auto_spin_config(bot: Bot, update: Update, args: list, job_queue: JobQueue):
    msg = update.effective_message
    if len(args) == 0:
        return
    is_moder = core.can_change_spin_name(msg.chat_id, msg.from_user.id, bot)
    cmd = args.pop(0)
    if cmd == "set" and is_moder:
        try:
            time = args[0].split(':')
            time = "{:0>2}:{:0>2}".format(time[0], time[1])
            job = job_queue.run_daily(auto_spin, core.str_to_time(time), context=msg.chat_id)
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
def top(bot: Bot, update: Update, args: list):
    chat_id = update.message.chat_id
    reply_keyboard = [[]]
    if chat_id in locks:
        return
    if chat_id not in core.results_total:
        core.results_total[chat_id] = {}
    if len(args) == 1 and args[0] == "me":
        user = update.message.from_user
        username = user.name
        stat = core.results_total[chat_id].get(user.id, 0)
        text = f"Ваша статистика:\n*{username}*: {stat} раз(а)"
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        username = user.name
        stat = core.results_total[chat_id].get(user.id, 0)
        text = f"Статистика пользователя *{username}*: {stat} раз(а)"
    else:
        text, pages = core.make_top(chat_id, page=1)
        if pages > 1:
            reply_keyboard = [[InlineKeyboardButton(">>", callback_data="top:page_2")]]
    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=InlineKeyboardMarkup(reply_keyboard))


@core.not_pm
def change_spin_name(bot: Bot, update: Update, args: list):
    msg = update.effective_message
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
def admin_ctrl(bot: Bot, update: Update, args: list):
    msg = update.effective_message
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
def spin_count(bot: Bot, update: Update):
    update.message.reply_text(text=f"Кол-во людей, участвующих в розыгрыше: "
                                   f"_{len(core.chat_users[update.message.chat_id])}_",
                              parse_mode=ParseMode.MARKDOWN)


def ask_feedback(bot: Bot, update: Update):
    update.message.reply_text("Введите сообщение, которое будет отправлено создателю бота\n"
                              "Бот принимает текст, изображения и документы\n"
                              "Введите /cancel для отмены", reply_markup=ForceReply(selective=True))
    return 0


def send_feedback(bot: Bot, update: Update):
    if update.message.reply_to_message.from_user.id != bot.id:
        return
    bot.send_message(config.BOT_CREATOR, f"<b>Новое сообщение!</b>\n"
                                         f" - <i>Чат:</i> <pre>{update.message.chat}</pre>\n"
                                         f" - <i>Пользователь:</i> <pre>{update.message.from_user}</pre>\n"
                                         f" - <i>ID Сообщения:</i> <pre>{update.message.message_id}</pre>",
                     parse_mode=ParseMode.HTML)
    update.message.forward(config.BOT_CREATOR)
    update.message.reply_text("Ваше сообщение отправлено!", reply_markup=ReplyKeyboardRemove(selective=True))
    return ConversationHandler.END


def cancel_feedback(bot: Bot, update: Update):
    update.message.reply_text("Отменено", reply_markup=ReplyKeyboardRemove(selective=True))
    return ConversationHandler.END


jobs.run_repeating(auto_save, 60)
jobs.run_daily(reset, core.str_to_time(config.RESET_TIME))

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler('feedback', ask_feedback)],
    states={
        0: [MessageHandler(Filters.reply & (Filters.text | Filters.photo | Filters.document), send_feedback)]
    },
    fallbacks=[CommandHandler('cancel', cancel_feedback)]
)

dp.add_handler(CommandHandler(['start', 'help'], helper))
dp.add_handler(CommandHandler('admgroup', admin_ctrl, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('sudo', admin_shell, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('ping', ping))
dp.add_handler(CommandHandler('setname', change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('count', spin_count))
dp.add_handler(CommandHandler('spin', do_the_spin))
dp.add_handler(CommandHandler('auto', auto_spin_config, pass_args=True, allow_edited=True,
                              pass_job_queue=True))
dp.add_handler(CommandHandler('stat', top, pass_args=True))
dp.add_handler(feedback_handler)
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(CallbackQueryHandler(pages_handler, pattern=r"^top:page_[1-9]+[0-9]*$"))
dp.add_handler(CallbackQueryHandler(help_button_handler, pattern=r"^help:.+$"))
dp.add_handler(MessageHandler(Filters.all, update_cache, edited_updates=True), group=-1)

dp.add_error_handler(handle_error)

core.init(bot=updater.bot, job_queue=updater.job_queue, callback=auto_spin)

if config.TELESOCKET_TOKEN:
    from TeleSocketClient import TeleSocket
    updater.bot.set_webhook()
    sock = TeleSocket()
    sock.login(config.TELESOCKET_TOKEN)
    sock.add_telegram_handler(lambda update: core.read_update(updater, update))
    webhook = sock.set_webhook(updater.bot.username)
    updater._clean_updates()
    updater.bot.set_webhook(url=webhook.url, allowed_updates=ALLOWED_UPDATES)
    updater.job_queue.start()
    updater._init_thread(updater.dispatcher.start, "dispatcher")
    updater.running = True
else:
    updater.start_polling(clean=True, allowed_updates=ALLOWED_UPDATES)

log.info("Bot started")
updater.idle()

core.save_all()
log.info("Bot stopped")

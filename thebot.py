# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import logging
import re

from telegram import (Bot, Update, ParseMode, TelegramError,
                      InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ReplyKeyboardRemove)
from telegram.ext import (Updater, Job, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters, JobQueue, ConversationHandler)
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

from random import choice
from datetime import datetime
from subprocess import check_output

import config
import core

# Set all logging time in UTC
logging.Formatter.converter = __import__("time").gmtime

updater = Updater(config.BOT_TOKEN, workers=8)
jobs = updater.job_queue
dp = updater.dispatcher

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
    if config.SHOW_ERRORS:
        update.effective_message.reply_text(core.get_lang(update.effective_chat.id, 'error'))


def daily_job(bot: Bot, job: Job = None):
    core.results_today.clear()
    log.debug("Reset done")
    try:
        uid = core.choose_random_user(0, bot)
        text = choice(core.get_lang(uid, 'default_spin_texts'))[-1]
        bot.send_message(uid, text.format(s=core.get_lang(uid, 'wotd'), n=core.usernames.get(uid)),
                         parse_mode=ParseMode.MARKDOWN)
    except (TelegramError, IndexError):
        pass
    log.debug("Daily spin done")


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
        if user.id not in core.chat_users[chat_id]:
            core.chat_users[chat_id].append(user.id)
        if user.name != core.usernames.get(user.id):
            core.usernames.update({user.id: user.name})


def pages_handler(bot: Bot, update: Update):
    query = update.callback_query
    _type, data = query.data.split(':')
    msg = query.message
    page_n = int(data.split('_')[1])
    if _type == 'top':
        if msg.chat_id in locks:
            query.answer(core.get_lang(msg.chat_id, 'locked_buttons'))
            return
        text, max_pages = core.make_top(msg.chat_id, page=page_n)
    else:
        text, max_pages = core.make_userlist(msg.chat_id, page=page_n)

    reply_keyboard = [[]]
    if page_n != 1:
        reply_keyboard[0].append(InlineKeyboardButton("<<", callback_data=f"{_type}:page_{page_n - 1}"))
    if page_n != max_pages:
        reply_keyboard[0].append(InlineKeyboardButton(">>", callback_data=f"{_type}:page_{page_n + 1}"))
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(reply_keyboard),
                                parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        pass


def help_button_handler(bot: Bot, update: Update):
    query = update.callback_query
    data = query.data.split(':')[1]
    keys = []
    if data == 'main':
        text = core.get_lang(update.effective_chat.id, 'help_texts')['main'][0]
        for i, command in enumerate(core.get_lang(update.effective_chat.id, 'help_texts')['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))
    else:
        keys = [[
            InlineKeyboardButton(text=core.get_lang(update.effective_chat.id, 'helpbuttons_back'),
                                 callback_data='help:main')
        ]]
        command_info = core.get_lang(update.effective_chat.id, 'help_texts')['main'][1][data]

        text = '`/{0}` - {1}\n\n'.format(data, command_info['summary'])
        text += core.get_lang(update.effective_chat.id, 'help_usage') + '\n'
        for suffix, suffix_info in command_info['usage'].items():
            if suffix != '':
                suffix = ' ' + suffix
            text += f'/{data}{suffix} - {suffix_info["text"]} '
            if suffix_info.get('reply', False):
                text += core.get_lang(update.effective_chat.id, 'help_onlyreply') + ' '
            if suffix_info.get('admin', False):
                text += core.get_lang(update.effective_chat.id, 'help_onlyadmin')
            text += '\n'
    try:
        query.edit_message_text(reply_markup=InlineKeyboardMarkup(keys), parse_mode=ParseMode.MARKDOWN, text=text)
    except TelegramError:
        pass


def admin_shell(bot: Bot, update: Update, args: list):
    msg = update.effective_message
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
        daily_job(bot, None)
    elif cmd == "respin":
        if len(args) > 0:
            chat = int(args[0])
        else:
            chat = msg.chat_id
        core.results_today.pop(chat)
        log.info(f"Respin done in {chat}")
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
        msg.reply_text(f"Bot has {len(core.chat_users)} chats")
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
        msg.reply_text("Help:\n- exec <code> — execute code\n- vardump <variable> — print variable's value\n"
                       "- delete [<chat>_<msgid>] - delete replied or specified message\n"
                       "- send <chat>_<msgid>_<parsemode> - send message\n"
                       "- edit <chat>_<msgid>_<parsemode> - edit message\n"
                       "- reset — reset all spins\n- respin [chat] — reset spin in this or specified chat\n"
                       "- md_announce <text> — tell something to all chats (markdown is on)\n"
                       "- announce <text> — tell something to all chats (markdown is off)\n"
                       "- count - count known chats\n- sendlogs — send latest logs as document")


def svc_handler(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_members = update.message.new_chat_members
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or \
            (len(new_members) != 0 and any(new_member.id == bot.id for new_member in new_members)):
        # TODO: add admins to the list
        log.info(f"New chat! ({chat_id})")
        core.chat_users[chat_id] = []
        core.can_change_name[chat_id] = []
        start_help_handler(bot, update, [])
    elif new_members:
        for new_member in new_members:
            if new_member.is_bot:
                return
            if new_member.id not in core.chat_users[chat_id]:
                core.chat_users[chat_id].append(new_member.id)
            core.usernames.update({new_member.id: new_member.name})
    elif migrate_to_id:
        core.migrate(chat_id, migrate_to_id)
    elif left_member and left_member.id == bot.id:
        core.clear_data(chat_id)
    elif left_member:
        if left_member.is_bot:
            return
        try:
            core.chat_users[chat_id].pop(core.chat_users[chat_id].index(left_member.id))
        except KeyError:
            # Passing this because of unknown users
            pass


def helper(bot: Bot, update: Update, short: bool):
    chat_id = update.effective_chat.id
    keys = []
    if short:
        text = core.get_lang(chat_id, 'help_short')
        if not core.is_private(chat_id):
            text += core.get_lang(chat_id, 'help_moreinfo_chat')
            keys.append([InlineKeyboardButton(core.get_lang(chat_id, 'start_pm_button'),
                                              url=f't.me/{bot.username}?start=help')])
        else:
            text += core.get_lang(chat_id, 'help_moreinfo_pm')
    else:
        text = core.get_lang(chat_id, 'help_texts')['main'][0]
        for i, command in enumerate(core.get_lang(chat_id, 'help_texts')['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))

    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keys))


def start_help_handler(bot: Bot, update: Update, args: list):
    if (len(args) > 0 and args[0] == 'help') or (core.is_private(update.message.chat_id) and
                                                 not update.message.text.startswith('/start')):
        helper(bot, update, short=False)
    else:
        helper(bot, update, short=True)


def ping(bot: Bot, update: Update):
    update.message.reply_text(text="Ping? Pong!")


def about(bot: Bot, update: Update):
    git_version = check_output('git describe --tags', shell=True)[:-1].decode()
    version = re.sub(r'-(\d+)-g([a-z0-9]{7})', r'.r\1.\2', git_version)
    update.message.reply_text(core.get_lang(update.effective_chat.id, 'about_text').format(
        version, f'@{bot.get_chat(config.BOT_CREATOR).username}', config.REPO_URL
    ), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)


@core.not_pm
def do_the_spinn(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    spin_name = escape_markdown(core.spin_name.get(chat_id, core.get_lang(chat_id, 'default_spin_name')))
    winner = core.results_today.get(chat_id)
    if winner is None or chat_id in locks:
        return
    winner = update.message.from_user
    if not winner.name.startswith('@'):
        winner = core.mention_markdown(winner.id, winner.name)
    else:
        winner = escape_markdown(winner)
    bot.send_message(chat_id=chat_id,
                     text=core.get_lang(chat_id, 'already_spin').format(s=spin_name, n=winner),
                     parse_mode=ParseMode.MARKDOWN)


@run_async
@core.not_pm
def do_the_spin(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    spin_name = escape_markdown(core.spin_name.get(chat_id, core.get_lang(chat_id, 'default_spin_name')))
    winner = core.results_today.get(chat_id)
    if chat_id in locks:
        return
    if winner is not None:
        name = core.usernames.get(winner, f'id{winner}')
        if not name.startswith('@'):
            name = core.mention_markdown(winner, name)
        else:
            name = escape_markdown(name)
        bot.send_message(chat_id=chat_id, text=core.get_lang(chat_id, 'already_spin').format(s=spin_name, n=name),
                         parse_mode=ParseMode.MARKDOWN, disable_notification=True)
    else:
        if core.get_config_key(chat_id, 'restrict', default=False) and \
                not core.is_admin_for_bot(chat_id, update.message.from_user.id, bot):
            update.message.reply_text(core.get_lang(chat_id, 'spin_restricted'))
            return
        user = core.choose_random_user(chat_id, bot)
        winner = core.usernames.get(user)
        if not winner.startswith('@'):
            winner = core.mention_markdown(user, winner)
        else:
            winner = escape_markdown(winner)
        from time import sleep
        curr_text = choice(core.get_lang(chat_id, 'default_spin_texts'))
        locks.append(chat_id)
        if core.get_config_key(chat_id, 'fast', default=False):
            bot.send_message(chat_id=chat_id, text=curr_text[-1].format(s=spin_name, n=winner),
                             parse_mode=ParseMode.MARKDOWN)
        else:
            for t in curr_text:
                bot.send_message(chat_id=chat_id, text=t.format(s=spin_name, n=winner),
                                 parse_mode=ParseMode.MARKDOWN)
                sleep(2)
        locks.pop(locks.index(chat_id))


@core.not_pm
def auto_spin_config(bot: Bot, update: Update, args: list, job_queue: JobQueue):
    msg = update.effective_message
    if len(args) == 0:
        return
    is_moder = core.is_admin_for_bot(msg.chat_id, msg.from_user.id, bot)
    cmd = args.pop(0)
    if cmd == "set" and is_moder:
        try:
            time = args[0].split(':')
            time = "{:0>2}:{:0>2}".format(time[0], time[1])
            job = job_queue.run_daily(auto_spin, core.str_to_time(time), context=msg.chat_id)
            if msg.chat_id in core.auto_spins:
                core.auto_spin_jobs[msg.chat_id].schedule_removal()
        except (ValueError, IndexError):
            msg.reply_text(core.get_lang(msg.chat_id, 'time_error'))
            return

        core.auto_spins.update({msg.chat_id: time})
        core.auto_spin_jobs.update({msg.chat_id: job})
        msg.reply_text(core.get_lang(update.effective_chat.id, 'auto_spin_on').format(time))
    elif cmd == 'del' and is_moder:
        if msg.chat_id in core.auto_spins:
            core.auto_spin_jobs.pop(msg.chat_id).schedule_removal()
            core.auto_spins.pop(msg.chat_id)
            msg.reply_text(core.get_lang(msg.chat_id, 'auto_spin_set_off'))
        else:
            msg.reply_text(core.get_lang(msg.chat_id, 'auto_spin_still_off'))
    elif cmd == 'status':
        if msg.chat_id in core.auto_spins:
            msg.reply_text(core.get_lang(msg.chat_id, 'auto_spin_on').format(core.auto_spins.get(msg.chat_id)))
        else:
            msg.reply_text(core.get_lang(msg.chat_id, 'auto_spin_off'))
    elif not is_moder:
        msg.reply_text(core.get_lang(msg.chat_id, 'not_admin'))


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
        text = core.get_lang(chat_id, 'stats_me').format(username, stat)
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        username = user.name
        stat = core.results_total[chat_id].get(user.id, 0)
        text = core.get_lang(chat_id, 'stats_user').format(username, stat)
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
        spin = core.spin_name.get(msg.chat_id, core.get_lang(msg.chat_id, 'default_spin_name'))
        msg.reply_text(text=core.get_lang(msg.chat_id, 'spin_name_current').format(spin),
                       parse_mode=ParseMode.MARKDOWN)
        return
    if core.is_admin_for_bot(msg.chat_id, msg.from_user.id, bot):
        if args[-1].lower() == core.get_lang(msg.chat_id, 'spin_suffix') and len(args) > 1:
            args.pop(-1)
        spin = " ".join(args)
        core.spin_name[msg.chat_id] = spin
        msg.reply_text(text=core.get_lang(msg.chat_id, 'spin_name_changed').format(spin),
                       parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text(core.get_lang(msg.chat_id, 'not_admin'))


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
        if core.is_admin_for_bot(msg.chat_id, reply.from_user.id, bot):
            msg.reply_text(text=core.get_lang(msg.chat_id, 'admin_still_allow'),
                           parse_mode=ParseMode.MARKDOWN)
        else:
            core.can_change_name[msg.chat_id].append(reply.from_user.id)
            msg.reply_text(text=core.get_lang(msg.chat_id, 'admin_allow'),
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == "del" and reply and is_admin:
        if not core.is_admin_for_bot(msg.chat_id, reply.from_user.id, bot):
            msg.reply_text(text=core.get_lang(msg.chat_id, 'admin_still_deny'),
                           parse_mode=ParseMode.MARKDOWN)
        else:
            index = core.can_change_name[msg.chat_id].index(reply.from_user.id)
            core.can_change_name[msg.chat_id].pop(index)
            msg.reply_text(text=core.get_lang(msg.chat_id, 'admin_deny'),
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == "list":
        users = ""
        for user in core.can_change_name[msg.chat_id]:
            users += core.usernames.get(user, f"id{user}") + '\n'
        text = core.get_lang(msg.chat_id, 'admin_list').format(users)
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@core.not_pm
def spin_count(bot: Bot, update: Update):
    update.message.reply_text(text=core.get_lang(update.effective_chat.id,
                                                 'user_count').format(len(core.chat_users[update.message.chat_id])),
                              parse_mode=ParseMode.MARKDOWN)


@core.not_pm
def user_list(bot: Bot, update: Update):
    chat_id = update.message.chat_id
    if core.get_config_key(chat_id, 'show_list', default=False):
        reply_keyboard = [[]]
        text, pages = core.make_userlist(chat_id, page=1)
        if pages > 1:
            reply_keyboard = [[InlineKeyboardButton(">>", callback_data="userlist:page_2")]]
        update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=InlineKeyboardMarkup(reply_keyboard))
    else:
        update.message.reply_text(core.get_lang(chat_id, 'list_off'))


def settings(bot: Bot, update: Update):
    if update.callback_query:
        callback = True
        chat_id = int(update.callback_query.data.split(':')[1])
        chat_title = bot.get_chat(chat_id).title
    else:
        callback = False
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title

    if core.is_private(chat_id):
        pm = True
        chat_title = update.effective_user.name
    else:
        pm = False

    keyboard = [[InlineKeyboardButton(core.get_lang(chat_id, 'settings_lang'),
                                      callback_data=f'settings:{chat_id}:lang:')]]
    button_on = core.get_lang(chat_id, 'settings_on')
    button_off = core.get_lang(chat_id, 'settings_off')
    callback_off = f'settings:{chat_id}:{{}}:0'
    callback_on = f'settings:{chat_id}:{{}}:1'
    if not pm:
        if core.get_config_key(chat_id, 'fast', default=False):
            fast_text = button_on
            fast_callback = callback_off.format('fast')
        else:
            fast_text = button_off
            fast_callback = callback_on.format('fast')
        if core.get_config_key(chat_id, 'restrict', default=False):
            restrict_text = button_on
            restrict_callback = callback_off.format('restrict')
        else:
            restrict_text = button_off
            restrict_callback = callback_on.format('restrict')
        if core.get_config_key(chat_id, 'show_list', default=False):
            list_text = button_on
            list_callback = callback_off.format('show_list')
        else:
            list_text = button_off
            list_callback = callback_on.format('show_list')
        keyboard.extend([[InlineKeyboardButton(core.get_lang(chat_id, 'settings_fast_spin'),
                                               callback_data=f'settings:{chat_id}:fast:help+fast_spin'),
                          InlineKeyboardButton(fast_text, callback_data=fast_callback)],
                         [InlineKeyboardButton(core.get_lang(chat_id, 'settings_who_spin'),
                                               callback_data=f'settings:{chat_id}:restrict:help+who_spin'),
                          InlineKeyboardButton(restrict_text, callback_data=restrict_callback)],
                         [InlineKeyboardButton(core.get_lang(chat_id, 'settings_show_list'),
                                               callback_data=f'settings:{chat_id}:show_list:help+show_list'),
                          InlineKeyboardButton(list_text, callback_data=list_callback)]])

    if callback:
        update.effective_message.edit_text(core.get_lang(chat_id, 'settings').format(chat_title),
                                           reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        user_id = update.effective_user.id
        if (not pm and core.is_admin_for_bot(chat_id, user_id, bot)) or pm:
            try:
                bot.send_message(user_id, core.get_lang(chat_id, 'settings').format(chat_title),
                                 reply_markup=InlineKeyboardMarkup(keyboard))
                if not pm:
                    update.message.reply_text(core.get_lang(chat_id, 'check_pm'))
            except TelegramError:
                update.message.reply_text(text=core.get_lang(chat_id, 'pm_banned'),
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton(
                                                  core.get_lang(update.effective_chat.id, 'start_pm_button'),
                                                  url=f't.me/{bot.username}')
                                          ]]))
        else:
            update.message.reply_text(core.get_lang(chat_id, 'not_admin'))


def lang_handler(bot: Bot, update: Update):
    chosen_lang = update.callback_query.data.split(':')[-1]
    chat_id = int(update.callback_query.data.split(':')[1])
    if chosen_lang != "":
        core.update_config(chat_id, 'lang', chosen_lang)
        update.callback_query.answer(core.get_lang(chat_id, 'settings_changed'))
        return
    lang = []
    for i, (key, item) in enumerate(core.languages.items()):
        button = InlineKeyboardButton(item.get('_name', key), callback_data=f'settings:{chat_id}:lang:{key}')
        if i % 2 == 0:
            lang.append([button])
        else:
            lang[-1].append(button)
    lang.append([InlineKeyboardButton(core.get_lang(chat_id, 'settings_back'),
                                      callback_data=f'settings:{chat_id}:main:')])
    update.effective_message.edit_text(core.get_lang(chat_id, 'settings_lang_prompt'),
                                       reply_markup=InlineKeyboardMarkup(lang))


def two_state_handler(bot: Bot, update: Update):
    data = update.callback_query.data.split(':')
    chosen_option = data[-1]
    key = data[-2]
    chat_id = int(data[1])
    if chosen_option != "":
        chosen_option = bool(int(chosen_option))  # converting '1' to True, '0' to False
        core.update_config(chat_id, key, chosen_option)
        if chosen_option:
            answer = core.get_lang(chat_id, 'settings_turned_on')
        else:
            answer = core.get_lang(chat_id, 'settings_turned_off')
        update.callback_query.answer(answer)
        settings(bot, update)


def two_state_helper(bot: Bot, update: Update):
    chat_id = int(update.callback_query.data.split(':')[1])
    lang_key = update.callback_query.data.split(':')[-1].split('+')[1]
    update.callback_query.answer(core.get_lang(chat_id, f'settings_{lang_key}_caption'), show_alert=True)


def ask_feedback(bot: Bot, update: Update):
    update.message.reply_text(core.get_lang(update.effective_chat.id, 'feedback_prompt'),
                              reply_markup=ForceReply(selective=True))
    return 0


def send_feedback(bot: Bot, update: Update):
    if update.message.reply_to_message.from_user.id != bot.id:
        return
    bot.send_message(config.BOT_CREATOR, f"<b>New message!</b>\n"
                                         f" - <i>Chat:</i> <pre>{update.message.chat}</pre>\n"
                                         f" - <i>User:</i> <pre>{update.message.from_user}</pre>\n"
                                         f" - <i>Message ID:</i> <pre>{update.message.message_id}</pre>",
                     parse_mode=ParseMode.HTML)
    update.message.forward(config.BOT_CREATOR)
    update.message.reply_text(core.get_lang(update.effective_chat.id, 'feedback_sent'),
                              reply_markup=ReplyKeyboardRemove(selective=True))
    return ConversationHandler.END


def cancel_feedback(bot: Bot, update: Update):
    update.message.reply_text(core.get_lang(update.effective_chat.id, 'feedback_cancelled'),
                              reply_markup=ReplyKeyboardRemove(selective=True))
    return ConversationHandler.END


def uptime(bot, update):
    update.message.reply_text(core.get_lang(update.message.chat_id, 'uptime').format(datetime.now() - start_time))


def wotd(bot: Bot, update: Update, args: list):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if len(args) == 0:
        if core.wotd:
            update.message.reply_text(core.get_lang(chat_id, 'already_spin').format(
                s=core.get_lang(chat_id, 'wotd'), n=core.usernames.get(core.wotd)
            ), parse_mode=ParseMode.MARKDOWN, disable_notification=True)
        else:
            update.message.reply_text(core.get_lang(chat_id, 'wotd_nostats'))
    else:
        cmd = args.pop(0)
        if cmd == 'register':
            if user_id not in core.wotd_registered:
                core.wotd_registered.append(user_id)
                update.effective_message.reply_text(core.get_lang(chat_id, 'wotd_registered'))
            else:
                update.effective_message.reply_text(core.get_lang(chat_id, 'wotd_already_reg'))
        if cmd == 'count':
            update.effective_message.reply_text(core.get_lang(chat_id, 'user_count').format(len(core.wotd_registered)),
                                                parse_mode=ParseMode.MARKDOWN)


jobs.run_repeating(auto_save, 60)
jobs.run_daily(daily_job, core.str_to_time(config.RESET_TIME))

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler('feedback', ask_feedback)],
    states={
        0: [MessageHandler(Filters.reply & (Filters.text | Filters.photo | Filters.document), send_feedback)]
    },
    fallbacks=[CommandHandler('cancel', cancel_feedback)]
)

dp.add_handler(CommandHandler(['start', 'help'], start_help_handler, pass_args=True))
dp.add_handler(CommandHandler('about', about))
dp.add_handler(CommandHandler('admgroup', admin_ctrl, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('sudo', admin_shell, pass_args=True, allow_edited=True,
                              filters=Filters.user(user_id=config.BOT_CREATOR)))
dp.add_handler(CommandHandler('ping', ping))
dp.add_handler(CommandHandler('setname', change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('count', spin_count))
dp.add_handler(CommandHandler('userlist', user_list))
dp.add_handler(CommandHandler('spin', do_the_spin))
dp.add_handler(CommandHandler('sрin', do_the_spinn))
dp.add_handler(CommandHandler('auto', auto_spin_config, pass_args=True, allow_edited=True,
                              pass_job_queue=True))
dp.add_handler(CommandHandler('stat', top, pass_args=True))
dp.add_handler(CommandHandler('settings', settings))
dp.add_handler(CommandHandler('uptime', uptime))
dp.add_handler(CommandHandler('winner', wotd, pass_args=True))
dp.add_handler(feedback_handler)
dp.add_handler(MessageHandler(Filters.status_update, svc_handler))
dp.add_handler(CallbackQueryHandler(pages_handler, pattern=r"^(top|userlist):page_[1-9]+[0-9]*$"))
dp.add_handler(CallbackQueryHandler(help_button_handler, pattern=r"^help:.+$"))
dp.add_handler(CallbackQueryHandler(settings, pattern=r"^settings:-?\d+:main:$"))
dp.add_handler(CallbackQueryHandler(lang_handler, pattern=r"^settings:-?\d+:lang:\w*$"))
dp.add_handler(CallbackQueryHandler(two_state_handler, pattern=r"^settings:-?\d+:[a-z_]+:[01]$"))
dp.add_handler(CallbackQueryHandler(two_state_helper, pattern=r"^settings:-?\d+:[a-z_]+:help\+[a-z_]+$"))
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
start_time = datetime.now()
updater.idle()

core.save_all()
log.info("Bot stopped")

# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode, TelegramError
from telegram.ext.dispatcher import run_async
from logging import DEBUG
from time import sleep
from threading import Thread
from queue import Queue

import data
import utils
import config
from ._jobs import daily_job

log = utils.set_up_logger(__name__, DEBUG)
announcement_chats = Queue()


def sudo(bot, update, args: list):
    msg = update.effective_message
    try:
        cmd = args.pop(0)
    except IndexError:
        return
    if cmd in COMMANDS:
        COMMANDS[cmd](bot=bot, msg=msg, cmd=cmd, args=args)
    elif cmd == 'help':
        text = 'Help:\n'
        for command in COMMANDS.values():
            text += '* ' + command.__doc__ + '\n'
        msg.reply_text(text)


def _send(bot, msg, cmd, args):
    """(send|edit) <chat>_[msgid]_[parsemode] — send or edit message"""
    params = args.pop(0)
    text = ' '.join(args).replace('\\n', '\n')
    params = params.split('_')
    chat = params[0]
    if chat == 'current':
        chat = msg.chat_id
    try:
        msg_id = params[1]
        assert msg_id != ''
    except (KeyError, AssertionError, IndexError):
        msg_id = None
    try:
        parse_mode = params[2]
    except (KeyError, IndexError):
        parse_mode = None
    del params
    if cmd == 'send':
        new_msg = bot.send_message(chat, text, parse_mode=parse_mode, reply_to_message_id=msg_id)
        msg.reply_text(f'Sent message ID: {new_msg.message_id}')
    elif cmd == 'edit':
        bot.edit_message_text(chat_id=chat, text=text, parse_mode=parse_mode, message_id=msg_id)


def _respin(msg, args, **kwargs):
    """respin [chat] — reset spin in specified or current chat"""
    if len(args) > 0:
        chat = int(args[0])
    else:
        chat = msg.chat_id
    data.results_today.pop(chat)
    log.info(f'Respin done in {chat}')
    msg.reply_text('respin ok')


def _send_logs(msg, **kwargs):
    """sendlogs — send latest logs as document"""
    if config.LOG_FILE is None:
        msg.reply_text('Logging to file is not configured.')
        return
    with open(config.LOG_FILE, 'rb') as f:
        msg.reply_document(f)


def _delete(bot, msg, args, **kwargs):
    """delete [<chat>_<msgid>] - delete replied or specified message"""
    if len(args) == 0:
        msg.reply_to_message.delete()
    else:
        params = args.pop(0).split('_')
        if params[0] == 'current':
            params[0] = msg.chat_id
        bot.delete_message(chat_id=params[0], message_id=params[1])


def _exec(args, **kwargs):
    """exec <code> — execute code (exec)"""
    exec(' '.join(args))


def _vardump(bot, msg, args, **kwargs):
    """vardump <variable> — send variable value (eval)"""
    reply = msg.reply_to_message
    bot.send_message(chat_id=msg.chat_id,
                     text='```\n{}\n```'.format(eval(' '.join(args))),
                     parse_mode=ParseMode.MARKDOWN,
                     reply_to_message_id=msg.message_id)


def _reset(bot, *kwargs):
    """reset — begin new day"""
    daily_job(bot, None)


def _md_announce(bot, args, **kwargs):
    """md_announce <text> — send message to all chats (markdown is on)"""
    announce(bot, ' '.join(args), md=True)


def _announce(bot, args, **kwargs):
    """announce <text> — send message to all chats (markdown is off)"""
    announce(bot, ' '.join(args))


def _count(msg, **kwargs):
    """count — count known chats"""
    msg.reply_text(f'Bot has {len(data.chat_users)} chats')


def _reload_lang(msg, **kwargs):
    """lang_reload — reload localization files"""
    from lang import Localization
    Localization.reload()
    msg.reply_text('Done!')


@run_async
def announce(bot, text, md=False):
    for chat in data.chat_users.keys():
        announcement_chats.put(chat)
    text = text.replace('\\n', '\n')
    msg = bot.send_message(config.BOT_CREATOR, 'Announcing...')
    announcer = Thread(target=_announce_thread, name='Announce thread', args=(bot, text, md, msg))
    announcer.start()


def _announce_thread(bot, text, md, msg):
    total = announcement_chats.qsize()
    processed = 0
    deleted = 0
    while not announcement_chats.empty():
        chat = announcement_chats.get_nowait()
        try:
            if md:
                bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=chat, text=text)
        except TelegramError:
            log.debug(f'Chat {chat} is not reachable for messages, deleting it')
            deleted += 1
            data.chat_users.pop(chat)
        processed += 1
        msg.edit_text('Announcing to {1}...\n`|{0:<20}|` ({2:.2%})'.format('*' * (int(processed / total) * 20),
                                                                           chat, processed / total),
                      parse_mode=ParseMode.MARKDOWN)
        if processed % 7 == 0:
            msg.edit_text('Sleeping...\n`|{0:<20}|` ({1:.2%})'.format('*' * (int(processed / total) * 20),
                                                                      processed / total),
                          parse_mode=ParseMode.MARKDOWN)
            sleep(10)
    msg.edit_text(f'Announcing done!\nDeleted chats: {deleted}\nTotal chats: {total}')


COMMANDS = {
    'exec': _exec,
    'vardump': _vardump,
    'reset': _reset,
    'respin': _respin,
    'md_announce': _md_announce,
    'announce': _announce,
    'sendlogs': _send_logs,
    'delete': _delete,
    'count': _count,
    'send': _send,
    'edit': _send,
    'lang_reload': _reload_lang
}

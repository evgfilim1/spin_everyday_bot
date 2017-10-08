# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode, TelegramError
from telegram.ext.dispatcher import run_async
from logging import DEBUG
from time import sleep

import data
import utils
import config
from ._jobs import daily_job

log = utils.set_up_logger(__name__, DEBUG)
announcement_chats = []


def sudo(bot, update, args: list):
    msg = update.effective_message
    try:
        cmd = args.pop(0)
    except IndexError:
        return
    if cmd == 'exec':
        exec(' '.join(args))
    elif cmd == 'vardump':
        bot.send_message(chat_id=msg.chat_id, text='```\n{}\n```'.format(
            eval(' '.join(args))
        ), parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg.message_id)
    elif cmd == 'reset':
        daily_job(bot, None)
    elif cmd == 'respin':
        if len(args) > 0:
            chat = int(args[0])
        else:
            chat = msg.chat_id
        data.results_today.pop(chat)
        log.info(f'Respin done in {chat}')
        msg.reply_text('respin ok')
    elif cmd == 'md_announce':
        announce(bot, ' '.join(args), md=True)
    elif cmd == 'announce':
        announce(bot, ' '.join(args))
    elif cmd == 'sendlogs':
        if config.LOG_FILE is None:
            msg.reply_text('Logging to file is not configured.')
            return
        with open(config.LOG_FILE, 'rb') as f:
            msg.reply_document(f)
    elif cmd == 'delete':
        if len(args) == 0:
            msg.reply_to_message.delete()
        else:
            params = args.pop(0).split('_')
            if params[0] == 'current':
                params[0] = msg.chat_id
            bot.delete_message(chat_id=params[0], message_id=params[1])
    elif cmd == 'count':
        msg.reply_text(f'Bot has {len(data.chat_users)} chats')
    elif cmd == 'send' or cmd == 'edit':
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
    elif cmd == 'help':
        msg.reply_text('Help:\n- exec <code> — execute code\n- vardump <variable> — print variable value\n'
                       '- delete [<chat>_<msgid>] - delete replied or specified message\n'
                       '- send <chat>_<msgid>_<parsemode> - send message\n'
                       '- edit <chat>_<msgid>_<parsemode> - edit message\n'
                       '- reset — reset all spins\n- respin [chat] — reset spin in this or specified chat\n'
                       '- md_announce <text> — tell something to all chats (markdown is on)\n'
                       '- announce <text> — tell something to all chats (markdown is off)\n'
                       '- count - count known chats\n- sendlogs — send latest logs as document')


@run_async
def announce(bot, text, md=False):
    # Sending announcement to 15 chats, then sleep
    sleep_border = 15
    announcement_chats.extend(data.chat_users.keys())
    text = text.replace('\\n', '\n')
    while len(announcement_chats) > 0:
        chat = announcement_chats.pop()
        try:
            if md:
                bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=chat, text=text)
            sleep_border -= 1
        except TelegramError:
            log.warning(f'Chat {chat} is not reachable for messages, deleting it')
            data.chat_users.pop(chat)
            # pass
        if sleep_border == 0:
            sleep(5)
            sleep_border = 15

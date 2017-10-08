# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from datetime import datetime
from telegram import ParseMode

import data
import utils

start_time = None


def bot_started():
    global start_time
    start_time = datetime.now()


def uptime(bot, update):
    update.message.reply_text(utils.get_lang(update.message.chat_id,
                                             'uptime').format(datetime.now() - start_time))


def ping(bot, update):
    update.message.reply_text(text='Ping? Pong!')


@utils.not_pm
def spin_count(bot, update):
    update.message.reply_text(text=utils.get_lang(update.effective_chat.id,
                                                  'user_count').format(len(data.chat_users[update.message.chat_id])),
                              parse_mode=ParseMode.MARKDOWN)

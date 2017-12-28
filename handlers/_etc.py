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


@utils.localize
@utils.flood_limit
def uptime(bot, update, tr):
    update.message.reply_text(tr.uptime.format(datetime.now() - start_time))


@utils.flood_limit
def ping(bot, update):
    update.message.reply_text(text='Ping? Pong!')


@utils.localize
@utils.flood_limit
@utils.not_pm
def spin_count(bot, update, tr):
    update.message.reply_text(text=tr.user.count.format(len(data.chat_users[update.message.chat_id])),
                              parse_mode=ParseMode.MARKDOWN)

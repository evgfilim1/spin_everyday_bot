# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from logging import DEBUG
from random import choice
from telegram import ParseMode, TelegramError

import data
import utils
from ._spin import choose_random_user

log = utils.set_up_logger(__name__, DEBUG)


def daily_job(bot, job=None):
    data.results_today.clear()
    log.debug('Reset done')
    try:
        uid = choose_random_user(0, bot)
        text = choice(utils.get_lang(uid, 'default_spin_texts'))[-1]
        bot.send_message(uid, text.format(s=utils.get_lang(uid, 'wotd'), n=data.usernames.get(uid)),
                         parse_mode=ParseMode.MARKDOWN)
    except (TelegramError, IndexError):
        pass
    log.debug('Daily spin done')


def hourly_job(bot=None, job=None):
    data.save_all()
    data.flood.clear()

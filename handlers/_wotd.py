# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode

import data
import utils


@utils.flood_limit
def wotd(bot, update, args):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if len(args) == 0:
        if data.wotd:
            update.message.reply_text(utils.get_lang(chat_id, 'already_spin').format(
                s=utils.get_lang(chat_id, 'wotd'), n=data.usernames.get(data.wotd)
            ), parse_mode=ParseMode.MARKDOWN, disable_notification=True)
        else:
            update.message.reply_text(utils.get_lang(chat_id, 'wotd_nostats'))
    else:
        cmd = args.pop(0)
        if cmd == 'register':
            if user_id not in data.wotd_registered:
                data.wotd_registered.append(user_id)
                update.effective_message.reply_text(utils.get_lang(chat_id, 'wotd_registered'))
            else:
                update.effective_message.reply_text(utils.get_lang(chat_id, 'wotd_already_reg'))
        if cmd == 'count':
            update.effective_message.reply_text(utils.get_lang(chat_id, 'user_count').format(len(data.wotd_registered)),
                                                parse_mode=ParseMode.MARKDOWN)

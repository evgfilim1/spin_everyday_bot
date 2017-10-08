# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ForceReply, ReplyKeyboardRemove, ParseMode
from telegram.ext import ConversationHandler

import config
import utils


def ask_feedback(bot, update):
    update.message.reply_text(utils.get_lang(update.effective_chat.id, 'feedback_prompt'),
                              reply_markup=ForceReply(selective=True))
    return 0


def send_feedback(bot, update):
    if update.message.reply_to_message.from_user.id != bot.id:
        return
    bot.send_message(config.BOT_CREATOR, f'<b>New message!</b>\n'
                                         f' - <i>Chat:</i> <pre>{update.message.chat}</pre>\n'
                                         f' - <i>User:</i> <pre>{update.message.from_user}</pre>\n'
                                         f' - <i>Message ID:</i> <pre>{update.message.message_id}</pre>',
                     parse_mode=ParseMode.HTML)
    update.message.forward(config.BOT_CREATOR)
    update.message.reply_text(utils.get_lang(update.effective_chat.id, 'feedback_sent'),
                              reply_markup=ReplyKeyboardRemove(selective=True))
    return ConversationHandler.END

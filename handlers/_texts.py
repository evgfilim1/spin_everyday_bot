# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode, TelegramError, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.utils.helpers import escape_markdown

import data
import utils


@utils.flood_limit
@utils.not_pm
def new_text(bot, update, chat_data):
    chat_id = update.message.chat_id
    if not utils.is_admin_for_bot(chat_id, update.message.from_user.id, bot):
        update.message.reply_text(utils.get_lang(chat_id, 'not_admin'))
        return
    update.message.reply_text(utils.get_lang(chat_id, 'newtext_prompt'),
                              parse_mode=ParseMode.MARKDOWN)
    chat_data['p_user'] = update.message.from_user.id
    return 0


def fill_text(bot, update, chat_data):
    chat_id = update.message.chat_id
    if update.message.from_user.id != chat_data.get('p_user'):
        return
    if chat_data.get('texts') is None:
        chat_data['texts'] = []
    try:
        update.message.text_markdown.format(s='test', n='@user')
    except (ValueError, KeyError, TelegramError):
        update.message.reply_text(utils.get_lang(chat_id, 'newtext_invalid'))
        return
    chat_data['texts'].append(update.message.text_markdown)


def remove_text(bot, update, chat_data):
    if update.message.from_user.id != chat_data.get('p_user'):
        return
    if not update.message.reply_to_message:
        return
    try:
        i = chat_data.get('texts', []).index(update.message.reply_to_message.text)
        chat_data['texts'].pop(i)
        update.message.reply_text(utils.get_lang(update.message.chat_id, 'newtext_deleted'))
    except ValueError:
        pass


def record_text(bot, update, chat_data: dict):
    chat_id = update.message.chat_id
    if update.message.from_user.id != chat_data.get('p_user'):
        return
    texts = chat_data.get('texts')
    if texts is None:
        update.message.reply_text(utils.get_lang(chat_id, 'newtext_empty'))
        return
    text = utils.get_lang(chat_id, 'newtext_added')
    for line in texts:
        text += line.format(s='test', n=update.message.from_user.name) + '\n'
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove(selective=True))
    if chat_id not in data.chat_texts:
        data.chat_texts[chat_id] = []
    data.chat_texts[chat_id].append(chat_data.pop('texts'))
    return ConversationHandler.END


@utils.flood_limit
@utils.not_pm
def list_text(bot, update):
    chat_id = update.message.chat_id
    text = utils.get_lang(chat_id, 'texts_list') + '\n\n'
    spin_name = escape_markdown(data.spin_name.get(chat_id, utils.get_lang(chat_id, 'default_spin_name')))
    count = len(data.chat_texts.get(chat_id, []))
    if count == 0:
        update.message.reply_text(utils.get_lang(chat_id, 'no_texts'))
        return
    for line in data.chat_texts.get(chat_id, [[]])[0]:
        text += line.format(s=spin_name, n=update.message.from_user.name) + '\n'
    text = text.format(1, count)
    keyboard = [[InlineKeyboardButton(utils.get_lang(chat_id, 'delete'), callback_data='texts:1:del')]]
    if count > 1:
        keyboard[0].append(InlineKeyboardButton('>>', callback_data='texts:2:'))
    else:
        keyboard = [[]]
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


def text_handler(bot, update):
    query = update.callback_query
    _, page, _del = query.data.split(':')
    page = int(page)
    _del = _del == 'del'
    msg = query.message
    chat_id = msg.chat_id

    if _del:
        if not utils.is_admin_for_bot(chat_id, query.from_user.id, bot):
            query.answer(utils.get_lang(chat_id, 'not_admin'))
            return
        data.chat_texts[chat_id].pop(page - 1)
        query.answer(utils.get_lang(chat_id, 'success'))
        page -= 1

    text = utils.get_lang(chat_id, 'texts_list') + '\n\n'
    spin_name = escape_markdown(data.spin_name.get(chat_id, utils.get_lang(chat_id, 'default_spin_name')))
    count = len(data.chat_texts.get(chat_id, []))
    if count == 0:
        query.edit_message_text(utils.get_lang(chat_id, 'no_texts'))
        return
    for line in data.chat_texts.get(chat_id)[page - 1]:
        text += line.format(s=spin_name, n=query.from_user.name) + '\n'
    text = text.format(page, count)
    keyboard = [[]]
    if page > 1:
        keyboard[0].append(InlineKeyboardButton('<<', callback_data=f'texts:{page - 1}:'))
    if count > 0:
        keyboard[0].append(InlineKeyboardButton(utils.get_lang(chat_id, 'delete'), callback_data=f'texts:{page}:del'))
    if page < count:
        keyboard[0].append((InlineKeyboardButton('>>', callback_data=f'texts:{page + 1}:')))

    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        pass


def cancel_conversation(bot, update, **kwargs):
    update.message.reply_text(utils.get_lang(update.effective_chat.id, 'cancelled'),
                              reply_markup=ReplyKeyboardRemove(selective=True))
    try:
        kwargs['chat_data'].pop('texts')
    except (KeyError, ValueError):
        pass

    return ConversationHandler.END

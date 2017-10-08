# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, TelegramError

import data
import utils
from ._spin import locks


def top_win(chat_id):
    return sorted(data.results_total.get(chat_id, {}).items(), key=lambda x: x[1], reverse=True)


def make_top(chat_id, page):
    winners = top_win(chat_id)
    winners, total_pages = utils.pages(winners, page)
    text = utils.get_lang(chat_id, 'stats_all').format(page, total_pages)
    for user in winners:
        username = data.usernames.get(user[0], f'id{user[0]}')
        text += utils.get_lang(chat_id, 'stats_user_short').format(username, user[1])
    return text, total_pages


def make_userlist(chat_id: int, page: int) -> (str, int):
    users, total_pages = utils.pages(data.chat_users[chat_id], page)
    text = utils.get_lang(chat_id, 'list').format(page, total_pages)
    for user in users:
        username = data.usernames.get(user, f'id{user}')
        text += f'`{username}`\n'
    return text, total_pages


def pages_handler(bot, update):
    query = update.callback_query
    _type, data = query.data.split(':')
    msg = query.message
    page_n = int(data.split('_')[1])
    if _type == 'top':
        if msg.chat_id in locks:
            query.answer(utils.get_lang(msg.chat_id, 'locked_buttons'))
            return
        text, max_pages = make_top(msg.chat_id, page=page_n)
    else:
        text, max_pages = make_userlist(msg.chat_id, page=page_n)

    reply_keyboard = [[]]
    if page_n != 1:
        reply_keyboard[0].append(InlineKeyboardButton('<<', callback_data=f'{_type}:page_{page_n - 1}'))
    if page_n != max_pages:
        reply_keyboard[0].append(InlineKeyboardButton('>>', callback_data=f'{_type}:page_{page_n + 1}'))
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(reply_keyboard),
                                parse_mode=ParseMode.MARKDOWN)
    except TelegramError:
        pass


@utils.not_pm
def top(bot, update, args):
    chat_id = update.message.chat_id
    reply_keyboard = [[]]
    if chat_id in locks:
        return
    if chat_id not in data.results_total:
        data.results_total[chat_id] = {}
    if len(args) == 1 and args[0] == 'me':
        user = update.message.from_user
        username = user.name
        stat = data.results_total[chat_id].get(user.id, 0)
        text = utils.get_lang(chat_id, 'stats_me').format(username, stat)
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        username = user.name
        stat = data.results_total[chat_id].get(user.id, 0)
        text = utils.get_lang(chat_id, 'stats_user').format(username, stat)
    else:
        text, pages = make_top(chat_id, page=1)
        if pages > 1:
            reply_keyboard = [[InlineKeyboardButton('>>', callback_data='top:page_2')]]
    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=InlineKeyboardMarkup(reply_keyboard))


@utils.not_pm
def user_list(bot, update):
    chat_id = update.message.chat_id
    if utils.get_config_key(chat_id, 'show_list', default=False):
        reply_keyboard = [[]]
        text, pages = make_userlist(chat_id, page=1)
        if pages > 1:
            reply_keyboard = [[InlineKeyboardButton('>>', callback_data='userlist:page_2')]]
        update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=InlineKeyboardMarkup(reply_keyboard))
    else:
        update.message.reply_text(utils.get_lang(chat_id, 'list_off'))

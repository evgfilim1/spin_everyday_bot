# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import re
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, TelegramError
from subprocess import check_output

import utils
import config


def bot_version():
    git_version = check_output('git describe --tags', shell=True)[:-1].decode()
    return re.sub(r'-(\d+)-g([a-z0-9]{7})', r'.r\1.\2', git_version)


def helper(bot, update, short):
    chat_id = update.effective_chat.id
    keys = []
    if short:
        text = utils.get_lang(chat_id, 'help_short')
        if not utils.is_private(chat_id):
            text += utils.get_lang(chat_id, 'help_moreinfo_chat')
            keys.append([InlineKeyboardButton(utils.get_lang(chat_id, 'start_pm_button'),
                                              url=f't.me/{bot.username}?start=help')])
        else:
            text += utils.get_lang(chat_id, 'help_moreinfo_pm')
    else:
        text = utils.get_lang(chat_id, 'help_texts')['main'][0]
        for i, command in enumerate(utils.get_lang(chat_id, 'help_texts')['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))

    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keys))


@utils.flood_limit
def start_help_handler(bot, update, args):
    if (len(args) > 0 and args[0] == 'help') or (utils.is_private(update.message.chat_id) and
                                                 not update.message.text.startswith('/start')):
        helper(bot, update, short=False)
    else:
        helper(bot, update, short=True)


@utils.flood_limit
def about(bot, update):
    version = bot_version()
    update.message.reply_text(utils.get_lang(update.effective_chat.id, 'about_text').format(
        version, f'@{bot.get_chat(config.BOT_CREATOR).username}', config.REPO_URL
    ), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)


def help_button_handler(bot, update):
    query = update.callback_query
    data = query.data.split(':')[1]
    keys = []
    if data == 'main':
        text = utils.get_lang(update.effective_chat.id, 'help_texts')['main'][0]
        for i, command in enumerate(utils.get_lang(update.effective_chat.id, 'help_texts')['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))
    else:
        keys = [[
            InlineKeyboardButton(text=utils.get_lang(update.effective_chat.id, 'helpbuttons_back'),
                                 callback_data='help:main')
        ]]
        command_info = utils.get_lang(update.effective_chat.id, 'help_texts')['main'][1][data]

        text = '`/{0}` - {1}\n\n'.format(data, command_info['summary'])
        text += utils.get_lang(update.effective_chat.id, 'help_usage') + '\n'
        for suffix, suffix_info in command_info['usage'].items():
            if suffix != '':
                suffix = ' ' + suffix
            text += f'/{data}{suffix} - {suffix_info["text"]} '
            if suffix_info.get('reply', False):
                text += utils.get_lang(update.effective_chat.id, 'help_onlyreply') + ' '
            if suffix_info.get('admin', False):
                text += utils.get_lang(update.effective_chat.id, 'help_onlyadmin')
            text += '\n'
    try:
        query.edit_message_text(reply_markup=InlineKeyboardMarkup(keys), parse_mode=ParseMode.MARKDOWN, text=text)
    except TelegramError:
        pass

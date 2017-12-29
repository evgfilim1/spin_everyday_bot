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


@utils.localize
def helper(bot, update, short, tr):
    chat_id = update.effective_chat.id
    keys = []
    if short:
        text = tr.help.short
        if not utils.is_private(chat_id):
            text += tr.help.moreinfo_chat
            keys.append([InlineKeyboardButton(tr.status.start_pm_button,
                                              url=f't.me/{bot.username}?start=help')])
        else:
            text += tr.help.moreinfo_pm
    else:
        text = tr.help_texts['main'][0]
        for i, command in enumerate(tr.help_texts['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))

    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keys))


@utils.localize
@utils.flood_limit
def start_help_handler(bot, update, args, tr):
    from functools import partial
    _help = partial(helper, bot, update)
    # '/start' => short help
    # '/start help' => long help
    # '/help' in PM => long help
    # '/help' in chat => short help
    # '/help <command>' => help for the command
    if update.effective_message.text.startswith('/start'):
        if len(args) > 0 and args[0] == 'help':
            _help(short=False)
        else:
            _help(short=True)
    else:  # /help
        if len(args) > 0:
            if args[0][0] == '/':
                command = args[0][1:]
            else:
                command = args[0]
            if command not in tr.help_texts['main'][1]:
                update.effective_message.reply_text(tr.errors.command.format(f'/{command}'))
                return
            update.effective_message.reply_text(help_command(command, tr), parse_mode=ParseMode.MARKDOWN)
        elif utils.is_private(update.effective_chat.id):
            _help(short=False)
        else:
            _help(short=True)


def help_command(command, tr):
    command_info = tr.help_texts['main'][1][command]
    text = '`/{0}` - {1}\n\n'.format(command, command_info['summary'])
    text += tr.help.usage + '\n'
    for suffix, suffix_info in command_info['usage'].items():
        if suffix != '':
            suffix = ' ' + suffix
        text += f'/{command}{suffix} - {suffix_info["text"]} '
        if suffix_info.get('reply', False):
            text += tr.help.onlyreply + ' '
        if suffix_info.get('admin', False):
            text += tr.help.onlyadmin
        text += '\n'
    return text


@utils.localize
@utils.flood_limit
def about(bot, update, tr):
    version = bot_version()
    update.message.reply_text(tr.about_text.format(
        version, f'@{bot.get_chat(config.BOT_CREATOR).username}', config.REPO_URL
    ), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)


@utils.localize
def help_button_handler(bot, update, tr):
    query = update.callback_query
    data = query.data.split(':')[1]
    keys = []
    if data == 'main':
        text = tr.help_texts['main'][0]
        for i, command in enumerate(tr.help_texts['main'][1]):
            if i % 3 == 0:
                keys.append([InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}')])
            else:
                keys[-1].append(InlineKeyboardButton(text=f'/{command}', callback_data=f'help:{command}'))
    else:
        keys = [[
            InlineKeyboardButton(text=tr.back, callback_data='help:main')
        ]]
        text = help_command(data, tr)
    try:
        query.edit_message_text(reply_markup=InlineKeyboardMarkup(keys), parse_mode=ParseMode.MARKDOWN, text=text)
    except TelegramError:
        pass

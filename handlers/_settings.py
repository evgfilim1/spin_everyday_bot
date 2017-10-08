# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError

import data
import utils


def settings(bot, update):
    if update.callback_query:
        callback = True
        chat_id = int(update.callback_query.data.split(':')[1])
        chat_title = bot.get_chat(chat_id).title
    else:
        callback = False
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title

    if utils.is_private(chat_id):
        pm = True
        chat_title = update.effective_user.name
    else:
        pm = False

    keyboard = [[InlineKeyboardButton(utils.get_lang(chat_id, 'settings_lang'),
                                      callback_data=f'settings:{chat_id}:lang:')]]
    button_on = utils.get_lang(chat_id, 'settings_on')
    button_off = utils.get_lang(chat_id, 'settings_off')
    callback_off = f'settings:{chat_id}:{{}}:0'
    callback_on = f'settings:{chat_id}:{{}}:1'
    if not pm:
        if utils.get_config_key(chat_id, 'fast', default=False):
            fast_text = button_on
            fast_callback = callback_off.format('fast')
        else:
            fast_text = button_off
            fast_callback = callback_on.format('fast')
        if utils.get_config_key(chat_id, 'restrict', default=False):
            restrict_text = button_on
            restrict_callback = callback_off.format('restrict')
        else:
            restrict_text = button_off
            restrict_callback = callback_on.format('restrict')
        if utils.get_config_key(chat_id, 'show_list', default=False):
            list_text = button_on
            list_callback = callback_off.format('show_list')
        else:
            list_text = button_off
            list_callback = callback_on.format('show_list')
        keyboard.extend([[InlineKeyboardButton(utils.get_lang(chat_id, 'settings_fast_spin'),
                                               callback_data=f'settings:{chat_id}:fast:help+fast_spin'),
                          InlineKeyboardButton(fast_text, callback_data=fast_callback)],
                         [InlineKeyboardButton(utils.get_lang(chat_id, 'settings_who_spin'),
                                               callback_data=f'settings:{chat_id}:restrict:help+who_spin'),
                          InlineKeyboardButton(restrict_text, callback_data=restrict_callback)],
                         [InlineKeyboardButton(utils.get_lang(chat_id, 'settings_show_list'),
                                               callback_data=f'settings:{chat_id}:show_list:help+show_list'),
                          InlineKeyboardButton(list_text, callback_data=list_callback)]])

    if callback:
        update.effective_message.edit_text(utils.get_lang(chat_id, 'settings').format(chat_title),
                                           reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        user_id = update.effective_user.id
        if (not pm and utils.is_admin_for_bot(chat_id, user_id, bot)) or pm:
            try:
                bot.send_message(user_id, utils.get_lang(chat_id, 'settings').format(chat_title),
                                 reply_markup=InlineKeyboardMarkup(keyboard))
                if not pm:
                    update.message.reply_text(utils.get_lang(chat_id, 'check_pm'))
            except TelegramError:
                update.message.reply_text(text=utils.get_lang(chat_id, 'pm_banned'),
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton(
                                                  utils.get_lang(update.effective_chat.id, 'start_pm_button'),
                                                  url=f't.me/{bot.username}')
                                          ]]))
        else:
            update.message.reply_text(utils.get_lang(chat_id, 'not_admin'))


def lang_handler(bot, update):
    chosen_lang = update.callback_query.data.split(':')[-1]
    chat_id = int(update.callback_query.data.split(':')[1])
    if chosen_lang != '':
        utils.update_config(chat_id, 'lang', chosen_lang)
        update.callback_query.answer(utils.get_lang(chat_id, 'settings_changed'))
        return
    lang = []
    for i, (key, item) in enumerate(data.languages.items()):
        button = InlineKeyboardButton(item.get('_name', key), callback_data=f'settings:{chat_id}:lang:{key}')
        if i % 2 == 0:
            lang.append([button])
        else:
            lang[-1].append(button)
    lang.append([InlineKeyboardButton(utils.get_lang(chat_id, 'settings_back'),
                                      callback_data=f'settings:{chat_id}:main:')])
    update.effective_message.edit_text(utils.get_lang(chat_id, 'settings_lang_prompt'),
                                       reply_markup=InlineKeyboardMarkup(lang))


def two_state_handler(bot, update):
    data = update.callback_query.data.split(':')
    chosen_option = data[-1]
    key = data[-2]
    chat_id = int(data[1])
    if chosen_option != '':
        chosen_option = bool(int(chosen_option))  # converting '1' to True, '0' to False
        utils.update_config(chat_id, key, chosen_option)
        if chosen_option:
            answer = utils.get_lang(chat_id, 'settings_turned_on')
        else:
            answer = utils.get_lang(chat_id, 'settings_turned_off')
        update.callback_query.answer(answer)
        settings(bot, update)


def two_state_helper(bot, update):
    chat_id = int(update.callback_query.data.split(':')[1])
    lang_key = update.callback_query.data.split(':')[-1].split('+')[1]
    update.callback_query.answer(utils.get_lang(chat_id, f'settings_{lang_key}_caption'), show_alert=True)

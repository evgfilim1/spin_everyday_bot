# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError

from lang import Localization
import utils


@utils.flood_limit
def settings_command(*args, **kwargs):
    settings(callback=False, *args, **kwargs)


def generate_two_state_button(chat_id, callback_id, config_key, default_key):
    tr = Localization(chat_id)
    if utils.get_config_key(chat_id, config_key, default=default_key):
        _text = tr.settings.state_on
        _data = f'settings:{chat_id}:{callback_id}:0'
    else:
        _text = tr.settings.state_off
        _data = f'settings:{chat_id}:{callback_id}:1'
    return InlineKeyboardButton(_text, callback_data=_data)


def generate_help_button(chat_id, callback_id, lang_id):
    tr = Localization(chat_id)
    return InlineKeyboardButton(tr.settings[lang_id],
                                callback_data=f'settings:{chat_id}:{callback_id}:help+{lang_id}')


@utils.localize
def settings(bot, update, tr, callback=True):
    if callback:
        chat_id = int(update.callback_query.data.split(':')[1])
        chat_title = bot.get_chat(chat_id).title
    else:
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title

    if utils.is_private(chat_id):
        pm = True
        chat_title = update.effective_user.name
    else:
        pm = False

    keyboard = [[InlineKeyboardButton(tr.settings.lang, callback_data=f'settings:{chat_id}:lang:')]]
    if not pm:
        keyboard.extend([[generate_help_button(chat_id, 'fast', 'fast_spin'),
                          generate_two_state_button(chat_id, 'fast', 'fast', default_key=False)],
                         [generate_help_button(chat_id, 'restrict', 'who_spin'),
                          generate_two_state_button(chat_id, 'restrict', 'restrict', default_key=False)],
                         [generate_help_button(chat_id, 'show_list', 'show_list'),
                          generate_two_state_button(chat_id, 'show_list', 'show_list', default_key=False)]])

    if callback:
        update.effective_message.edit_text(tr.settings.title.format(chat_title),
                                           reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        user_id = update.effective_user.id
        if (not pm and utils.is_admin_for_bot(chat_id, user_id)) or pm:
            try:
                bot.send_message(user_id, tr.settings.title.format(chat_title),
                                 reply_markup=InlineKeyboardMarkup(keyboard))
                if not pm:
                    update.message.reply_text(tr.status.check_pm)
            except TelegramError:
                update.message.reply_text(text=tr.status.pm_banned,
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton(
                                                  tr.status.start_pm_button,
                                                  url=f'https://t.me/{bot.username}')
                                          ]]))
        else:
            update.message.reply_text(tr.errors.not_admin)


def lang_handler(bot, update):
    chosen_lang = update.callback_query.data.split(':')[-1]
    chat_id = int(update.callback_query.data.split(':')[1])
    tr = Localization(chat_id)
    if chosen_lang != '':
        utils.update_config(chat_id, 'lang', chosen_lang)
        update.callback_query.answer(Localization(chosen_lang).settings.changed)
        return
    lang = []
    for i, (key, item) in enumerate(Localization.available_languages.items()):
        button = InlineKeyboardButton(item, callback_data=f'settings:{chat_id}:lang:{key}')
        if i % 2 == 0:
            lang.append([button])
        else:
            lang[-1].append(button)
    lang.append([InlineKeyboardButton(tr.back, callback_data=f'settings:{chat_id}:main:')])
    update.effective_message.edit_text(tr.settings.lang_prompt, reply_markup=InlineKeyboardMarkup(lang))


def two_state_handler(bot, update):
    data = update.callback_query.data.split(':')
    chosen_option = data[-1]
    key = data[-2]
    chat_id = int(data[1])
    tr = Localization(chat_id)
    if chosen_option != '':
        chosen_option = bool(int(chosen_option))  # converting '1' to True, '0' to False
        utils.update_config(chat_id, key, chosen_option)
        if chosen_option:
            answer = tr.settings.turned_on
        else:
            answer = tr.settings.turned_off
        update.callback_query.answer(answer)
        settings(bot, update)


def two_state_helper(bot, update):
    chat_id = int(update.callback_query.data.split(':')[1])
    tr = Localization(chat_id)
    lang_key = update.callback_query.data.split(':')[-1].split('+')[1]
    update.callback_query.answer(tr.settings.captions[lang_key], show_alert=True)

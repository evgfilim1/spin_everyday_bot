# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import logging
import pickle
from datetime import datetime, timezone, time
from os.path import exists
from telegram import (ChatMember, ParseMode, Update, Bot)
from telegram.ext import BaseFilter
from functools import wraps

import config
import data

_bot = Bot(config.BOT_TOKEN)


class TelegramHandler(logging.Handler):
    def __init__(self):
        super(TelegramHandler, self).__init__()

    def emit(self, record):
        if config.LOG_CHANNEL is None:
            return
        if record.exc_info:
            record.exc_text = f'\n_Exception brief info:_\n`{record.exc_info[0].__name__}: {record.exc_info[1]}`'
        msg = self.format(record)
        _bot.send_message(chat_id=config.LOG_CHANNEL, text=msg, parse_mode=ParseMode.MARKDOWN)


class _BotReply(BaseFilter):
    def filter(self, message):
        return bool(message.reply_to_message) and message.reply_to_message.from_user.id == message.bot.id


def set_up_logger(name, level):
    _log = logging.getLogger(name)
    _log.addHandler(output_handler)
    _log.addHandler(tg_handler)
    _log.setLevel(level)
    return _log


def _migrate_to_v2():
    from shutil import copy, move
    if exists('data/unames.pkl') or (not exists('data/users.pkl') and not exists('users.pkl')):
        return  # Already migrated or nothing to migrate
    if not exists('data/users.pkl'):
        print('==> Moving your *.pkl files to data/ directory...')
        move('*.pkl', 'data/')

    print('==> Migrating bot data...')
    with open(f'data/users.pkl', 'rb') as ff:
        chats_users = pickle.load(ff)
    unames = {}

    print(' -> Extracting usernames...')
    for chat, users in chats_users.items():
        for user, name in users.items():
            unames.update({user: name})
        chats_users[chat] = list(users.keys())

    print(' -> Copying data/users.pkl to data/users.bak.pkl...')
    if exists('data/users.bak.pkl'):
        raise FileExistsError("Can't backup old data")
    copy('data/users.pkl', 'data/users.bak.pkl')

    print(' -> Saving generated data...')
    with open(f'data/users.pkl', 'wb') as ff:
        pickle.dump(chats_users, ff, pickle.HIGHEST_PROTOCOL)
    with open(f'data/unames.pkl', 'wb') as ff:
        pickle.dump(unames, ff, pickle.HIGHEST_PROTOCOL)
    print('==> Migrating completed!')


def read_update(updater, update):
    upd = Update.de_json(update, updater.bot)
    updater.update_queue.put(upd)


def init(job_queue, callback):
    _migrate_to_v2()
    for chat in data.auto_spins:
        job = job_queue.run_daily(callback, str_to_time(data.auto_spins[chat]), context=chat)
        data.auto_spin_jobs.update({chat: job})


def is_private(chat_id) -> bool:
    return chat_id > 0


def not_pm(f):
    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        msg = update.effective_message
        if is_private(msg.chat_id):
            msg.reply_text(get_lang(msg.chat_id, 'not_in_pm'))
            return
        return f(bot, update, *args, **kwargs)

    return wrapper


def flood_limit(f):
    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        chat_id = update.effective_chat.id
        count = data.flood[chat_id]
        if count == config.FLOOD_LIMIT:
            data.flood[chat_id] += 1
            update.effective_message.reply_text(get_lang(chat_id, 'flood_lim'))
        if count >= config.FLOOD_LIMIT:
            return
        else:
            data.flood[chat_id] += 1
            return f(bot, update, *args, **kwargs)

    return wrapper


def admin_only(f):
    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        chat_id = update.effective_chat.id
        if not is_admin_for_bot(chat_id, update.effective_user.id):
            update.effective_message.reply_text(get_lang(chat_id, 'not_admin'))
            return
        return f(bot, update, *args, **kwargs)

    return wrapper


def is_user_left(chat_user):
    return chat_user.status == ChatMember.LEFT or \
           chat_user.status == ChatMember.KICKED


def str_to_time(s):
    t = s.split(':')
    hours = int(t[0])
    minutes = int(t[1])
    offset = datetime.now(timezone.utc).astimezone().tzinfo.utcoffset(None).seconds // 3600
    return time((hours + offset) % 24, minutes, tzinfo=None)


def mention_markdown(user_id, name):
    return f'[{name}](tg://user?id={user_id})'


def pages(obj, page):
    total_pages = len(obj) // config.PAGE_SIZE
    begin = (page - 1) * config.PAGE_SIZE
    end = begin + config.PAGE_SIZE
    if len(obj) % config.PAGE_SIZE != 0:
        total_pages += 1
    return obj[begin:end], total_pages


def is_admin_for_bot(chat_id, user_id):
    return user_id == config.BOT_CREATOR or user_id in get_admins_ids(chat_id) or \
           user_id in data.can_change_name.get(chat_id, [])


def get_admins_ids(chat_id) -> list:
    admins = _bot.get_chat_administrators(chat_id=chat_id)
    result = [admin.user.id for admin in admins]
    return result


def update_config(chat_id, key, value):
    if data.chat_config.get(chat_id) is None:
        data.chat_config[chat_id] = {}
    data.chat_config[chat_id].update({key: value})


def get_config_key(chat_id, key, default=None):
    return data.chat_config.get(chat_id, {}).get(key, default)


def get_lang(chat_id, key):
    lang = get_config_key(chat_id, 'lang', default=config.FALLBACK_LANG)
    if data.languages.get(lang) is None or data.languages.get(lang).get(key) is None:
        lang = config.FALLBACK_LANG
    return data.languages.get(lang, {}).get(key, '!!!Translation is missing!!!')


if config.LOG_FILE is None:
    output_handler = logging.StreamHandler()
else:
    output_handler = logging.FileHandler(config.LOG_FILE)
output_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, style='{'))

tg_handler = TelegramHandler()
tg_handler.setFormatter(logging.Formatter(config.LOG_TG_FORMAT, style='{'))

bot_reply_filter = _BotReply()
log = set_up_logger(__name__, logging.INFO)

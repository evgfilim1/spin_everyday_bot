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
from collections import Counter, defaultdict

import config
import data

_bot = Bot(config.BOT_TOKEN)
migrated = False


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


def _needs_migrating():
    return not migrated and (exists('data/unames.pkl') or
                             (not exists('data/users.pkl') and not exists('users.pkl')))


def migrate_to_v2():
    global migrated
    from shutil import copy, move

    if not exists('data/users.pkl'):
        print('==> Moving your *.pkl files to data/ directory...')
        move('*.pkl', 'data/')

    print('==> Migrating bot data...')
    print(' -> (1 of 4) Extracting usernames...')
    with open(f'data/users.pkl', 'rb') as ff:
        chat_users = pickle.load(ff)
    usernames = {}
    for chat, users in chat_users.items():
        for user, name in users.items():
            usernames.update({user: name})
        chat_users[chat] = set(users.keys())

    print(' -> (2 of 4) Changing some data types...')
    chat_users = defaultdict(set, chat_users)

    with open('data/changers.pkl', 'rb') as ff:
        bot_admins = pickle.load(ff)
    for chat in bot_admins:
        bot_admins[chat] = set(bot_admins[chat])
    bot_admins = defaultdict(set, bot_admins)

    with open('data/total.pkl', 'rb') as ff:
        results = pickle.load(ff)
    for chat in results:
        results[chat] = Counter(results[chat])
    results = defaultdict(Counter, results)

    with open('data/wotdreg.pkl', 'rb') as ff:
        wotd = set(pickle.load(ff))

    print(' -> (3 of 4) Backing up data...')
    for file in ('users', 'changers', 'total', 'wotdreg'):
        if exists(f'data/{file}.bak.pkl'):
            raise FileExistsError(f"Can't backup old data: data/{file}.bak.pkl exists")
        copy(f'data/{file}.pkl', f'data/{file}.bak.pkl')

    print(' -> (4 of 4) Saving generated data...')
    with open('data/users.pkl', 'wb') as ff:
        pickle.dump(chat_users, ff, pickle.HIGHEST_PROTOCOL)
    with open('data/unames.pkl', 'wb') as ff:
        pickle.dump(usernames, ff, pickle.HIGHEST_PROTOCOL)
    with open('data/changers.pkl', 'wb') as ff:
        pickle.dump(bot_admins, ff, pickle.HIGHEST_PROTOCOL)
    with open('data/total.pkl', 'wb') as ff:
        pickle.dump(results, ff, pickle.HIGHEST_PROTOCOL)
    with open('data/wotdreg.pkl', 'wb') as ff:
        pickle.dump(wotd, ff, pickle.HIGHEST_PROTOCOL)
    print('==> Migrating completed!')
    migrated = True


def read_update(updater, update):
    upd = Update.de_json(update, updater.bot)
    updater.update_queue.put(upd)


def init(job_queue, callback):
    if _needs_migrating():
        migrate_to_v2()
    for chat in data.auto_spins:
        job = job_queue.run_daily(callback, str_to_time(data.auto_spins[chat]), context=chat)
        data.auto_spin_jobs.update({chat: job})


def is_private(chat_id) -> bool:
    return chat_id > 0


def localize(f):
    from lang import Localization

    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        locale = Localization(update.effective_chat.id)
        return f(bot, update, *args, tr=locale, **kwargs)

    return wrapper


def not_pm(f):
    from lang import Localization

    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        msg = update.effective_message
        tr = Localization(msg.chat_id)
        if is_private(msg.chat_id):
            msg.reply_text(tr.status.not_in_pm)
            return
        return f(bot, update, *args, **kwargs)

    return wrapper


def flood_limit(f):
    from lang import Localization

    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        chat_id = update.effective_chat.id
        tr = Localization(chat_id)
        count = data.flood[chat_id]
        if count == config.FLOOD_LIMIT:
            data.flood[chat_id] += 1
            update.effective_message.reply_text(tr.flood_lim)
        if count >= config.FLOOD_LIMIT:
            return
        else:
            data.flood[chat_id] += 1
            return f(bot, update, *args, **kwargs)

    return wrapper


def admin_only(f):
    from lang import Localization

    @wraps(f)
    def wrapper(bot, update, *args, **kwargs):
        chat_id = update.effective_chat.id
        tr = Localization(chat_id)
        if not is_admin_for_bot(chat_id, update.effective_user.id):
            update.effective_message.reply_text(tr.errors.not_admin)
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
    if isinstance(obj, set):
        obj = list(obj)
    total_pages = len(obj) // config.PAGE_SIZE
    begin = (page - 1) * config.PAGE_SIZE
    end = begin + config.PAGE_SIZE
    if len(obj) % config.PAGE_SIZE != 0:
        total_pages += 1
    return obj[begin:end], total_pages


def is_admin_for_bot(chat_id, user_id):
    return user_id == config.BOT_CREATOR or user_id in get_admins_ids(chat_id) or \
           user_id in data.can_change_name[chat_id]


def get_admins_ids(chat_id):
    admins = _bot.get_chat_administrators(chat_id=chat_id)
    result = [admin.user.id for admin in admins]
    return result


def update_config(chat_id, key, value):
    if data.chat_config.get(chat_id) is None:
        data.chat_config[chat_id] = {}
    data.chat_config[chat_id].update({key: value})


def get_config_key(chat_id, key, default=None):
    return data.chat_config.get(chat_id, {}).get(key, default)


# def get_lang(chat_id, key):
#     from warnings import warn
#     from lang import Localization
#     warn(f'utils.get_lang is deprecated, use lang.Localization instead', DeprecationWarning, stacklevel=1)
#     return Localization('ru_old')[key]


if config.LOG_FILE is None:
    output_handler = logging.StreamHandler()
else:
    output_handler = logging.FileHandler(config.LOG_FILE)
output_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, style='{'))

tg_handler = TelegramHandler()
tg_handler.setFormatter(logging.Formatter(config.LOG_TG_FORMAT, style='{'))

bot_reply_filter = _BotReply()
log = set_up_logger(__name__, logging.INFO)

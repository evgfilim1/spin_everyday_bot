# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import pickle
from datetime import time

from telegram import (ChatMember, ParseMode, TelegramError, Update, Bot)
from telegram.ext import JobQueue, BaseFilter
from telegram.ext.dispatcher import run_async
from os.path import exists
import logging

import config


class TelegramHandler(logging.Handler):
    def __init__(self, bot: Bot):
        super(TelegramHandler, self).__init__()
        self.bot = bot

    def emit(self, record):
        if config.LOG_CHANNEL is None:
            return
        if record.exc_info:
            record.exc_text = f"\n_Exception brief info:_\n`{record.exc_info[0].__name__}: {record.exc_info[1]}`"
        msg = self.format(record)
        self.bot.send_message(chat_id=config.LOG_CHANNEL, text=msg, parse_mode=ParseMode.MARKDOWN)


class _BotReply(BaseFilter):
    def filter(self, message):
        return bool(message.reply_to_message) and message.reply_to_message.from_user.id == message.bot.id


bot_reply_filter = _BotReply()

chat_users = {}
usernames = {}
spin_name = {}
can_change_name = {}
results_today = {}
results_total = {}
auto_spins = {}
auto_spin_jobs = {}
chat_config = {}
languages = {}
wotd_registered = []
wotd = 0
chat_texts = {}

announcement_chats = []
log = None
if config.LOG_FILE is None:
    handler = logging.StreamHandler()
else:
    handler = logging.FileHandler(config.LOG_FILE)
handler.setFormatter(logging.Formatter(config.LOG_FORMAT, style='{'))


def _migrate_to_v2():
    from shutil import copy, move
    if exists("data/unames.pkl") or (not exists("data/users.pkl") and not exists("users.pkl")):
        return  # Already migrated or nothing to migrate
    if not exists("data/users.pkl"):
        print("==> Moving your *.pkl files to data/ directory...")
        move('*.pkl', 'data/')
    print("==> Migrating bot data...")
    chats_users = _load("users.pkl")
    unames = {}
    print(" -> Extracting usernames...")
    for chat, users in chats_users.items():
        for user, name in users.items():
            unames.update({user: name})
        chats_users[chat] = list(users.keys())
    print(" -> Copying data/users.pkl to data/users.bak.pkl...")
    if exists("data/users.bak.pkl"):
        raise FileExistsError("Can't backup old data")
    copy("data/users.pkl", "data/users.bak.pkl")
    print(" -> Saving generated data...")
    _save(chats_users, "users.pkl")
    _save(unames, "unames.pkl")
    print("==> Migrating completed!")


def read_update(updater, update):
    upd = Update.de_json(update, updater.bot)
    updater.update_queue.put(upd)


def init(*, bot: Bot, job_queue: JobQueue, callback: callable):
    _migrate_to_v2()
    _load_all()
    _configure_logging(bot)
    for chat in auto_spins:
        job = job_queue.run_daily(callback, str_to_time(auto_spins[chat]), context=chat)
        auto_spin_jobs.update({chat: job})


def _configure_logging(bot: Bot):
    global log
    tg_handler = TelegramHandler(bot)
    tg_handler.setFormatter(logging.Formatter(config.LOG_TG_FORMAT, style='{'))
    log = logging.getLogger(__name__)
    log.addHandler(handler)
    log.addHandler(tg_handler)
    log.setLevel(logging.INFO)


def is_private(chat_id: int) -> bool:
    return chat_id > 0


def not_pm(f: callable):
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        msg = update.effective_message
        if is_private(msg.chat_id):
            msg.reply_text(get_lang(msg.chat_id, 'not_in_pm'))
            return
        return f(bot, update, *args, **kwargs)

    return wrapper


def _load(filename: str, default: type = dict):
    if not exists(f'data/{filename}'):
        return default()
    with open(f'data/{filename}', 'rb') as ff:
        return pickle.load(ff)


def _save(obj, filename: str):
    with open(f'data/{filename}', 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def _load_lang():
    from os import listdir
    from yaml import load
    for lang in listdir("lang"):
        if not lang.endswith(".yaml"):
            continue
        with open(f"lang/{lang}", encoding='utf-8') as file:
            strings = load(file)
        lang = lang[:-5]
        languages.update({lang: strings})


def _load_all():
    global chat_users, usernames, spin_name, can_change_name, results_today, results_total
    global auto_spins, chat_config, wotd_registered, wotd, chat_texts
    chat_users = _load("users.pkl")
    usernames = _load("unames.pkl")
    spin_name = _load("spin.pkl")
    can_change_name = _load("changers.pkl")
    results_today = _load("results.pkl")
    results_total = _load("total.pkl")
    auto_spins = _load("auto.pkl")
    chat_config = _load("config.pkl")
    wotd_registered = _load("wotdreg.pkl", default=list)
    wotd = _load("wotdwin.pkl", default=int)
    chat_texts = _load("texts.pkl")
    _load_lang()


def save_all():
    _save(chat_users, "users.pkl")
    _save(spin_name, "spin.pkl")
    _save(can_change_name, "changers.pkl")
    _save(results_today, "results.pkl")
    _save(results_total, "total.pkl")
    _save(auto_spins, "auto.pkl")
    _save(chat_config, "config.pkl")
    _save(usernames, "unames.pkl")
    _save(wotd, "wotdwin.pkl")
    _save(wotd_registered, "wotdreg.pkl")
    _save(chat_texts, "texts.pkl")
    log.debug('Data saved')


def clear_data(chat_id: int):
    log.info(f"Clearing data of chat {chat_id}")
    chat_users.pop(chat_id)
    try:
        spin_name.pop(chat_id)
    except KeyError:
        pass

    try:
        can_change_name.pop(chat_id)
    except KeyError:
        pass

    try:
        results_today.pop(chat_id)
    except KeyError:
        pass


def migrate(from_chat: int, to_chat: int):
    log.info(f"Migrating from {from_chat} to {to_chat}")
    chat_users.update({to_chat: chat_users.get(from_chat)})
    spin_name.update({to_chat: spin_name.get(from_chat)})
    can_change_name.update({to_chat: can_change_name.get(from_chat)})
    results_today.update({to_chat: results_today.get(from_chat)})
    clear_data(from_chat)


def is_user_left(chat_user: ChatMember) -> bool:
    return chat_user.status == ChatMember.LEFT or \
           chat_user.status == ChatMember.KICKED


def str_to_time(s: str) -> time:
    from datetime import datetime, timezone
    t = s.split(':')
    hours = int(t[0])
    minutes = int(t[1])
    offset = datetime.now(timezone.utc).astimezone().tzinfo.utcoffset(None).seconds // 3600
    return time((hours + offset) % 24, minutes, tzinfo=None)


def mention_markdown(user_id: int, name: str) -> str:
    return f'[{name}](tg://user?id={user_id})'


def choose_random_user(chat_id: int, bot: Bot) -> int:
    global wotd
    from random import choice
    if chat_id:
        user_id = choice(chat_users[chat_id])
        try:
            member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if is_user_left(member):
                raise TelegramError("User left the group")
        except TelegramError as e:
            chat_users[chat_id].pop(chat_users[chat_id].index(user_id))
            log.debug(f"{e}. User_id: {user_id}, chat_id: {chat_id}")
            return choose_random_user(chat_id, bot)
        user = member.user
    else:
        user_id = choice(wotd_registered)
        user = bot.get_chat(user_id)
    if user.first_name == '':
        usernames.update({user_id: f"DELETED/id{user_id}"})
        return choose_random_user(chat_id, bot)
    if user.username:
        name = f'@{user.username}'
    elif user.last_name:
        name = f'{user.first_name} {user.last_name}'
    else:
        name = user.first_name
    if chat_id:
        results_today.update({chat_id: user.id})
        if chat_id not in results_total:
            results_total.update({chat_id: {}})
        results_total[chat_id].update({user.id: results_total[chat_id].get(user.id, 0) + 1})
    else:
        wotd = user.id
    usernames.update({user.id: name})
    return user.id


def pages(obj, page: int):
    total_pages = len(obj) // config.PAGE_SIZE
    begin = (page - 1) * config.PAGE_SIZE
    end = begin + config.PAGE_SIZE
    if len(obj) % config.PAGE_SIZE != 0:
        total_pages += 1
    return obj[begin:end], total_pages


def top_win(chat_id: int) -> list:
    return sorted(results_total.get(chat_id, {}).items(), key=lambda x: x[1], reverse=True)


def make_top(chat_id: int, *, page: int) -> (str, int):
    winners = top_win(chat_id)
    winners, total_pages = pages(winners, page)
    text = get_lang(chat_id, 'stats_all').format(page, total_pages)
    for user in winners:
        username = usernames.get(user[0], f"id{user[0]}")
        text += get_lang(chat_id, 'stats_user_short').format(username, user[1])
    return text, total_pages


def make_userlist(chat_id: int, page: int) -> (str, int):
    users, total_pages = pages(chat_users[chat_id], page)
    text = get_lang(chat_id, 'list').format(page, total_pages)
    for user in users:
        username = usernames.get(user, f'id{user}')
        text += f'`{username}`\n'
    return text, total_pages


def is_admin_for_bot(chat_id: int, user_id: int, bot: Bot) -> bool:
    return user_id == config.BOT_CREATOR or user_id in get_admins_ids(bot, chat_id) or \
           user_id in can_change_name.get(chat_id, [])


@run_async
def announce(bot: Bot, text: str, md: bool = False):
    from time import sleep
    # Sending announcement to 15 chats, then sleep
    sleep_border = 15
    announcement_chats.extend(chat_users.keys())
    text = text.replace("\\n", "\n")
    while len(announcement_chats) > 0:
        chat = announcement_chats.pop()
        try:
            if md:
                bot.send_message(chat_id=chat, text=text, parse_mode=ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=chat, text=text)
            sleep_border -= 1
        except TelegramError:
            log.warning(f"Chat {chat} is not reachable for messages, deleting it")
            chat_users.pop(chat)
            # pass
        if sleep_border == 0:
            sleep(5)
            sleep_border = 15


def get_admins_ids(bot: Bot, chat_id: int) -> list:
    admins = bot.get_chat_administrators(chat_id=chat_id)
    result = [admin.user.id for admin in admins]
    return result


def update_config(chat_id: int, key, value):
    if chat_config.get(chat_id) is None:
        chat_config[chat_id] = {}
    chat_config[chat_id].update({key: value})


def get_config_key(chat_id: int, key, default=None):
    return chat_config.get(chat_id, {}).get(key, default)


def get_lang(chat_id: int, key: str):
    lang = get_config_key(chat_id, 'lang', default=config.FALLBACK_LANG)
    if languages.get(lang) is None or languages.get(lang).get(key) is None:
        lang = config.FALLBACK_LANG
    return languages.get(lang, {}).get(key, "!!!Translation is missing!!!")

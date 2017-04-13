import pickle
from datetime import datetime

from telegram import (ChatMember, ParseMode, TelegramError,
                      User, Update, Message, Bot)
from telegram.ext import Job, JobQueue
from telegram.ext.dispatcher import run_async
import logging

import config


class TelegramHandler(logging.Handler):
    def __init__(self, bot: Bot):
        logging.Handler.__init__(self)
        self.bot = bot

    def emit(self, record):
        if record.exc_info:
            record.exc_text = f"\n_Exception brief info:_\n`{record.exc_info[0].__name__}: {record.exc_info[1]}`"
        msg = self.format(record)
        self.bot.send_message(chat_id=config.LOG_CHANNEL, text=msg, parse_mode=ParseMode.MARKDOWN)

chat_users = {}
spin_name = {}
can_change_name = {}
results_today = {}
results_total = {}
auto_spins = {}
auto_spin_jobs = {}

announcement_chats = []
log = None
file_handler = logging.FileHandler(config.LOG_FILE)
file_handler.setFormatter(logging.Formatter(config.LOG_FILE_FORMAT, style='{'))


def read_update(updater, update):
    upd = Update.de_json(update, updater.bot)
    updater.update_queue.put(upd)


def init(*, bot: Bot, job_queue: JobQueue, callback: callable):
    _load_all()
    _configure_logging(bot)
    for chat in auto_spins:
        job = Job(callback, 86400.0, context=auto_spins[chat])
        job_queue.put(job, next_t=time_diff(auto_spins[chat]))
        auto_spin_jobs.update({chat: job})


def _configure_logging(bot: Bot):
    global log
    tg_handler = TelegramHandler(bot)
    tg_handler.setFormatter(logging.Formatter(config.LOG_TG_FORMAT, style='{'))
    log = logging.getLogger(__name__)
    log.addHandler(file_handler)
    log.addHandler(tg_handler)
    log.setLevel(logging.INFO)


def _check_destination(bot_name: str, message_text: str) -> bool:
    msg = message_text.split()
    msg = msg[0].split('@')
    msg.append('')
    return msg[1] == bot_name or msg[1] == ''


def is_private(chat_id: int) -> bool:
    return chat_id > 0


def not_pm(f: callable):
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        msg = get_message(update)
        if is_private(msg.chat_id):
            msg.reply_text("Эта команда недоступна в ЛС")
            return
        f(bot, update, *args, **kwargs)

    return wrapper


def check_destination(f: callable):
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        msg = get_message(update)
        if not _check_destination(bot.username, msg.text):
            return
        f(bot, update, *args, **kwargs)

    return wrapper


def get_name(user: User) -> str:
    if bool(user.username):
        return '@' + user.username
    else:
        return user.first_name


def _load(filename: str) -> dict:
    with open(filename, 'rb') as ff:
        return pickle.load(ff)


def _save(obj: dict, filename: str):
    with open(filename, 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def _load_all():
    global chat_users, spin_name, can_change_name, results_today, results_total
    global auto_spins
    if not __import__("os").path.exists("users.pkl"):
        return
    chat_users = _load("users.pkl")
    spin_name = _load("spin.pkl")
    can_change_name = _load("changers.pkl")
    results_today = _load("results.pkl")
    results_total = _load("total.pkl")
    auto_spins = _load("auto.pkl")


def save_all():
    _save(chat_users, "users.pkl")
    _save(spin_name, "spin.pkl")
    _save(can_change_name, "changers.pkl")
    _save(results_today, "results.pkl")
    _save(results_total, "total.pkl")
    _save(auto_spins, "auto.pkl")


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


def time_diff(t: str=config.RESET_TIME) -> float:
    t = t.split(':')
    # now = datetime.now()
    now = datetime.utcnow()
    then = datetime(2017, 1, 1, int(t[0]), int(t[1]))
    diff = then - now
    delta = float(diff.seconds) + (diff.microseconds / 10 ** 6)
    return delta


def get_message(update: Update) -> Message:
    return update.message or update.edited_message


def choose_random_user(chat_id: int, bot: Bot) -> str:
    from random import choice
    user = choice(list(chat_users[chat_id].items()))  # Getting tuple (user_id, username)
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user[0])
        if is_user_left(member):
            raise TelegramError("User left the group")
        if get_name(member.user) == '':
            raise TelegramError("User deleted from Telegram")
    except TelegramError as e:
        chat_users[chat_id].pop(user[0])
        log.debug(f"{e}. User info: {user}, chat_id: {chat_id}")
        return choose_random_user(chat_id, bot)
    user = get_name(member.user)
    uid = member.user.id
    results_today.update({chat_id: user})
    chat_users[chat_id].update({uid: user})
    if chat_id not in results_total:
        results_total.update({chat_id: {}})
    results_total[chat_id].update({uid: results_total[chat_id].get(uid, 0) + 1})
    return user


def top_win(chat_id: int) -> list:
    return sorted(results_total.get(chat_id, {}).items(), key=lambda x: x[1], reverse=True)


def make_top(chat_id: int, *, page: int) -> (str, int):
    winners = top_win(chat_id)
    total_pages = len(winners) // config.TOP_PAGE_SIZE
    begin = (page - 1) * config.TOP_PAGE_SIZE
    end = begin + config.TOP_PAGE_SIZE
    if len(winners) % config.TOP_PAGE_SIZE != 0:
        total_pages += 1
    text = f"Статистика пользователей в данном чате: (страница {page} из {total_pages})\n"
    for user in winners[begin:end]:
        username = chat_users[chat_id].get(user[0], f"id{user[0]}")
        text += f"*{username}*: {user[1]} раз(а)\n"
    return text, total_pages


def can_change_spin_name(chat_id: int, user_id: int, bot: Bot) -> bool:
    return user_id in get_admins_ids(bot, chat_id) or \
           user_id in can_change_name[chat_id] or user_id == config.BOT_CREATOR


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


def fix_md(text: str) -> str:
    md_symbols = '*_`['
    for symbol in md_symbols:
        try:
            text = text.replace(symbol, '\\' + symbol)
        except AttributeError:
            break
    return text

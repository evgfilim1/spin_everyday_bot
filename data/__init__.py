# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import pickle
from os import listdir
from os.path import exists
from yaml import load
from collections import Counter

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
flood = Counter()


def _load(filename: str, default: type = dict):
    if not exists(f'data/{filename}'):
        return default()
    with open(f'data/{filename}', 'rb') as ff:
        return pickle.load(ff)


def _save(obj, filename: str):
    with open(f'data/{filename}', 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def _load_lang():
    for lang in listdir('lang'):
        if not lang.endswith('.yaml'):
            continue
        with open(f'lang/{lang}', encoding='utf-8') as file:
            strings = load(file)
        lang = lang[:-5]  # Throw extension away
        languages.update({lang: strings})


def _load_all():
    global chat_users, usernames, spin_name, can_change_name, results_today, results_total, auto_spins
    global chat_config, wotd_registered, wotd, chat_texts
    chat_users = _load('users.pkl')
    usernames = _load('unames.pkl')
    spin_name = _load('spin.pkl')
    can_change_name = _load('changers.pkl')
    results_today = _load('results.pkl')
    results_total = _load('total.pkl')
    auto_spins = _load('auto.pkl')
    chat_config = _load('config.pkl')
    wotd_registered = _load('wotdreg.pkl', default=list)
    wotd = _load('wotdwin.pkl', default=int)
    chat_texts = _load('texts.pkl')
    _load_lang()


def save_all():
    _save(chat_users, 'users.pkl')
    _save(spin_name, 'spin.pkl')
    _save(can_change_name, 'changers.pkl')
    _save(results_today, 'results.pkl')
    _save(results_total, 'total.pkl')
    _save(auto_spins, 'auto.pkl')
    _save(chat_config, 'config.pkl')
    _save(usernames, 'unames.pkl')
    _save(wotd, 'wotdwin.pkl')
    _save(wotd_registered, 'wotdreg.pkl')
    _save(chat_texts, 'texts.pkl')


def clear_chat_data(chat_id):
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


def migrate(from_chat, to_chat):
    chat_users.update({to_chat: chat_users.get(from_chat)})
    spin_name.update({to_chat: spin_name.get(from_chat)})
    can_change_name.update({to_chat: can_change_name.get(from_chat)})
    results_today.update({to_chat: results_today.get(from_chat)})
    clear_chat_data(from_chat)


_load_all()

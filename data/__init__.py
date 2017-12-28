# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import pickle
from os.path import exists
from collections import Counter, defaultdict
from functools import partial

chat_users = defaultdict(set)           # {chat_id[int]: {user_id0[int], user_id1[int]}}
usernames = {}                          # {user_id[int]: username[str]}
spin_name = {}                          # {chat_id[int]: name[str]}
can_change_name = defaultdict(set)      # {chat_id[int]: {user_id0[int], user_id1[int]}}
results_today = {}                      # {chat_id[int]: user_id[int]}
results_total = defaultdict(Counter)    # {chat_id[int]: Counter({user_id[int]: count[int]})}
auto_spins = {}                         # {chat_id[int]: time[str]}
auto_spin_jobs = {}                     # {chat_id[int]: job[telegram.ext.JobQueue.Job]}
chat_config = {}                        # {chat_id[int]: {key[str]: value[bool|str]}
wotd_registered = set()                 # {user_id0[int], user_id1[int]}
wotd = 0                                # wotd[int]
chat_texts = {}                         # {chat_id: [[line1[str], line2[str]]}
flood = Counter()                       # Counter({chat_id[int]: messages[int]})


def _load(filename: str, default: type = dict):
    if not exists(f'data/{filename}'):
        return default()
    with open(f'data/{filename}', 'rb') as ff:
        return pickle.load(ff)


def _save(obj, filename: str):
    with open(f'data/{filename}', 'wb') as ff:
        pickle.dump(obj, ff, pickle.HIGHEST_PROTOCOL)


def _load_all():
    from lang import Localization
    global chat_users, usernames, spin_name, can_change_name, results_today, results_total, auto_spins
    global chat_config, wotd_registered, wotd, chat_texts
    p_set = partial(defaultdict, set)
    p_counter = partial(defaultdict, Counter)
    chat_users = _load('users.pkl', default=p_set)
    usernames = _load('unames.pkl')
    spin_name = _load('spin.pkl')
    can_change_name = _load('changers.pkl', default=p_set)
    results_today = _load('results.pkl')
    results_total = _load('total.pkl', default=p_counter)
    auto_spins = _load('auto.pkl')
    chat_config = _load('config.pkl')
    wotd_registered = _load('wotdreg.pkl', default=set)
    wotd = _load('wotdwin.pkl', default=int)
    chat_texts = _load('texts.pkl')
    Localization.reload()


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
    if chat_id in can_change_name:
        can_change_name.pop(chat_id)
    if chat_id in results_total:
        results_total.pop(chat_id)
    if chat_id in auto_spins:
        auto_spins.pop(chat_id)
        auto_spin_jobs.pop(chat_id).schedule_removal()
    if chat_id in chat_config:
        chat_config.pop(chat_id)
    if chat_id in chat_texts:
        chat_texts.pop(chat_id)


def migrate(from_chat, to_chat):
    chat_users.update({to_chat: chat_users.get(from_chat)})
    spin_name.update({to_chat: spin_name.get(from_chat)})
    can_change_name.update({to_chat: can_change_name.get(from_chat)})
    results_today.update({to_chat: results_today.get(from_chat)})
    clear_chat_data(from_chat)


_load_all()

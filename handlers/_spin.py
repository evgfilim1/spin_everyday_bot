# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode, TelegramError, Update, Message, Chat
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown
from random import choice

import data
import utils

locks = []


def auto_spin(bot, job):
    u = Update(0, message=Message(0, None, 0, Chat(job.context, '')))
    if data.results_today.get(job.context) is None:
        do_the_spin(bot, u)


@run_async
@utils.flood_limit
@utils.not_pm
def do_the_spin(bot, update):
    chat_id = update.message.chat_id
    spin_name = escape_markdown(data.spin_name.get(chat_id, utils.get_lang(chat_id, 'default_spin_name')))
    winner = data.results_today.get(chat_id)
    if chat_id in locks:
        return
    if winner is not None:
        name = data.usernames.get(winner, f'id{winner}')
        if not name.startswith('@'):
            name = utils.mention_markdown(winner, name)
        else:
            name = escape_markdown(name)
        bot.send_message(chat_id=chat_id, text=utils.get_lang(chat_id, 'already_spin').format(s=spin_name, n=name),
                         parse_mode=ParseMode.MARKDOWN, disable_notification=True)
    else:
        if utils.get_config_key(chat_id, 'restrict', default=False) and \
                not utils.is_admin_for_bot(chat_id, update.message.from_user.id):
            update.message.reply_text(utils.get_lang(chat_id, 'spin_restricted'))
            return
        user = choose_random_user(chat_id, bot)
        winner = data.usernames.get(user)
        if not winner.startswith('@'):
            winner = utils.mention_markdown(user, winner)
        else:
            winner = escape_markdown(winner)
        from time import sleep
        spin_texts = utils.get_lang(chat_id, 'default_spin_texts').copy()
        if chat_id in data.chat_texts:
            spin_texts += data.chat_texts[chat_id]
        curr_text = choice(spin_texts)
        locks.append(chat_id)
        if utils.get_config_key(chat_id, 'fast', default=False):
            bot.send_message(chat_id=chat_id, text=curr_text[-1].format(s=spin_name, n=winner),
                             parse_mode=ParseMode.MARKDOWN)
        else:
            for t in curr_text:
                bot.send_message(chat_id=chat_id, text=t.format(s=spin_name, n=winner),
                                 parse_mode=ParseMode.MARKDOWN)
                sleep(2)
        locks.pop(locks.index(chat_id))


@utils.flood_limit
@utils.not_pm
def change_spin_name(bot, update, args: list):
    msg = update.effective_message
    if len(args) == 0:
        spin = data.spin_name.get(msg.chat_id, utils.get_lang(msg.chat_id, 'default_spin_name'))
        msg.reply_text(text=utils.get_lang(msg.chat_id, 'spin_name_current').format(spin),
                       parse_mode=ParseMode.MARKDOWN)
        return
    if utils.is_admin_for_bot(msg.chat_id, msg.from_user.id):
        if args[-1].lower() == utils.get_lang(msg.chat_id, 'spin_suffix') and len(args) > 1:
            args.pop(-1)
        spin = ' '.join(args)
        data.spin_name[msg.chat_id] = spin
        msg.reply_text(text=utils.get_lang(msg.chat_id, 'spin_name_changed').format(spin),
                       parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text(utils.get_lang(msg.chat_id, 'not_admin'))


@utils.flood_limit
@utils.not_pm
def auto_spin_config(bot, update, args, job_queue):
    msg = update.effective_message
    if len(args) == 0:
        return
    is_moder = utils.is_admin_for_bot(msg.chat_id, msg.from_user.id)
    cmd = args.pop(0)
    if cmd == 'set' and is_moder:
        try:
            time = args[0].split(':')
            time = '{:0>2}:{:0>2}'.format(time[0], time[1])
            job = job_queue.run_daily(auto_spin, utils.str_to_time(time), context=msg.chat_id)
            if msg.chat_id in data.auto_spins:
                data.auto_spin_jobs[msg.chat_id].schedule_removal()
        except (ValueError, IndexError):
            msg.reply_text(utils.get_lang(msg.chat_id, 'time_error'))
            return

        data.auto_spins.update({msg.chat_id: time})
        data.auto_spin_jobs.update({msg.chat_id: job})
        msg.reply_text(utils.get_lang(update.effective_chat.id, 'auto_spin_on').format(time))
    elif cmd == 'del' and is_moder:
        if msg.chat_id in data.auto_spins:
            data.auto_spin_jobs.pop(msg.chat_id).schedule_removal()
            data.auto_spins.pop(msg.chat_id)
            msg.reply_text(utils.get_lang(msg.chat_id, 'auto_spin_set_off'))
        else:
            msg.reply_text(utils.get_lang(msg.chat_id, 'auto_spin_still_off'))
    elif cmd == 'status':
        if msg.chat_id in data.auto_spins:
            msg.reply_text(utils.get_lang(msg.chat_id, 'auto_spin_on').format(data.auto_spins.get(msg.chat_id)))
        else:
            msg.reply_text(utils.get_lang(msg.chat_id, 'auto_spin_off'))
    elif not is_moder:
        msg.reply_text(utils.get_lang(msg.chat_id, 'not_admin'))


def choose_random_user(chat_id, bot) -> int:
    if chat_id:
        user_id = choice(tuple(data.chat_users[chat_id]))
        try:
            member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if utils.is_user_left(member):
                raise TelegramError('User left the group')
        except TelegramError:
            data.chat_users[chat_id].discard(user_id)
            return choose_random_user(chat_id, bot)
        user = member.user
    else:
        user_id = choice(tuple(data.wotd_registered))
        user = bot.get_chat(user_id)
    if user.first_name == '':
        data.usernames.update({user_id: f'DELETED/id{user_id}'})
        return choose_random_user(chat_id, bot)
    if user.username:
        name = f'@{user.username}'
    elif user.last_name:
        name = f'{user.first_name} {user.last_name}'
    else:
        name = user.first_name
    if chat_id:
        data.results_today.update({chat_id: user.id})
        data.results_total[chat_id][user.id] += 1
    else:
        data.wotd = user.id
    data.usernames.update({user.id: name})
    return user.id

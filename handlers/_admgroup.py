# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from telegram import ParseMode

import data
import utils
import config


@utils.flood_limit
@utils.not_pm
def admin_ctrl(bot, update, args):
    msg = update.effective_message
    reply = msg.reply_to_message
    admins = utils.get_admins_ids(msg.chat_id)
    admins.append(config.BOT_CREATOR)
    is_admin = msg.from_user.id in admins
    if len(args) == 0:
        return
    cmd = args.pop(0)
    if msg.chat_id not in data.can_change_name:
        data.can_change_name[msg.chat_id] = []
    if cmd == 'add' and reply and is_admin:
        if utils.is_admin_for_bot(msg.chat_id, reply.from_user.id):
            msg.reply_text(text=utils.get_lang(msg.chat_id, 'admin_still_allow'),
                           parse_mode=ParseMode.MARKDOWN)
        else:
            data.can_change_name[msg.chat_id].append(reply.from_user.id)
            msg.reply_text(text=utils.get_lang(msg.chat_id, 'admin_allow'),
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == 'del' and reply and is_admin:
        if not utils.is_admin_for_bot(msg.chat_id, reply.from_user.id):
            msg.reply_text(text=utils.get_lang(msg.chat_id, 'admin_still_deny'),
                           parse_mode=ParseMode.MARKDOWN)
        else:
            index = data.can_change_name[msg.chat_id].index(reply.from_user.id)
            data.can_change_name[msg.chat_id].pop(index)
            msg.reply_text(text=utils.get_lang(msg.chat_id, 'admin_deny'),
                           parse_mode=ParseMode.MARKDOWN)
    elif cmd == 'list':
        users = ''
        for user in data.can_change_name[msg.chat_id]:
            users += data.usernames.get(user, f'id{user}') + '\n'
        text = utils.get_lang(msg.chat_id, 'admin_list').format(users)
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

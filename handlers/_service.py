# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from logging import DEBUG
from telegram.error import TimedOut

import data
import utils
import config
from ._help import start_help_handler

log = utils.set_up_logger(__name__, DEBUG)


@utils.localize
def handle_error(bot, update, error, tr):
    if (isinstance(error, TimedOut) or update is None) and config.LOG_CHANNEL is not None:
        return
    log.error(f'Update {update} caused error: {error}')
    if config.SHOW_ERRORS:
        update.effective_message.reply_text(tr.error)


def update_cache(bot, update):
    user = update.effective_user
    chat_id = update.effective_message.chat_id
    # Also skip first update when the bot is added
    if not utils.is_private(chat_id):
        if user.id not in data.chat_users[chat_id]:
            data.chat_users[chat_id].add(user.id)
        if user.name != data.usernames.get(user.id):
            data.usernames.update({user.id: user.name})


def svc_handler(bot, update):
    chat_id = update.message.chat_id
    migrate_to_id = update.message.migrate_to_chat_id
    new_members = update.message.new_chat_members
    left_member = update.message.left_chat_member
    if update.message.group_chat_created or \
            (len(new_members) != 0 and any(new_member.id == bot.id for new_member in new_members)):
        # TODO: add admins to the list
        log.debug(f'New chat! ({chat_id})')
        start_help_handler(bot, update, [])
    elif new_members:
        for new_member in new_members:
            if new_member.is_bot:
                return
            if new_member.id not in data.chat_users[chat_id]:
                data.chat_users[chat_id].add(new_member.id)
            data.usernames.update({new_member.id: new_member.name})
    elif migrate_to_id:
        log.debug(f'Migrating from {chat_id} to {migrate_to_id}')
        data.migrate(chat_id, migrate_to_id)
    elif left_member and left_member.id == bot.id:
        log.debug(f'Clearing data of chat {chat_id}')
        data.clear_chat_data(chat_id)
    elif left_member:
        if left_member.is_bot:
            return
        data.chat_users[chat_id].discard(left_member.id)

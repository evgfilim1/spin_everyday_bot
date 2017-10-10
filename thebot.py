# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters, ConversationHandler)
from datetime import datetime
from time import gmtime

import config
import data
import utils
import handlers

ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']


# Set all logging time in UTC
logging.Formatter.converter = gmtime

log = utils.set_up_logger(__name__, logging.DEBUG)
updater = Updater(config.BOT_TOKEN, workers=8)
jobs = updater.job_queue
dp = updater.dispatcher

utils.set_up_logger('telegram.ext', logging.INFO)
utils.set_up_logger('TeleSocket', logging.INFO)

jobs.run_repeating(handlers.hourly_job, 60)
jobs.run_daily(handlers.daily_job, utils.str_to_time(config.RESET_TIME))

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler('feedback', handlers.ask_feedback)],
    states={
        0: [MessageHandler(utils.bot_reply_filter & (Filters.text | Filters.photo | Filters.document),
                           handlers.send_feedback)]
    },
    fallbacks=[CommandHandler('cancel', handlers.cancel_conversation)]
)

new_text_handler = ConversationHandler(
    entry_points=[CommandHandler('newtext', handlers.new_text, pass_chat_data=True)],
    states={
        0: [MessageHandler(Filters.text, handlers.fill_text, pass_chat_data=True)]
    },
    fallbacks=[CommandHandler('cancel', handlers.cancel_conversation, pass_chat_data=True),
               CommandHandler('done', handlers.record_text, pass_chat_data=True),
               CommandHandler('remove', handlers.remove_text, pass_chat_data=True)]
)

dp.add_handler(CommandHandler(['start', 'help'], handlers.start_help_handler, pass_args=True))
dp.add_handler(CommandHandler('about', handlers.about))
dp.add_handler(CommandHandler('admgroup', handlers.admin_ctrl, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('sudo', handlers.sudo, pass_args=True, allow_edited=True,
                              filters=Filters.user(user_id=config.BOT_CREATOR)))
dp.add_handler(CommandHandler('ping', handlers.ping))
dp.add_handler(CommandHandler('setname', handlers.change_spin_name, pass_args=True, allow_edited=True))
dp.add_handler(CommandHandler('count', handlers.spin_count))
dp.add_handler(CommandHandler('userlist', handlers.user_list))
dp.add_handler(CommandHandler('spin', handlers.do_the_spin))
dp.add_handler(CommandHandler('auto', handlers.auto_spin_config, pass_args=True, allow_edited=True,
                              pass_job_queue=True))
dp.add_handler(CommandHandler('stat', handlers.top, pass_args=True))
dp.add_handler(CommandHandler('settings', handlers.settings_command))
dp.add_handler(CommandHandler('uptime', handlers.uptime))
dp.add_handler(CommandHandler('winner', handlers.wotd, pass_args=True))
dp.add_handler(CommandHandler('chattexts', handlers.list_text))
dp.add_handler(new_text_handler)
dp.add_handler(feedback_handler)
dp.add_handler(MessageHandler(Filters.status_update, handlers.svc_handler))
dp.add_handler(CallbackQueryHandler(handlers.pages_handler, pattern=r'^(top|userlist):page_[1-9]+[0-9]*$'))
dp.add_handler(CallbackQueryHandler(handlers.text_handler, pattern=r'^texts:[1-9]+[0-9]*:(del)?$'))
dp.add_handler(CallbackQueryHandler(handlers.help_button_handler, pattern=r'^help:.+$'))
dp.add_handler(CallbackQueryHandler(handlers.settings, pattern=r'^settings:-?\d+:main:$'))
dp.add_handler(CallbackQueryHandler(handlers.lang_handler, pattern=r'^settings:-?\d+:lang:\w*$'))
dp.add_handler(CallbackQueryHandler(handlers.two_state_handler, pattern=r'^settings:-?\d+:[a-z_]+:[01]$'))
dp.add_handler(CallbackQueryHandler(handlers.two_state_helper, pattern=r'^settings:-?\d+:[a-z_]+:help\+[a-z_]+$'))
dp.add_handler(MessageHandler(Filters.all, handlers.update_cache, edited_updates=True), group=-1)

dp.add_error_handler(handlers.handle_error)

utils.init(job_queue=updater.job_queue, callback=handlers.auto_spin)

if config.TELESOCKET_TOKEN:
    from TeleSocketClient import TeleSocket
    updater.bot.set_webhook()
    sock = TeleSocket()
    sock.login(config.TELESOCKET_TOKEN)
    sock.add_telegram_handler(lambda update: utils.read_update(updater, update))
    webhook = sock.set_webhook(updater.bot.username)
    updater._clean_updates()
    updater.bot.set_webhook(url=webhook.url, allowed_updates=ALLOWED_UPDATES)
    updater.job_queue.start()
    updater._init_thread(updater.dispatcher.start, 'dispatcher')
    updater.running = True
else:
    updater.start_polling(clean=True, allowed_updates=ALLOWED_UPDATES)

log.info('Bot started')
handlers.bot_started()
utils.start_time = datetime.now()
updater.idle()

data.save_all()
log.info('Bot stopped')

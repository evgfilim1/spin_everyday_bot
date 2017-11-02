# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

# This is example bot settings file.

# You can find out necessary IDs from @ShowJsonBot

# Repository URL to be shown in /about
REPO_URL = 'https://github.com/evgfilim1/spin_everyday_bot'

# Your bot's token, which you can get from @BotFather
BOT_TOKEN = '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi'

# Your TeleSocket service token, which you can get from @TeleSocketBot
# Set `None` if you don't want to use TeleSocket Service
TELESOCKET_TOKEN = '1234567890abcdef1234567890abcdef1234567890abcdef'

# Webhook config. If you want to use webhooks, set this to `True`
USE_WEBHOOKS = False

# Relative path to your key and cert file respectively. This can be missing while `USE_WEBHOOKS` is False
# More info about webhooks: 'https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks'
WEBHOOK_CERT = 'data/cert.pem'
WEBHOOK_KEY = 'data/private.key'

# Your Telegram User ID
BOT_CREATOR = 123456987

# How much users will be shown on one page
PAGE_SIZE = 10

# Time of resetting spin results (in UTC)
RESET_TIME = '21:00'

# Logging channel. You can put here "@telegramChannelName" or channel's ID
# If you don't want to use logging to Telegram, set this to `None`
LOG_CHANNEL = ''

# Log file
# If you want to use logging to console instead of writing logs to file, set this to `None`
LOG_FILE = 'data/bot.log'

# Log formats. For more info, look 'https://docs.python.org/3/library/logging.html#logrecord-attributes'
# Telegram logging format (message format that will be sent to `LOG_CHANNEL`)
LOG_TG_FORMAT = '*{name}*: #{levelname}\n```\n{message}\n```\n\n{asctime}'

# Logging format (message format that will be written in `LOG_FILE` or console)
LOG_FORMAT = '{levelname:<8} [{asctime}]: {name}: {message}'

# If this is set to `False`, users will not be notified about errors
SHOW_ERRORS = True

# If specified key is missing from language file, translation will fallback to this language
FALLBACK_LANG = 'ru'

# Command limit per minute
FLOOD_LIMIT = 7

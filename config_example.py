# This is example bot settings file.

# You can find out necessary IDs from @ShowJsonBot

# Your bot's token, which you can get from @BotFather
BOT_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"

# Your Telegram User ID
BOT_CREATOR = 123456987

# Default name of spin
DEFAULT_SPIN_NAME = "ноунейм"

# Spin texts
# {s} is replaced with name of spin and {n} -- with user name
TEXTS = [["Итак, кто же сегодня *{s} дня*?", "_Хмм, интересно..._", "*АГА!*",
         "Сегодня ты *{s} дня,* {n}"],
         ["*Колесо сансары запущено!*", "_Что за дичь?!_", "Ну ок...",
          "Поздравляю, ты *{s} дня,* {n}"],
         ["Кручу-верчу, *наебать* хочу", "Сегодня ты *{s} дня*, @spin\_everyday\_bot",
          "_(нет)_", "На самом деле, это {n}"]]

# Text that shows if spin was done already
TEXT_ALREADY = "Согласно сегодняшнему розыгрышу, *{s} дня* -- `{n}`"

# Help text
HELP_TEXT = """*Привет!* Я бот, который делает ежедневные розыгрыши.
Для начала, _придумайте,_ что вы будете разыгрывать и _измените_ текст при помощи /setname
Затем, _подождите,_ пока бот запомнит пользователей чата, получая от них сообщения \
(количество пользователей можно узнать при помощи команды /count)
И _стартуйте_ розыгрыши при помощи команды /spin!
После нескольких розыгрышей _смотрите_ статистику:
 - ... себя при помощи команды /stat me
 - ... другого пользователя, ответив на сообщение интересующего пользователя командой /stat
 - ... чата при помощи команды /stat
\_\_\_\_\_\_
По всем вопросам обращайтесь к @USER
Если вы не можете изменить текст розыгрыша и \
если вы являетесь админом чата, используйте /adminF5 для ручного обновления списка админов"""

# Time of resetting spin results
RESET_TIME = "0:00"

# Logging channel. You can put here "@telegramChannelName" or channel's ID
LOG_CHANNEL = ""

# Message that will be shown in group chats if the bot can't write in PM
PM_ONLY_MESSAGE = "Для начала, запусти или разбань меня в ЛС"

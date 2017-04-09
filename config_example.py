# This is example bot settings file.

# You can find out necessary IDs from @ShowJsonBot

# Your bot's token, which you can get from @BotFather
BOT_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"

# Your TeleSocket service token, which you can get from @TeleSocketBot
# Set `None` if you don't want to use TeleSocket Service
TELESOCKET_TOKEN = "1234567890abcdef1234567890abcdef1234567890abcdef"

# Your Telegram User ID
BOT_CREATOR = 123456987

# Default name of spin
DEFAULT_SPIN_NAME = "ноунейм"

# Spin texts
# {s} is replaced with name of spin and {n} -- with user name
TEXTS = [["Итак, кто же сегодня *{s} дня*?", "_Хмм, интересно..._", "*АГА!*",
         "Сегодня ты *{s} дня,* {n}"],
         ["*Колесо Сансары запущено!*", "_Что за дичь?!_", "Ну ок...",
          "Поздравляю, ты *{s} дня,* {n}"],
         ["Кручу-верчу, *наебать* хочу", "Сегодня ты *{s} дня*, @spin\_everyday\_bot",
          "_(нет)_", "На самом деле, это {n}"],
         ["Эмм... Ты уверен?", "Ты *точно* уверен?", "Хотя ладно, процесс уже необратим",
          "Сегодня я назначаю тебе должность *{s} дня*, {n}!"],
         ["_Ищем рандомного кота на улице..._", "_Ищем палку..._", "_Ищем шапку..._", "_Рисуем ASCII-арт..._",
          "*Готово!*", """```
.∧＿∧
( ･ω･｡)つ━☆・*。
⊂　 ノ 　　　・゜+.
しーＪ　　　°。+ *´¨)
　　　　　　　　　.· ´¸.·*´¨) ¸.·*¨)
　　　　　　　　　　(¸.·´ (¸.·'* ☆ ВЖУХ, И ТЫ {s} ДНЯ,```{n}
"""]]

# Text that shows if spin was done already
TEXT_ALREADY = "Согласно сегодняшнему розыгрышу, *{s} дня* — `{n}`"

# How much users will be shown on one page of top
TOP_PAGE_SIZE = 10

# Help text
HELP_TEXT = """*Привет!* Я бот, который делает ежедневные розыгрыши.
Для начала, _придумайте,_ что вы будете разыгрывать и _измените_ текст при помощи /setname
Вы можете _дать право изменять_ название розыгрыша кому-либо, ответив на сообщение того пользователя \
командой /admgroup add
... и _отобрать_ у него это право, ответив командой /admgroup del
... а также _посмотреть,_ кто может изменять название розыгрыша, написав /admgroup list
Затем, _подождите,_ пока бот запомнит пользователей чата, получая от них сообщения \
(количество пользователей можно узнать при помощи команды /count)
И _стартуйте_ розыгрыши при помощи команды /spin!
Также можно _настроить_ автоматические розыгрыши! Для этого введите
 - /auto set \[GMT_TIME], где \[GMT_TIME] — время розыгрышей в GMT (МСК-3)
 - /auto del — для удаления автоматического розыгрыша
 - /auto status — для просмотра статуса автоматического розыгрыша
После нескольких розыгрышей _смотрите_ статистику:
 - ... себя при помощи команды /stat me
 - ... другого пользователя, ответив на сообщение интересующего пользователя командой /stat
 - ... чата при помощи команды /stat
\_\_\_\_\_\_
По всем вопросам обращайтесь к @USER"""

# Time of resetting spin results (in GMT)
RESET_TIME = "21:00"

# Logging channel. You can put here "@telegramChannelName" or channel's ID
LOG_CHANNEL = ""

# Log file
LOG_FILE = "bot.log"

# Log formats. For more info, look 'https://docs.python.org/3/library/logging.html#logrecord-attributes'
# Telegram logging format (message format that will be sent to `LOG_CHANNEL`)
LOG_TG_FORMAT = "*{name}*: #{levelname}\n```\n{message}\n```\n\n{asctime}"

# File logging format (message format that will be written in `LOG_FILE`
LOG_FILE_FORMAT = '{levelname:<8} [{asctime}]: {name}: {message}'

# Message that will be shown in group chats if the bot can't write in PM
PM_ONLY_MESSAGE = "Для начала, запусти или разбань меня в ЛС"

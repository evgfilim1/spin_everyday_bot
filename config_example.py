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
HELP_TEXT = {"main": ("*Привет!* Я бот, который делает ежедневные розыгрыши. Чтобы узнать о моих возможностях, "
             "выберите пункт меню", ("Команды%commands", "О боте%about")),
             "commands": ("Выберите нужную команду, чтобы узнать подробнее о ней",
                          ("/setname%name", "/admgroup%admin", "/count%count", "/spin%spin", "/auto%auto",
                           "/stat%stat", "Назад%main")),
             "about": ("SpinEverydayBot v.1.5.1\nПо всем вопросам обращайтесь к <username>\n", ("Назад%main",)),
             "name": ("`/setname` — устанавливает название розыгрыша.\nИспользование:\n"
                      "/setname — покажет текущее название розыгрыша\n"
                      "/setname \[TEXT] — установит названием розыгрыша `TEXT`", ("Назад%commands",)),
             "admin": ("`/admgroup` — управляет правами.\nИспользование:\n"
                       "/admgroup add — разрешает пользователю выполнять административные операции\n"
                       "/admgroup del — запрещает пользователю выполнять административные операции\n"
                       "/admgroup list — показывает список тех, кто может выполнять административные операции",
                       ("Назад%commands",)),
             "count": ("`/count` — считает кол-во пользователей, принимающих участие в розыгрыше",
                       ("Назад%commands",)),
             "spin": ("`/spin` — запускает розыгрыш. Если розыгрыш уже был запущен в течение текущего дня, "
                      "показывает результат.", ("Назад%commands",)),
             "auto": ("`/auto` - управление автоматическими розыгрышами.\nИспользование:\n"
                      "/auto set \[TIME] — устанавливает розыгрыш на \[TIME] GMT+0 (MSK-3). Формат времени: `hh:mm`\n"
                      "/auto del — отключает автоматический розыгрыш\n"
                      "/auto status — просмотр состояния и времени автоматического розыгрыша", ("Назад%commands",)),
             "stat": ("`/stat` — просмотр статистики в чате.\nИспользование:\n"
                      "/stat — просмотр статистики всего чата или конкретного пользователя\n"
                      "/stat me — просмотр собственной статистики", ("Назад%commands",))}

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

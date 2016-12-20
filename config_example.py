# This is example bot settings file.

# You can find out necessary IDs from @ShowJsonBot

# Your bot's token, which you can get from @BotFather
botTOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"

# Your Telegram User ID
botCREATOR = 123456987

# Default name of spin
defaultSpinName = "победитель"

# Spin texts
# {s} is replaced with name of spin and {n} -- with user name
texts = ["Итак, кто же сегодня *{s} дня*?", "_Хмм, интересно..._", "*АГА!*",
         "Сегодня ты *{s} дня,* {n}"]

# Text that shows if spin was done already
textAlready = "Согласно сегодняшнему розыгрышу, *{s} дня* -- `{n}`"

# Help text
helpText = """*Привет!* Я бот, который делает ежедневные розыгрыши.
Для начала, _придумайте,_ что вы будете разыгрывать и _измените_ текст при помощи /setsn
Затем, _подождите,_ пока бот запомнит пользователей чата, получая от них сообщения \
(количество пользователей можно узнать при помощи команды /countsn)
И _стартуйте_ розыгрыши при помощи команды /spinsn!
------
По всем вопросам обращайтесь к @USER
Если вы не можете изменить текст розыгрыша и \
если вы являетесь админом чата, используйте /adminF5sn для ручного обновления списка админов"""

# Time of resetting spin results
resetTime = "0:00"

# Logging channel. You can put here "@telegramChannelName" or channel's ID
logChannel = ""

# Message that will be shown in group chats if the bot can't write in PM
pmOnlyMessage = "Для начала, запусти или разбань меня в ЛС"

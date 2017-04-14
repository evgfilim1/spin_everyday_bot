from os import path
from shutil import copy
from sys import version


def check(value, var_name, classes: list):
    if None in classes:
        classes.pop(classes.index(None))
        classes.append(type(None))
    if not isinstance(value, tuple(classes)):
        class_name = [c.__name__ for c in classes]
        types = ", ".join(class_name[:-1])
        if len(class_name) > 1:
            types += " or {}".format(class_name[-1])
        exit("ERROR: '{var}' must be {types}, not {type}".format(var=var_name, types=types,
                                                                 type=type(value).__name__))


def check_token(token: str):
    from telegram.error import InvalidToken
    import string
    if token is None:
        return
    if len(token) != 48:
        raise InvalidToken()

    for symbol in token:
        if symbol not in string.hexdigits:
            raise InvalidToken()


def check_config():
    import config
    from telegram import Bot

    print("Checking bot token...", end=' ')
    Bot(config.BOT_TOKEN)
    print("ok")

    print("Checking TeleSocket token...", end=' ')
    check(config.TELESOCKET_TOKEN, "TELESOCKET_TOKEN", [str, None])
    check_token(config.TELESOCKET_TOKEN)
    print("ok")

    print("Checking value types...", end=' ')

    check(config.BOT_CREATOR, "BOT_CREATOR", [int])
    check(config.DEFAULT_SPIN_NAME, "DEFAULT_SPIN_NAME", [str])
    check(config.TEXTS, "TEXTS", [list, tuple])
    check(config.TEXT_ALREADY, "TEXT_ALREADY", [str])
    check(config.TOP_PAGE_SIZE, "TOP_PAGE_SIZE", [int])
    check(config.HELP_TEXT, "HELP_TEXT", [dict])
    check(config.RESET_TIME, "RESET_TIME", [str])
    check(config.LOG_CHANNEL, "LOG_CHANNEL", [int, str, None])
    check(config.LOG_FILE, "LOG_FILE", [str, None])
    check(config.LOG_TG_FORMAT, "LOG_TG_FORMAT", [str])
    check(config.LOG_FORMAT, "LOG_FORMAT", [str, None])
    check(config.PM_ONLY_MESSAGE, "PM_ONLY_MESSAGE", [str])
    print("ok")

    print("Checking values...", end=' ')

    try:
        time = config.RESET_TIME.split(':')
        if len(time) != 2:
            raise ValueError
        int(time[0])
        int(time[1])
    except ValueError:
        exit("ERROR: 'NEW_DAY_TIME' is invalid")

    if config.TOP_PAGE_SIZE <= 0:
        exit("ERROR: 'TOP_PAGE_SIZE' should be greater than zero")
    print("ok")

    print("Config tests passed.")


def main():
    from pip import main as pip_main
    print("Setting up SpinEverydayBot...")

    ver = version.split()[0].split('.')
    if not (int(ver[0]) >= 3 and int(ver[1]) >= 6):
        exit("ERROR: You need to install Python 3.6 or newer to use this bot")

    try:
        import telegram
    except ImportError:
        print("WARNING: 'python-telegram-bot' package is not installed. Installing...")
        if pip_main(['install', 'python-telegram-bot']) != 0:
            exit("""ERROR: An error occurred while installing packages.
Check that you're running this script as root or administrator""")
        import telegram

    del telegram

    try:
        import TeleSocketClient
    except ImportError:
        if input("Do you want to use TeleSocket Service? (y/N): ").lower().strip() != "y":
            pass
        print("WARNING: 'TeleSocketClient' package is not installed. Installing...")
        if pip_main(['install', 'TeleSocketClient']) != 0:
            exit("""ERROR: An error occurred while installing packages.
        Check that you're running this script as root or administrator""")
        import TeleSocketClient

    del TeleSocketClient

    if not path.exists("config.py"):
        print("WARNING: 'config.py' doesn't exist, copying example...")
        copy("config_example.py", "config.py")
        input("Now change example values to yours in file 'config.py' and press <Enter>")

    check_config()
    print("Setup finished")
    print("Now you can run your bot via 'python3.6 bot.py' command")
    exit(0)


if __name__ == '__main__':
    main()

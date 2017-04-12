# SpinEverydayBot by @evgfilim1

### Install guide:
Check that you have `python3.6` and `python-pip` installed, then run this command in your shell:
```bash 
$ sudo pip install python-telegram-bot
```
If you want to use [TeleSocket Service](https://pypi.python.org/pypi/TeleSocketClient), 
append `TeleSocketClient` to the command:
```bash
$ sudo pip install python-telegram-bot TeleSocketClient
```

If you don't know, how to create new bot in Telegram, google it, there are a lot of docs :)
But don't forget to disable privacy mode

Then do these steps to set up the bot:
```bash
$ git clone https://github.com/evgfilim1/spin_everyday_bot.git
$ cd spin_everyday_bot
$ cp config_example.py config.py
$ nano config.py
```
Change example values to your ones, then press `Ctrl+X`, `Y`.

### Running bot:

Simply type in your shell:
```bash 
$ python3.6 thebot.py
```

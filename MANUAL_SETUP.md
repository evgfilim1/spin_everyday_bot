# Manual installation guide for SpinEverydayBot
## Preparing

Check that you have `python3.6` and `python3-pip` installed, then run this command in your shell:
```bash 
sudo pip install python-telegram-bot
```
If you want to use [TeleSocket Service](https://pypi.python.org/pypi/TeleSocketClient), 
append `TeleSocketClient` to the command:
```bash
sudo pip install python-telegram-bot TeleSocketClient
```
**For Windows users**: instead of typing `sudo` in command prompt, run `cmd.exe` as Administrator

## Setting up

Do these steps to set up the bot:
```bash
git clone https://github.com/evgfilim1/spin_everyday_bot.git
cd spin_everyday_bot
cp config_example.py config.py
```
Now open `config.py` in your favourite text editor and change example values to suit your needs

**For Windows users:** use `copy` instead of `cp`

## Running bot:

Simply type in your shell:
```bash 
python3.6 thebot.py
```

**For Windows users:** use `python3` or `python` instead of `python3.6`

# SpinEverydayBot

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ab340c80e3e64d75b0fd32b82d790f8f)](https://www.codacy.com/app/evgfilim1/spin_everyday_bot)

## Setting up

* Check that you have Python 3.6+ and pip installed:
```bash
$ python3 --version
Python 3.6.2
$ pip3 --version
pip 9.0.1 from /usr/lib/python3.6/site-packages (python 3.6)
```

* Clone the repository
```bash
$ git clone https://github.com/evgfilim1/spin_everyday_bot.git
$ cd spin_everyday_bot
```
* Copy example config file
```bash
$ cp config_example.py config.py
```
**For Windows users:** use `copy` instead of `cp`

* Now open `config.py` in your favourite text editor and change default values to suit your needs
* Install dependencies
```bash
$ pip3 install -U -r requirements.txt
```

**Note**: If you want to use [TeleSocket Service](https://pypi.python.org/pypi/TeleSocketClient), 
append `TeleSocketClient` to the command:
```bash
$ pip3 install -U -r requirements.txt TeleSocketClient
```
**For Windows users:** use `pip` instead of `pip3` 


## Running bot:

It is very easy:
```bash 
$ python3 thebot.py
```

**For Windows users:** use `python` or `py` instead of `python3.6`

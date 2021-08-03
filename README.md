# SpinEverydayBot v2

[![Codacy badge](https://app.codacy.com/project/badge/Grade/1f7e6b1eba5b42ccb9b3243f18db4f02)](https://www.codacy.com/gh/evgfilim1/spin_everyday_bot/dashboard)
[![wakatime badge](https://wakatime.com/badge/github/evgfilim1/spin_everyday_bot.svg)](https://wakatime.com/badge/github/evgfilim1/spin_everyday_bot)
[![Crowdin badge](https://badges.crowdin.net/spin_everyday_bot/localized.svg)](https://crowdin.com/project/spin_everyday_bot)
[![Requirements badge](https://requires.io/github/evgfilim1/spin_everyday_bot/requirements.svg?branch=v2-dev)](https://requires.io/github/evgfilim1/spin_everyday_bot/requirements/?branch=v2-dev)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License badge](https://img.shields.io/github/license/evgfilim1/spin_everyday_bot)](LICENSE)

Telegram bot for everyday raffles. **HIGHLY EXPERIMENTAL! WORK IN PROGRESS!**

## Setting up

### Requirements

- Python 3.9+
- PostgreSQL 13+

Older versions might work, but not tested. If they do work, submit an issue.

### Steps

1. (Optional.) Create and set up new virtualenv for the project.
1. Install requirements from [`requirements.txt`](requirements.txt) by running
   `pip install -Ur requirements.txt`.
1. Create `config.yaml` in current directory or in `~/.config/spin_everyday_bot/2.x/`.
1. Open your `config.yaml` and edit it to match your setup.
   ```yaml
   telegram:
     token: ...
     superuser_id: ...
   db:
     host: 127.0.0.1
     port: 5432
     user: ...
     database: ...
     password: ...
   ```
1. Migrate database by running `alembic upgrade head`

## Running

### Polling

It's as easy as `python -m spin_everyday_bot`

### Webhooks

1. Make sure you've got HTTPS certificate. Please note that **self-signed ones are not yet
   supported**, go and create one with
   [Let's Encrypt](https://letsencrypt.org/getting-started/). If you don't have a domain name, but
   you have static IP, use [nip.io](https://nip.io) to create
   "fake" domain.
1. Set up a reverse-proxy like [nginx](https://nginx.org) with above certificate and pointing
   to `http://localhost:8880/`.
1. Install additional requirements: `pip install -U "FastAPI~=0.68.0" uvicorn`.
1. Run `python -m spin_everyday_bot webhook -u "<WEBHOOK_URL>"`, where `<WEBHOOK_URL>` is the URL
   for Telegram to make requests to.

### Updating

Before you run a new version after updating, make sure your database is up-to-date by running
migrations and check whether your config matches (see _Setting up_ section for more info).

## Contributing

Oh, you wanna contribute? That's nice!

1. Make sure the project is set up and up-to-date.
1. Install additional requirements from [`dev-requirements.txt`](dev-requirements.txt).
1. Make changes to the code.
  - If you made any changes to db, make sure you created a migration by running
    `alembic revision --autogenerate -m '<description>'` and verified it.
  - If you made any changes which require translation changes, make sure you generated a new
    translation template by running
    ```bash
    pybabel extract \
       --msgid-bugs-address="evgfilim1@yandex.ru" \
       --copyright-holder="Evgeniy Filimonov <evgfilim1@yandex.ru>" \
       --project=spin_everyday_bot --version=2.0.0-alpha.0 \
       -o spin_everyday_bot/lang/spin_everyday_bot.pot -w 99 \
       spin_everyday_bot
    ```
1. Run some tools to make code style better
   ```bash
   isort --py 39 -p spin_everyday_bot --profile black -l 100 --tc --gitignore spin_everyday_bot
   black -l 100 -t py39 spin_everyday_bot
   ```
1. Commit and push changes to your branch/fork.
1. Create a pull request.

## License

Licensed under GNU AGPL v3, see [LICENSE](LICENSE).

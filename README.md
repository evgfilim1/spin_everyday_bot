# SpinEverydayBot v2

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
1. Create `config.yaml` in root project directory or in `~/.config/spin_everyday_bot/`.
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
It's as easy as `python -m spin_everyday_bot`

### Updating
Before you run a new version after updating, make sure your database is up-to-date by running
migrations and check whether your config matches (see _Setting up_ section for more info).

## Contributing
Oh, you wanna contribute? That's nice!

1. Make sure the project is set up and up-to-date.
1. Install additional requirements from [`requirements-dev.txt`](requirements-dev.txt).
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
   isort spin_everyday_bot
   black -l 99 -t py39 spin_everyday_bot
   ```
1. Commit and push changes to your branch/fork.
1. Create a pull request.

## License
Licensed under GNU AGPL v3, see [LICENSE](LICENSE).

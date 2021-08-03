#  SpinEverydayBot
#  Copyright © 2016-2021 Evgeniy Filimonov <evgfilim1@yandex.ru>
#
#  This program is free software: you can redistribute it and/or modify it under the terms of the
#  GNU Affero General Public License as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#  even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License along with this program.
#  If not, see <http://www.gnu.org/licenses/>.

__all__ = ["start_webhook"]

from functools import partial
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI
from uvicorn import run

from .common import setup_dispatcher

# Don't run the app directly with uvicorn CLI!
_app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, include_in_schema=False)


async def startup(bot: Bot, webhook_url: str):
    await bot.set_webhook(webhook_url)


async def shutdown(bot: Bot):
    await bot.delete_webhook()


async def handle_update(update: Update, bot: Bot, dp: Dispatcher, **kwargs: Any) -> dict:
    return await dp.feed_webhook_update(bot, update, **kwargs)


def start_webhook(
    bot: Bot,
    host: str,
    port: int,
    webhook_url: str,
    shutdown_remove: bool,
    **kwargs: Any,
):
    _app.add_api_route(
        "/", partial(handle_update, bot=bot, dp=setup_dispatcher(), **kwargs), methods=["POST"]
    )
    _app.add_event_handler("startup", partial(startup, bot=bot, webhook_url=webhook_url))
    if shutdown_remove:
        _app.add_event_handler("shutdown", partial(shutdown, bot=bot))

    run("spin_everyday_bot.webhook:_app", host=host, port=port)

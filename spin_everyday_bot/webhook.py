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

from functools import wraps
from inspect import iscoroutine
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from uvicorn import run

from .common import setup_dispatcher


async def handle_update(request: Request, update: Update) -> Response:
    dp: Dispatcher = request.app.state.dp
    bot: Bot = request.app.state.bot
    kwargs: dict[str, Any] = request.app.state.kwargs
    r = await dp.feed_webhook_update(bot, update, **kwargs)
    if r is None:
        return Response()
    return JSONResponse(r)


def async_partial(func, *args, **kwargs):
    @wraps(func)
    async def wrapper(*a, **kw):
        r = func(*args, *a, **kwargs, **kw)
        if iscoroutine(r):
            r = await r
        return r

    return wrapper


def start_webhook(
    bot: Bot,
    host: str,
    port: int,
    loglevel: str,
    **kwargs: Any,
):
    dp = setup_dispatcher()
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, include_in_schema=False)
    app.add_api_route("/", handle_update, methods=["POST"])

    local_kwargs = {
        "dispatcher": dp,
        "bots": (bot,),
        "bot": bot,
        **kwargs,
    }

    app.add_event_handler("startup", async_partial(dp.emit_startup, **local_kwargs))
    app.add_event_handler("shutdown", async_partial(dp.emit_shutdown, **local_kwargs))

    app.state.dp = dp
    app.state.bot = bot
    app.state.kwargs = kwargs

    run(app, host=host, port=port, log_level=loglevel)

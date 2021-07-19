#  SpinEverydayBot
#  Copyright © 2016-2021 Evgeniy Filimonov <evgfilim1@yandex.ru>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ["setup"]

from typing import Any, Awaitable, Callable, Optional, Type, TypeVar, Union

from aiogram import Dispatcher, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from ..lang import Translation

_T = TypeVar("_T", bound=types.TelegramObject)
_RT = TypeVar("_RT")
_DT = dict[str, Any]
_DBT = TypeVar("_DBT", Type[models.Chat], Type[models.User])


async def _get_language(
    conn: AsyncSession,
    obj_class: _DBT,
    obj_id: int,
) -> Optional[str]:
    query = await conn.execute(select(obj_class).where(obj_class.id == obj_id))
    obj: Optional[_DBT] = query.one_or_none()
    if obj is not None:
        return obj.language
    return None


async def translate(
    handler: Callable[[_T, _DT], Awaitable[_RT]],
    event: _T,
    data: _DT,
) -> _RT:
    conn: AsyncSession = data["db"]
    lang: Optional[str] = None
    chat: types.Chat
    user: types.User
    if (chat := data.get("event_chat")) is not None and chat.type != "private":
        lang = await _get_language(conn, models.Chat, chat.id)
    if lang is None and (user := data.get("event_user")) is not None:
        lang = await _get_language(conn, models.User, user.id)
        if lang is None:
            lang = user.language_code
    data["tr"] = Translation(lang)
    return await handler(event, data)


def setup(dp: Dispatcher) -> None:
    dp.update.middleware(translate)

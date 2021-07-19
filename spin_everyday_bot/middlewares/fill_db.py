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

from typing import Any, Awaitable, Callable, TypeVar

from aiogram import Dispatcher, types
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models

_T = TypeVar("_T", bound=types.TelegramObject)
_RT = TypeVar("_RT")
_DT = dict[str, Any]


async def fill_event(
    handler: Callable[[_T, _DT], Awaitable[_RT]],
    event: _T,
    data: _DT,
) -> _RT:
    conn: AsyncSession = data["db"]
    chat: types.Chat
    user: types.User
    if (user := data.get("event_user")) is not None:
        res = await conn.execute(
            insert(models.User)
            .values(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
            )
            .on_conflict_do_update(
                constraint=models.User.id,
                set_={
                    models.User.username: user.username,
                    models.User.full_name: user.full_name,
                },
            ),
        )
        db_user: models.User = res.one()
        data["user"] = db_user
        if (chat := data.get("event_chat")) is not None and chat.type != "private":
            # event.chat always exists when event.user exists
            res = await conn.execute(
                insert(models.Chat)
                .values(
                    id=chat.id,
                )
                .on_conflict_do_nothing(),
            )
            db_chat: models.Chat = res.one()
            await conn.execute(
                insert(models.ChatUser)
                .values(
                    chat_id=db_chat.id,
                    user_id=db_user.id,
                )
                .on_conflict_do_nothing()
            )
        await conn.commit()
    return await handler(event, data)


def setup(dp: Dispatcher) -> None:
    dp.update.middleware(fill_event)

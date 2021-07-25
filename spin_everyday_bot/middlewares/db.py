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

__all__ = ["setup"]


from typing import Any, Awaitable, Callable, TypeVar

from aiogram import Dispatcher, types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

_T = TypeVar("_T", bound=types.TelegramObject)
_RT = TypeVar("_RT")
_DT = dict[str, Any]


async def create_session(
    handler: Callable[[_T, _DT], Awaitable[_RT]],
    event: _T,
    data: _DT,
) -> _RT:
    session_factory: sessionmaker = data["session_factory"]
    session: AsyncSession
    async with session_factory() as session:
        data["db"] = session
        r = await handler(event, data)
        await session.commit()
    return r


def setup(dp: Dispatcher) -> None:
    dp.update.middleware(create_session)

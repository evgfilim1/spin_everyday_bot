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

import logging
from typing import Any, Awaitable, Callable, Optional, TypeVar

from aiogram import Dispatcher, types
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound=types.TelegramObject)
_RT = TypeVar("_RT")
_DT = dict[str, Any]


async def migrate(
    handler: Callable[[types.Message, _DT], Awaitable[_RT]],
    message: types.Message,
    data: _DT,
) -> Optional[_RT]:
    conn: AsyncSession = data["db"]
    migrate_to: int
    if (migrate_to := message.migrate_to_chat_id) is not None:
        await conn.execute(
            update(models.Chat).where(models.Chat.id == message.chat.id).values(id=migrate_to),
            execution_options={"synchronize_session": "fetch"},
        )
        await conn.commit()
        # Further update processing is useless as we have migrated
        return
    return await handler(message, data)


def setup(dp: Dispatcher) -> None:
    dp.message.outer_middleware(migrate)

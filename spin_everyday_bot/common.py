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

__all__ = ["create_bot", "get_session_factory", "setup_dispatcher"]

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from . import handlers, middlewares


def create_bot(token: str) -> Bot:
    return Bot(token, parse_mode="HTML")


def get_session_factory(dsn: str) -> sessionmaker:
    engine = create_async_engine(dsn, future=True)
    session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True,
    )

    return session_factory


def setup_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    handlers.register(dp)
    middlewares.register(dp)

    return dp

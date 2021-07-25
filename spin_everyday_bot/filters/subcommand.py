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

__all__ = ["SubcommandFilter"]

from dataclasses import replace
from typing import Any, Union, cast

from aiogram import Bot
from aiogram.dispatcher.filters import Command, CommandObject
from aiogram.types import Message


class SubcommandFilter(Command):
    subcommand: str

    async def __call__(self, message: Message, bot: Bot) -> Union[bool, dict[str, Any]]:
        result = await super().__call__(message, bot)
        if not result:
            return False
        command: CommandObject = cast(dict, result)["command"]
        subcommand, *args = command.args.split(" ", maxsplit=1)
        if subcommand != self.subcommand:
            return False
        return {"command": replace(command, args=args[0] if args else "")}

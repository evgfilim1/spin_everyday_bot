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

__all__ = ["router"]

from aiogram import Router
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from ..filters import SubcommandFilter, is_superuser
from ..lang import Translation

router = Router()


@router.message(is_superuser, SubcommandFilter(commands=["sudo"], subcommand="reset"))
async def reset(message: Message, db: AsyncSession, tr: Translation, command: CommandObject):
    _ = tr.gettext
    if not command.args:
        await message.reply(_("No chat ID specified"))
        return
    try:
        chat_id = int(command.args.strip())
    except ValueError:
        await message.reply(_("Invalid chat ID specified"))
        return
    await db.execute(update(models.Chat).where(models.Chat.id == chat_id).values(winner_id=None))
    await message.reply(_("Raffle result was reset in chat {0}").format(chat_id))


# If you want to notify user when they don't have permission on "/sudo", uncomment this.
# @router.message(commands=["sudo"])
# async def fallback(message: Message, tr: Translation):
#     _ = tr.gettext
#     await message.reply(_("You don't have permission to execute this."))

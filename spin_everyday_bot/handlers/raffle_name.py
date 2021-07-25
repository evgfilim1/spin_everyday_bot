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

from aiogram import F, Router
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from ..filters import is_chat_admin, is_group_chat
from ..lang import Translation
from ..misc import DEFAULT_RAFFLE_NAME, ONLY_GROUPS

router = Router()


@router.message(
    is_group_chat,
    is_chat_admin,
    content_types=["text"],
    commands=["setname"],
    command_magic=F.args,
)
async def set_raffle_name(
    message: Message,
    db: AsyncSession,
    chat: models.Chat,
    command: CommandObject,
    tr: Translation,
):
    _ = tr.gettext
    raffle_name = command.args.strip()
    old_raffle_name = chat.raffle_name or _(DEFAULT_RAFFLE_NAME)
    await db.execute(
        update(models.Chat).where(models.Chat.id == chat.id).values(raffle_name=raffle_name)
    )

    await message.reply(
        _("Raffle name updated: <i>{0}</i> → <i>{1}</i>.").format(old_raffle_name, raffle_name)
    )


@router.message(is_group_chat, is_chat_admin, content_types=["text"], commands=["setname"])
@router.message(is_group_chat, content_types=["text"], commands=["setname"])
async def get_raffle_name(
    message: Message,
    chat: models.Chat,
    command: CommandObject,
    tr: Translation,
):
    _ = tr.gettext
    raffle_name = chat.raffle_name or _(DEFAULT_RAFFLE_NAME)
    await message.reply(
        _(
            "Current raffle name: <i>{0}</i>.\n\n"
            "To change raffle name, send <code>/{1} &lt;new_name&gt;</code>."
        ).format(raffle_name, command.command)
    )


@router.message(content_types=["text"], commands=["setname"])
async def fallback(message: Message, tr: Translation):
    _ = tr.gettext
    await message.reply(_(ONLY_GROUPS))

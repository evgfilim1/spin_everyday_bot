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

import asyncio
import random
from asyncio import create_task
from datetime import datetime
from gettext import NullTranslations
from html import escape
from typing import Any, Awaitable, Callable, Iterable, Sequence

from aiogram import Bot, Router
from aiogram.types import Message
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from ..filters import has_winner, is_group_chat
from ..lang import Translation
from ..misc import DEFAULT_RAFFLE_NAME

router = Router()

_ = NullTranslations().gettext
DEFAULT_RAFFLE_TEXTS = (
    (
        _("So, who's <b>{name} of the day</b>?"),
        _("Hmm... Interesting."),
        _("Wow! You are <b>{name} of the day</b>, {user}!"),
    ),
    (
        _("Are you sure?"),
        _("Are you <b>REALLY</b> sure?!"),
        _("Anyway, I won't stop."),
        _("Now you are <b>{name} of the day</b>, {user}. Deal with it."),
    ),
)
TEXT_SEND_DELAY = 2
del _


def tag_user(user: models.User) -> str:
    return (
        f"@{user.username}"
        if user.username
        else f'<a href="tg://user?id={user.id}>{escape(user.full_name)}</a>'
    )


async def _random_member_from_chat(
    all_users: Sequence[tuple[models.ChatUser]],
    chat_id: int,
    bot: Bot,
    db: AsyncSession,
) -> models.ChatUser:
    """
    Choose random chat member who hasn't left the chat or wasn't banned.

    When left or banned user is encountered, `DELETE` query is issued in database.

    :param all_users: Sequence of all users.
    :param chat_id: Chat ID where to check in.
    :param bot: Current bot instance.
    :param db: Current database session.
    :return: Present random chat member.
    :raises: ValueError
    """
    transaction = await db.begin_nested()
    _users: list[models.ChatUser] = [u[0] for u in all_users]
    try:
        while len(_users) != 0:
            i = random.randrange(len(_users))
            chosen_one = _users[i]
            if (await bot.get_chat_member(chat_id, chosen_one.user_id)).status not in (
                "kicked",
                "left",
            ):
                return chosen_one
            await db.execute(delete(models.ChatUser).where(models.ChatUser.id == chosen_one.id))
            _users.pop(i)
        raise ValueError
    finally:
        await transaction.commit()


async def _sender_task(
    texts: Iterable[str],
    sender: Callable[[str], Awaitable[Any]],
) -> None:
    for msg in texts:
        await sender(msg)
        await asyncio.sleep(TEXT_SEND_DELAY)


@router.message(has_winner, is_group_chat, commands=["spin", "raffle"])
async def show_winner(
    message: Message,
    chat: models.Chat,
    tr: Translation,
):
    _ = tr.gettext
    raffle = chat.raffle_name or _(DEFAULT_RAFFLE_NAME)
    winner: models.User = chat.winner
    tag = tag_user(winner)
    await message.reply(
        _("According to today raffle, <b>{name} of the day</b> is {user}.").format(
            name=raffle, user=tag
        )
    )


@router.message(is_group_chat, commands=["spin", "raffle"])
async def start_raffle(
    message: Message,
    bot: Bot,
    db: AsyncSession,
    chat: models.Chat,
    tr: Translation,
):
    _ = tr.gettext
    raffle = chat.raffle_name or _(DEFAULT_RAFFLE_NAME)
    full_chat = await bot.get_chat(message.chat.id)
    texts = random.choice(DEFAULT_RAFFLE_TEXTS)
    r = await db.execute(select(models.ChatUser).where(models.ChatUser.chat_id == chat.id))
    try:
        winner = await _random_member_from_chat(r.all(), message.chat.id, bot, db)
    except ValueError:
        # no users left
        await message.reply(_("No users are registered in the raffle :("))
        return
    await db.execute(
        update(models.Chat).where(models.Chat.id == chat.id).values(winner_id=winner.user_id)
    )
    await db.execute(
        insert(models.WinHistoryItem).values(chat_user_id=winner.id, won_at=datetime.utcnow())
    )
    tag = tag_user(winner.user)
    if full_chat.slow_mode_delay or chat.fast is not False:  # fast raffles by default
        await message.answer(_(texts[-1]).format(name=raffle, user=tag))
    else:
        create_task(
            _sender_task((_(text).format(name=raffle, user=tag) for text in texts), message.answer)
        )

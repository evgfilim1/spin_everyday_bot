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

__all__ = ["Chat", "ChatUser", "ChatText", "User", "WinHistoryItem"]

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger(), nullable=False, primary_key=True)
    username = Column(String())
    full_name = Column(String(), nullable=False)
    language = Column(String())
    wotd_registered = Column(Boolean(), nullable=False, default=False)
    wotd = Column(Boolean(), nullable=False, default=False)

    def __repr__(self) -> str:
        return f'<User {self.id} "{self.full_name}" ("{self.username}")>'

    @property
    def effective_name(self) -> str:
        if self.username:
            return ("@" if not self.username.startswith("@") else "") + self.username
        return self.full_name or f"deleted (id{self.id})"  # empty full name means deleted account


class Chat(Base):
    __tablename__ = "chats"

    id = Column(BigInteger(), primary_key=True)
    raffle_name = Column(String())
    winner_id = Column(ForeignKey(User.id, ondelete="set null", onupdate="cascade"))
    winner = relationship("User", uselist=False)
    users = relationship("User", secondary="chat_users")
    language = Column(String())
    timezone_offset_min = Column(SmallInteger(), nullable=False, default=0)

    auto_at = Column(Time())
    fast = Column(Boolean())
    admin_only = Column(Boolean())
    opt_in = Column(Boolean())
    show_user_list = Column(Boolean(), default=True)

    def __repr__(self) -> str:
        return f"<Chat {self.id}>"


class ChatUser(Base):
    __tablename__ = "chat_users"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey(User.id, ondelete="cascade", onupdate="cascade"), nullable=False)
    chat_id = Column(ForeignKey(Chat.id, ondelete="cascade", onupdate="cascade"), nullable=False)

    __table_args__ = (UniqueConstraint(user_id, chat_id),)

    def __repr__(self) -> str:
        return f"<ChatUser {self.user_id} in chat {self.chat_id}>"


class WinHistoryItem(Base):
    __tablename__ = "win_history"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    chat_user_id = Column(ForeignKey(ChatUser.id, ondelete="cascade"), nullable=False)
    won_at = Column(DateTime(), nullable=False)

    def __repr__(self) -> str:
        return f"<WinHistoryItem at {self.won_at} for {self.chat_user_id}>"


class ChatText(Base):
    __tablename__ = "chat_texts"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    chat_id = Column(ForeignKey(Chat.id, ondelete="cascade", onupdate="cascade"))
    group = Column(Integer(), nullable=False)
    order = Column(Integer(), nullable=False)
    text = Column(String(), nullable=False)

    __table_args__ = (UniqueConstraint(group, order),)

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

__all__ = [
    "has_winner",
    "is_chat_admin",
    "is_group_chat",
    "is_superuser",
    "SubcommandFilter",
]

from .chat_admin import is_chat_admin
from .chat_winner import has_winner
from .group_chat import is_group_chat
from .subcommand import SubcommandFilter
from .superuser import is_superuser

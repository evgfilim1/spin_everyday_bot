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
    "DEFAULT_RAFFLE_NAME",
    "dirs",
    "ONLY_GROUPS",
]

from gettext import NullTranslations

from platformdirs import PlatformDirs

from . import APP_NAME, __author__

dirs = PlatformDirs(APP_NAME, __author__, "2.x")

_ = NullTranslations().gettext  # stub, constants in the file will be translated lazily later

# region Common Constants
ONLY_GROUPS = _("This command will work only in group chats.")
DEFAULT_RAFFLE_NAME = _("winner")
# endregion

del _

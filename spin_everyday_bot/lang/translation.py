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

from gettext import translation
from os import getcwd, path
from typing import Optional

from .. import APP_NAME


class Translation:
    def __init__(self, language: Optional[str] = None):
        """Provides access to translations

        :param language: Desired language or `None` to use system default.
        """
        languages = (language,) if language else None
        try:
            self.tr = translation(APP_NAME, languages=languages, fallback=False)
        except FileNotFoundError:
            # no translations are installed into system, falling back to bundled ones
            self.tr = translation(
                APP_NAME,
                localedir=path.join(getcwd(), "lang"),
                languages=languages,
                fallback=True,
            )

    def gettext(self, message: str) -> str:
        """Get translation for specified message"""
        return self.tr.gettext(message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Get translation for specified message with plural support"""
        return self.tr.ngettext(singular, plural, n)

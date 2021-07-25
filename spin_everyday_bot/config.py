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

__all__ = ["Config", "DatabaseConfig", "read_config", "TelegramConfig"]

from pathlib import Path
from typing import Optional

from pydantic import AnyUrl, SecretStr
from pydantic.dataclasses import dataclass
from yaml import safe_load as yaml_load

from .misc import dirs

CONFIG_FILE_NAME = "config.yaml"


def _find_config() -> Optional[Path]:
    for d in (Path.cwd(), dirs.user_config_path):
        if (cfg_path := d / CONFIG_FILE_NAME).exists():
            return cfg_path
    raise FileNotFoundError(cfg_path)


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    superuser_id: str


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: SecretStr
    database: str

    @property
    def dsn(self) -> str:
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            user=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=str(self.port),
            path=f"/{self.database}",
        )


@dataclass(frozen=True)
class Config:
    telegram: TelegramConfig
    db: DatabaseConfig


def read_config(path: Optional[Path] = None) -> Config:
    """Read config file and return a :class:`spin_everyday_bot.config.Config` object."""
    if path is None:
        path = _find_config()
    with path.open() as f:
        return Config(**yaml_load(f))

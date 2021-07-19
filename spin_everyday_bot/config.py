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

__all__ = ["Config", "DatabaseConfig", "read_config", "TelegramConfig"]

from os import getcwd, path
from pathlib import Path

from pydantic import IPvAnyAddress, PostgresDsn, SecretStr
from pydantic.dataclasses import dataclass
from xdg import BaseDirectory
from yaml import safe_load as yaml_load

from . import APP_NAME

CONFIG_FILE_NAME = "config.yaml"


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    superuser_id: str


@dataclass(frozen=True)
class DatabaseConfig:
    host: IPvAnyAddress
    port: int
    user: str
    password: SecretStr
    database: str

    @property
    def dsn(self) -> PostgresDsn:
        return PostgresDsn(
            None,
            scheme="postgresql",
            user=self.user,
            password=self.password.get_secret_value(),
            host=str(self.host),
            port=str(self.port),
            path=f"/{self.database}",
        )


@dataclass(frozen=True)
class Config:
    telegram: TelegramConfig
    db: DatabaseConfig


def read_config() -> Config:
    """Read config file and return a :class:`spin_everyday_bot.config.Config` object"""
    config_file = Path(
        BaseDirectory.load_first_config(APP_NAME, CONFIG_FILE_NAME)
        or path.join(getcwd(), CONFIG_FILE_NAME)
    )
    if not config_file.exists():
        raise FileNotFoundError("Configuration file not found")
    with config_file.open() as f:
        return Config(**yaml_load(f))

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

__all__ = ["main"]

import logging
from argparse import ArgumentParser, ArgumentTypeError
from dataclasses import dataclass
from inspect import getfullargspec
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .common import create_bot, get_session_factory
from .config import read_config
from .lang import gettext as _


@dataclass(frozen=True)
class Args:
    strategy: Optional[str]
    loglevel: str
    config: Optional[Path]
    host: Optional[str] = None
    port: Optional[int] = None
    webhook_url: str = ""
    shutdown_remove: bool = False


def _existing_file(path: str) -> Path:
    if not (p := Path(path).resolve()).exists():
        raise ArgumentTypeError(_("No such file: {0!r}").format(path))
    if p.is_dir():
        raise ArgumentTypeError(_("Is a directory: {0!r}").format(path))
    return p


def _init_parser() -> ArgumentParser:
    loglevels = ("debug", "info", "warning", "error", "critical")
    parser = ArgumentParser(
        description=_("Telegram bot for everyday raffles"),
    )
    parser.add_argument(
        "-L",
        "--loglevel",
        default="INFO",
        choices=loglevels,
        metavar="LEVEL",
        help=_("log level, can be one of {0}").format(", ".join(loglevels)),
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument("-c", "--config", type=_existing_file, help=_("full path to config file"))

    run_type = parser.add_subparsers(
        help=_("How to fetch updates, see https://core.telegram.org/bots/api#getting-updates"),
        dest="strategy",
    )
    run_type.add_parser("polling", help=_("run with polling (default)"))

    webhook = run_type.add_parser("webhook", help=_("run with webhooks"))
    webhook.add_argument("-H", "--host", default="localhost", help=_("host to listen at"))
    webhook.add_argument("-p", "--port", type=int, default=8880, help=_("port to listen at"))
    webhook.add_argument("-u", "--webhook-url", help=_("url for Telegram to make requests to"))
    webhook.add_argument(
        "--shutdown-remove", action="store_true", help=_("remove webhook on app shutdown")
    )

    return parser


def _parse_args(argv: Optional[Sequence[str]] = None) -> Args:
    parser = _init_parser()
    args = parser.parse_args(argv)

    spec = getfullargspec(Args)
    params = {}
    for k, v in args.__dict__.items():
        if k not in spec.args:
            raise TypeError(f"{Args!r} doesn't accept {k!r} param")
        current_type = spec.annotations.get(k)
        is_optional = type(None) in getattr(current_type, "__args__", ())
        if v is None and not is_optional:
            continue
        params[k] = v

    return Args(**params)


def main() -> None:
    args = _parse_args()
    config = read_config(args.config)

    bot = create_bot(config.telegram.token)
    kwargs = dict(
        session_factory=get_session_factory(config.db.dsn),
        superuser_id=config.telegram.superuser_id,
        webhook_url=args.webhook_url,
        remove_webhook=args.shutdown_remove,
    )
    if args.strategy == "webhook":
        try:
            from .webhook import start_webhook
        except ImportError as e:
            raise ImportError("Make sure 'uvicorn' and 'FastAPI' are installed") from e

        start_webhook(
            bot,
            args.host,
            args.port,
            args.loglevel,
            **kwargs,
        )
    elif args.strategy == "polling" or args.strategy is None:
        from .polling import start_polling

        logging.basicConfig(level=args.loglevel.upper())
        start_polling(bot, **kwargs)
    else:
        raise AssertionError

# SpinEverydayBot
# Copyright © 2016-2017 Evgeniy Filimonov <https://t.me/evgfilim1>
# See full NOTICE at http://github.com/evgfilim1/spin_everyday_bot

from collections import defaultdict
from os import listdir
from os.path import isdir
from gettext import translation
from . import texts
from utils import get_config_key
from config import FALLBACK_LANG


class Localization:
    available_languages = {}
    __languages = defaultdict(dict)

    def __init__(self, lang, data=None):
        if isinstance(lang, int):
            self._lang = get_config_key(lang, 'lang', default=FALLBACK_LANG)
        elif isinstance(lang, str):
            self._lang = lang
        else:
            raise TypeError(f'first argument must be str or int, not {lang.__class__.__name__}')
        self._data = data
        self.reload()
        if self._lang not in self.available_languages:
            raise ValueError(f'{self._lang} is not supported')

    @classmethod
    def reload(cls):
        cls.__languages.clear()
        cls.available_languages.clear()
        for lang in listdir('lang'):
            if not isdir(f'lang/{lang}') or lang.startswith('_'):
                continue
            _ = translation('messages', localedir='./lang/', languages=(lang,)).gettext
            cls.available_languages.update({lang: _(texts._NAME)})
            cls.__languages.update({lang: _})

    def __getitem__(self, item):
        if self._data is None:
            if item.upper() in dir(texts):
                result = getattr(texts, item.upper())
            else:
                raise KeyError(item)
        else:
            result = self._data[item]
        if isinstance(result, dict):
            return self.__class__(self._lang, data=result)
        elif not isinstance(result, str):
            return result
        else:
            return self.__languages.get(self._lang, self.__languages.get(FALLBACK_LANG))(result)

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.__getitem__(item)

    def __call__(self, item):
        return self.__getitem__(item)

    def get(self, item):
        return self.__getitem__(item)


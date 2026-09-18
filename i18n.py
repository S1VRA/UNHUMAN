import json
import os
import sys

_current_lang = "en"
_strings = {}


def _base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def load_language(lang_code):
    global _current_lang, _strings
    locales_dir = os.path.join(_base_dir(), "locales")
    path = os.path.join(locales_dir, f"{lang_code}.json")
    if not os.path.exists(path):
        path = os.path.join(locales_dir, "en.json")
        lang_code = "en"
    with open(path, "r", encoding="utf-8") as f:
        _strings = json.load(f)
    _current_lang = lang_code


def t(key, **kwargs):
    text = _strings.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def get_current_language():
    return _current_lang

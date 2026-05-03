import json
import os
from flask import current_app, g, request, session
from config import DEFAULT_LOCALE, LANGUAGE_NAMES, SUPPORTED_LANGUAGES


def load_translations():
    translations = {}
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join("i18n", f"{lang}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                translations[lang] = json.load(f)
        except FileNotFoundError:
            translations[lang] = {}
    return translations


TRANSLATIONS = load_translations()


def get_translations():
    if current_app and current_app.debug:
        return load_translations()
    return TRANSLATIONS


def _get_translation_value(lang, key_parts):
    translations = get_translations()
    data = translations.get(lang, {})
    for part in key_parts:
        if isinstance(data, dict):
            data = data.get(part)
        else:
            data = None
        if data is None:
            break
    if data is None and lang != DEFAULT_LOCALE:
        return _get_translation_value(DEFAULT_LOCALE, key_parts)
    return data


def translate_text(key, locale=None, default=None, **kwargs):
    if not key:
        return ""
    lang = locale or getattr(g, "current_locale", None) or session.get("lang") or DEFAULT_LOCALE
    parts = key.split(".")
    value = _get_translation_value(lang, parts)
    if value is None:
        value = default if default is not None else _get_translation_value(DEFAULT_LOCALE, parts)
    if value is None:
        value = default if default is not None else key
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    return value


def select_locale():
    lang = session.get("lang")
    if lang in SUPPORTED_LANGUAGES:
        g.current_locale = lang
        return lang
    best_match = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
    selected = best_match or DEFAULT_LOCALE
    g.current_locale = selected
    return selected


def inject_translation_helpers():
    return {
        "t": translate_text,
        "current_locale": getattr(g, "current_locale", DEFAULT_LOCALE),
        "supported_languages": SUPPORTED_LANGUAGES,
        "language_names": LANGUAGE_NAMES,
    }

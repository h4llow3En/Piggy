"""
Translation utilities for Piggy.
"""

import json
import logging
import os
from contextvars import ContextVar
from typing import Annotated

from fastapi import Header

LOCALE_DEFAULT: str = "en"
LOCALES_DIR: str = os.path.join(os.path.dirname(__file__), "..", "locales")

locale_ctx: ContextVar[str] = ContextVar("locale", default=LOCALE_DEFAULT)

logger = logging.getLogger(__name__)


class Translator:  # pylint: disable=too-few-public-methods
    """
    Translator class for handling internationalization and localization.
    """

    def __init__(self):
        self._catalogs = {}

    def _load_lang(self, lang: str) -> dict:
        if lang not in self._catalogs:
            path = os.path.join(LOCALES_DIR, f"{lang}.json")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._catalogs[lang] = json.load(f)
            except FileNotFoundError:
                self._catalogs[lang] = {}
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Failed to load locale file %s: %s", path, exc)
                self._catalogs[lang] = {}
        return self._catalogs[lang]

    @staticmethod
    def _resolve_key(catalog: dict, key: str):
        node = catalog
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node if isinstance(node, str) else None

    def t(self, message: str) -> str:
        """Look up the translation for the given key."""
        lang = locale_ctx.get()
        catalog = self._load_lang(lang)
        value = self._resolve_key(catalog, message)
        return value or message


_translator = Translator()


async def i18n(
    accept_language: Annotated[
        str,
        Header(title="Accept-Language"),
    ] = LOCALE_DEFAULT,
):
    """
    Adds the locale to the request context.
    """
    lang = LOCALE_DEFAULT
    if accept_language:
        lang = accept_language.split(",")[0].split("-")[0].split(";")[0].lower()

    if not os.path.exists(os.path.join(LOCALES_DIR, f"{lang}.json")):
        logger.debug("Locale %s not found, falling back to default locale.", lang)
        lang = LOCALE_DEFAULT

    locale_ctx.set(lang)


def _(message: str) -> str:
    return _translator.t(message)


def get_translations(lang: str):
    """Return the content of the translations files."""
    lang = "".join(c for c in lang if c.isalnum() or c in "-_")

    locale_path = os.path.join(
        os.path.dirname(__file__), "..", "locales", f"{lang}.json"
    )
    if not os.path.exists(locale_path):
        locale_path = os.path.join(
            os.path.dirname(__file__), "..", "locales", "en.json"
        )
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:  # pylint: disable=bare-except
        return {}

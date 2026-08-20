#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint:disable=W0301
#  
#  Copyright 2018- William Martinez Bas <metfar@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
#import warnings;
#warnings.filterwarnings("ignore", category=UserWarning);

"""Shared language-profile normalization for the phonem command-line toolkit.

EN: Every project tool accepts ``-l LANG`` and ``--language LANG`` for its main
    language. Short language names are aliases for the project's default study
    profiles: en -> en-ca, es -> es-uy and fr -> fr-fr. Backend adapters may
    collapse a study profile to a language family when the external engine does
    not understand regional profiles.
ES: Todas las herramientas aceptan ``-l LANG`` y ``--language LANG`` para su
    idioma principal. Los nombres cortos son alias de los perfiles de estudio
    predeterminados: en -> en-ca, es -> es-uy y fr -> fr-fr. Los adaptadores de
    backend pueden reducir el perfil a su familia cuando el motor externo no
    entiende variantes regionales.
FR: Tous les outils acceptent ``-l LANG`` et ``--language LANG`` pour leur
    langue principale. Les codes courts sont des alias des profils d'étude par
    défaut : en -> en-ca, es -> es-uy et fr -> fr-fr. Les adaptateurs peuvent
    réduire un profil à sa famille lorsque le moteur externe ne connaît pas les
    variantes régionales.
"""

import os;
import re;

SHORT_LANGUAGE_ALIASES = {
    "en": "en-ca",
    "es": "es-uy",
    "fr": "fr-fr",
};

CANONICAL_PROJECT_LANGUAGES = (
    "en-ca", "en-us", "en-gb", "en-rp", "en-lancashire", "en-nyc",
    "es-uy", "es-es",
    "fr-fr", "fr-ca", "fr-be", "fr-ch", "fr-ch-qv",
);

# EN: Locale-like values are normalized before alias resolution.
# ES: Los valores tipo locale se normalizan antes de resolver alias.
# FR: Les valeurs de type locale sont normalisées avant la résolution des alias.
_LOCALE_MODIFIER_RE = re.compile(r"[.@].*$");


def normalize_language_tag(language, allow_auto=False):
    """EN: Normalize LANG/locale spelling and apply project short aliases.
    ES: Normaliza LANG/locales y aplica los alias cortos del proyecto.
    FR: Normalise LANG/locale et applique les alias courts du projet.""";
    if language is None:
        return "";
    value = str(language).strip();
    if not value:
        return "";
    lowered = value.lower();
    if allow_auto and lowered == "auto":
        return "auto";
    if lowered in {"c", "posix", "c.utf-8", "c.utf8"}:
        return "";
    value = _LOCALE_MODIFIER_RE.sub("", value);
    value = value.strip().lower().replace("_", "-");
    value = re.sub(r"-+", "-", value).strip("-");
    if allow_auto and value == "auto":
        return "auto";
    return SHORT_LANGUAGE_ALIASES.get(value, value);


def canonical_language(language, allow_auto=False):
    """EN: Return the canonical project spelling when an alias is known.
    ES: Devuelve la grafía canónica del proyecto cuando existe un alias.
    FR: Renvoie la forme canonique du projet lorsqu'un alias est connu.""";
    return normalize_language_tag(language, allow_auto=allow_auto);


def language_family(language):
    """EN: Return a normalized base language code.
    ES: Devuelve el código base normalizado del idioma.
    FR: Renvoie le code de langue de base normalisé.""";
    value = canonical_language(language, allow_auto=True);
    if value in {"", "auto"}:
        return value;
    return value.split("-", 1)[0];


def short_alias_for(language):
    """EN: Return the short alias for a canonical default profile, if any.
    ES: Devuelve el alias corto del perfil canónico predeterminado, si existe.
    FR: Renvoie l'alias court du profil canonique par défaut, s'il existe.""";
    canonical = canonical_language(language);
    for alias, target in SHORT_LANGUAGE_ALIASES.items():
        if canonical == target:
            return alias;
    return "";


def environment_language(environ=None):
    """EN: Resolve the user's locale from LC_ALL, LC_MESSAGES or LANG.
    ES: Resuelve la locale del usuario desde LC_ALL, LC_MESSAGES o LANG.
    FR: Résout la locale utilisateur depuis LC_ALL, LC_MESSAGES ou LANG.""";
    values = os.environ if environ is None else environ;
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        raw = values.get(name, "");
        normalized = canonical_language(raw);
        if normalized:
            return normalized, name, raw;
    return "", "", "";


def backend_family_language(language, allow_auto=False):
    """EN: Collapse known study profiles to a backend language family.
    ES: Reduce perfiles conocidos a la familia entendida por el backend.
    FR: Réduit les profils connus à la famille comprise par le backend.""";
    value = canonical_language(language, allow_auto=allow_auto);
    if value == "auto":
        return "auto";
    if value in CANONICAL_PROJECT_LANGUAGES:
        return language_family(value);
    return value;

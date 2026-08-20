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

"""phonem.py - Small command-line pronunciation study tool built around phonemizer/eSpeak.

EN: Logical study profiles are kept separate from installed eSpeak voices. Regional
    study profiles such as fr-ca, en-ca and es-uy are explicit approximations, never
    presented as native models. Cardinal integers are expanded before phonemization
    so French/Spanish long scale and modern English short scale remain visible and
    correct. es-uy is a formal Uruguayan study profile based on Latin-American
    Spanish (with seseo) plus a small, editable IPA overlay for [ʃ] yeismo.
ES: Los perfiles lógicos de estudio se separan de las voces eSpeak instaladas. Las
    voces dialectales inexistentes, como fr-ca, en-ca y es-uy, son aproximaciones
    explícitas y nunca se presentan como modelos nativos. Los enteros cardinales se
    expanden antes de fonemizar para mantener visibles y correctas la escala larga
    de francés/español y la escala corta del inglés moderno. es-uy es un perfil
    uruguayo formal basado en español latinoamericano con seseo, más una pequeña
    capa IPA editable para el yeísmo con [ʃ].
FR: Les profils logiques d'étude sont séparés des voix eSpeak installées. Les voix
    dialectales absentes, comme fr-ca, en-ca et es-uy, restent des approximations
    explicites et ne sont jamais présentées comme des modèles natifs. Les entiers
    cardinaux sont développés avant la phonémisation afin de respecter l'échelle
    longue du français/de l'espagnol et l'échelle courte de l'anglais moderne.
    es-uy est un profil formel uruguayen fondé sur l'espagnol latino-américain avec
    seseo, plus une petite couche IPA modifiable pour le yeísmo en [ʃ].

EN: License: GNU GPL version 2 or (at your option) any later version.
ES: Licencia: GNU GPL versión 2 o, a elección del usuario, cualquier versión posterior.
FR: Licence : GNU GPL version 2 ou, à votre choix, toute version ultérieure.
"""

import argparse;
import copy;
import json;
import re;
import sys;
from pathlib import Path;

from language_profiles import (
    SHORT_LANGUAGE_ALIASES,
    canonical_language,
    language_family as project_language_family,
    short_alias_for,
);

PROGRAM = "phonem.py";
VERSION = "1.6.0";

LANGUAGE_PROFILES = {
    "en-ca": {
        "family": "en",
        "label": "Canadian English study profile (approximate backend)",
        "approximation": True,
    },
    "en-us": {
        "family": "en",
        "label": "US English",
    },
    "en-gb": {
        "family": "en",
        "label": "British English",
    },
    "en-rp": {
        "family": "en",
        "label": "British English (Received Pronunciation)",
    },
    "en-lancashire": {
        "family": "en",
        "label": "British English (Lancastrian)",
    },
    "en-nyc": {
        "family": "en",
        "label": "US English (New York, when available)",
    },
    "es-es": {
        "family": "es",
        "label": "Spanish (Spain)",
    },
    "es-uy": {
        "family": "es",
        "label": "Uruguayan Spanish formal study profile (approximate backend)",
        "approximation": True,
    },
    "fr-fr": {
        "family": "fr",
        "label": "French (France)",
    },
    "fr-ca": {
        "family": "fr",
        "label": "Quebec French study profile (approximate backend; not a native Quebec voice)",
        "approximation": True,
    },
    "fr-be": {
        "family": "fr",
        "label": "French (Belgium)",
    },
    "fr-ch": {
        "family": "fr",
        "label": "Swiss French (huitante study profile: regional)",
    },
    "fr-ch-qv": {
        "family": "fr",
        "label": "Swiss French (quatre-vingts study profile)",
    },
};

AUTO_TARGETS = {
    "en": "en-ca",
    "es": "es-uy",
    "fr": "fr-fr",
};

FRENCH_WORDS = {
    "alors", "au", "aux", "avec", "avoir", "bonjour", "bonsoir", "car",
    "ce", "ces", "cette", "comme", "comment", "dans", "de", "des", "du",
    "elle", "elles", "en", "est", "et", "etre", "être", "faire", "il",
    "ils", "je", "la", "le", "les", "mais", "merci", "mes", "mon", "ne",
    "non", "nous", "oui", "ou", "où", "par", "pas", "plus", "pour",
    "pourquoi", "quand", "que", "qui", "quoi", "sa", "sans", "se", "ses",
    "si", "son", "sont", "sur", "ta", "tes", "ton", "tout", "tu", "un",
    "une", "vous", "votre", "vos", "veux", "vais", "suis", "peux", "faut",
};

ENGLISH_WORDS = {
    "a", "about", "am", "an", "and", "are", "as", "at", "be", "because",
    "but", "by", "can", "could", "did", "do", "does", "for", "from", "had",
    "has", "have", "he", "hello", "her", "here", "his", "how", "i", "if",
    "in", "is", "it", "me", "my", "no", "not", "of", "on", "or", "our",
    "she", "should", "so", "that", "the", "their", "them", "there", "these",
    "they", "this", "those", "to", "us", "want", "was", "we", "were", "what",
    "when", "where", "which", "who", "why", "will", "with", "would", "yes",
    "you", "your", "thanks", "thank", "please", "wanna", "going",
};

SPANISH_WORDS = {
    "a", "al", "algo", "aquí", "aunque", "bien", "buen", "buena", "buenas", "buenos",
    "cada", "como", "cómo", "con", "cuando", "cuándo", "de", "del", "donde", "dónde",
    "el", "ella", "ellas", "ellos", "en", "es", "esa", "ese", "eso", "esta", "está", "este",
    "gracias", "hay", "hola", "la", "las", "lo", "los", "más", "me", "mi", "muy", "no",
    "nos", "o", "para", "pero", "por", "porque", "que", "qué", "se", "sí", "sin", "soy",
    "su", "sus", "también", "te", "tengo", "tu", "tú", "un", "una", "uno", "usted", "ustedes",
    "vamos", "vos", "vosotros", "y", "ya", "yo", "quiero", "puedo", "trabajo", "uruguay",
};

FRENCH_STRONG_DIACRITICS = set("àâæçèêëîïôœùûÿÀÂÆÇÈÊËÎÏÔŒÙÛŸ");
SPANISH_STRONG_MARKS = set("ñÑ¿¡áíóúÁÍÓÚ");
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÆæ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿŒœÆæ]+)?");
FRENCH_CONTRACTION_RE = re.compile(r"\b(?:c|d|j|l|m|n|qu|s|t)['’]", re.IGNORECASE);
ENGLISH_CONTRACTION_RE = re.compile(r"\b(?:i['’]m|you['’]re|we['’]re|they['’]re|it['’]s|don['’]t|doesn['’]t|didn['’]t|can['’]t|won['’]t|wouldn['’]t|shouldn['’]t|couldn['’]t)\b", re.IGNORECASE);

# EN: Only standalone integer tokens are normalized. Decimal numbers, dates,
#     times and obvious slash/hyphen-delimited identifiers are left untouched.
# ES: Sólo se normalizan enteros aislados. Decimales, fechas, horas e
#     identificadores evidentes con barra/guion se dejan intactos.
# FR: Seuls les entiers isolés sont normalisés. Les décimaux, dates, heures et
#     identifiants évidents avec barre/tiret sont laissés tels quels.
INTEGER_TOKEN_RE = re.compile(
    r"(?<![\w\d/.:,\-‐‑‒–—−])"
    r"[+-]?(?:\d{1,3}(?:[\u00A0\u202F_\'’]\d{3})+|\d+)"
    r"(?![\w\d/.:,\-‐‑‒–—−])"
);

PROTECTED_NUMERIC_RES = (
    re.compile(r"(?<!\w)[+-]?\d+[.,]\d+(?!\w)"),
    re.compile(r"(?<!\w)\d{1,4}[-/‐‑‒–—−]\d{1,2}[-/‐‑‒–—−]\d{1,4}(?!\w)"),
    re.compile(r"(?<!\w)\d{1,2}:\d{2}(?::\d{2})?(?!\w)"),
    re.compile(
        r"(?<!\w)(?:\+?1[ \u00A0\u202F.\-‐‑‒–—−]*)?"
        r"(?:\(?\d{3}\)?)[ \u00A0\u202F.\-‐‑‒–—−]+"
        r"\d{3}[\-‐‑‒–—−]\d{4}(?!\w)"
    ),
);

FRENCH_SMALL = {
    0: "zéro",
    1: "un",
    2: "deux",
    3: "trois",
    4: "quatre",
    5: "cinq",
    6: "six",
    7: "sept",
    8: "huit",
    9: "neuf",
    10: "dix",
    11: "onze",
    12: "douze",
    13: "treize",
    14: "quatorze",
    15: "quinze",
    16: "seize",
    17: "dix-sept",
    18: "dix-huit",
    19: "dix-neuf",
};

FRENCH_DECIMAL_TENS = {
    20: "vingt",
    30: "trente",
    40: "quarante",
    50: "cinquante",
    60: "soixante",
};

# EN: French long-scale names. This is deliberately finite: absurdly huge
#     values fail clearly instead of being invented by the program.
# ES: Nombres de la escala larga francesa. Es deliberadamente finita: ante un
#     valor absurdamente grande el programa falla claramente en vez de inventar.
# FR: Noms français de l'échelle longue. La liste est volontairement finie :
#     une valeur démesurée provoque une erreur claire au lieu d'être inventée.
FRENCH_SCALE_WORDS = (
    "",
    "mille",
    "million",
    "milliard",
    "billion",
    "billiard",
    "trillion",
    "trilliard",
    "quadrillion",
    "quadrilliard",
    "quintillion",
    "quintilliard",
    "sextillion",
    "sextilliard",
    "septillion",
    "septilliard",
    "octillion",
    "octilliard",
    "nonillion",
    "nonilliard",
    "décillion",
    "décilliard",
);

# EN: Modern English in the US, Canada and the UK uses the short scale.
# ES: El inglés moderno de EE. UU., Canadá y Reino Unido usa la escala corta.
# FR: L'anglais moderne des États-Unis, du Canada et du Royaume-Uni utilise l'échelle courte.
ENGLISH_SMALL = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
    18: "eighteen", 19: "nineteen",
};
ENGLISH_TENS = {
    20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
    70: "seventy", 80: "eighty", 90: "ninety",
};
ENGLISH_SCALE_WORDS = (
    "", "thousand", "million", "billion", "trillion", "quadrillion",
    "quintillion", "sextillion", "septillion", "octillion", "nonillion",
    "decillion", "undecillion", "duodecillion", "tredecillion",
);

# EN: Spanish uses the long scale: 10^9 = mil millones, 10^12 = billón,
#     10^18 = trillón. The list below names powers of one million.
# ES: El español usa la escala larga: 10^9 = mil millones, 10^12 = billón,
#     10^18 = trillón. La lista nombra potencias de un millón.
# FR: L'espagnol utilise l'échelle longue : 10^9 = mil millones, 10^12 = billón,
#     10^18 = trillón. La liste nomme les puissances d'un million.
SPANISH_SMALL = {
    0: "cero", 1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis",
    7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce",
    13: "trece", 14: "catorce", 15: "quince", 16: "dieciséis", 17: "diecisiete",
    18: "dieciocho", 19: "diecinueve", 20: "veinte", 21: "veintiuno",
    22: "veintidós", 23: "veintitrés", 24: "veinticuatro", 25: "veinticinco",
    26: "veintiséis", 27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
};
SPANISH_TENS = {
    30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
    70: "setenta", 80: "ochenta", 90: "noventa",
};
SPANISH_HUNDREDS = {
    2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
    6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos",
};
SPANISH_LONG_SCALE_NAMES = (
    "", "millón", "billón", "trillón", "cuatrillón", "quintillón",
    "sextillón", "septillón", "octillón", "nonillón", "decillón",
);

# EN: These are study profiles, not a claim that every speaker inside a country
#     uses one single form. fr-ch intentionally models the huitante variety.
# ES: Son perfiles de estudio, no una afirmación de que todos los hablantes de
#     un país usen una única forma. fr-ch modela intencionalmente huitante.
# FR: Il s'agit de profils d'étude, non d'une affirmation selon laquelle tous
#     les locuteurs d'un pays utilisent une seule forme. fr-ch modélise huitante.
DEFAULT_EXCEPTIONS = {
    "schema_version": 4,
    "notes": {
        "en": "Edit backend_candidates, number_profiles, number_scales, replacements, ipa_replacements or ipa_regex_replacements, then load the file with --exceptions FILE.",
        "es": "Edite backend_candidates, number_profiles, number_scales, replacements, ipa_replacements o ipa_regex_replacements y cargue el archivo con --exceptions FILE.",
        "fr": "Modifiez backend_candidates, number_profiles, number_scales, replacements, ipa_replacements ou ipa_regex_replacements, puis chargez le fichier avec --exceptions FILE.",
    },
    "license": "GPL-2.0-or-later",
    "profile_notes": {
        "en": {
            "en-ca": "Upstream eSpeak NG has no native en-ca voice; en-us is only a practical Canadian-English approximation for this study profile.",
            "es-es": "eSpeak NG exposes Spanish (Spain) as es. The es-es study profile adds a small yeismo overlay so <ll> follows the widespread modern /ʝ/ realization instead of eSpeak's conservative /ʎ/.",
            "es-uy": "Upstream eSpeak NG has no native es-uy voice. This formal Uruguayan study profile uses Latin-American Spanish (es-419, legacy es-la) for seseo and applies an IPA overlay for voiceless rehilated yeismo (consonantal y/ll -> [ʃ]). The overlay handles both palatal symbols and the /jj/ sequence emitted by some Latin-American eSpeak backends (ella -> /ejja/), yielding the study target /eʃa/ while leaving word-final vocalic y untouched. Final /s/ is preserved; no aspiration or deletion is introduced.",
            "fr-ca": "Uses Quebec/France number forms for 70/80/90. Upstream eSpeak NG has no native fr-ca voice; fr-be is only this project's pragmatic pronunciation approximation, not a claim of equivalence or of being linguistically the closest voice.",
            "fr-be": "Uses septante, quatre-vingts and nonante.",
            "fr-ch": "Study profile using septante, huitante and nonante; huitante is regional within French-speaking Switzerland.",
            "fr-ch-qv": "Alternate Swiss study profile using septante, quatre-vingts and nonante.",
        },
        "es": {
            "en-ca": "eSpeak NG upstream no tiene una voz nativa en-ca; en-us es sólo una aproximación práctica al inglés canadiense para este perfil de estudio.",
            "es-es": "eSpeak NG expone el español de España como es. El perfil de estudio es-es agrega una pequeña capa de yeísmo para que <ll> siga la realización moderna extendida /ʝ/ en vez del /ʎ/ conservador de eSpeak.",
            "es-uy": "eSpeak NG upstream no tiene una voz nativa es-uy. Este perfil formal uruguayo usa español latinoamericano (es-419, es-la legado) para el seseo y aplica una capa IPA para el yeísmo rehilado sordo (y/ll consonánticas -> [ʃ]). La capa maneja tanto símbolos palatales como la secuencia /jj/ que algunos backends latinoamericanos de eSpeak emiten (ella -> /ejja/), para obtener el objetivo /eʃa/ sin alterar la y vocálica final. Se conservan las /s/ finales; no se introduce aspiración ni elisión.",
            "fr-ca": "Usa las formas de Quebec/Francia para 70/80/90. eSpeak NG upstream no tiene una voz nativa fr-ca; fr-be es sólo la aproximación pragmática elegida por este proyecto, no una afirmación de equivalencia ni de que sea lingüísticamente la voz más cercana.",
            "fr-be": "Usa septante, quatre-vingts y nonante.",
            "fr-ch": "Perfil de estudio con septante, huitante y nonante; huitante es regional dentro de la Suiza francófona.",
            "fr-ch-qv": "Perfil suizo alternativo con septante, quatre-vingts y nonante.",
        },
        "fr": {
            "en-ca": "eSpeak NG upstream ne fournit pas de voix native en-ca; en-us n'est qu'une approximation pratique de l'anglais canadien pour ce profil d'étude.",
            "es-es": "eSpeak NG expose l'espagnol d'Espagne sous le code es. Le profil d'étude es-es ajoute une petite couche de yeísmo afin que <ll> suive la réalisation moderne largement répandue /ʝ/ plutôt que le /ʎ/ conservateur d'eSpeak.",
            "es-uy": "eSpeak NG upstream ne fournit pas de voix native es-uy. Ce profil formel uruguayen utilise l'espagnol latino-américain (es-419, ancien es-la) pour le seseo et applique une couche IPA pour le yeísmo rehilado sourd (y/ll consonantiques -> [ʃ]). Cette couche gère les symboles palataux ainsi que la séquence /jj/ émise par certains backends latino-américains d'eSpeak (ella -> /ejja/), afin d'obtenir la cible /eʃa/ sans modifier le y vocalique final. Les /s/ finales sont conservées; aucune aspiration ni élision n'est ajoutée.",
            "fr-ca": "Utilise les formes du Québec/de France pour 70/80/90. eSpeak NG upstream ne fournit pas de voix native fr-ca; fr-be n'est que l'approximation pragmatique choisie par ce projet, sans prétendre à l'équivalence ni à la plus grande proximité linguistique.",
            "fr-be": "Utilise septante, quatre-vingts et nonante.",
            "fr-ch": "Profil d'étude avec septante, huitante et nonante; huitante est régional en Suisse romande.",
            "fr-ch-qv": "Profil suisse alternatif avec septante, quatre-vingts et nonante.",
        },
    },
    # EN: Backend candidates are data on purpose. Missing native dialect voices are
    #     explicit approximations that can be exported, inspected and changed.
    # ES: Los backends son datos a propósito. Las voces dialectales inexistentes se
    #     modelan como aproximaciones explícitas, exportables y modificables.
    # FR: Les backends sont volontairement des données. Les voix dialectales absentes
    #     sont des approximations explicites, exportables et modifiables.
    "backend_candidates": {
        "en-ca": ["en-us", "en", "en-gb"],
        "en-us": ["en-us", "en"],
        "en-gb": ["en-gb", "en", "en-gb-x-rp", "en-uk-rp"],
        "en-rp": ["en-gb-x-rp", "en-uk-rp", "en-gb", "en"],
        "en-lancashire": ["en-gb-x-gbclan", "en-uk-north", "en-gb", "en"],
        "en-nyc": ["en-us-nyc", "en-us", "en"],
        "es-es": ["es", "es-es"],
        # EN: No Spain fallback here: formal Uruguayan Spanish is seseante.
        # ES: Sin fallback a España: el español uruguayo formal es seseante.
        # FR: Pas de repli vers l'Espagne : l'espagnol uruguayen formel est seseante.
        "es-uy": ["es-419", "es-la"],
        "fr-fr": ["fr-fr", "fr"],
        "fr-ca": ["fr-be", "fr-fr", "fr"],
        "fr-be": ["fr-be", "fr-fr", "fr"],
        "fr-ch": ["fr-ch", "fr-fr", "fr"],
        "fr-ch-qv": ["fr-ch", "fr-fr", "fr"],
    },
    # EN: French lexical number variants. All French profiles use the long scale.
    # ES: Variantes léxicas de los números franceses. Todos usan escala larga.
    # FR: Variantes lexicales des nombres français. Tous utilisent l'échelle longue.
    "number_profiles": {
        "fr": {"seventy_style": "soixante-dix", "eighty_style": "quatre-vingt", "ninety_style": "quatre-vingt-dix"},
        "fr-fr": {"seventy_style": "soixante-dix", "eighty_style": "quatre-vingt", "ninety_style": "quatre-vingt-dix"},
        "fr-ca": {"seventy_style": "soixante-dix", "eighty_style": "quatre-vingt", "ninety_style": "quatre-vingt-dix"},
        "fr-be": {"seventy_style": "septante", "eighty_style": "quatre-vingt", "ninety_style": "nonante"},
        "fr-ch": {"seventy_style": "septante", "eighty_style": "huitante", "ninety_style": "nonante"},
        "fr-ch-qv": {"seventy_style": "septante", "eighty_style": "quatre-vingt", "ninety_style": "nonante"},
    },
    # EN: Scale and English conjunction style are data too. Modern English in the
    #     US, Canada and UK is short-scale; Spanish and French are long-scale.
    # ES: La escala y el uso inglés de "and" también son datos. El inglés moderno
    #     de EE. UU., Canadá y Reino Unido usa escala corta; español y francés, larga.
    # FR: L'échelle et l'usage anglais de "and" sont aussi des données. L'anglais
    #     moderne US/Canada/R.-U. est à échelle courte; espagnol et français, longue.
    "number_scales": {
        "en": {"scale": "short", "and_style": "british"},
        "en-ca": {"scale": "short", "and_style": "british"},
        "en-us": {"scale": "short", "and_style": "american"},
        "en-gb": {"scale": "short", "and_style": "british"},
        "en-rp": {"scale": "short", "and_style": "british"},
        "en-lancashire": {"scale": "short", "and_style": "british"},
        "en-nyc": {"scale": "short", "and_style": "american"},
        "es": {"scale": "long"},
        "es-es": {"scale": "long"},
        "es-uy": {"scale": "long"},
        "fr": {"scale": "long"},
        "fr-fr": {"scale": "long"},
        "fr-ca": {"scale": "long"},
        "fr-be": {"scale": "long"},
        "fr-ch": {"scale": "long"},
        "fr-ch-qv": {"scale": "long"},
    },
    "replacements": {
        "en-ca": {}, "en-us": {}, "en-gb": {}, "en-rp": {}, "en-lancashire": {}, "en-nyc": {},
        "es-es": {}, "es-uy": {},
        "fr-fr": {}, "fr-ca": {}, "fr-be": {}, "fr-ch": {}, "fr-ch-qv": {},
    },
    # EN: Literal IPA post-processing is intentionally small. Spain's eSpeak
    #     rules retain /ʎ/ for <ll>, while modern cultivated Spanish is broadly
    #     yeista; es-es therefore maps that lateral to /ʝ/. The formal es-uy
    #     profile maps consonantal y/ll to [ʃ]. Some Latin-American eSpeak
    #     backends encode intervocalic consonantal y/ll as /jj/ (ella -> /ejja/),
    #     so a contextual regex below maps /jj/ to [ʃ] only when another vowel
    #     follows. This deliberately avoids changing word-final vocalic y in
    #     words such as muy.
    # ES: El postprocesado IPA es deliberadamente pequeño. Las reglas de eSpeak
    #     para España conservan /ʎ/ en <ll>, mientras que el español culto moderno
    #     es mayoritariamente yeísta; por eso es-es lleva esa lateral a /ʝ/. El
    #     perfil formal es-uy lleva y/ll consonánticas a [ʃ]. Algunos backends
    #     latinoamericanos de eSpeak codifican la y/ll consonántica intervocálica
    #     como /jj/ (ella -> /ejja/); por eso una regex contextual transforma /jj/
    #     en [ʃ] sólo cuando sigue otra vocal. Así no se altera la y vocálica final
    #     de palabras como muy.
    # FR: Le post-traitement IPA reste volontairement limité. Les règles eSpeak
    #     pour l'Espagne conservent /ʎ/ pour <ll>, tandis que l'espagnol cultivé
    #     moderne est largement yeíste; es-es transforme donc cette latérale en
    #     /ʝ/. Le profil formel es-uy transforme y/ll consonantiques en [ʃ].
    #     Certains backends latino-américains d'eSpeak codent le y/ll consonantique
    #     intervocalique comme /jj/ (ella -> /ejja/); une regex contextuelle change
    #     donc /jj/ en [ʃ] seulement lorsqu'une autre voyelle suit, sans modifier
    #     le y vocalique final de mots comme muy.
    "ipa_replacements": {
        "es-es": {"ʎj": "ʝ", "ʎ": "ʝ"},
        "es-uy": {"ɟʝj": "ʃ", "ʝj": "ʃ", "ʎj": "ʃ", "ɟʝ": "ʃ", "ʝ": "ʃ", "ʎ": "ʃ"},
    },
    "ipa_regex_replacements": {
        "es-uy": [
            {"pattern": "jj(?=[ˈˌ]?[aeiouɛɔ])", "replacement": "ʃ"},
        ],
    },
};

SEVENTY_STYLES = {"soixante-dix", "septante"};
EIGHTY_STYLES = {"quatre-vingt", "huitante"};
NINETY_STYLES = {"quatre-vingt-dix", "nonante"};

# EN: Representative values used by --number-table: French dialect-sensitive tens
#     plus the powers where long and short scales stop sharing the same names.
# ES: Valores representativos de --number-table: decenas sensibles al dialecto
#     francés y potencias donde las escalas larga y corta dejan de coincidir.
# FR: Valeurs représentatives de --number-table : dizaines sensibles aux variantes
#     françaises et puissances où les échelles longue et courte divergent.
NUMBER_TABLE_VALUES = (
    70, 80, 90, 100, 1000, 1000000, 1000000000, 1000000000000,
    1000000000000000, 1000000000000000000,
);
NUMBER_TABLE_LANGUAGES = (
    "en-us", "en-ca", "en-gb", "fr-fr", "fr-ca", "fr-be", "fr-ch", "fr-ch-qv", "es-es", "es-uy",
);


def build_parser():
    """EN: Build the CLI parser. ES: Construye el parser CLI. FR: Construit l'analyseur CLI."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Study English/French/Spanish pronunciation variants with phonemizer/eSpeak NG.",
        epilog=(
            "Examples:\n"
            "  phonem.py -t \"Bonjour, comment allez-vous ?\" -l fr-ca\n"
            "  phonem.py -t \"Do you want a poutine?\" -l en-ca\n"
            "  phonem.py -t \"Lluvia, yo, pacto, verdad, casas.\" -l es-uy\n"
            "  phonem.py -i texte.txt -l fr-fr\n"
            "  cat texte.txt | phonem.py\n"
            "  phonem.py --normalize-only -t \"70 80 90 1970\" -l fr-ca\n"
            "  phonem.py --number-table\n"
            "  phonem.py --export-exceptions phonem-exceptions.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    );
    parser.add_argument("text_arg", nargs="?", help="text to phonemize (positional alternative to -t)");
    source = parser.add_mutually_exclusive_group();
    source.add_argument("-t", "--text", help="text to phonemize");
    source.add_argument("-i", "--input", metavar="FILE", help="UTF-8 input file; use '-' for stdin");
    parser.add_argument(
        "-l",
        "--language",
        default="auto",
        metavar="LANG",
        help="project language/profile or eSpeak code; en=en-ca, es=es-uy, fr=fr-fr (default: auto)",
    );
    punctuation = parser.add_mutually_exclusive_group();
    punctuation.add_argument(
        "-p",
        "--preserve-punctuation",
        dest="preserve_punctuation",
        action="store_true",
        default=True,
        help="preserve punctuation in the IPA output (default; useful for pronounce.py)",
    );
    punctuation.add_argument(
        "--strip-punctuation",
        dest="preserve_punctuation",
        action="store_false",
        help="remove punctuation and emit phonetic symbols/spacing only",
    );
    parser.add_argument(
        "-s",
        "--stress",
        action="store_true",
        help="include primary/secondary stress marks when supported",
    );
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show detected language, normalized text and resolved eSpeak voice on stderr",
    );
    parser.add_argument(
        "--show-normalized",
        action="store_true",
        help="show the text after dialect normalization on stderr",
    );
    parser.add_argument(
        "--normalize-only",
        action="store_true",
        help="print normalized text and exit without phonemizer/eSpeak",
    );
    parser.add_argument(
        "--no-number-normalization",
        action="store_true",
        help="do not rewrite cardinal integer tokens before phonemization",
    );
    parser.add_argument(
        "--exceptions",
        metavar="FILE",
        help="load JSON overrides exported by --export-exceptions",
    );
    parser.add_argument(
        "--export-exceptions",
        metavar="FILE",
        help="export built-in study profiles and literal/regex replacements as JSON; use '-' for stdout",
    );
    parser.add_argument(
        "--number-table",
        action="store_true",
        help="print Markdown comparison tables for dialect-sensitive and large cardinal numbers",
    );
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="list configured aliases and the installed eSpeak voice selected for each",
    );
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}");
    return parser;


def normalize_language(language):
    """EN: Normalize a project language/profile name.
    ES: Normaliza un nombre de idioma/perfil del proyecto.
    FR: Normalise un nom de langue/profil du projet.""";
    return canonical_language(language, allow_auto=True);


def read_input(args, parser):
    """EN: Read positional text, -t, -i or stdin. ES: Lee texto, -t, -i o stdin. FR: Lit texte, -t, -i ou stdin."""
    if args.text_arg is not None and (args.text is not None or args.input is not None):
        parser.error("positional text cannot be combined with -t/--text or -i/--input");
    if args.text_arg is not None:
        return args.text_arg;
    if args.text is not None:
        return args.text;
    if args.input is not None:
        if args.input == "-":
            return sys.stdin.read();
        try:
            return Path(args.input).read_text(encoding="utf-8");
        except OSError as exc:
            parser.error(f"cannot read '{args.input}': {exc}");
    if not sys.stdin.isatty():
        return sys.stdin.read();
    parser.error("no input: use positional TEXT, -t TEXT, -i FILE, or pipe text through stdin");
    return "";


def detect_language(text):
    """EN: Detect EN/FR/ES conservatively. ES: Detecta EN/FR/ES con cautela. FR: Détecte EN/FR/ES prudemment."""
    if not text.strip():
        raise ValueError("cannot detect the language of empty input");
    tokens = [token.lower().replace("’", "'") for token in TOKEN_RE.findall(text)];
    if not tokens:
        raise ValueError("cannot detect a language: input contains no words; specify -l explicitly");

    scores = {"en": 0, "es": 0, "fr": 0};
    scores["fr"] += sum(5 for char in text if char in FRENCH_STRONG_DIACRITICS);
    scores["es"] += sum(5 for char in text if char in SPANISH_STRONG_MARKS);
    scores["fr"] += len(FRENCH_CONTRACTION_RE.findall(text)) * 4;
    scores["en"] += len(ENGLISH_CONTRACTION_RE.findall(text)) * 4;

    for token in tokens:
        if token in FRENCH_WORDS:
            scores["fr"] += 2;
        if token in ENGLISH_WORDS:
            scores["en"] += 2;
        if token in SPANISH_WORDS:
            scores["es"] += 2;

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True);
    best_language, best_score = ranked[0];
    second_score = ranked[1][1];
    if best_score == 0:
        raise ValueError("language is ambiguous; specify -l/--language explicitly");
    if best_score - second_score < 2:
        detail = ", ".join(f"{language}={score}" for language, score in sorted(scores.items()));
        raise ValueError(f"language is ambiguous ({detail}); specify -l explicitly");
    return best_language;


def select_logical_language(requested, text):
    """EN: Resolve auto to a study alias. ES: Resuelve auto a un alias. FR: Résout auto vers un alias d'étude."""
    requested = normalize_language(requested);
    if requested == "auto":
        detected = detect_language(text);
        return detected, AUTO_TARGETS[detected];
    return None, canonical_language(requested);


def deep_merge(base, override):
    """EN: Recursively merge dictionaries. ES: Fusiona diccionarios. FR: Fusionne récursivement des dictionnaires."""
    result = copy.deepcopy(base);
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value);
        else:
            result[key] = copy.deepcopy(value);
    return result;


def validate_config(config):
    """EN: Validate editable study data. ES: Valida datos editables. FR: Valide les données modifiables."""
    candidates = config.get("backend_candidates", {});
    if not isinstance(candidates, dict):
        raise ValueError("exceptions JSON: backend_candidates must be an object");
    for language, values in candidates.items():
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            raise ValueError(
                f"exceptions JSON: backend_candidates.{language} must be a non-empty array of strings"
            );

    profiles = config.get("number_profiles", {});
    if not isinstance(profiles, dict):
        raise ValueError("exceptions JSON: number_profiles must be an object");
    for language, profile in profiles.items():
        if not isinstance(profile, dict):
            raise ValueError(f"exceptions JSON: number_profiles.{language} must be an object");
        seventy = profile.get("seventy_style");
        eighty = profile.get("eighty_style");
        ninety = profile.get("ninety_style");
        if seventy not in SEVENTY_STYLES:
            raise ValueError(f"exceptions JSON: invalid seventy_style for {language}: {seventy}");
        if eighty not in EIGHTY_STYLES:
            raise ValueError(f"exceptions JSON: invalid eighty_style for {language}: {eighty}");
        if ninety not in NINETY_STYLES:
            raise ValueError(f"exceptions JSON: invalid ninety_style for {language}: {ninety}");

    scales = config.get("number_scales", {});
    if not isinstance(scales, dict):
        raise ValueError("exceptions JSON: number_scales must be an object");
    for language, profile in scales.items():
        if not isinstance(profile, dict):
            raise ValueError(f"exceptions JSON: number_scales.{language} must be an object");
        if profile.get("scale") not in {"short", "long"}:
            raise ValueError(f"exceptions JSON: invalid scale for {language}: {profile.get('scale')}");
        if "and_style" in profile and profile["and_style"] not in {"american", "british"}:
            raise ValueError(f"exceptions JSON: invalid and_style for {language}: {profile['and_style']}");

    for section_name in ("replacements", "ipa_replacements"):
        section = config.get(section_name, {});
        if not isinstance(section, dict):
            raise ValueError(f"exceptions JSON: {section_name} must be an object");
        for language, mapping in section.items():
            if not isinstance(mapping, dict):
                raise ValueError(f"exceptions JSON: {section_name}.{language} must be an object");
            if not all(isinstance(key, str) and isinstance(value, str) for key, value in mapping.items()):
                raise ValueError(f"exceptions JSON: {section_name}.{language} must contain string:string pairs");

    regex_section = config.get("ipa_regex_replacements", {});
    if not isinstance(regex_section, dict):
        raise ValueError("exceptions JSON: ipa_regex_replacements must be an object");
    for language, rules in regex_section.items():
        if not isinstance(rules, list):
            raise ValueError(f"exceptions JSON: ipa_regex_replacements.{language} must be an array");
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValueError(
                    f"exceptions JSON: ipa_regex_replacements.{language}[{index}] must be an object"
                );
            pattern = rule.get("pattern");
            replacement = rule.get("replacement");
            if not isinstance(pattern, str) or not isinstance(replacement, str):
                raise ValueError(
                    f"exceptions JSON: ipa_regex_replacements.{language}[{index}] requires string pattern/replacement"
                );
            try:
                re.compile(pattern);
            except re.error as exc:
                raise ValueError(
                    f"exceptions JSON: invalid regex for {language}[{index}]: {exc}"
                ) from exc;
    return config;


def load_config(path=None):
    """EN: Load optional JSON overrides. ES: Carga overrides JSON. FR: Charge les surcharges JSON."""
    config = copy.deepcopy(DEFAULT_EXCEPTIONS);
    if path is None:
        return validate_config(config);
    try:
        override = json.loads(Path(path).read_text(encoding="utf-8"));
    except OSError as exc:
        raise ValueError(f"cannot read exceptions file '{path}': {exc}") from exc;
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in exceptions file '{path}': {exc}") from exc;
    if not isinstance(override, dict):
        raise ValueError("exceptions JSON root must be an object");
    return validate_config(deep_merge(config, override));


def export_config(config, destination):
    """EN: Export study data as JSON. ES: Exporta datos a JSON. FR: Exporte les données d'étude en JSON."""
    payload = json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n";
    if destination == "-":
        sys.stdout.write(payload);
        return;
    try:
        Path(destination).write_text(payload, encoding="utf-8");
    except OSError as exc:
        raise ValueError(f"cannot write exceptions file '{destination}': {exc}") from exc;


def get_number_profile(logical_language, config):
    """EN: Get a French number profile. ES: Obtiene perfil numérico. FR: Obtient le profil numérique français."""
    profiles = config.get("number_profiles", {});
    if logical_language in profiles:
        return profiles[logical_language];
    if logical_language.startswith("fr-"):
        return profiles.get("fr");
    if logical_language == "fr":
        return profiles.get("fr");
    return None;



def language_family(logical_language):
    """EN: Return language family for study profiles and raw backend codes.
    ES: Devuelve la familia para perfiles de estudio y códigos de backend.
    FR: Renvoie la famille des profils d'étude et des codes backend.""";
    profile = LANGUAGE_PROFILES.get(canonical_language(logical_language), {});
    if profile.get("family"):
        return profile["family"];
    return project_language_family(logical_language);

def get_number_scale(logical_language, config):
    """EN: Get scale/style data. ES: Obtiene escala/estilo. FR: Obtient l'échelle/le style."""
    scales = config.get("number_scales", {});
    if logical_language in scales:
        return scales[logical_language];
    family = language_family(logical_language);
    return scales.get(family);


def decimal_tens(base_word, unit, use_et_un=True):
    """EN: Build regular x0..x9 tens. ES: Forma decenas regulares. FR: Forme les dizaines régulières."""
    if unit == 0:
        return base_word;
    if unit == 1 and use_et_un:
        return f"{base_word} et un";
    return f"{base_word}-{FRENCH_SMALL[unit]}";


def french_under_hundred(number, profile, suppress_final_plural=False):
    """EN: Spell 0..99 by profile. ES: Escribe 0..99 por perfil. FR: Écrit 0..99 selon le profil."""
    if number < 20:
        return FRENCH_SMALL[number];
    if number < 70:
        tens = (number // 10) * 10;
        unit = number % 10;
        return decimal_tens(FRENCH_DECIMAL_TENS[tens], unit, use_et_un=True);
    if number < 80:
        if profile["seventy_style"] == "septante":
            return decimal_tens("septante", number - 70, use_et_un=True);
        remainder = number - 60;
        if remainder == 11:
            return "soixante et onze";
        return f"soixante-{FRENCH_SMALL[remainder]}";
    if number < 90:
        if profile["eighty_style"] == "huitante":
            return decimal_tens("huitante", number - 80, use_et_un=True);
        if number == 80:
            if suppress_final_plural:
                return "quatre-vingt";
            return "quatre-vingts";
        return f"quatre-vingt-{FRENCH_SMALL[number - 80]}";
    if profile["ninety_style"] == "nonante":
        return decimal_tens("nonante", number - 90, use_et_un=True);
    return f"quatre-vingt-{FRENCH_SMALL[number - 80]}";


def french_under_thousand(number, profile, suppress_final_plural=False):
    """EN: Spell 0..999. ES: Escribe 0..999. FR: Écrit 0..999."""
    if number < 100:
        return french_under_hundred(number, profile, suppress_final_plural=suppress_final_plural);
    hundreds, remainder = divmod(number, 100);
    if hundreds == 1:
        prefix = "cent";
    else:
        prefix = f"{FRENCH_SMALL[hundreds]} cent";
        if remainder == 0 and not suppress_final_plural:
            prefix += "s";
    if remainder == 0:
        return prefix;
    return f"{prefix} {french_under_hundred(remainder, profile, suppress_final_plural=suppress_final_plural)}";


def french_integer_to_words(value, profile):
    """EN: Spell a signed integer with French long scale. ES: Escribe un entero. FR: Écrit un entier en échelle longue."""
    if value == 0:
        return FRENCH_SMALL[0];
    if value < 0:
        return f"moins {french_integer_to_words(-value, profile)}";

    groups = [];
    remaining = value;
    while remaining:
        groups.append(remaining % 1000);
        remaining //= 1000;

    if len(groups) > len(FRENCH_SCALE_WORDS):
        maximum_power = len(FRENCH_SCALE_WORDS) * 3;
        raise ValueError(f"integer is too large; supported values are below 10^{maximum_power}");

    parts = [];
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index];
        if group == 0:
            continue;
        if index == 0:
            parts.append(french_under_thousand(group, profile));
            continue;
        if index == 1:
            if group == 1:
                parts.append("mille");
            else:
                group_words = french_under_thousand(group, profile, suppress_final_plural=True);
                parts.append(f"{group_words} mille");
            continue;
        scale = FRENCH_SCALE_WORDS[index];
        if group == 1:
            parts.append(f"un {scale}");
        else:
            group_words = french_under_thousand(group, profile);
            parts.append(f"{group_words} {scale}s");
    return " ".join(parts);




def english_under_hundred(number):
    """EN: Spell 0..99. ES: Escribe 0..99 en inglés. FR: Écrit 0..99 en anglais."""
    if number < 20:
        return ENGLISH_SMALL[number];
    tens, unit = divmod(number, 10);
    base = ENGLISH_TENS[tens * 10];
    if unit == 0:
        return base;
    return f"{base}-{ENGLISH_SMALL[unit]}";


def english_under_thousand(number, and_style="american"):
    """EN: Spell 0..999. ES: Escribe 0..999 en inglés. FR: Écrit 0..999 en anglais."""
    if number < 100:
        return english_under_hundred(number);
    hundreds, remainder = divmod(number, 100);
    prefix = f"{ENGLISH_SMALL[hundreds]} hundred";
    if remainder == 0:
        return prefix;
    conjunction = " and " if and_style == "british" else " ";
    return f"{prefix}{conjunction}{english_under_hundred(remainder)}";


def english_integer_to_words(value, profile):
    """EN: Spell a signed integer using modern short scale. ES: Usa escala corta. FR: Utilise l'échelle courte."""
    if profile.get("scale") != "short":
        raise ValueError("English number spelling currently requires scale=short");
    if value == 0:
        return ENGLISH_SMALL[0];
    if value < 0:
        return f"minus {english_integer_to_words(-value, profile)}";
    groups = [];
    remaining = value;
    while remaining:
        groups.append(remaining % 1000);
        remaining //= 1000;
    if len(groups) > len(ENGLISH_SCALE_WORDS):
        maximum_power = len(ENGLISH_SCALE_WORDS) * 3;
        raise ValueError(f"integer is too large; supported English values are below 10^{maximum_power}");
    parts = [];
    and_style = profile.get("and_style", "american");
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index];
        if group == 0:
            continue;
        words = english_under_thousand(group, and_style=and_style);
        scale = ENGLISH_SCALE_WORDS[index];
        if scale:
            parts.append(f"{words} {scale}");
        else:
            parts.append(words);
    if and_style == "british" and len(parts) > 1 and 0 < groups[0] < 100:
        return " ".join(parts[:-1]) + " and " + parts[-1];
    return " ".join(parts);


def spanish_under_hundred(number):
    """EN: Spell 0..99 in Spanish. ES: Escribe 0..99. FR: Écrit 0..99 en espagnol."""
    if number < 30:
        return SPANISH_SMALL[number];
    tens, unit = divmod(number, 10);
    base = SPANISH_TENS[tens * 10];
    if unit == 0:
        return base;
    return f"{base} y {SPANISH_SMALL[unit]}";


def spanish_under_thousand(number):
    """EN: Spell 0..999 in Spanish. ES: Escribe 0..999. FR: Écrit 0..999 en espagnol."""
    if number < 100:
        return spanish_under_hundred(number);
    if number == 100:
        return "cien";
    hundreds, remainder = divmod(number, 100);
    if hundreds == 1:
        prefix = "ciento";
    else:
        prefix = SPANISH_HUNDREDS[hundreds];
    if remainder == 0:
        return prefix;
    return f"{prefix} {spanish_under_hundred(remainder)}";


def spanish_apocopate_one(words):
    """EN: Apocopate uno before mil/-illón nouns. ES: Apocopa uno. FR: Apocope uno."""
    if words == "uno":
        return "un";
    if words.endswith("veintiuno"):
        return words[:-9] + "veintiún";
    if words.endswith(" y uno"):
        return words[:-6] + " y un";
    if words.endswith(" uno"):
        return words[:-4] + " un";
    return words;


def spanish_scale_plural(name):
    """EN: millón -> millones. ES: Forma el plural. FR: Forme le pluriel."""
    if name.endswith("llón"):
        return name[:-2] + "ones";
    raise ValueError(f"cannot pluralize Spanish scale name: {name}");


def spanish_integer_to_words(value, profile):
    """EN: Spell a signed integer using Spanish long scale. ES: Usa escala larga. FR: Utilise l'échelle longue espagnole."""
    if profile.get("scale") != "long":
        raise ValueError("Spanish number spelling currently requires scale=long");
    if value == 0:
        return SPANISH_SMALL[0];
    if value < 0:
        return f"menos {spanish_integer_to_words(-value, profile)}";
    groups = [];
    remaining = value;
    while remaining:
        groups.append(remaining % 1000);
        remaining //= 1000;
    maximum_group_index = (len(SPANISH_LONG_SCALE_NAMES) - 1) * 2 + 1;
    if len(groups) - 1 > maximum_group_index:
        maximum_power = (maximum_group_index + 1) * 3;
        raise ValueError(f"integer is too large; supported Spanish values are below 10^{maximum_power}");
    parts = [];
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index];
        if group == 0:
            continue;
        if index == 0:
            parts.append(spanish_under_thousand(group));
            continue;
        group_words = spanish_apocopate_one(spanish_under_thousand(group));
        if index == 1:
            if group == 1:
                parts.append("mil");
            else:
                parts.append(f"{group_words} mil");
            continue;
        scale_number = index // 2;
        scale = SPANISH_LONG_SCALE_NAMES[scale_number];
        plural = spanish_scale_plural(scale);
        if index % 2 == 0:
            if group == 1:
                parts.append(f"un {scale}");
            else:
                parts.append(f"{group_words} {plural}");
        else:
            if group == 1:
                parts.append(f"mil {plural}");
            else:
                parts.append(f"{group_words} mil {plural}");
    return " ".join(parts);


def integer_to_words(value, logical_language, config):
    """EN: Dispatch cardinal spelling by language family. ES: Despacha por idioma. FR: Distribue selon la langue."""
    family = language_family(logical_language);
    scale = get_number_scale(logical_language, config);
    if family == "fr":
        profile = get_number_profile(logical_language, config);
        if profile is None:
            raise ValueError(f"no French number profile configured for {logical_language}");
        if scale is not None and scale.get("scale") != "long":
            raise ValueError("French number spelling currently requires scale=long");
        return french_integer_to_words(value, profile);
    if family == "es":
        if scale is None:
            raise ValueError(f"no Spanish number scale configured for {logical_language}");
        return spanish_integer_to_words(value, scale);
    if family == "en":
        if scale is None:
            raise ValueError(f"no English number scale configured for {logical_language}");
        return english_integer_to_words(value, scale);
    raise ValueError(f"no integer normalizer for language: {logical_language}");


def protected_numeric_spans(text):
    """EN: Find non-cardinal numeric spans. ES: Detecta números no cardinales. FR: Repère les nombres non cardinaux."""
    spans = [];
    for pattern in PROTECTED_NUMERIC_RES:
        spans.extend((match.start(), match.end()) for match in pattern.finditer(text));
    return spans;


def overlaps_spans(start, end, spans):
    """EN: Test span overlap. ES: Comprueba solapamiento. FR: Vérifie le chevauchement."""
    return any(start < span_end and end > span_start for span_start, span_end in spans);


def normalize_integers(text, logical_language, config):
    """EN: Expand standalone cardinal integers. ES: Expande enteros cardinales. FR: Développe les entiers cardinaux."""
    family = language_family(logical_language);
    if family not in {"en", "es", "fr"}:
        return text;
    protected = protected_numeric_spans(text);
    positive_word = {"en": "plus", "es": "más", "fr": "plus"}[family];

    def replace(match):
        if overlaps_spans(match.start(), match.end(), protected):
            return match.group(0);
        raw_token = match.group(0);
        token = re.sub(r"[\u00A0\u202F_\'’]", "", raw_token);
        words = integer_to_words(int(token), logical_language, config);
        if raw_token.startswith("+"):
            return f"{positive_word} {words}";
        return words;

    return INTEGER_TOKEN_RE.sub(replace, text);


def apply_replacements(text, logical_language, config):
    """EN: Apply editable literal corrections. ES: Aplica correcciones. FR: Applique les corrections littérales."""
    mapping = config.get("replacements", {}).get(logical_language, {});
    result = text;
    for source in sorted(mapping, key=len, reverse=True):
        replacement = mapping[source];
        escaped = re.escape(source);
        left = r"(?<!\w)" if source and (source[0].isalnum() or source[0] == "_") else "";
        right = r"(?!\w)" if source and (source[-1].isalnum() or source[-1] == "_") else "";
        result = re.sub(left + escaped + right, replacement, result, flags=re.IGNORECASE);
    return result;


def normalize_study_text(text, logical_language, config, normalize_numbers=True):
    """EN: Apply dialect preprocessing. ES: Preprocesa el dialecto. FR: Prétraite la variété dialectale."""
    result = text;
    if normalize_numbers and language_family(logical_language) in {"en", "es", "fr"}:
        result = normalize_integers(result, logical_language, config);
    result = apply_replacements(result, logical_language, config);
    return result;


def load_espeak_backend():
    """EN: Load phonemizer's eSpeak backend lazily. ES: Carga eSpeak. FR: Charge le backend eSpeak à la demande."""
    try:
        from phonemizer.backend import EspeakBackend;
    except ImportError as exc:
        raise RuntimeError(
            "phonemizer is not installed; install the Python package and eSpeak NG first"
        ) from exc;
    if not EspeakBackend.is_available():
        raise RuntimeError("phonemizer is installed, but the eSpeak backend is not available");
    return EspeakBackend;


def get_supported_languages():
    """EN: Return installed eSpeak languages. ES: Devuelve idiomas eSpeak. FR: Renvoie les langues eSpeak installées."""
    backend = load_espeak_backend();
    return backend.supported_languages();


def resolve_language(requested, supported, config):
    """EN: Map a study alias to an installed backend. ES: Resuelve alias. FR: Résout un alias d'étude."""
    requested = normalize_language(requested);
    supported_keys = {key.lower(): key for key in supported};

    if requested in LANGUAGE_PROFILES:
        profile = LANGUAGE_PROFILES[requested];
        candidates = config.get("backend_candidates", {}).get(requested, []);
        for candidate in candidates:
            key = supported_keys.get(candidate.lower());
            if key is not None:
                return requested, key, profile["label"];
        tried = ", ".join(candidates) if candidates else "(none configured)";
        raise ValueError(f"no installed eSpeak voice matches {requested}; tried: {tried}");

    key = supported_keys.get(requested);
    if key is not None:
        return requested, key, supported[key];
    raise ValueError(f"unknown or unsupported language/accent: {requested}");


def phonemize_text(text, backend_language, preserve_punctuation=True, with_stress=False):
    """EN: Make one phonemizer call. ES: Hace una llamada a phonemizer. FR: Effectue un appel à phonemizer."""
    try:
        from phonemizer import phonemize;
    except ImportError as exc:
        raise RuntimeError(
            "phonemizer is not installed; install the Python package and eSpeak NG first"
        ) from exc;
    return phonemize(
        text,
        language=backend_language,
        backend="espeak",
        strip=True,
        preserve_punctuation=preserve_punctuation,
        with_stress=with_stress,
    );


def apply_ipa_replacements(ipa, logical_language, config):
    """EN: Apply editable literal/regex IPA overlays. ES: Aplica ajustes IPA editables. FR: Applique les ajustements IPA modifiables."""
    mapping = config.get("ipa_replacements", {}).get(logical_language, {});
    result = ipa;
    for source in sorted(mapping, key=len, reverse=True):
        result = result.replace(source, mapping[source]);

    regex_rules = config.get("ipa_regex_replacements", {}).get(logical_language, []);
    for rule in regex_rules:
        result = re.sub(rule["pattern"], rule["replacement"], result);
    return result;


def print_languages(supported, config):
    """EN: Print alias resolution. ES: Muestra resolución. FR: Affiche la résolution des alias."""
    print("Profile          Short  eSpeak backend     Mode           Description");
    print("---------------  -----  -----------------  -------------  ------------------------------------------------------------");
    for alias, profile in LANGUAGE_PROFILES.items():
        try:
            _, backend_language, _ = resolve_language(alias, supported, config);
            has_ipa_overlay = bool(config.get("ipa_replacements", {}).get(alias, {})) or bool(
                config.get("ipa_regex_replacements", {}).get(alias, [])
            );
            if profile.get("approximation", False) and backend_language != alias:
                mode = "approximation";
            elif has_ipa_overlay:
                mode = "study overlay";
            elif backend_language == alias or (alias == "fr-fr" and backend_language in {"fr", "fr-fr"}) or (alias == "es-es" and backend_language in {"es", "es-es"}):
                mode = "direct";
            elif alias == "fr-ch-qv" and backend_language == "fr-ch":
                mode = "study overlay";
            else:
                mode = "fallback";
        except ValueError:
            backend_language = "(unavailable)";
            mode = "-";
        short = short_alias_for(alias) or "-";
        print(f"{alias:<15}  {short:<5}  {backend_language:<17}  {mode:<13}  {profile['label']}");


def print_number_table(config):
    """EN: Print comparison tables as Markdown. ES: Imprime tablas Markdown. FR: Affiche des tableaux Markdown."""
    print("| Profile | 70 | 80 | 90 | 10^9 | 10^12 | 10^18 |");
    print("|---|---|---|---|---|---|---|");
    values = (70, 80, 90, 10 ** 9, 10 ** 12, 10 ** 18);
    for language in NUMBER_TABLE_LANGUAGES:
        forms = [integer_to_words(value, language, config) for value in values];
        print("| " + " | ".join([language] + forms) + " |");
    print();
    print("| Power | Spanish long scale | French long scale | Modern English short scale |");
    print("|---|---|---|---|");
    for value in (10 ** 6, 10 ** 9, 10 ** 12, 10 ** 15, 10 ** 18):
        print(
            "| " + " | ".join((
                f"10^{len(str(value)) - 1}",
                integer_to_words(value, "es-es", config),
                integer_to_words(value, "fr-fr", config),
                integer_to_words(value, "en-us", config),
            )) + " |"
        );


def main():
    """EN: Program entry point. ES: Punto de entrada. FR: Point d'entrée du programme."""
    parser = build_parser();
    args = parser.parse_args();

    try:
        config = load_config(args.exceptions);
        if args.export_exceptions is not None:
            export_config(config, args.export_exceptions);
            return 0;

        if args.number_table:
            print_number_table(config);
            return 0;

        if args.list_languages:
            supported = get_supported_languages();
            print_languages(supported, config);
            return 0;

        text = read_input(args, parser);
        detected, logical = select_logical_language(args.language, text);
        normalized = normalize_study_text(
            text,
            logical,
            config,
            normalize_numbers=not args.no_number_normalization,
        );

        if args.normalize_only:
            print(normalized);
            return 0;

        supported = get_supported_languages();
        alias, backend_language, label = resolve_language(logical, supported, config);
        approximation = (
            LANGUAGE_PROFILES.get(alias, {}).get("approximation", False)
            and backend_language != alias
        );
        result = phonemize_text(
            normalized,
            backend_language,
            preserve_punctuation=args.preserve_punctuation,
            with_stress=args.stress,
        );
        result = apply_ipa_replacements(result, alias, config);

        if args.verbose:
            if detected is not None:
                print(
                    f"{PROGRAM}: detected={detected}; alias={alias}; "
                    f"espeak={backend_language}; approximation={str(approximation).lower()}; profile={label}",
                    file=sys.stderr,
                );
            else:
                print(
                    f"{PROGRAM}: alias={alias}; espeak={backend_language}; "
                    f"approximation={str(approximation).lower()}; profile={label}",
                    file=sys.stderr,
                );
        if args.verbose or args.show_normalized:
            print(f"{PROGRAM}: normalized={normalized}", file=sys.stderr);
        print(result.strip());
        return 0;
    except (RuntimeError, ValueError) as exc:
        print(f"{PROGRAM}: error: {exc}", file=sys.stderr);
        return 2;


if __name__ == "__main__":
    sys.exit(main());

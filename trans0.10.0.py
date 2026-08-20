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

"""trans.py - Asynchronous text translation for Unix pipelines.

EN: The preferred interface uses -s/--source-language for the source and
    -l/--language for the destination. The source defaults to auto detection;
    when the destination is omitted it is inferred from LC_ALL, LC_MESSAGES or
    LANG. The historical ``trans SRC DEST`` form remains accepted. ANSI terminal
    escape sequences are removed by default before translation.
ES: La interfaz preferida usa -s/--source-language para el origen y -l/--language
    para el destino. El origen usa autodetección por defecto; si se omite el
    destino se obtiene de LC_ALL, LC_MESSAGES o LANG. La forma histórica
    ``trans SRC DEST`` sigue aceptándose. Las secuencias ANSI se eliminan por
    defecto antes de traducir.
FR: L'interface recommandée utilise -s/--source-language pour la source et
    -l/--language pour la destination. La source est détectée automatiquement par
    défaut; si la destination est absente elle est déduite de LC_ALL,
    LC_MESSAGES ou LANG. L'ancienne forme ``trans SRC DEST`` reste acceptée. Les
    séquences ANSI sont supprimées par défaut avant traduction.
"""

import argparse;
import asyncio;
import re;
import sys;
from pathlib import Path;

from language_profiles import (
    SHORT_LANGUAGE_ALIASES,
    backend_family_language,
    canonical_language,
    environment_language,
    language_family,
);

PROGRAM = "trans.py";
VERSION = "0.10.0";
DEFAULT_CHUNK_SIZE = 5000;
MAX_GOOGLETRANS_CHUNK = 15000;

# EN: Remove CSI, OSC and simple ESC terminal sequences before web translation.
# ES: Elimina secuencias CSI, OSC y ESC simples antes de traducir por la web.
# FR: Supprime CSI, OSC et les séquences ESC simples avant la traduction web.
ANSI_ESCAPE_RE = re.compile(
    r"(?:"
    r"(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~]"
    r"|\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)"
    r"|\x1B[@-_]"
    r")"
);
LANGUAGE_TOKEN_RE = re.compile(r"^(?:auto|[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*)$");


def strip_ansi_sequences(text):
    """EN: Remove ANSI/ECMA-48 terminal escapes.
    ES: Elimina escapes ANSI/ECMA-48 del terminal.
    FR: Supprime les échappements ANSI/ECMA-48 du terminal.""";
    return ANSI_ESCAPE_RE.subn("", text);


def prepare_input_text(text, keep_ansi=False):
    """EN: Sanitize terminal input and return text plus removed-sequence count.
    ES: Limpia la entrada y devuelve texto más cantidad de secuencias eliminadas.
    FR: Nettoie l'entrée et renvoie le texte plus le nombre de séquences retirées.""";
    if keep_ansi:
        clean = text;
        removed = 0;
    else:
        clean, removed = strip_ansi_sequences(text);
    clean = clean.strip();
    if not clean:
        raise RuntimeError("input text is empty after ANSI filtering");
    return clean, removed;


def import_googletrans():
    """EN: Import googletrans lazily. ES: Importa googletrans tarde. FR: Importe googletrans tardivement.""";
    try:
        from googletrans import LANGUAGES, Translator;
    except ImportError as exc:
        raise RuntimeError(
            "Python package 'googletrans' is not installed; run: "
            "python3 -m pip install -r requirements.txt"
        ) from exc;
    return LANGUAGES, Translator;


def split_text(text, max_len=DEFAULT_CHUNK_SIZE):
    """EN: Split long text at useful boundaries.
    ES: Divide texto largo en límites razonables.
    FR: Découpe un texte long à des limites utiles.""";
    if max_len <= 0:
        raise ValueError("chunk size must be greater than zero");
    if max_len > MAX_GOOGLETRANS_CHUNK:
        raise ValueError(f"chunk size cannot exceed {MAX_GOOGLETRANS_CHUNK} characters");
    remaining = text.strip();
    parts = [];
    while len(remaining) > max_len:
        window = remaining[:max_len + 1];
        candidates = [];
        for marker in ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "):
            position = window.rfind(marker);
            if position >= 0:
                candidates.append(position + len(marker));
        cut = max(candidates, default=max_len);
        if cut < max_len // 2:
            cut = max_len;
        part = remaining[:cut].strip();
        if part:
            parts.append(part);
        remaining = remaining[cut:].lstrip();
    if remaining:
        parts.append(remaining);
    return parts;


def looks_like_language(value):
    """EN: Recognize legacy positional language tokens conservatively.
    ES: Reconoce de forma conservadora códigos de idioma posicionales antiguos.
    FR: Reconnaît prudemment les anciens codes de langue positionnels.""";
    return bool(LANGUAGE_TOKEN_RE.fullmatch(str(value or "")));


def read_file_or_stdin(input_name):
    """EN: Read UTF-8 input file or '-'. ES: Lee archivo UTF-8 o '-'. FR: Lit un fichier UTF-8 ou '-'.""";
    if input_name == "-":
        return sys.stdin.read();
    try:
        return Path(input_name).read_text(encoding="utf-8");
    except OSError as exc:
        raise RuntimeError(f"cannot read input file '{input_name}': {exc}") from exc;


def resolve_cli(args):
    """EN: Resolve new options, legacy SRC DEST syntax and environment destination.
    ES: Resuelve opciones nuevas, sintaxis antigua SRC DEST y destino de entorno.
    FR: Résout les nouvelles options, l'ancienne syntaxe SRC DEST et la destination d'environnement.""";
    words = list(args.arguments or []);
    source = args.source_language;
    destination = args.language;
    legacy = False;

    if source is None and destination is None and len(words) >= 2 and looks_like_language(words[0]) and looks_like_language(words[1]):
        source = words.pop(0);
        destination = words.pop(0);
        legacy = True;

    source = canonical_language(source or "auto", allow_auto=True);
    if not source:
        source = "auto";

    environment_source = "";
    environment_raw = "";
    if destination is None:
        destination, environment_source, environment_raw = environment_language();
        if not destination:
            raise RuntimeError(
                "destination language is not set and no usable LC_ALL/LC_MESSAGES/LANG locale was found; "
                "use -l/--language LANG"
            );
    else:
        destination = canonical_language(destination);
    if not destination or destination == "auto":
        raise RuntimeError("destination language must be explicit or inferable from the environment; 'auto' is not valid for a destination");

    source_count = int(bool(words)) + int(args.text is not None) + int(args.input is not None);
    if source_count > 1:
        raise RuntimeError("use only one text source: positional text, --text, or --input");
    if words:
        text = " ".join(words);
    elif args.text is not None:
        text = args.text;
    elif args.input is not None:
        text = read_file_or_stdin(args.input);
    elif not sys.stdin.isatty():
        text = sys.stdin.read();
    else:
        raise RuntimeError("no text input; provide text, --text, --input FILE, or pipe stdin");
    if not text.strip():
        raise RuntimeError("input text is empty");
    return source, destination, text, legacy, environment_source, environment_raw;


def resolve_googletrans_language(language, languages, allow_auto=False):
    """EN: Map project profiles/locales to a code accepted by googletrans.
    ES: Mapea perfiles/locales a un código aceptado por googletrans.
    FR: Mappe les profils/locales vers un code accepté par googletrans.""";
    logical = canonical_language(language, allow_auto=allow_auto);
    if allow_auto and logical == "auto":
        return "auto";
    normalized = logical.lower();
    family = language_family(logical);
    candidates = [];
    for candidate in (normalized, family):
        if candidate and candidate not in candidates:
            candidates.append(candidate);
    for candidate in candidates:
        if candidate in languages:
            return candidate;
    raise RuntimeError(
        f"language '{language}' resolves to project profile '{logical}', but installed googletrans does not expose "
        f"any of: {', '.join(candidates)}"
    );


async def translate_text(text, src, dest, chunk_size=DEFAULT_CHUNK_SIZE, verbose=False):
    """EN: Translate through one reusable asynchronous Translator session.
    ES: Traduce mediante una sesión Translator asíncrona reutilizable.
    FR: Traduit avec une session Translator asynchrone réutilisable.""";
    _languages, Translator = import_googletrans();
    parts = split_text(text, max_len=chunk_size);
    translated = [];
    try:
        async with Translator() as translator:
            for index, part in enumerate(parts, start=1):
                if verbose:
                    print(f"{PROGRAM}: chunk={index}/{len(parts)} chars={len(part)}", file=sys.stderr);
                result = await translator.translate(part, src=src, dest=dest);
                translated.append(result.text);
    except Exception as exc:
        raise RuntimeError(f"translation failed ({src}->{dest}): {exc}") from exc;
    return " ".join(part.strip() for part in translated if part.strip()).strip();


def print_languages():
    """EN: Print project aliases and googletrans language codes.
    ES: Muestra alias del proyecto y códigos googletrans.
    FR: Affiche les alias du projet et les codes googletrans.""";
    languages, _translator = import_googletrans();
    print("PROJECT SHORT ALIASES");
    for alias, target in SHORT_LANGUAGE_ALIASES.items():
        print(f"  {alias:8} -> {target}");
    print();
    print(f"{'CODE':10} LANGUAGE");
    for code, name in sorted(languages.items(), key=lambda item: (str(item[1]).lower(), str(item[0]).lower())):
        print(f"{str(code):10} {name}");
    print(f"{'auto':10} automatic source-language detection");


def build_parser():
    """EN: Build CLI parser. ES: Construye argparse. FR: Construit argparse.""";
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Translate UTF-8 text with googletrans; destination defaults to the environment locale.",
        epilog=(
            "Preferred:\n"
            "  trans.py -s en -l es \"Hello world\"\n"
            "  echo \"Hello world\" | trans.py -s auto -l fr\n"
            "  trans.py \"Hello world\"              # destination from LANG/LC_*\n"
            "Legacy compatibility:\n"
            "  trans.py en es \"Hello world\""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    );
    parser.add_argument("arguments", nargs="*", help="text; or legacy SRC DEST [TEXT]");
    parser.add_argument("-s", "--source-language", metavar="LANG", help="source language/profile (default: auto)");
    parser.add_argument("-l", "--language", "-d", "--destination-language", dest="language", metavar="LANG", help="destination language/profile; default: LC_ALL/LC_MESSAGES/LANG");
    source = parser.add_mutually_exclusive_group();
    source.add_argument("-t", "--text", help="text to translate");
    source.add_argument("-i", "--input", metavar="FILE", help="read UTF-8 text from FILE; use - for stdin");
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"maximum characters per request (default: %(default)s; maximum: {MAX_GOOGLETRANS_CHUNK})");
    parser.add_argument("--list-languages", action="store_true", help="list project aliases and language codes known by installed googletrans");
    parser.add_argument("--keep-ansi", action="store_true", help="preserve ANSI terminal escape sequences instead of stripping them");
    parser.add_argument("-v", "--verbose", action="store_true", help="write resolved languages/chunk diagnostics to stderr");
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}");
    return parser;


def main():
    """EN: Program entry point. ES: Punto de entrada. FR: Point d'entrée.""";
    parser = build_parser();
    args = parser.parse_args();
    try:
        if args.list_languages:
            print_languages();
            return 0;
        source, destination, raw_text, legacy, environment_source, environment_raw = resolve_cli(args);
        text, ansi_removed = prepare_input_text(raw_text, keep_ansi=args.keep_ansi);
        source_hint = backend_family_language(source, allow_auto=True);
        destination_hint = backend_family_language(destination);
        if source_hint != "auto" and source_hint == destination_hint:
            if args.verbose:
                print(f"{PROGRAM}: source={source}; language={destination}; translation=bypassed; ansi_removed={ansi_removed}", file=sys.stderr);
            print(text);
            return 0;
        languages, _translator = import_googletrans();
        source_backend = resolve_googletrans_language(source, languages, allow_auto=True);
        destination_backend = resolve_googletrans_language(destination, languages, allow_auto=False);
        if args.verbose:
            print(f"{PROGRAM}: source={source}; source_backend={source_backend}", file=sys.stderr);
            print(f"{PROGRAM}: language={destination}; language_backend={destination_backend}", file=sys.stderr);
            if environment_source:
                print(f"{PROGRAM}: language_source={environment_source}; locale={environment_raw}", file=sys.stderr);
            print(f"{PROGRAM}: legacy_cli={str(legacy).lower()}; chars={len(text)}; chunk_size={args.chunk_size}; ansi_removed={ansi_removed}", file=sys.stderr);
        if source_backend != "auto" and source_backend == destination_backend:
            print(text);
            return 0;
        result = asyncio.run(translate_text(text, source_backend, destination_backend, chunk_size=args.chunk_size, verbose=args.verbose));
        print(result);
        return 0;
    except (RuntimeError, ValueError) as exc:
        print(f"{PROGRAM}: error: {exc}", file=sys.stderr);
        return 2;


if __name__ == "__main__":
    sys.exit(main());

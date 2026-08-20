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

"""trans.py - Small asynchronous text translator for Unix pipelines.

EN: trans.py translates UTF-8 text with googletrans. It accepts text as a
    positional argument, with -t/--text, from -i/--input, or from stdin.
    ANSI terminal escape sequences are stripped from input by default. Normal
    translated text is written only to stdout so it can be piped into phonem.py
    or another command. googletrans uses Google's unofficial web API,
    so network/service failures are reported cleanly on stderr.
ES: trans.py traduce texto UTF-8 con googletrans. Puede recibir texto como
    argumento posicional, con -t/--text, desde -i/--input o desde stdin. La
    entrada elimina por defecto las secuencias de escape ANSI del terminal. La
    traducción normal se escribe solamente en stdout para poder encadenarla con
    phonem.py u otro comando. googletrans usa la API web no oficial de Google,
    por lo que los fallos de red/servicio se informan claramente por stderr.
FR: trans.py traduit du texte UTF-8 avec googletrans. Le texte peut être fourni
    comme argument positionnel, avec -t/--text, depuis -i/--input ou via stdin.
    Les séquences d'échappement ANSI du terminal sont supprimées par défaut. La
    traduction normale est écrite uniquement sur stdout afin de pouvoir être
    transmise à phonem.py ou à une autre commande. googletrans utilise l'API web
    non officielle de Google; les erreurs réseau/service sont donc signalées sur
    stderr.

EN/ES/FR: License / Licencia / Licence: GNU GPL version 2 or, at your option,
          any later version (GPL-2.0-or-later).
"""

import argparse;
import asyncio;
import re;
import sys;
from pathlib import Path;

PROGRAM = "trans.py";
VERSION = "0.9.5";
DEFAULT_CHUNK_SIZE = 5000;
MAX_GOOGLETRANS_CHUNK = 15000;

# EN: ANSI_ESCAPE_RE removes terminal control sequences before they reach the
#     translation service. This matters for Unix pipes such as
#     `ls --color=always | trans.py en es`.
# ES: ANSI_ESCAPE_RE elimina secuencias de control del terminal antes de enviarlas
#     al servicio de traducción. Es importante en pipes como
#     `ls --color=always | trans.py en es`.
# FR: ANSI_ESCAPE_RE supprime les séquences de contrôle du terminal avant leur
#     envoi au service de traduction, notamment dans les pipelines Unix.
ANSI_ESCAPE_RE = re.compile(
    r"(?:"
    r"(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~]"        # CSI: colours, cursor, erase, etc.
    r"|\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)"  # OSC: title/hyperlink-like sequences.
    r"|\x1B[@-_]"                              # Two-byte ESC sequences.
    r")"
);


def strip_ansi_sequences(text):
    """EN: Remove ANSI/ECMA-48 terminal escape sequences from text.
    ES: Elimina secuencias de escape ANSI/ECMA-48 del texto.
    FR: Supprime les séquences d'échappement ANSI/ECMA-48 du texte.""";
    return ANSI_ESCAPE_RE.subn("", text);


def prepare_input_text(text, keep_ansi=False):
    """EN: Sanitize terminal input and return (clean_text, removed_sequence_count).
    ES: Limpia la entrada de terminal y devuelve (texto_limpio, secuencias_eliminadas).
    FR: Nettoie l'entrée du terminal et renvoie (texte_propre, séquences_supprimées).""";
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
    """EN: Import googletrans lazily so --help/--version still work if absent.
    ES: Importa googletrans tarde para que --help/--version funcionen si falta.
    FR: Importe googletrans tardivement pour garder --help/--version utilisables.""";
    try:
        from googletrans import LANGUAGES, Translator;
    except ImportError as exc:
        raise RuntimeError(
            "Python package 'googletrans' is not installed; run: "
            "python3 -m pip install -r requirements.txt"
        ) from exc;
    return LANGUAGES, Translator;


def split_text(text, max_len=DEFAULT_CHUNK_SIZE):
    """EN: Split long text at useful boundaries without exceeding max_len.
    ES: Divide textos largos en límites razonables sin superar max_len.
    FR: Découpe les longs textes à des limites utiles sans dépasser max_len.""";
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
                candidates.append((position + len(marker), marker));
        cut = max((position for position, _marker in candidates), default=max_len);
        # EN: Very early boundaries waste requests; in that case use a hard cut.
        # ES: Un corte demasiado temprano desperdicia solicitudes; usa corte duro.
        # FR: Une limite trop précoce gaspille des requêtes; on coupe alors à max_len.
        if cut < max_len // 2:
            cut = max_len;
        part = remaining[:cut].strip();
        if part:
            parts.append(part);
        remaining = remaining[cut:].lstrip();
    if remaining:
        parts.append(remaining);
    return parts;


def read_input(args):
    """EN: Read text from exactly one CLI/file/stdin source.
    ES: Lee texto desde una única fuente CLI/archivo/stdin.
    FR: Lit le texte depuis une seule source CLI/fichier/stdin.""";
    sources = int(args.positional_text is not None) + int(args.text is not None) + int(args.input is not None);
    if sources > 1:
        raise RuntimeError("use only one text source: positional text, --text, or --input");

    if args.positional_text is not None:
        value = args.positional_text;
    elif args.text is not None:
        value = args.text;
    elif args.input is not None:
        if args.input == "-":
            value = sys.stdin.read();
        else:
            try:
                value = Path(args.input).read_text(encoding="utf-8");
            except OSError as exc:
                raise RuntimeError(f"cannot read input file '{args.input}': {exc}") from exc;
    elif not sys.stdin.isatty():
        value = sys.stdin.read();
    else:
        raise RuntimeError("no text input; provide text, --text, --input FILE, or pipe stdin");

    value = value.strip();
    if not value:
        raise RuntimeError("input text is empty");
    return value;


async def translate_text(text, src="en", dest="es", chunk_size=DEFAULT_CHUNK_SIZE, verbose=False):
    """EN: Translate text sequentially through one reusable async Translator session.
    ES: Traduce el texto en una única sesión asíncrona reutilizable.
    FR: Traduit le texte dans une seule session asynchrone réutilisable.""";
    _languages, Translator = import_googletrans();
    parts = split_text(text, max_len=chunk_size);
    translated_parts = [];

    try:
        async with Translator() as translator:
            for index, part in enumerate(parts, start=1):
                if verbose:
                    print(f"{PROGRAM}: chunk={index}/{len(parts)} chars={len(part)}", file=sys.stderr);
                result = await translator.translate(part, src=src, dest=dest);
                translated_parts.append(result.text);
    except Exception as exc:
        raise RuntimeError(f"translation failed ({src}->{dest}): {exc}") from exc;

    return " ".join(part.strip() for part in translated_parts if part.strip()).strip();


def print_languages():
    """EN: Print language codes exposed by the installed googletrans version.
    ES: Muestra los códigos de idioma de la versión instalada de googletrans.
    FR: Affiche les codes de langue fournis par la version installée de googletrans.""";
    languages, _translator = import_googletrans();
    print(f"{'CODE':10} LANGUAGE");
    for code, name in sorted(languages.items(), key=lambda item: (str(item[1]).lower(), str(item[0]).lower())):
        print(f"{str(code):10} {name}");
    print(f"{'auto':10} automatic source-language detection");


def build_parser():
    """EN: Build the command-line parser. ES: Construye argparse. FR: Construit argparse.""";
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Translate UTF-8 text with googletrans; stdin/stdout are pipe-friendly.",
    );
    parser.add_argument("src", nargs="?", help="source language code, for example en, es, fr, or auto");
    parser.add_argument("dest", nargs="?", help="destination language code, for example es, en, fr");
    parser.add_argument("positional_text", nargs="?", help="text to translate; stdin is used when omitted");
    parser.add_argument("-t", "--text", help="text to translate");
    parser.add_argument("-i", "--input", metavar="FILE", help="read UTF-8 text from FILE; use - for stdin");
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"maximum characters per request (default: %(default)s; maximum: {MAX_GOOGLETRANS_CHUNK})",
    );
    parser.add_argument("--list-languages", action="store_true", help="list language codes known by installed googletrans");
    parser.add_argument("--keep-ansi", action="store_true", help="preserve ANSI terminal escape sequences instead of stripping them");
    parser.add_argument("-v", "--verbose", action="store_true", help="write source/destination/chunk diagnostics to stderr");
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
        if not args.src or not args.dest:
            raise RuntimeError("source and destination language codes are required (for example: trans.py en es)");
        raw_text = read_input(args);
        text, ansi_removed = prepare_input_text(raw_text, keep_ansi=args.keep_ansi);
        if args.src == args.dest:
            # EN: Keep pipelines deterministic and avoid an unnecessary network request.
            # ES: Mantiene pipelines deterministas y evita una solicitud de red innecesaria.
            # FR: Garde les pipelines déterministes et évite une requête réseau inutile.
            if args.verbose:
                print(
                    f"{PROGRAM}: src={args.src}; dest={args.dest}; translation=bypassed; "
                    f"ansi_removed={ansi_removed}",
                    file=sys.stderr,
                );
            print(text);
            return 0;

        if args.verbose:
            print(
                f"{PROGRAM}: src={args.src}; dest={args.dest}; chars={len(text)}; "
                f"chunk_size={args.chunk_size}; ansi_removed={ansi_removed}",
                file=sys.stderr,
            );
        result = asyncio.run(translate_text(
            text,
            src=args.src,
            dest=args.dest,
            chunk_size=args.chunk_size,
            verbose=args.verbose,
        ));
        print(result);
        return 0;
    except (RuntimeError, ValueError) as exc:
        print(f"{PROGRAM}: error: {exc}", file=sys.stderr);
        return 2;


if __name__ == "__main__":
    sys.exit(main());

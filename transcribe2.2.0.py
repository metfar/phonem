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

"""transcribe.py - Local audio transcription with faster-whisper.

EN: Transcribes local audio to text or subtitle/document formats. The main language
    option is -l/--language, matching the rest of the project. Regional project
    profiles are collapsed to the base language understood by Whisper.
ES: Transcribe audio local a texto o formatos de subtítulos/documentos. La opción
    principal de idioma es -l/--language, como en el resto del proyecto. Los
    perfiles regionales se reducen al idioma base que entiende Whisper.
FR: Transcrit l'audio local vers du texte ou des formats de sous-titres/documents.
    L'option principale de langue est -l/--language, comme dans le reste du projet.
    Les profils régionaux sont réduits à la langue de base comprise par Whisper.
""";

import argparse;
import html;
import json;
import math;
import re;
import shutil;
import sys;

from dataclasses import asdict, dataclass;
from pathlib import Path;
from statistics import median;

from language_profiles import backend_family_language, canonical_language;


PROGRAM_VERSION = "2.2.0";
DEFAULT_MODEL = "small";
SAMPLE_RATE = 16000;
ANSI_BOLD = "\033[1m";
ANSI_RESET = "\033[0m";


@dataclass
class WordRecord:
    """EN: One recognized word. ES: Información de una palabra reconocida. FR: Informations sur un mot reconnu.""";

    start: float;
    end: float;
    text: str;
    probability: float;
    emphasized: bool = False;
    emphasis_score: float = 1.0;
    energy_ratio: float = 1.0;
    duration_ratio: float = 1.0;


@dataclass
class SegmentRecord:
    """EN: One recognized segment. ES: Información de un segmento reconocido. FR: Informations sur un segment reconnu.""";

    start: float;
    end: float;
    text: str;
    words: list[WordRecord];


def positive_integer(value):
    """EN: Validate positive integers. ES: Valida enteros mayores que cero. FR: Valide les entiers positifs.""";

    try:
        number = int(value);
    except ValueError as error:
        raise argparse.ArgumentTypeError("debe ser un número entero") from error;

    if number <= 0:
        raise argparse.ArgumentTypeError("debe ser mayor que cero");

    return number;


def non_negative_integer(value):
    """EN: Validate non-negative integers. ES: Valida enteros mayores o iguales que cero. FR: Valide les entiers positifs ou nuls.""";

    try:
        number = int(value);
    except ValueError as error:
        raise argparse.ArgumentTypeError("debe ser un número entero") from error;

    if number < 0:
        raise argparse.ArgumentTypeError("debe ser mayor o igual que cero");

    return number;


def positive_float(value):
    """EN: Validate positive real numbers. ES: Valida números reales positivos. FR: Valide les nombres réels positifs.""";

    try:
        number = float(value);
    except ValueError as error:
        raise argparse.ArgumentTypeError("debe ser un número real") from error;

    if number <= 0.0:
        raise argparse.ArgumentTypeError("debe ser mayor que cero");

    return number;


def get_arguments():
    """EN: Parse command-line arguments. ES: Procesa los argumentos de la línea de comandos. FR: Analyse les arguments de la ligne de commande.""";

    examples = """Ejemplos:
  %(prog)s audio.mp3
  %(prog)s audio.mp3 --line-length 72
  %(prog)s audio.mp3 --format srt --output subtitulos.srt
  %(prog)s audio.mp3 --format markdown --output texto.md --emphasis
  %(prog)s audio.mp3 --format json --output -
  %(prog)s audio.mp3 -l auto --model medium
  %(prog)s --list-models

Sin --output, la transcripción se escribe en la salida estándar.
El valor '-' también representa la salida estándar.
""";

    parser = argparse.ArgumentParser(
        description="Transcribe audio localmente mediante faster-whisper.",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    );

    parser.add_argument(
        "audio",
        nargs="?",
        type=Path,
        help="archivo de audio que se desea transcribir",
    );

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="lista los modelos reconocidos por faster-whisper y termina",
    );

    parser.add_argument(
        "-o",
        "--output",
        metavar="ARCHIVO",
        help="archivo de salida; '-' o la omisión escriben en stdout",
    );

    parser.add_argument(
        "-f",
        "--format",
        choices=("auto", "text", "markdown", "srt", "vtt", "json", "html"),
        default="auto",
        help=(
            "formato de salida; auto lo deduce por la extensión y usa "
            "text cuando no hay archivo (predeterminado: auto)"
        ),
    );

    parser.add_argument(
        "-w",
        "--line-length",
        type=non_negative_integer,
        default=None,
        metavar="COLUMNAS",
        help=(
            "longitud máxima de línea; omitido usa el ancho de la terminal "
            "interactiva y 0 desactiva el ajuste"
        ),
    );

    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="incluye tiempos por segmento en text o markdown",
    );

    parser.add_argument(
        "--emphasis",
        action="store_true",
        help="intenta detectar palabras resaltadas por energía y duración",
    );

    parser.add_argument(
        "--emphasis-style",
        choices=("auto", "none", "ansi", "markdown", "html"),
        default="auto",
        help=(
            "representación de la negrita; auto usa ANSI en terminal, "
            "Markdown en .md y etiquetas en HTML/SRT/VTT"
        ),
    );

    parser.add_argument(
        "--emphasis-threshold",
        type=positive_float,
        default=1.35,
        metavar="FACTOR",
        help=(
            "umbral combinado para marcar énfasis; valores menores marcan "
            "más palabras (predeterminado: 1.35)"
        ),
    );

    parser.add_argument(
        "--emphasis-context",
        type=non_negative_integer,
        default=4,
        metavar="PALABRAS",
        help=(
            "cantidad de palabras vecinas para estimar el nivel normal "
            "del locutor (predeterminado: 4)"
        ),
    );

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="MODELO",
        help=(
            "modelo, ruta local o ID de Hugging Face; consulte "
            "--list-models (predeterminado: %(default)s)"
        ),
    );

    parser.add_argument(
        "-l",
        "--language",
        default="es",
        metavar="IDIOMA",
        help="idioma/perfil del proyecto; en=en-ca, es=es-uy, fr=fr-fr; use auto para detectar",
    );

    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="dispositivo de inferencia (predeterminado: cpu)",
    );

    parser.add_argument(
        "--compute-type",
        default=None,
        metavar="TIPO",
        help="tipo de cálculo; por defecto int8 en CPU y float16 en CUDA",
    );

    parser.add_argument(
        "--beam-size",
        type=positive_integer,
        default=5,
        metavar="N",
        help="tamaño del haz de búsqueda (predeterminado: 5)",
    );

    parser.add_argument(
        "--min-silence",
        type=non_negative_integer,
        default=500,
        metavar="MS",
        help="silencio mínimo para el filtro VAD (predeterminado: 500 ms)",
    );

    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="desactiva el filtro de actividad de voz",
    );

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suprime los mensajes informativos enviados a stderr",
    );

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PROGRAM_VERSION}",
    );

    arguments = parser.parse_args();

    if not arguments.list_models and arguments.audio is None:
        parser.error("se requiere AUDIO, salvo cuando se usa --list-models");

    return arguments;


def status(message, quiet=False):
    """EN: Write operational status to stderr. ES: Escribe información operativa sin contaminar stdout. FR: Écrit l’état opérationnel sur stderr.""";

    if not quiet:
        print(message, file=sys.stderr, flush=True);


def model_note(model_name):
    """EN: Return a short note for known models. ES: Devuelve una descripción breve para modelos conocidos. FR: Renvoie une brève description des modèles connus.""";

    notes = {
        "tiny": "mínimo consumo; máxima velocidad; menor precisión",
        "tiny.en": "tiny especializado exclusivamente en inglés",
        "base": "muy ligero; algo más preciso que tiny",
        "base.en": "base especializado exclusivamente en inglés",
        "small": "equilibrio práctico entre velocidad y precisión",
        "small.en": "small especializado exclusivamente en inglés",
        "medium": "mayor precisión; más lento y exigente",
        "medium.en": "medium especializado exclusivamente en inglés",
        "large-v1": "modelo grande de primera generación",
        "large-v2": "modelo grande de segunda generación",
        "large-v3": "modelo grande de tercera generación",
        "large": "alias de large-v3",
        "distil-small.en": "modelo destilado small para inglés",
        "distil-medium.en": "modelo destilado medium para inglés",
        "distil-large-v2": "modelo large-v2 destilado y más rápido",
        "distil-large-v3": "modelo large-v3 destilado y más rápido",
        "distil-large-v3.5": "revisión destilada de large-v3",
        "large-v3-turbo": "variante de large-v3 optimizada para velocidad",
        "turbo": "alias de large-v3-turbo",
    };

    return notes.get(model_name, "modelo reconocido por la versión instalada");


def print_available_models():
    """EN: List models recognized by installed faster-whisper. ES: Lista los alias que reconoce la versión instalada. FR: Liste les modèles reconnus par faster-whisper installé.""";

    try:
        from faster_whisper.utils import available_models;
    except ImportError as error:
        raise RuntimeError(
            "Falta faster-whisper. Instálelo con: "
            "python3 -m pip install faster-whisper"
        ) from error;

    models = available_models();
    name_width = max(len(model) for model in models);

    print("Modelos reconocidos por la versión instalada de faster-whisper:");
    print();

    for model_name in models:
        default_marker = " [predeterminado]" if model_name == DEFAULT_MODEL else "";
        print(
            f"  {model_name:<{name_width}}  {model_note(model_name)}"
            f"{default_marker}"
        );

    print();
    print(
        "También puede usar una ruta a un modelo CTranslate2 local o un "
        "ID de Hugging Face como usuario/modelo."
    );


def resolve_output_format(requested_format, output_name):
    """EN: Resolve explicit output format or infer it from the extension. ES: Determina el formato explícito o lo infiere por la extensión. FR: Résout le format explicite ou le déduit de l’extension.""";

    if requested_format != "auto":
        return requested_format;

    if output_name and output_name != "-":
        extension = Path(output_name).suffix.lower();
        extension_formats = {
            ".txt": "text",
            ".text": "text",
            ".md": "markdown",
            ".markdown": "markdown",
            ".srt": "srt",
            ".vtt": "vtt",
            ".json": "json",
            ".html": "html",
            ".htm": "html",
        };

        return extension_formats.get(extension, "text");

    return "text";


def output_is_stdout(output_name):
    """EN: Return whether the selected output is stdout. ES: Indica si el destino seleccionado es stdout. FR: Indique si la sortie sélectionnée est stdout.""";

    return output_name in (None, "-");


def resolve_line_length(requested_length, using_stdout):
    """EN: Resolve effective line width. ES: Calcula la longitud efectiva de las líneas. FR: Calcule la largeur de ligne effective.""";

    if requested_length is not None:
        return requested_length;

    if using_stdout and sys.stdout.isatty():
        return max(20, shutil.get_terminal_size(fallback=(100, 24)).columns);

    return 0;


def resolve_emphasis_style(arguments, output_format, using_stdout):
    """EN: Select the appropriate emphasis representation. ES: Selecciona la representación adecuada del énfasis. FR: Sélectionne la représentation appropriée de l’emphase.""";

    if not arguments.emphasis:
        return "none";

    if arguments.emphasis_style != "auto":
        return arguments.emphasis_style;

    if output_format == "text":
        if using_stdout and sys.stdout.isatty():
            return "ansi";

        return "none";

    if output_format == "markdown":
        return "markdown";

    if output_format in ("html", "srt", "vtt"):
        return "html";

    return "none";


def format_srt_timestamp(seconds):
    """EN: Convert seconds to HH:MM:SS,mmm. ES: Convierte segundos a HH:MM:SS,mmm. FR: Convertit les secondes en HH:MM:SS,mmm.""";

    milliseconds = max(0, round(seconds * 1000.0));
    hours, remainder = divmod(milliseconds, 3600000);
    minutes, remainder = divmod(remainder, 60000);
    whole_seconds, milliseconds = divmod(remainder, 1000);

    return (
        f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},"
        f"{milliseconds:03d}"
    );


def format_vtt_timestamp(seconds):
    """EN: Convert seconds to HH:MM:SS.mmm. ES: Convierte segundos a HH:MM:SS.mmm. FR: Convertit les secondes en HH:MM:SS.mmm.""";

    return format_srt_timestamp(seconds).replace(",", ".");


def format_console_timestamp(seconds):
    """EN: Convert seconds to a compact text timestamp. ES: Convierte segundos a una marca compacta para texto. FR: Convertit les secondes en horodatage texte compact.""";

    milliseconds = max(0, round(seconds * 1000.0));
    hours, remainder = divmod(milliseconds, 3600000);
    minutes, remainder = divmod(remainder, 60000);
    whole_seconds, milliseconds = divmod(remainder, 1000);

    if hours:
        return (
            f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}."
            f"{milliseconds:03d}"
        );

    return f"{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}";


def copy_segments(raw_segments):
    """EN: Materialize segments yielded by faster-whisper. ES: Materializa los segmentos generados por faster-whisper. FR: Matérialise les segments produits par faster-whisper.""";

    records = [];

    for segment in raw_segments:
        words = [];

        if segment.words:
            for word in segment.words:
                words.append(
                    WordRecord(
                        start=float(word.start),
                        end=float(word.end),
                        text=str(word.word),
                        probability=float(word.probability),
                    )
                );

        records.append(
            SegmentRecord(
                start=float(segment.start),
                end=float(segment.end),
                text=str(segment.text),
                words=words,
            )
        );

    return records;


def word_character_count(text):
    """EN: Count lexical characters, excluding spaces and punctuation. ES: Cuenta caracteres léxicos y descarta espacios y puntuación. FR: Compte les caractères lexicaux hors espaces et ponctuation.""";

    return len(re.sub(r"[^\w]+", "", text, flags=re.UNICODE));


def calculate_word_energy(audio, start, end, numpy_module):
    """EN: Compute RMS energy for a word time region. ES: Calcula la energía RMS de la región temporal de una palabra. FR: Calcule l’énergie RMS de la région temporelle d’un mot.""";

    duration = max(0.0, end - start);
    trim = min(0.025, duration * 0.12);
    first_sample = max(0, int((start + trim) * SAMPLE_RATE));
    last_sample = min(len(audio), int((end - trim) * SAMPLE_RATE));

    if last_sample <= first_sample:
        first_sample = max(0, int(start * SAMPLE_RATE));
        last_sample = min(len(audio), int(end * SAMPLE_RATE));

    if last_sample <= first_sample:
        return 0.0;

    samples = audio[first_sample:last_sample].astype("float64", copy=False);

    if samples.size == 0:
        return 0.0;

    return float(numpy_module.sqrt(numpy_module.mean(samples * samples) + 1.0e-12));


def annotate_emphasis(segments, audio, threshold, context, numpy_module):
    """EN: Mark emphasis from relative energy and local duration. ES: Marca énfasis mediante energía relativa y alargamiento local. FR: Marque l’emphase selon l’énergie relative et la durée locale.""";

    words = [word for segment in segments for word in segment.words];

    if not words:
        return;

    energies = [];
    durations_per_character = [];

    for word in words:
        energy = calculate_word_energy(
            audio,
            word.start,
            word.end,
            numpy_module,
        );
        character_count = max(1, word_character_count(word.text));
        duration = max(0.02, word.end - word.start);
        energies.append(energy);
        durations_per_character.append(duration / character_count);

    positive_energies = [value for value in energies if value > 0.0];
    global_energy = median(positive_energies) if positive_energies else 1.0;
    global_duration = median(durations_per_character);

    for index, word in enumerate(words):
        first_neighbor = max(0, index - context);
        last_neighbor = min(len(words), index + context + 1);
        neighbor_indexes = [
            neighbor
            for neighbor in range(first_neighbor, last_neighbor)
            if neighbor != index
        ];
        neighbor_energies = [
            energies[neighbor]
            for neighbor in neighbor_indexes
            if energies[neighbor] > 0.0
        ];
        neighbor_durations = [
            durations_per_character[neighbor]
            for neighbor in neighbor_indexes
        ];
        baseline_energy = (
            median(neighbor_energies)
            if neighbor_energies
            else global_energy
        );
        baseline_duration = (
            median(neighbor_durations)
            if neighbor_durations
            else global_duration
        );
        energy_ratio = energies[index] / max(baseline_energy, 1.0e-12);
        duration_ratio = (
            durations_per_character[index]
            / max(baseline_duration, 1.0e-12)
        );
        combined_score = (
            math.pow(max(energy_ratio, 1.0e-6), 0.75)
            * math.pow(max(duration_ratio, 1.0e-6), 0.25)
        );
        lexical_length = word_character_count(word.text);

        word.energy_ratio = energy_ratio;
        word.duration_ratio = duration_ratio;
        word.emphasis_score = combined_score;
        word.emphasized = bool(
            lexical_length >= 2
            and word.probability >= 0.25
            and energy_ratio >= 1.10
            and combined_score >= threshold
        );


def split_outer_whitespace(text):
    """EN: Split outer whitespace from word content. ES: Separa los espacios externos del contenido de una palabra. FR: Sépare les espaces externes du contenu d’un mot.""";

    match = re.match(r"^(\s*)(.*?)(\s*)$", text, flags=re.DOTALL);

    if not match:
        return "", text, "";

    return match.group(1), match.group(2), match.group(3);


def style_word(word, style, escape_all=False):
    """EN: Render a word with the selected emphasis style. ES: Representa una palabra con el estilo de énfasis seleccionado. FR: Rend un mot avec le style d’emphase sélectionné.""";

    prefix, core, suffix = split_outer_whitespace(word.text);
    visible_core = html.escape(core) if escape_all else core;

    if not word.emphasized or style == "none" or not core:
        return prefix + visible_core + suffix;

    if style == "ansi":
        return prefix + ANSI_BOLD + visible_core + ANSI_RESET + suffix;

    if style == "markdown":
        return prefix + "**" + visible_core + "**" + suffix;

    if style == "html":
        return prefix + "<b>" + html.escape(core) + "</b>" + suffix;

    return prefix + visible_core + suffix;


def segment_pieces(segment, style, escape_all=False):
    """EN: Return visible/rendered text pairs. ES: Devuelve pares de texto visible y texto representado. FR: Renvoie des paires texte visible/texte rendu.""";

    if segment.words:
        return [
            (
                word.text,
                style_word(word, style, escape_all=escape_all),
            )
            for word in segment.words
        ];

    plain_tokens = re.findall(r"\s*\S+|\s+$", segment.text);

    if not plain_tokens:
        return [("", "")];

    return [
        (
            token,
            html.escape(token) if escape_all else token,
        )
        for token in plain_tokens
    ];


def all_pieces(segments, style, escape_all=False):
    """EN: Combine pieces from all segments. ES: Combina las piezas de todos los segmentos. FR: Combine les éléments de tous les segments.""";

    pieces = [];

    for segment_index, segment in enumerate(segments):
        current = segment_pieces(segment, style, escape_all=escape_all);

        if segment_index and current:
            first_plain, first_rendered = current[0];

            if not first_plain.startswith((" ", "\n", "\t")):
                current[0] = (" " + first_plain, " " + first_rendered);

        pieces.extend(current);

    return pieces;


def wrap_pieces(pieces, width):
    """EN: Wrap lines counting visible characters only. ES: Ajusta líneas contando sólo caracteres visibles, no el marcado. FR: Coupe les lignes en comptant uniquement les caractères visibles.""";

    if width <= 0:
        return ["".join(rendered for _, rendered in pieces).strip()];

    lines = [];
    current_rendered = "";
    current_visible_length = 0;

    for plain, rendered in pieces:
        visible_piece = plain;
        rendered_piece = rendered;

        if not current_rendered:
            visible_piece = visible_piece.lstrip();
            rendered_piece = rendered_piece.lstrip();

        proposed_length = current_visible_length + len(visible_piece);

        if current_rendered and proposed_length > width:
            lines.append(current_rendered.rstrip());
            visible_piece = visible_piece.lstrip();
            rendered_piece = rendered_piece.lstrip();
            current_rendered = rendered_piece;
            current_visible_length = len(visible_piece);
        else:
            current_rendered += rendered_piece;
            current_visible_length = proposed_length;

    if current_rendered or not lines:
        lines.append(current_rendered.rstrip());

    return lines;


def render_text(segments, style, width, timestamps=False):
    """EN: Render plain text or Markdown. ES: Genera texto plano o Markdown. FR: Produit du texte brut ou Markdown.""";

    if not timestamps:
        return "\n".join(wrap_pieces(all_pieces(segments, style), width)).strip() + "\n";

    output_lines = [];

    for segment in segments:
        prefix = (
            f"[{format_console_timestamp(segment.start)} --> "
            f"{format_console_timestamp(segment.end)}] "
        );
        available_width = max(10, width - len(prefix)) if width else 0;
        lines = wrap_pieces(segment_pieces(segment, style), available_width);
        output_lines.append(prefix + lines[0]);
        output_lines.extend(" " * len(prefix) + line for line in lines[1:]);

    return "\n".join(output_lines).rstrip() + "\n";


def render_srt(segments, style, width):
    """EN: Render SubRip subtitles. ES: Genera subtítulos SubRip. FR: Produit des sous-titres SubRip.""";

    blocks = [];

    for number, segment in enumerate(segments, start=1):
        lines = wrap_pieces(
            segment_pieces(segment, style, escape_all=(style == "html")),
            width,
        );
        blocks.append(
            "\n".join(
                (
                    str(number),
                    (
                        f"{format_srt_timestamp(segment.start)} --> "
                        f"{format_srt_timestamp(segment.end)}"
                    ),
                    *lines,
                )
            )
        );

    return "\n\n".join(blocks).rstrip() + "\n";


def render_vtt(segments, style, width):
    """EN: Render WebVTT subtitles. ES: Genera subtítulos WebVTT. FR: Produit des sous-titres WebVTT.""";

    blocks = ["WEBVTT"];

    for segment in segments:
        lines = wrap_pieces(
            segment_pieces(segment, style, escape_all=(style == "html")),
            width,
        );
        blocks.append(
            "\n".join(
                (
                    (
                        f"{format_vtt_timestamp(segment.start)} --> "
                        f"{format_vtt_timestamp(segment.end)}"
                    ),
                    *lines,
                )
            )
        );

    return "\n\n".join(blocks).rstrip() + "\n";


def render_html(segments, style, title, language):
    """EN: Render a complete HTML document. ES: Genera un documento HTML completo. FR: Produit un document HTML complet.""";

    paragraphs = [];

    for segment in segments:
        content = "".join(
            rendered
            for _, rendered in segment_pieces(
                segment,
                style,
                escape_all=True,
            )
        ).strip();
        paragraphs.append(
            (
                f'<p data-start="{segment.start:.3f}" '
                f'data-end="{segment.end:.3f}">{content}</p>'
            )
        );

    safe_title = html.escape(title);

    return "\n".join(
        (
            "<!DOCTYPE html>",
            f'<html lang="{html.escape(language or "und")}">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{safe_title}</title>",
            "</head>",
            "<body>",
            *["  " + paragraph for paragraph in paragraphs],
            "</body>",
            "</html>",
            "",
        )
    );


def render_json(segments, information, arguments, audio_path):
    """EN: Render structured JSON output. ES: Genera una salida JSON estructurada. FR: Produit une sortie JSON structurée.""";

    payload = {
        "source": str(audio_path),
        "model": arguments.model,
        "requested_language": canonical_language(arguments.language, allow_auto=True),
        "language": information.language,
        "language_probability": information.language_probability,
        "segments": [asdict(segment) for segment in segments],
    };

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n";


def render_output(
        output_format,
        segments,
        information,
        arguments,
        audio_path,
        emphasis_style,
        width,
):
    """EN: Select the requested serializer. ES: Selecciona el serializador solicitado. FR: Sélectionne le sérialiseur demandé.""";

    if output_format in ("text", "markdown"):
        return render_text(
            segments,
            emphasis_style,
            width,
            timestamps=arguments.timestamps,
        );

    if output_format == "srt":
        return render_srt(segments, emphasis_style, width);

    if output_format == "vtt":
        return render_vtt(segments, emphasis_style, width);

    if output_format == "html":
        return render_html(segments, emphasis_style, audio_path.name, information.language);

    if output_format == "json":
        return render_json(segments, information, arguments, audio_path);

    raise ValueError(f"Formato de salida no implementado: {output_format}");


def write_output(content, output_name):
    """EN: Write output to stdout or UTF-8 file. ES: Escribe el resultado en stdout o en un archivo UTF-8. FR: Écrit la sortie sur stdout ou dans un fichier UTF-8.""";

    if output_is_stdout(output_name):
        sys.stdout.write(content);
        sys.stdout.flush();
        return;

    output_path = Path(output_name).expanduser();

    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(content);


def transcribe(arguments):
    """EN: Run transcription and render requested format. ES: Ejecuta la transcripción y genera el formato solicitado. FR: Exécute la transcription et produit le format demandé.""";

    try:
        import numpy as np;
        from faster_whisper import WhisperModel;
        from faster_whisper.audio import decode_audio;
    except ImportError as error:
        raise RuntimeError(
            "Falta faster-whisper. Instálelo con: "
            "python3 -m pip install faster-whisper"
        ) from error;

    audio_path = arguments.audio.expanduser().resolve();

    if not audio_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {audio_path}");

    using_stdout = output_is_stdout(arguments.output);
    output_format = resolve_output_format(arguments.format, arguments.output);
    width = resolve_line_length(arguments.line_length, using_stdout);
    emphasis_style = resolve_emphasis_style(
        arguments,
        output_format,
        using_stdout,
    );
    logical_language = canonical_language(arguments.language, allow_auto=True);
    if not logical_language:
        raise ValueError(f"Idioma inválido: {arguments.language}");
    language = None if logical_language == "auto" else backend_family_language(logical_language);
    compute_type = arguments.compute_type;

    if compute_type is None:
        if arguments.device == "cuda":
            compute_type = "float16";
        elif arguments.device == "cpu":
            compute_type = "int8";
        else:
            compute_type = "default";

    status(f"Archivo: {audio_path}", arguments.quiet);
    status(f"Modelo: {arguments.model}", arguments.quiet);
    status(
        f"Idioma solicitado: {logical_language}; Whisper: {language or 'auto'}",
        arguments.quiet,
    );
    status(
        f"Dispositivo: {arguments.device}; cálculo: {compute_type}",
        arguments.quiet,
    );

    if arguments.emphasis and output_format == "text" and emphasis_style == "none":
        status(
            "Aviso: el énfasis se analizó, pero text hacia archivo o tubería "
            "no admite negrita automática. Use --format markdown, --format html "
            "o --emphasis-style ansi.",
            arguments.quiet,
        );

    audio_samples = None;
    transcription_input = str(audio_path);

    if arguments.emphasis:
        status("Decodificando audio para analizar énfasis...", arguments.quiet);
        audio_samples = decode_audio(
            str(audio_path),
            sampling_rate=SAMPLE_RATE,
        );
        transcription_input = audio_samples;

    status("Cargando el modelo...", arguments.quiet);
    model = WhisperModel(
        arguments.model,
        device=arguments.device,
        compute_type=compute_type,
    );
    need_word_timestamps = arguments.emphasis or output_format == "json";
    transcription_options = {
        "language": language,
        "beam_size": arguments.beam_size,
        "vad_filter": not arguments.no_vad,
        "word_timestamps": need_word_timestamps,
    };

    if not arguments.no_vad:
        transcription_options["vad_parameters"] = {
            "min_silence_duration_ms": arguments.min_silence,
        };

    status("Transcribiendo...", arguments.quiet);
    raw_segments, information = model.transcribe(
        transcription_input,
        **transcription_options,
    );
    segments = copy_segments(raw_segments);

    status(
        (
            f"Idioma: {information.language} "
            f"({information.language_probability:.2%})"
        ),
        arguments.quiet,
    );

    if arguments.emphasis and audio_samples is not None:
        status("Analizando énfasis acústico...", arguments.quiet);
        annotate_emphasis(
            segments,
            audio_samples,
            arguments.emphasis_threshold,
            arguments.emphasis_context,
            np,
        );

    content = render_output(
        output_format,
        segments,
        information,
        arguments,
        audio_path,
        emphasis_style,
        width,
    );
    write_output(content, arguments.output);

    if not using_stdout:
        status(f"Salida guardada en: {arguments.output}", arguments.quiet);


def main():
    """EN: Main entry point. ES: Punto de entrada principal. FR: Point d’entrée principal.""";

    try:
        arguments = get_arguments();

        if arguments.list_models:
            print_available_models();
        else:
            transcribe(arguments);
    except BrokenPipeError:
        try:
            sys.stdout.close();
        except OSError:
            pass;

        return 0;
    except KeyboardInterrupt:
        print("\nTranscripción interrumpida.", file=sys.stderr);
        return 130;
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr);
        return 1;

    return 0;


if __name__ == "__main__":
    sys.exit(main());

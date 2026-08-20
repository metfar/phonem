# Languages

- [English](#english)
- [Español](#español)
- [Français](#français)

Current tools: **phonem.py 1.6.0**, **pronounce.py 0.6.0**, **trans.py 0.10.0**, **transcribe.py 2.2.0**.

---

# English

## Project

This is a small GPL-2.0-or-later Unix-style language study toolkit. Each program performs one main transformation and keeps ordinary data on `stdout` while operational diagnostics go to `stderr`.

| Tool | Input | Main output | Purpose |
|---|---|---|---|
| `transcribe.py` | audio | text | local speech recognition with faster-whisper |
| `trans.py` | text | translated text | asynchronous translation with googletrans |
| `phonem.py` | text | IPA | phonemization and study-profile normalization |
| `pronounce.py` | IPA | audio | Piper speech synthesis |

Conceptually:

```text
audio -> transcribe.py -> text -> trans.py -> translated text
      -> phonem.py -> IPA -> pronounce.py -> audio
```

The `.py` names and shorter executable aliases are equivalent inside the package: `transcribe`, `trans`, `phonem`, and `pronounce` are symlinks to their stable `.py` names.

### Common language convention

Every tool uses the same option for its **main language**:

```text
-l LANG
--language LANG
```

The short project language names are aliases, not separate profiles:

| Short name | Canonical project profile |
|---|---|
| `en` | `en-ca` |
| `es` | `es-uy` |
| `fr` | `fr-fr` |

Thus `-l es` and `-l es-uy` mean the same project profile. External engines do not necessarily understand regional profiles, so each tool adapts the canonical profile to its backend. For example, `es-uy` becomes `es` for Whisper/googletrans, uses the Latin-American eSpeak backend plus the project IPA overlay in `phonem.py`, and uses the configured Rioplatense approximation in Piper.

## Quick start

Transcribe local audio:

```bash
./transcribe.py recording.mp3 -l auto
```

Translate English to the default Spanish profile:

```bash
./trans.py -s en -l es "Hello world"
```

Get IPA. `phonem.py` defaults to conservative language detection, so `-l` is optional when EN/ES/FR can be identified confidently:

```bash
./phonem.py "La casa de ella es azul."
./phonem.py "Bonjour tout le monde." -l fr
```

Speak IPA through the configured Piper voice:

```bash
./phonem.py "La casa de ella es azul." -l es | ./pronounce.py -l es
```

## Tools

### transcribe.py

Local audio -> text with faster-whisper. It keeps its existing subtitle/document features, but now accepts both `-l` and `--language` and understands the same project aliases as the other tools.

```bash
./transcribe.py interview.mp3 -l auto
./transcribe.py interview.mp3 -l en --format srt -o interview.srt
```

### trans.py

Text -> translated text. The preferred interface is now option-based:

```bash
./trans.py -s en -l es "Hello world"
echo "Bonjour" | ./trans.py -s fr -l en
```

`-s/--source-language` defaults to `auto`. If `-l/--language` is omitted, the destination is inferred from the process locale, in the usual precedence order `LC_ALL`, `LC_MESSAGES`, then `LANG`.

For example:

```bash
LANG=en_CA.UTF-8 ./trans.py -s fr "Bonjour"
```

resolves the destination to project profile `en-ca`; googletrans receives its base language `en`.

The historical interface remains accepted for compatibility:

```bash
./trans.py en es "Hello world"
```

ANSI/ECMA-48 terminal escapes are stripped by default:

```bash
ls --color=always -1 | ./trans.py -s en -l es
```

Use `--keep-ansi` only when those raw escape sequences are intentionally wanted.

### phonem.py

Text -> IPA through phonemizer/eSpeak NG. It normalizes study-sensitive numbers and applies small editable IPA overlays. Language detection is the default:

```bash
./phonem.py "Hello, how are you?"      # detects English -> en-ca
./phonem.py "¿Cómo estás?"             # detects Spanish -> es-uy
./phonem.py "Bonjour, comment ça va ?" # detects French -> fr-fr
```

When the text is too short or ambiguous, it refuses to guess and asks for `-l/--language`.

### pronounce.py

IPA -> audio through Piper. IPA itself does not reliably identify a language or acoustic speaker, so `pronounce.py` does **not** use text-language autodetection. Use a configured default or pass the profile explicitly:

```bash
./phonem.py "La casa de ella" -l es | ./pronounce.py -l es
./pronounce.py "bɔ̃ʒuʁ" -l fr --wav bonjour.wav
```

## Installation

The primary target is GNU/Linux/POSIX with Python 3.9 or newer.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Python dependencies in the package:

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
faster-whisper>=1,<2
numpy>=1.24,<3
```

Initialize/update the Piper configuration and install the unique default voices:

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

## Complete pipelines

Audio -> recognized text:

```bash
./transcribe.py recording.mp3 -l auto -q
```

Audio -> translated text:

```bash
./transcribe.py recording.mp3 -l auto -q | \
    ./trans.py -s auto -l es
```

Audio -> translation -> IPA:

```bash
./transcribe.py recording.mp3 -l auto -q | \
    ./trans.py -s auto -l es | \
    ./phonem.py -l es
```

Complete round trip:

```bash
./transcribe.py recording.mp3 -l auto -q | \
    ./trans.py -s auto -l es | \
    ./phonem.py -l es | \
    ./pronounce.py -l es
```

## Detailed reference

### Transcription

`transcribe.py` keeps the functionality of the previous 2.1.1 tool and adds the common language contract. Its main language option is now:

```text
-l LANG == --language LANG
```

For continuity, the default remains `es`, which now means canonical project profile `es-uy`; faster-whisper receives `es`. Use `-l auto` for Whisper language detection.

Regional project profiles are collapsed to the base language Whisper understands:

```text
en-ca -> en
es-uy -> es
fr-ca -> fr
```

Supported output modes remain:

```text
text, markdown, srt, vtt, json, html
```

Examples:

```bash
./transcribe.py audio.mp3 -l auto
./transcribe.py audio.mp3 -l fr-ca --format srt -o audio.srt
./transcribe.py audio.mp3 -l es --format markdown --emphasis -o audio.md
./transcribe.py audio.mp3 -l auto --format json -o -
```

JSON output includes both the normalized requested project language and the language reported by Whisper. HTML output uses the language reported by Whisper in the document's `lang` attribute instead of hard-coding Spanish.

The optional emphasis analysis uses local word energy and duration relative to neighboring words. It remains experimental and independent from transcription probability.

### Translation

`trans.py` accepts positional text, `-t/--text`, `-i/--input`, or stdin. Only translated data is written to `stdout`.

Preferred language interface:

```text
-s, --source-language LANG       source; default auto
-l, --language LANG              destination
-d, --destination-language LANG  synonym for -l/--language
```

If the destination is omitted, locale inference works as follows:

```text
LC_ALL -> LC_MESSAGES -> LANG
```

Locale spelling is normalized before project aliases are applied:

```text
en_CA.UTF-8 -> en-ca
es_UY.UTF-8 -> es-uy
fr_FR.UTF-8 -> fr-fr
fr_CA.UTF-8 -> fr-ca
```

`C`, `POSIX`, and their UTF-8 variants are not treated as usable destination languages; in that case `trans.py` asks for `-l` explicitly.

For known project profiles, googletrans receives the base family code because it translates languages rather than this project's pronunciation profiles:

```text
en-ca, en-us, en-gb, ... -> en
es-uy, es-es             -> es
fr-fr, fr-ca, fr-be, ... -> fr
```

Other googletrans languages remain usable. For a locale-like value such as `de_DE.UTF-8`, `trans.py` first tries the normalized exact code and then its base family (`de`).

The original positional `SRC DEST` syntax is retained in the 0.10 series for backward compatibility, but new scripts should use `-s` and `-l`.

Long input is split at useful boundaries. Default chunk size is 5000 characters; `--chunk-size` may change it up to 15000.

### Phonemization

`phonem.py` separates a **logical study profile** from the installed eSpeak backend. The profile can therefore remain precise even when upstream does not offer a native voice for that exact region.

Current canonical profiles:

| Profile | Short alias | Intended study target | Typical eSpeak path |
|---|---|---|---|
| `en-ca` | `en` | Canadian English | `en-us` then fallbacks |
| `en-us` | — | US English | `en-us` |
| `en-gb` | — | British English | `en-gb` |
| `en-rp` | — | Received Pronunciation | RP voice when installed, then British fallback |
| `en-lancashire` | — | Lancashire | regional voice when installed, then British fallback |
| `en-nyc` | — | New York City | NYC voice when installed, then US fallback |
| `es-uy` | `es` | formal Uruguayan Spanish | `es-419`, then legacy `es-la` |
| `es-es` | — | Spain Spanish | `es`/`es-es` |
| `fr-fr` | `fr` | France French | `fr-fr`, then `fr` |
| `fr-ca` | — | Quebec study profile | approximation |
| `fr-be` | — | Belgian French | `fr-be` |
| `fr-ch` | — | Swiss French with `huitante` | `fr-ch` |
| `fr-ch-qv` | — | Swiss `quatre-vingts` study overlay | `fr-ch` |

Automatic detection is deliberately conservative and currently distinguishes only English, Spanish, and French. Its defaults are exactly the short aliases:

```text
English -> en -> en-ca
Spanish -> es -> es-uy
French  -> fr -> fr-fr
```

#### Formal Uruguayan Spanish

`es-uy` remains a study profile, not a claim that eSpeak or Piper has a native Uruguayan model. It retains seseo and final `/s/`, does not add a Madrid-style final-`d` substitution, keeps groups such as `/kt/`, and applies the project's consonantal `y/ll` target `[ʃ]` through editable IPA replacements. The contextual handling avoids turning vocalic/final `y` into `[ʃ]` indiscriminately.

### Pronunciation

`pronounce.py` resolves a project profile to a configured Piper model. The shipped defaults are conservative acoustic starting points; only `es-uy` has been user-tested in this project so far.

| Profile(s) | Default Piper model | Length | Volume | Status |
|---|---|---:|---:|---|
| `es-uy` / `es` | `es_AR-daniela-high` | 2.0 | 1.0 | user-tested approximation |
| `es-es` | `es_ES-davefx-medium` | 1.0 | 1.0 | starting point |
| `en-ca` / `en` | `en_US-lessac-high` | 1.0 | 1.0 | approximation |
| `en-us`, `en-nyc` | `en_US-lessac-high` | 1.0 | 1.0 | starting point / approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | 1.0 | 1.0 | starting point / approximation |
| `en-lancashire` | `en_GB-northern_english_male-medium` | 1.0 | 1.0 | approximation |
| `fr-fr` / `fr` | `fr_FR-siwis-medium` | 1.0 | 1.0 | starting point |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | 1.0 | 1.0 | acoustic approximation |

Extra hard study pauses remain available with `--extra-pauses`, but are disabled by default because post-synthesis silence was found to make word endings less natural. Piper-native timing is the default.

Useful inventory commands:

```bash
./pronounce.py --list-languages
./pronounce.py --list-catalog-languages
./pronounce.py --list-voices es
./pronounce.py --list-models es
```

### Language profiles

The common normalization code lives in `language_profiles.py`. That file is intentionally small and shared by all four tools so aliases cannot silently drift apart.

Core rules:

```text
en -> en-ca
es -> es-uy
fr -> fr-fr
```

A profile is a project-level study target. A backend language is what an external service/model accepts. Those are deliberately separate concepts.

| Project input | Canonical profile | Translation/Whisper family | Pronunciation layer |
|---|---|---|---|
| `en` | `en-ca` | `en` | Canadian study profile / configured Piper approximation |
| `es` | `es-uy` | `es` | Uruguayan study IPA overlay / Rioplatense Piper approximation |
| `fr` | `fr-fr` | `fr` | France French study profile / France Piper model |

### Configuration

Piper configuration defaults to:

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

`pronounce.py 0.6.0` uses configuration schema 2. The schema change makes `en`, `es`, and `fr` true aliases instead of independent profile entries. Updating an old schema-1 JSON creates a timestamped backup, migrates the canonical entries, removes the obsolete duplicate alias keys, and preserves canonical user tuning and unknown custom keys.

```bash
./pronounce.py --update-config
```

Possible statuses:

```text
created
updated   # also reports backup=...
unchanged
```

A clean template can still be written with:

```bash
./pronounce.py --init-config
```

Download each unique configured default voice once:

```bash
./pronounce.py --download-defaults
```

### Number normalization

`phonem.py` expands standalone cardinal integers before phonemization when the language family is English, Spanish, or French. This keeps dialect-sensitive vocabulary under project control instead of asking a fallback voice to interpret raw digits.

Modern English profiles use the short scale; Spanish and French use the long scale:

| Power | Spanish | French | Modern English |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

French 70/80/90 study forms:

| Profile | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

Generate the current table from code:

```bash
./phonem.py --number-table
```

Decimals, dates, times and clearly formatted phone-number-like structures are intentionally not guessed as ordinary cardinal sequences.

### Audio and Piper models

Piper voices are separate ONNX models with a matching `.onnx.json` configuration file. Model licenses are independent from this project's GPL-2.0-or-later license and should be checked before redistribution.

Models are searched in explicit `--data-dir` paths, configured directories, `${XDG_DATA_HOME:-~/.local/share}/piper`, and the current directory.

Audio output:

```bash
./pronounce.py "...IPA..." -l es --wav speech.wav
./pronounce.py "...IPA..." -l fr --ogg speech.ogg
./pronounce.py "...IPA..." -l en --mp3 speech.mp3
```

Without an output option, `ffplay` is used for normal playback.

## License

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Project code is distributed under the **GNU General Public License version 2 or, at your option, any later version** (`GPL-2.0-or-later`). See `COPYING` / `LICENSE`.

External models and dependencies retain their own licenses.

## Sources

- eSpeak NG language list: <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- phonemizer: <https://github.com/bootphon/phonemizer>
- Piper / OHF Voice: <https://github.com/OHF-Voice/piper1-gpl>
- Piper voice catalogue: <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- googletrans: <https://github.com/ssut/py-googletrans>
- faster-whisper: <https://github.com/SYSTRAN/faster-whisper>
- FFmpeg / ffplay: <https://ffmpeg.org/>
- RAE/ASALE, *números*: <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *y*: <https://www.rae.es/dpd/y>
- RAE/ASALE, *yeísmo*: <https://www.rae.es/dpd/ye%C3%ADsmo>
- Office québécois de la langue française, large numbers: <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library, large numbers: <https://commonslibrary.parliament.uk/research-briefings/sn04440/>

---

# Español

## Proyecto

Este es un pequeño conjunto de herramientas Unix para estudio de idiomas bajo GPL-2.0-or-later. Cada programa hace una transformación principal, deja los datos normales en `stdout` y manda diagnósticos operativos a `stderr`.

| Herramienta | Entrada | Salida principal | Función |
|---|---|---|---|
| `transcribe.py` | audio | texto | reconocimiento local con faster-whisper |
| `trans.py` | texto | texto traducido | traducción asíncrona con googletrans |
| `phonem.py` | texto | IPA | fonemización y perfiles de estudio |
| `pronounce.py` | IPA | audio | síntesis con Piper |

La cadena completa es:

```text
audio -> transcribe.py -> texto -> trans.py -> texto traducido
      -> phonem.py -> IPA -> pronounce.py -> audio
```

Los nombres sin extensión (`transcribe`, `trans`, `phonem`, `pronounce`) son enlaces a los nombres estables `.py`.

### Convención común de idiomas

En los cuatro programas el **idioma principal** se indica igual:

```text
-l LANG
--language LANG
```

Los nombres cortos son alias reales:

| Alias | Perfil canónico |
|---|---|
| `en` | `en-ca` |
| `es` | `es-uy` |
| `fr` | `fr-fr` |

Por tanto, `-l es` y `-l es-uy` significan exactamente el mismo perfil dentro del proyecto. Cada backend recibe después el código que realmente entiende.

## Inicio rápido

Transcribir audio:

```bash
./transcribe.py grabacion.mp3 -l auto
```

Traducir al español predeterminado del proyecto:

```bash
./trans.py -s en -l es "Hello world"
```

Obtener IPA; `phonem.py` autodetecta EN/ES/FR por defecto:

```bash
./phonem.py "La casa de ella es azul."
./phonem.py "Bonjour tout le monde." -l fr
```

Pronunciar:

```bash
./phonem.py "La casa de ella es azul." -l es | ./pronounce.py -l es
```

## Herramientas

### transcribe.py

Audio local -> texto mediante faster-whisper. Conserva los formatos y el análisis de énfasis de la versión anterior, pero ahora `-l` y `--language` son equivalentes y aceptan los perfiles del proyecto.

```bash
./transcribe.py entrevista.mp3 -l auto
./transcribe.py entrevista.mp3 -l en --format srt -o entrevista.srt
```

### trans.py

Texto -> texto traducido. La interfaz recomendada pasa a ser:

```bash
./trans.py -s en -l es "Hello world"
echo "Bonjour" | ./trans.py -s fr -l en
```

`-s/--source-language` usa `auto` si se omite. Si falta `-l/--language`, el destino se toma de la locale del proceso: primero `LC_ALL`, después `LC_MESSAGES` y finalmente `LANG`.

Con:

```bash
echo $LANG
# en_CA.UTF-8
```

esto funciona sin indicar destino:

```bash
./trans.py -s fr "Bonjour"
```

y resuelve `en_CA.UTF-8 -> en-ca`; googletrans recibe `en`.

La sintaxis histórica sigue funcionando:

```bash
./trans.py en es "Hello world"
```

Los códigos ANSI/ECMA-48 se eliminan por defecto antes de traducir:

```bash
ls --color=always -1 | ./trans.py -s en -l es
```

### phonem.py

Texto -> IPA mediante phonemizer/eSpeak NG. La autodetección es ahora el valor predeterminado:

```bash
./phonem.py "Hello, how are you?"      # en -> en-ca
./phonem.py "¿Cómo estás?"             # es -> es-uy
./phonem.py "Bonjour, comment ça va ?" # fr -> fr-fr
```

Si no hay evidencia suficiente, no inventa un idioma: pide `-l/--language`.

### pronounce.py

IPA -> audio mediante Piper. Como un flujo IPA no transporta de forma fiable el perfil acústico deseado, acá no se intenta autodetección textual.

```bash
./phonem.py "La casa de ella" -l es | ./pronounce.py -l es
./pronounce.py "bɔ̃ʒuʁ" -l fr --wav bonjour.wav
```

## Instalación

El objetivo principal es GNU/Linux/POSIX con Python 3.9 o posterior.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Dependencias Python:

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
faster-whisper>=1,<2
numpy>=1.24,<3
```

Configuración y voces Piper:

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

## Pipelines completos

Audio -> texto:

```bash
./transcribe.py audio.mp3 -l auto -q
```

Audio -> traducción:

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l es
```

Audio -> traducción -> IPA:

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l es | \
    ./phonem.py -l es
```

Vuelta completa a audio:

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l es | \
    ./phonem.py -l es | \
    ./pronounce.py -l es
```

## Referencia detallada

### Transcripción

`transcribe.py 2.2.0` conserva las funciones de la 2.1.1 y adopta el contrato común:

```text
-l LANG == --language LANG
```

Por continuidad, el predeterminado sigue siendo `es`, que ahora se canoniza como `es-uy`; Whisper recibe simplemente `es`. Para detectar idioma:

```bash
./transcribe.py audio.mp3 -l auto
```

Los perfiles regionales se reducen a la familia que entiende Whisper:

```text
en-ca -> en
es-uy -> es
fr-ca -> fr
```

Formatos de salida conservados:

```text
text, markdown, srt, vtt, json, html
```

Ejemplos:

```bash
./transcribe.py audio.mp3 -l auto
./transcribe.py audio.mp3 -l fr-ca --format srt -o audio.srt
./transcribe.py audio.mp3 -l es --format markdown --emphasis -o audio.md
./transcribe.py audio.mp3 -l auto --format json -o -
```

El JSON incluye el perfil solicitado normalizado y el idioma informado por Whisper. El HTML usa ahora el idioma detectado/informado por Whisper en el atributo `lang` en lugar de dejar `lang="es"` fijo.

El análisis opcional de énfasis sigue usando energía y duración local de cada palabra respecto de sus vecinas. Es una heurística experimental separada de la probabilidad de reconocimiento.

### Traducción

`trans.py` acepta texto posicional, `-t/--text`, `-i/--input` o stdin. La salida traducida normal queda limpia en `stdout`.

Interfaz nueva:

```text
-s, --source-language LANG       origen; predeterminado auto
-l, --language LANG              destino
-d, --destination-language LANG  sinónimo de -l/--language
```

Si falta destino:

```text
LC_ALL -> LC_MESSAGES -> LANG
```

Las locales se normalizan antes de aplicar los alias:

```text
en_CA.UTF-8 -> en-ca
es_UY.UTF-8 -> es-uy
fr_FR.UTF-8 -> fr-fr
fr_CA.UTF-8 -> fr-ca
```

`C`, `POSIX`, `C.UTF-8`, etc. no son un idioma de destino útil; en esos casos hay que indicar `-l`.

Para perfiles conocidos, googletrans recibe la familia base:

```text
en-ca, en-us, en-gb, ... -> en
es-uy, es-es             -> es
fr-fr, fr-ca, fr-be, ... -> fr
```

Los demás idiomas de googletrans siguen disponibles. Por ejemplo, una locale `de_DE.UTF-8` se normaliza a `de-de` y el traductor puede caer al código `de` si ése es el que publica googletrans.

La sintaxis antigua `trans SRC DEST` se conserva por compatibilidad durante esta serie, pero los scripts nuevos deberían usar `-s` y `-l`.

El texto largo se corta en límites razonables. El bloque predeterminado es de 5000 caracteres y puede ajustarse con `--chunk-size` hasta 15000.

### Fonemización

`phonem.py` separa el **perfil lógico de estudio** de la voz eSpeak realmente instalada.

| Perfil | Alias | Objetivo | Backend típico |
|---|---|---|---|
| `en-ca` | `en` | inglés canadiense | `en-us` y fallbacks |
| `en-us` | — | inglés de EE. UU. | `en-us` |
| `en-gb` | — | inglés británico | `en-gb` |
| `en-rp` | — | Received Pronunciation | RP si existe; fallback británico |
| `en-lancashire` | — | Lancashire | regional si existe; fallback británico |
| `en-nyc` | — | Nueva York | NYC si existe; fallback estadounidense |
| `es-uy` | `es` | español uruguayo formal | `es-419`, luego `es-la` legado |
| `es-es` | — | español de España | `es`/`es-es` |
| `fr-fr` | `fr` | francés de Francia | `fr-fr`, luego `fr` |
| `fr-ca` | — | perfil de Quebec | aproximación |
| `fr-be` | — | francés belga | `fr-be` |
| `fr-ch` | — | francés suizo con `huitante` | `fr-ch` |
| `fr-ch-qv` | — | variante suiza con `quatre-vingts` | overlay sobre `fr-ch` |

La autodetección sólo pretende distinguir de forma conservadora inglés, español y francés:

```text
inglés   -> en -> en-ca
español  -> es -> es-uy
francés  -> fr -> fr-fr
```

#### Español uruguayo formal

`es-uy` sigue siendo un perfil de estudio, no una voz uruguaya nativa de eSpeak o Piper. Conserva seseo y `/s/` final, no agrega una transformación madrileña de `d` final, no simplifica grupos como `/kt/` y usa la realización objetivo `[ʃ]` para `y/ll` consonánticas mediante reglas IPA editables. El tratamiento contextual evita convertir indiscriminadamente la `y` vocálica/final en `[ʃ]`.

### Pronunciación

`pronounce.py` resuelve el perfil del proyecto hacia un modelo Piper configurado. Los perfiles acústicos son aproximaciones explícitas salvo donde exista validación empírica.

| Perfil(es) | Modelo Piper | `length_scale` | Volumen | Estado |
|---|---|---:|---:|---|
| `es-uy` / `es` | `es_AR-daniela-high` | 2.0 | 1.0 | aproximación probada por el usuario |
| `es-es` | `es_ES-davefx-medium` | 1.0 | 1.0 | punto de partida |
| `en-ca` / `en` | `en_US-lessac-high` | 1.0 | 1.0 | aproximación |
| `en-us`, `en-nyc` | `en_US-lessac-high` | 1.0 | 1.0 | punto de partida / aproximación |
| `en-gb`, `en-rp` | `en_GB-cori-high` | 1.0 | 1.0 | punto de partida / aproximación |
| `en-lancashire` | `en_GB-northern_english_male-medium` | 1.0 | 1.0 | aproximación |
| `fr-fr` / `fr` | `fr_FR-siwis-medium` | 1.0 | 1.0 | punto de partida |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | 1.0 | 1.0 | aproximación acústica |

Las pausas duras extra siguen disponibles con `--extra-pauses`, pero están desactivadas por defecto porque en las pruebas podían volver artificiales las terminaciones. El ritmo nativo de Piper es el predeterminado.

```bash
./pronounce.py --list-languages
./pronounce.py --list-catalog-languages
./pronounce.py --list-voices es
./pronounce.py --list-models es
```

### Perfiles de idioma

`language_profiles.py` concentra la normalización compartida para impedir que los cuatro programas diverjan con el tiempo.

```text
en -> en-ca
es -> es-uy
fr -> fr-fr
```

Un **perfil del proyecto** y un **idioma de backend** son cosas distintas:

| Entrada | Perfil canónico | googletrans/Whisper | Capa de pronunciación |
|---|---|---|---|
| `en` | `en-ca` | `en` | perfil canadiense / aproximación Piper |
| `es` | `es-uy` | `es` | overlay uruguayo / aproximación rioplatense Piper |
| `fr` | `fr-fr` | `fr` | perfil Francia / Piper Francia |

### Configuración

La configuración Piper queda por defecto en:

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

`pronounce.py 0.6.0` usa **schema 2**. El cambio elimina `en`, `es` y `fr` como perfiles JSON independientes: pasan a ser alias auténticos de `en-ca`, `es-uy` y `fr-fr`.

Al actualizar un JSON de schema 1:

```bash
./pronounce.py --update-config
```

se crea primero un backup con fecha, se migran las claves canónicas, se eliminan los duplicados de alias antiguos y se preservan los ajustes del perfil canónico y las claves personalizadas desconocidas.

Estados posibles:

```text
created
updated
unchanged
```

Plantilla limpia:

```bash
./pronounce.py --init-config
```

Voces predeterminadas únicas:

```bash
./pronounce.py --download-defaults
```

### Normalización de números

`phonem.py` expande cardinales enteros independientes antes de fonemizar en inglés, español y francés. El inglés moderno usa escala corta; español y francés, escala larga.

| Potencia | Español | Francés | Inglés moderno |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

Formas francesas 70/80/90:

| Perfil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

```bash
./phonem.py --number-table
```

Decimales, fechas, horas y estructuras claramente parecidas a teléfonos no se reinterpretan como una lista ordinaria de cardinales.

### Audio y modelos Piper

Las voces Piper son modelos ONNX independientes con su `.onnx.json`. Sus licencias no necesariamente coinciden con la GPL del proyecto y deben revisarse antes de redistribuir los modelos.

```bash
./pronounce.py "...IPA..." -l es --wav voz.wav
./pronounce.py "...IPA..." -l fr --ogg voz.ogg
./pronounce.py "...IPA..." -l en --mp3 voz.mp3
```

Sin formato de salida se usa `ffplay` para reproducir por el dispositivo normal.

## Licencia

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

El código del proyecto se distribuye bajo **GNU General Public License versión 2 o, a elección del usuario, cualquier versión posterior** (`GPL-2.0-or-later`). Véase `COPYING` / `LICENSE`.

Los modelos y dependencias externas conservan sus propias licencias.

## Fuentes

- eSpeak NG: <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- phonemizer: <https://github.com/bootphon/phonemizer>
- Piper / OHF Voice: <https://github.com/OHF-Voice/piper1-gpl>
- Catálogo de voces Piper: <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- googletrans: <https://github.com/ssut/py-googletrans>
- faster-whisper: <https://github.com/SYSTRAN/faster-whisper>
- FFmpeg / ffplay: <https://ffmpeg.org/>
- RAE/ASALE, *números*: <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *y*: <https://www.rae.es/dpd/y>
- RAE/ASALE, *yeísmo*: <https://www.rae.es/dpd/ye%C3%ADsmo>
- Office québécois de la langue française: <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library: <https://commonslibrary.parliament.uk/research-briefings/sn04440/>

---

# Français

## Projet

Petit ensemble d'outils Unix d'étude linguistique sous GPL-2.0-or-later. Chaque programme réalise une transformation principale; les données normales vont sur `stdout` et les diagnostics opérationnels sur `stderr`.

| Outil | Entrée | Sortie principale | Fonction |
|---|---|---|---|
| `transcribe.py` | audio | texte | reconnaissance locale avec faster-whisper |
| `trans.py` | texte | texte traduit | traduction asynchrone avec googletrans |
| `phonem.py` | texte | API | phonémisation et profils d'étude |
| `pronounce.py` | API | audio | synthèse vocale Piper |

Chaîne complète :

```text
audio -> transcribe.py -> texte -> trans.py -> texte traduit
      -> phonem.py -> IPA -> pronounce.py -> audio
```

Les noms sans extension (`transcribe`, `trans`, `phonem`, `pronounce`) sont des liens vers les noms stables `.py`.

### Convention commune des langues

Tous les outils utilisent la même option pour leur **langue principale** :

```text
-l LANG
--language LANG
```

Les codes courts sont de vrais alias :

| Alias | Profil canonique |
|---|---|
| `en` | `en-ca` |
| `es` | `es-uy` |
| `fr` | `fr-fr` |

Ainsi `-l fr` et `-l fr-fr` désignent exactement le même profil du projet. Chaque moteur reçoit ensuite le code qu'il comprend réellement.

## Démarrage rapide

Transcrire :

```bash
./transcribe.py enregistrement.mp3 -l auto
```

Traduire :

```bash
./trans.py -s en -l fr "Hello world"
```

Obtenir l'API; `phonem.py` détecte EN/ES/FR par défaut :

```bash
./phonem.py "Bonjour tout le monde."
./phonem.py "La casa es azul." -l es
```

Prononcer :

```bash
./phonem.py "Bonjour tout le monde." -l fr | ./pronounce.py -l fr
```

## Outils

### transcribe.py

Audio local -> texte avec faster-whisper. Les formats existants et l'analyse d'emphase restent disponibles; `-l` et `--language` sont maintenant équivalents et utilisent les profils communs.

```bash
./transcribe.py entretien.mp3 -l auto
./transcribe.py entretien.mp3 -l fr --format srt -o entretien.srt
```

### trans.py

Texte -> texte traduit. Interface recommandée :

```bash
./trans.py -s en -l fr "Hello world"
echo "Hola" | ./trans.py -s es -l fr
```

`-s/--source-language` vaut `auto` par défaut. Sans `-l/--language`, la destination est déduite de `LC_ALL`, puis `LC_MESSAGES`, puis `LANG`.

```bash
LANG=en_CA.UTF-8 ./trans.py -s fr "Bonjour"
```

résout `en_CA.UTF-8 -> en-ca`; googletrans reçoit `en`.

L'ancienne syntaxe reste compatible :

```bash
./trans.py en fr "Hello world"
```

Les séquences ANSI/ECMA-48 sont supprimées par défaut avant traduction.

### phonem.py

Texte -> API via phonemizer/eSpeak NG. La détection automatique est le comportement par défaut :

```bash
./phonem.py "Hello, how are you?"      # en -> en-ca
./phonem.py "¿Cómo estás?"             # es -> es-uy
./phonem.py "Bonjour, comment ça va ?" # fr -> fr-fr
```

En cas d'ambiguïté, il demande explicitement `-l/--language`.

### pronounce.py

API -> audio via Piper. L'API seul ne suffit pas à déduire de façon fiable le profil acoustique souhaité, donc aucune détection textuelle n'est tentée ici.

```bash
./phonem.py "Bonjour" -l fr | ./pronounce.py -l fr
./pronounce.py "bɔ̃ʒuʁ" -l fr --wav bonjour.wav
```

## Installation

Cible principale : GNU/Linux/POSIX, Python 3.9 ou plus récent.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Dépendances Python :

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
faster-whisper>=1,<2
numpy>=1.24,<3
```

Configuration Piper :

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

## Pipelines complets

Audio -> texte :

```bash
./transcribe.py audio.mp3 -l auto -q
```

Audio -> traduction :

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l fr
```

Audio -> traduction -> API :

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l fr | \
    ./phonem.py -l fr
```

Boucle complète :

```bash
./transcribe.py audio.mp3 -l auto -q | \
    ./trans.py -s auto -l fr | \
    ./phonem.py -l fr | \
    ./pronounce.py -l fr
```

## Référence détaillée

### Transcription

`transcribe.py 2.2.0` conserve les fonctions de 2.1.1 et adopte :

```text
-l LANG == --language LANG
```

Pour continuité, la valeur par défaut reste `es`, désormais alias de `es-uy`; Whisper reçoit `es`. Utilisez `-l auto` pour la détection.

```text
en-ca -> en
es-uy -> es
fr-ca -> fr
```

Formats conservés :

```text
text, markdown, srt, vtt, json, html
```

```bash
./transcribe.py audio.mp3 -l auto
./transcribe.py audio.mp3 -l fr-ca --format srt -o audio.srt
./transcribe.py audio.mp3 -l es --format markdown --emphasis -o audio.md
```

Le JSON contient le profil demandé normalisé et la langue signalée par Whisper. Le document HTML utilise maintenant la langue Whisper dans son attribut `lang`.

### Traduction

`trans.py` accepte du texte positionnel, `-t/--text`, `-i/--input` ou stdin. La traduction normale reste propre sur `stdout`.

```text
-s, --source-language LANG       source; auto par défaut
-l, --language LANG              destination
-d, --destination-language LANG  synonyme de -l/--language
```

Destination absente :

```text
LC_ALL -> LC_MESSAGES -> LANG
```

Normalisation des locales :

```text
en_CA.UTF-8 -> en-ca
es_UY.UTF-8 -> es-uy
fr_FR.UTF-8 -> fr-fr
fr_CA.UTF-8 -> fr-ca
```

`C` et `POSIX` ne sont pas considérés comme des langues de destination utilisables.

Les profils connus deviennent leur famille pour googletrans :

```text
en-* -> en
es-* -> es
fr-* -> fr
```

Les autres langues googletrans restent disponibles; une locale comme `de_DE.UTF-8` essaie la forme normalisée puis la famille `de`.

L'ancienne forme `trans SRC DEST` reste compatible, mais `-s`/`-l` est l'interface recommandée.

### Phonémisation

`phonem.py` sépare le profil logique d'étude de la voix eSpeak installée.

| Profil | Alias | Cible | Backend typique |
|---|---|---|---|
| `en-ca` | `en` | anglais canadien | `en-us` et replis |
| `en-us` | — | anglais US | `en-us` |
| `en-gb` | — | anglais britannique | `en-gb` |
| `en-rp` | — | Received Pronunciation | RP si disponible |
| `en-lancashire` | — | Lancashire | régional si disponible |
| `en-nyc` | — | New York | NYC si disponible |
| `es-uy` | `es` | espagnol uruguayen formel | `es-419`, puis `es-la` ancien |
| `es-es` | — | Espagne | `es`/`es-es` |
| `fr-fr` | `fr` | France | `fr-fr`, puis `fr` |
| `fr-ca` | — | Québec | approximation |
| `fr-be` | — | Belgique | `fr-be` |
| `fr-ch` | — | Suisse avec `huitante` | `fr-ch` |
| `fr-ch-qv` | — | Suisse avec `quatre-vingts` | overlay `fr-ch` |

Détection automatique :

```text
anglais  -> en -> en-ca
espagnol -> es -> es-uy
français -> fr -> fr-fr
```

#### Profil uruguayen formel

`es-uy` reste un profil d'étude. Il conserve le seseo et `/s/` final, n'ajoute pas de transformation madrilène du `d` final, ne simplifie pas `/kt/` et applique la cible `[ʃ]` aux `y/ll` consonantiques avec des règles API modifiables.

### Prononciation

`pronounce.py` résout le profil vers un modèle Piper configuré.

| Profil(s) | Modèle Piper | Longueur | Volume | État |
|---|---|---:|---:|---|
| `es-uy` / `es` | `es_AR-daniela-high` | 2.0 | 1.0 | approximation testée par l'utilisateur |
| `es-es` | `es_ES-davefx-medium` | 1.0 | 1.0 | point de départ |
| `en-ca` / `en` | `en_US-lessac-high` | 1.0 | 1.0 | approximation |
| `en-us`, `en-nyc` | `en_US-lessac-high` | 1.0 | 1.0 | départ / approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | 1.0 | 1.0 | départ / approximation |
| `en-lancashire` | `en_GB-northern_english_male-medium` | 1.0 | 1.0 | approximation |
| `fr-fr` / `fr` | `fr_FR-siwis-medium` | 1.0 | 1.0 | point de départ |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | 1.0 | 1.0 | approximation acoustique |

Les pauses dures supplémentaires restent disponibles avec `--extra-pauses`, mais Piper seul gère le rythme par défaut.

### Profils linguistiques

`language_profiles.py` centralise les règles communes :

```text
en -> en-ca
es -> es-uy
fr -> fr-fr
```

| Entrée | Profil canonique | googletrans/Whisper | Couche de prononciation |
|---|---|---|---|
| `en` | `en-ca` | `en` | profil canadien / approximation Piper |
| `es` | `es-uy` | `es` | overlay uruguayen / approximation rioplatense Piper |
| `fr` | `fr-fr` | `fr` | profil France / Piper France |

### Configuration

Configuration Piper :

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

Le schéma 2 de `pronounce.py 0.6.0` transforme `en`, `es` et `fr` en vrais alias au lieu de profils JSON séparés. Une mise à jour depuis le schéma 1 crée d'abord une sauvegarde, migre les entrées canoniques, supprime les doublons d'alias devenus obsolètes et conserve les réglages canoniques/personnalisés.

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
```

### Normalisation des nombres

L'anglais moderne utilise ici l'échelle courte; le français et l'espagnol l'échelle longue.

| Puissance | Espagnol | Français | Anglais moderne |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

| Profil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

```bash
./phonem.py --number-table
```

### Audio et modèles Piper

Les voix Piper sont des modèles ONNX avec leur `.onnx.json`. Leurs licences sont indépendantes de celle du projet.

```bash
./pronounce.py "...IPA..." -l es --wav voix.wav
./pronounce.py "...IPA..." -l fr --ogg voix.ogg
./pronounce.py "...IPA..." -l en --mp3 voix.mp3
```

Sans fichier de sortie, `ffplay` assure la lecture normale.

## Licence

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Le code du projet est distribué sous la **GNU General Public License version 2 ou, à votre choix, toute version ultérieure** (`GPL-2.0-or-later`). Voir `COPYING` / `LICENSE`.

Les modèles et dépendances externes conservent leurs propres licences.

## Sources

- eSpeak NG : <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- phonemizer : <https://github.com/bootphon/phonemizer>
- Piper / OHF Voice : <https://github.com/OHF-Voice/piper1-gpl>
- Catalogue Piper : <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- googletrans : <https://github.com/ssut/py-googletrans>
- faster-whisper : <https://github.com/SYSTRAN/faster-whisper>
- FFmpeg / ffplay : <https://ffmpeg.org/>
- RAE/ASALE : <https://www.rae.es/dpd/n%C3%BAmeros>
- Office québécois de la langue française : <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library : <https://commonslibrary.parliament.uk/research-briefings/sn04440/>

---

<p align="center"><b>- oOo -</b></p>

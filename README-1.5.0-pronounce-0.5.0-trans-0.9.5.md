# phonem.py 1.5.0 / pronounce.py 0.5.0 / trans.py 0.9.5

## Languages

- [English](#english)
- [Español](#español)
- [Français](#français)

---

<a id="english"></a>
# English

## Project

This is a small GPL-2.0-or-later Unix-style language study toolkit. The three programs are deliberately separate and composable:

```text
text ── trans.py ──> translated text ── phonem.py ──> IPA ── pronounce.py ──> audio
```

| Tool | Input | Output | Purpose |
|---|---|---|---|
| `trans.py` | text | translated text | translation through `googletrans` |
| `phonem.py` | text | IPA | phonemization and study-profile normalization |
| `pronounce.py` | IPA | audio | Piper synthesis and audio export/playback |

The toolkit currently concentrates on English, French and Spanish study profiles, with explicit approximations when upstream engines do not provide a native dialect voice.

## Quick start

```bash
# Translate
./trans.py en es "Hello world"

# Text -> IPA
./phonem.py "La casa de ella" -l es-uy

# Text -> IPA -> speech
./phonem.py "La casa de ella" -l es-uy | ./pronounce.py -l es-uy
```

After a fresh install, initialize/update the local pronunciation configuration and download the unique default voice models:

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
```

## Tools

### `trans.py`

Translates UTF-8 text while keeping normal output clean on `stdout` for Unix pipelines. ANSI/ECMA-48 terminal escape sequences are removed by default before translation.

```bash
./trans.py en es "Hello world"
echo "Hello world" | ./trans.py en es
```

Use `--keep-ansi` only when raw terminal control sequences must be preserved. See [Translation](#english-translation) for the full reference.

### `phonem.py`

Converts text to IPA through `phonemizer`/eSpeak NG, with logical language profiles and number normalization before phonemization.

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr
./phonem.py "La casa de ella." -l es-uy
```

Punctuation is preserved by default so it can continue down the speech pipeline. See [Phonemization](#english-phonemization).

### `pronounce.py`

Consumes IPA and renders it with a selected Piper voice. A language profile can supply the default voice and timing settings.

```bash
./phonem.py "La casa de ella." -l es-uy | ./pronounce.py -l es-uy
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --wav bonjour.wav
```

See [Pronunciation](#english-pronunciation).

## Installation

The primary target is a GNU/Linux/POSIX command-line environment. Python 3.9 or newer is required by the complete toolchain.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --check
```

Python dependencies shipped in `requirements.txt`:

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
```

`ffplay` is normally supplied by FFmpeg and is used for default-device playback. CUDA is optional and additionally requires `onnxruntime-gpu`.

## Complete pipelines

Translate Spanish to French, generate French IPA, then speak it:

```bash
./trans.py es fr "La casa es azul." | \
    ./phonem.py -l fr-fr | \
    ./pronounce.py -l fr-fr
```

Translate a file and keep the translated text:

```bash
./trans.py auto en -i notes.txt > notes-en.txt
```

Generate IPA into a file and synthesize it later:

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr > phrase.ipa
./pronounce.py -l fr-fr -i phrase.ipa --wav phrase.wav
```

The empirically tuned Uruguayan profile is intentionally short to invoke:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

## Detailed reference

<a id="english-translation"></a>
### Translation

`trans.py` 0.9.5 retains the old `SRC DEST` interface and also accepts positional text, `-t/--text`, `-i/--input`, or standard input. The package includes `trans -> trans.py` for compatibility with the old command name.

```bash
./trans.py en es "Hello world"
./trans.py en es -t "Hello world"
echo "Hello world" | ./trans.py en es
./trans.py auto fr -i notes.txt
```

Terminal escape sequences are stripped before translation by default. This prevents colored command output from leaking control codes into translated text:

```bash
ls --color=always -1 | ./trans.py en es
```

`--keep-ansi` disables that filter. If source and destination codes are identical, translation is bypassed but ANSI filtering still occurs, so the program can also act as a simple cleanup filter:

```bash
ls --color=always -1 | ./trans.py en en
```

Long text is split at useful boundaries into chunks of 5000 characters by default. `--chunk-size` can change this value up to 15000. One asynchronous `Translator` session is reused for all chunks.

`googletrans` uses Google's unofficial web translation interface. Service/network failures are therefore reported as ordinary runtime errors rather than hidden behind an unrelated fallback.

```bash
./trans.py --list-languages
./trans.py --version
./trans.py -v en fr "Text"
```

<a id="english-phonemization"></a>
### Phonemization

`phonem.py` accepts text as a positional argument, with `-t/--text`, from `-i/--input`, or from standard input. Normal IPA goes to `stdout`; diagnostics from `-v` go to `stderr`.

```bash
./phonem.py "1 2 3" -l fr-fr
./phonem.py -t "1 2 3" -l en-ca
cat phrases.txt | ./phonem.py -l es-uy
```

Punctuation is preserved by default. Use `--strip-punctuation` only when punctuation-free IPA is specifically required. `-p/--preserve-punctuation` remains accepted for explicit/backward-compatible scripts.

Automatic detection distinguishes English, French and Spanish conservatively. Its default study targets are:

```text
English -> en-ca
French  -> fr-ca
Spanish -> es-uy
```

Ambiguous or very short input should be given an explicit `-l` rather than relying on a guess.

Study assumptions remain exportable and editable:

```bash
./phonem.py --export-exceptions phonem-exceptions.json
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

The exceptions JSON contains backend candidates, number profiles/scales, text replacements, literal IPA replacements and contextual IPA regex replacements.

<a id="english-pronunciation"></a>
### Pronunciation

`pronounce.py` accepts IPA as a positional argument, from `-i/--input`, or from standard input. With no output option it plays through `ffplay`; it can also export WAV, OGG or MP3.

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --mp3 bonjour.mp3
```

Voice/model resolution follows this practical order: explicit `--model`, explicit `--voice`, configured legacy voice, configured profile voice, then configured default voice.

Synthesis settings follow `CLI > JSON profile > built-in profile`. `length_scale`, volume and pause mode can therefore be tuned in JSON and overridden temporarily on the command line.

All built-in profiles currently use Piper's own timing by default. The optional deterministic post-synthesis pause experiment is available with `--extra-pauses`, but it is not enabled by default because hard inserted silence was found to make word endings sound unnatural in listening tests.

The optional extra-pause defaults are:

| Boundary | Extra silence | Option |
|---|---:|---|
| word space | 0.04 s | `--word-pause` |
| comma `,` | 0.16 s | `--comma-pause` |
| colon/semicolon `:` `;` | 0.24 s | `--clause-pause` |
| period/question/exclamation `.?!` | 0.40 s | `--sentence-pause` |

`--no-extra-pauses` explicitly forces Piper-only timing.

<a id="english-language-profiles"></a>
### Language profiles

A logical study profile is not necessarily a native eSpeak or Piper voice. The program keeps those layers visible rather than pretending an approximation is native.

#### Phonemization profiles

| Profile | Intended study variety | Preferred eSpeak backend | Status |
|---|---|---|---|
| `en-us` | US English | `en-us` | direct when installed |
| `en-ca` | Canadian English | `en-us`, then fallbacks | approximation |
| `en-gb` | British English | `en-gb`, then fallbacks | direct/fallback |
| `en-rp` | Received Pronunciation | `en-gb-x-rp` | direct when installed |
| `en-lancashire` | Lancashire | `en-gb-x-gbclan` | direct when installed |
| `en-nyc` | New York City English | `en-us-nyc` | direct when installed |
| `fr-fr` | France | `fr-fr`, then `fr` | direct/fallback |
| `fr-ca` | Quebec study profile | `fr-be`, then France fallbacks | approximation |
| `fr-be` | Belgium | `fr-be` | direct when installed |
| `fr-ch` | Swiss French, `huitante` profile | `fr-ch` | study profile |
| `fr-ch-qv` | Swiss French, `quatre-vingts` profile | `fr-ch` | study overlay |
| `es-es` | Spain | `es` | Spain Spanish profile |
| `es-uy` | formal Uruguayan Spanish | `es-419`, then legacy `es-la` | approximation + IPA overlay |

#### Default Piper voices

| Logical profile(s) | Default model | Timing | Status |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, Piper timing | user-tested |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, Piper timing | starting point |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, Piper timing | starting point |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, Piper timing | approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, Piper timing | RP remains approximate |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, Piper timing | regional approximation |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, Piper timing | starting point |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, Piper timing | acoustic approximation |

The `es-uy` profile is the first acoustic profile calibrated by listening in this project. It uses Daniela as the closest available Rioplatense Piper target, but it remains an Argentine acoustic model, not a native `es_UY` voice.

For careful/formal Uruguayan Spanish, the IPA layer keeps seseo, retains final `/s/`, does not simplify `ct`, does not impose a Madrid-style final-`d` substitution, and maps consonantal `y`/`ll` toward the selected voiceless rehilated `[ʃ]` target. Vocalic `y` is not globally replaced.

<a id="english-configuration"></a>
### Configuration

#### `phonem.py`

Export the current study assumptions:

```bash
./phonem.py --export-exceptions phonem-exceptions.json
```

Reuse an edited copy:

```bash
./phonem.py --exceptions phonem-exceptions.json "lluvia y yo" -l es-uy
```

#### `pronounce.py`

The default configuration path is:

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

Create a clean configuration:

```bash
./pronounce.py --init-config
```

For upgrades, use the conservative merge command:

```bash
./pronounce.py --update-config
```

If the JSON does not exist it is created. If fields/profiles are missing, the existing file is backed up with a timestamp and new defaults are merged underneath user values. Existing custom values and unknown keys are preserved. If nothing changes, the command reports `status=unchanged` and does not create another backup.

A different configuration can be updated explicitly:

```bash
./pronounce.py --config ./my-pronounce.json --update-config
```

The file records `schema_version` and `generated_by` for future migrations.

<a id="english-number-normalization"></a>
### Number normalization

Integer tokens are expanded before phonemization when lexical form matters. Spanish and French use long-scale names; modern US, Canadian and British English use the short scale.

| Power | Spanish | French | Modern English |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

French 70/80/90 study profiles:

| Profile | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

The normalizer deliberately leaves structured values such as decimals, dates, times and clearly formatted phone numbers alone:

```text
3.14
2026-08-19
17:30
514 555-1234
```

Generate the current comparison directly from program logic:

```bash
./phonem.py --number-table
```

<a id="english-audio-models"></a>
### Audio and Piper models

Useful inventory commands:

```bash
./pronounce.py --list-profiles
./pronounce.py --list-catalog-languages
./pronounce.py --list-voices es-uy
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

Terminology used by the project:

- **logical profile**: study target such as `es-uy` or `fr-ca`;
- **Piper catalogue locale**: published acoustic locale such as `es_AR`, `es_ES`, `fr_FR`;
- **voice**: speaker/dataset name such as `daniela`;
- **voice model**: concrete ONNX quality variant such as `es_AR-daniela-high`;
- **installed model**: an `.onnx` file actually present in a configured data directory.

Install a single voice:

```bash
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
```

Install all effective profile defaults without duplicates:

```bash
./pronounce.py --download-defaults
```

The current configuration resolves to six unique default models:

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

Already installed models are skipped. `--force-download` deliberately downloads them again. `--auto-download` can be used when a selected catalogue voice should be fetched automatically.

Piper voices consist of an `.onnx` file and a matching `.onnx.json`. Voice/model licences may differ from this project's licence; check each voice's `MODEL_CARD` before redistributing it.

## License

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

This project is distributed under the **GNU General Public License, version 2 or (at your option) any later version** (`GPL-2.0-or-later`). See `COPYING`.

## Sources

- eSpeak NG language list: <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **números**: <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **y**: <https://www.rae.es/dpd/y>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **yeísmo**: <https://www.rae.es/dpd/ye%C3%ADsmo>
- RAE/ASALE, *Diccionario de la lengua española*, **billón**: <https://dle.rae.es/bill%C3%B3n>
- RAE/ASALE, *Diccionario de la lengua española*, **trillón**: <https://dle.rae.es/trill%C3%B3n>
- Office québécois de la langue française, **Écriture des grands nombres**: <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library, **What is a billion? And other large numbers**: <https://commonslibrary.parliament.uk/research-briefings/sn04440/>
- US NIST, **Metric (SI) Prefixes**: <https://www.nist.gov/pml/owm/metric-si-prefixes>
- Piper CLI: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md>
- Piper voices/models: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
- Piper voice catalogue: <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- Piper project: <https://github.com/OHF-Voice/piper1-gpl>
- PyPI `piper-tts`: <https://pypi.org/project/piper-tts/>
- Phonemizer: <https://github.com/bootphon/phonemizer>
- googletrans: <https://github.com/ssut/py-googletrans>
- FFmpeg / ffplay: <https://ffmpeg.org/>

---

<a id="español"></a>
# Español

## Proyecto

Este es un pequeño conjunto de herramientas Unix de estudio lingüístico, distribuido bajo GPL-2.0-or-later. Los tres programas se mantienen separados para poder combinarlos mediante pipes:

```text
texto ── trans.py ──> texto traducido ── phonem.py ──> IPA ── pronounce.py ──> audio
```

| Herramienta | Entrada | Salida | Función |
|---|---|---|---|
| `trans.py` | texto | texto traducido | traducción con `googletrans` |
| `phonem.py` | texto | IPA | fonemización y normalización de perfiles de estudio |
| `pronounce.py` | IPA | audio | síntesis Piper y reproducción/exportación |

El proyecto se concentra actualmente en perfiles del inglés, francés y español, marcando explícitamente las aproximaciones cuando los motores upstream no ofrecen una voz dialectal nativa.

## Inicio rápido

```bash
# Traducir
./trans.py en es "Hello world"

# Texto -> IPA
./phonem.py "La casa de ella" -l es-uy

# Texto -> IPA -> voz
./phonem.py "La casa de ella" -l es-uy | ./pronounce.py -l es-uy
```

Después de una instalación nueva:

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
```

## Herramientas

### `trans.py`

Traduce texto UTF-8 y deja la traducción limpia en `stdout`, lista para encadenarla con otros comandos. Por defecto elimina secuencias ANSI/ECMA-48 antes de enviar el texto al traductor.

```bash
./trans.py en es "Hello world"
echo "Hello world" | ./trans.py en es
```

`--keep-ansi` conserva explícitamente esas secuencias. Véase [Traducción](#es-translation).

### `phonem.py`

Convierte texto a IPA mediante `phonemizer`/eSpeak NG y aplica perfiles lógicos de idioma y normalización de números antes de fonemizar.

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr
./phonem.py "La casa de ella." -l es-uy
```

La puntuación se conserva por defecto para que pueda seguir aportando información al pipeline de audio. Véase [Fonemización](#es-phonemization).

### `pronounce.py`

Recibe IPA y lo sintetiza con una voz Piper. El perfil lógico puede proporcionar la voz y los parámetros de ritmo predeterminados.

```bash
./phonem.py "La casa de ella." -l es-uy | ./pronounce.py -l es-uy
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --wav bonjour.wav
```

Véase [Pronunciación](#es-pronunciation).

## Instalación

El objetivo principal es GNU/Linux/POSIX. El conjunto completo requiere Python 3.9 o posterior.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --check
```

Dependencias Python de `requirements.txt`:

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
```

`ffplay`, normalmente incluido con FFmpeg, reproduce por el dispositivo predeterminado. CUDA es opcional y necesita además `onnxruntime-gpu`.

## Pipelines completos

Traducir español a francés, generar IPA francés y reproducirlo:

```bash
./trans.py es fr "La casa es azul." | \
    ./phonem.py -l fr-fr | \
    ./pronounce.py -l fr-fr
```

Traducir un archivo:

```bash
./trans.py auto en -i notas.txt > notas-en.txt
```

Guardar IPA y sintetizarlo después:

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr > frase.ipa
./pronounce.py -l fr-fr -i frase.ipa --wav frase.wav
```

El perfil uruguayo calibrado queda deliberadamente simple:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

## Referencia detallada

<a id="es-translation"></a>
### Traducción

`trans.py` 0.9.5 conserva la interfaz histórica `SRC DEST` y además acepta texto posicional, `-t/--text`, `-i/--input` o stdin. El paquete incluye `trans -> trans.py` para mantener el nombre viejo.

```bash
./trans.py en es "Hello world"
./trans.py en es -t "Hello world"
echo "Hello world" | ./trans.py en es
./trans.py auto fr -i notas.txt
```

Las secuencias de control del terminal se filtran antes de traducir por defecto:

```bash
ls --color=always -1 | ./trans.py en es
```

`--keep-ansi` desactiva ese filtro. Si el idioma de origen y el de destino son iguales, se evita la petición de traducción pero se conserva el filtrado ANSI, de modo que también puede usarse como limpiador:

```bash
ls --color=always -1 | ./trans.py en en
```

Los textos largos se dividen en límites razonables, con bloques de 5000 caracteres por defecto. `--chunk-size` permite modificarlo hasta 15000. Se reutiliza una única sesión asíncrona de `Translator`.

`googletrans` usa la interfaz web no oficial de Google. Por eso un fallo de red o del servicio se informa como error normal de ejecución; el programa no inventa un fallback de traducción.

```bash
./trans.py --list-languages
./trans.py --version
./trans.py -v en fr "Texto"
```

<a id="es-phonemization"></a>
### Fonemización

`phonem.py` acepta texto posicional, `-t/--text`, `-i/--input` o stdin. El IPA normal va por `stdout`; `-v` escribe los diagnósticos por `stderr`.

```bash
./phonem.py "1 2 3" -l fr-fr
./phonem.py -t "1 2 3" -l en-ca
cat frases.txt | ./phonem.py -l es-uy
```

La puntuación se conserva por defecto. `--strip-punctuation` la elimina cuando se necesita IPA sin signos; `-p/--preserve-punctuation` sigue aceptándose para scripts explícitos o anteriores.

La detección automática distingue de forma conservadora inglés, francés y español, con estos perfiles de estudio predeterminados:

```text
Inglés  -> en-ca
Francés -> fr-ca
Español -> es-uy
```

Para entradas muy cortas o ambiguas conviene indicar `-l`.

Las decisiones del perfil pueden exportarse y editarse:

```bash
./phonem.py --export-exceptions phonem-exceptions.json
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

El JSON contiene backends candidatos, perfiles/escalas numéricas, reemplazos de texto, reemplazos IPA literales y reglas IPA contextuales mediante expresiones regulares.

<a id="es-pronunciation"></a>
### Pronunciación

`pronounce.py` acepta IPA posicional, desde `-i/--input` o por stdin. Sin opción de salida reproduce mediante `ffplay`; también escribe WAV, OGG o MP3.

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --mp3 bonjour.mp3
```

La resolución práctica del modelo prioriza: `--model`, `--voice`, voz legacy configurada, voz del perfil y finalmente voz predeterminada global.

Los parámetros de síntesis siguen `CLI > perfil JSON > perfil interno`. Así, `length_scale`, volumen y pausas pueden quedar guardados en el JSON y sobreescribirse temporalmente en línea de comandos.

Todos los perfiles internos usan por defecto el ritmo propio de Piper. El experimento de silencios deterministas post-síntesis sigue disponible mediante `--extra-pauses`, pero no es el valor predeterminado porque las pruebas auditivas mostraron que el silencio duro añadido podía deformar las terminaciones de las palabras.

Valores disponibles para pausas extra:

| Límite | Silencio extra | Opción |
|---|---:|---|
| espacio entre palabras | 0.04 s | `--word-pause` |
| coma `,` | 0.16 s | `--comma-pause` |
| dos puntos/punto y coma `:` `;` | 0.24 s | `--clause-pause` |
| punto/interrogación/exclamación `.?!` | 0.40 s | `--sentence-pause` |

`--no-extra-pauses` fuerza explícitamente el ritmo puro de Piper.

<a id="es-language-profiles"></a>
### Perfiles de idioma

Un perfil lógico de estudio no equivale necesariamente a una voz nativa de eSpeak o Piper. Cuando se usa una aproximación, el proyecto la presenta como tal.

#### Perfiles de fonemización

| Perfil | Variante de estudio | Backend eSpeak preferido | Estado |
|---|---|---|---|
| `en-us` | inglés de EE. UU. | `en-us` | directo si está instalado |
| `en-ca` | inglés canadiense | `en-us`, luego fallbacks | aproximación |
| `en-gb` | inglés británico | `en-gb`, luego fallbacks | directo/fallback |
| `en-rp` | Received Pronunciation | `en-gb-x-rp` | directo si está instalado |
| `en-lancashire` | Lancashire | `en-gb-x-gbclan` | directo si está instalado |
| `en-nyc` | Nueva York | `en-us-nyc` | directo si está instalado |
| `fr-fr` | Francia | `fr-fr`, luego `fr` | directo/fallback |
| `fr-ca` | perfil Quebec | `fr-be`, luego Francia | aproximación |
| `fr-be` | Bélgica | `fr-be` | directo si está instalado |
| `fr-ch` | Suiza, perfil `huitante` | `fr-ch` | perfil de estudio |
| `fr-ch-qv` | Suiza, `quatre-vingts` | `fr-ch` | overlay de estudio |
| `es-es` | España | `es` | perfil España |
| `es-uy` | español uruguayo formal | `es-419`, luego `es-la` legado | aproximación + overlay IPA |

#### Voces Piper predeterminadas

| Perfil(es) | Modelo | Ritmo | Estado |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, ritmo Piper | probado por el usuario |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, ritmo Piper | punto de partida |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, ritmo Piper | punto de partida |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, ritmo Piper | aproximación |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, ritmo Piper | RP sigue aproximado |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, ritmo Piper | aproximación regional |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, ritmo Piper | punto de partida |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, ritmo Piper | aproximación acústica |

`es-uy` es el primer perfil acústico calibrado por escucha en este proyecto. Usa Daniela como la aproximación rioplatense Piper disponible más cercana, pero sigue siendo un modelo acústico argentino, no una voz nativa `es_UY`.

En el nivel IPA, el perfil uruguayo formal mantiene el seseo, conserva `/s/` final, no simplifica `ct`, no impone una sustitución madrileña de `d` final y lleva la `y`/`ll` consonántica hacia el objetivo rehilado sordo `[ʃ]`. La `y` vocálica no se sustituye globalmente.

<a id="es-configuration"></a>
### Configuración

#### `phonem.py`

Exportar las decisiones de estudio actuales:

```bash
./phonem.py --export-exceptions phonem-exceptions.json
```

Usar una copia editada:

```bash
./phonem.py --exceptions phonem-exceptions.json "lluvia y yo" -l es-uy
```

#### `pronounce.py`

La ruta predeterminada es:

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

Crear un archivo limpio:

```bash
./pronounce.py --init-config
```

Para actualizaciones conviene la mezcla conservadora:

```bash
./pronounce.py --update-config
```

Si no existe, el JSON se crea. Si faltan claves o perfiles, se hace primero un backup con fecha y los nuevos defaults se agregan por debajo de los valores existentes. Los ajustes del usuario y las claves desconocidas se conservan. Si no hay cambios, informa `status=unchanged` y no crea otro backup.

También puede actualizarse un archivo explícito:

```bash
./pronounce.py --config ./mi-pronounce.json --update-config
```

El JSON guarda `schema_version` y `generated_by` para futuras migraciones.

<a id="es-number-normalization"></a>
### Normalización de números

Los enteros se expanden antes de fonemizar cuando la forma léxica importa. Español y francés usan escala larga; el inglés moderno de EE. UU., Canadá y Reino Unido usa escala corta.

| Potencia | Español | Francés | Inglés moderno |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

Perfiles franceses 70/80/90:

| Perfil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

El normalizador no intenta adivinar todos los contextos numéricos. Decimales, fechas, horas y teléfonos claramente formateados se mantienen:

```text
3.14
2026-08-19
17:30
514 555-1234
```

La comparación puede generarse desde el mismo código que hace la normalización:

```bash
./phonem.py --number-table
```

<a id="es-audio-models"></a>
### Audio y modelos Piper

Comandos de inventario:

```bash
./pronounce.py --list-profiles
./pronounce.py --list-catalog-languages
./pronounce.py --list-voices es-uy
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

Terminología del proyecto:

- **perfil lógico**: objetivo de estudio, por ejemplo `es-uy` o `fr-ca`;
- **locale del catálogo Piper**: variante acústica publicada, por ejemplo `es_AR`, `es_ES`, `fr_FR`;
- **voz**: hablante/dataset, por ejemplo `daniela`;
- **modelo de voz**: variante ONNX concreta, por ejemplo `es_AR-daniela-high`;
- **modelo instalado**: `.onnx` realmente presente en un directorio configurado.

Instalar una voz:

```bash
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
```

Instalar todos los defaults efectivos sin repetir modelos compartidos:

```bash
./pronounce.py --download-defaults
```

La configuración actual resuelve seis modelos únicos:

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

Los modelos ya instalados se omiten. `--force-download` fuerza una nueva descarga y `--auto-download` permite descargar automáticamente una voz seleccionada del catálogo.

Cada voz Piper necesita su `.onnx` y su `.onnx.json`. Las licencias de las voces pueden ser distintas de la licencia del proyecto; antes de redistribuir una voz conviene revisar su `MODEL_CARD`.

## Licencia

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Este proyecto se distribuye bajo **GNU General Public License versión 2 o, a elección del usuario, cualquier versión posterior** (`GPL-2.0-or-later`). Véase `COPYING`.

## Fuentes

- Lista de idiomas eSpeak NG: <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **números**: <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **y**: <https://www.rae.es/dpd/y>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **yeísmo**: <https://www.rae.es/dpd/ye%C3%ADsmo>
- RAE/ASALE, *Diccionario de la lengua española*, **billón**: <https://dle.rae.es/bill%C3%B3n>
- RAE/ASALE, *Diccionario de la lengua española*, **trillón**: <https://dle.rae.es/trill%C3%B3n>
- Office québécois de la langue française, **Écriture des grands nombres**: <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library, **What is a billion? And other large numbers**: <https://commonslibrary.parliament.uk/research-briefings/sn04440/>
- US NIST, **Metric (SI) Prefixes**: <https://www.nist.gov/pml/owm/metric-si-prefixes>
- Piper CLI: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md>
- Voces/modelos Piper: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
- Catálogo de voces Piper: <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- Proyecto Piper: <https://github.com/OHF-Voice/piper1-gpl>
- PyPI `piper-tts`: <https://pypi.org/project/piper-tts/>
- Phonemizer: <https://github.com/bootphon/phonemizer>
- googletrans: <https://github.com/ssut/py-googletrans>
- FFmpeg / ffplay: <https://ffmpeg.org/>

---

<a id="français"></a>
# Français

## Projet

Il s'agit d'un petit ensemble d'outils Unix d'étude linguistique, distribué sous GPL-2.0-or-later. Les trois programmes restent séparés afin de pouvoir être composés par pipelines :

```text
texte ── trans.py ──> texte traduit ── phonem.py ──> IPA ── pronounce.py ──> audio
```

| Outil | Entrée | Sortie | Fonction |
|---|---|---|---|
| `trans.py` | texte | texte traduit | traduction via `googletrans` |
| `phonem.py` | texte | IPA | phonémisation et normalisation des profils d'étude |
| `pronounce.py` | IPA | audio | synthèse Piper, lecture et export audio |

Le projet se concentre actuellement sur des profils d'anglais, de français et d'espagnol, en signalant explicitement les approximations lorsqu'un moteur amont ne fournit pas de voix dialectale native.

## Démarrage rapide

```bash
# Traduire
./trans.py en fr "Hello world"

# Texte -> IPA
./phonem.py "Bonjour tout le monde" -l fr-fr

# Texte -> IPA -> voix
./phonem.py "Bonjour tout le monde" -l fr-fr | ./pronounce.py -l fr-fr
```

Après une nouvelle installation :

```bash
./pronounce.py --update-config
./pronounce.py --download-defaults
```

## Outils

### `trans.py`

Traduit du texte UTF-8 en gardant la sortie normale propre sur `stdout`. Les séquences ANSI/ECMA-48 sont supprimées par défaut avant la traduction.

```bash
./trans.py en fr "Hello world"
echo "Hello world" | ./trans.py en fr
```

`--keep-ansi` les conserve explicitement. Voir [Traduction](#fr-translation).

### `phonem.py`

Transforme le texte en IPA via `phonemizer`/eSpeak NG, avec profils logiques et normalisation des nombres avant phonémisation.

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr
./phonem.py "La casa de ella." -l es-uy
```

La ponctuation est conservée par défaut pour rester disponible dans le pipeline audio. Voir [Phonémisation](#fr-phonemization).

### `pronounce.py`

Lit l'IPA et le synthétise avec une voix Piper. Le profil logique peut fournir la voix et les réglages rythmiques par défaut.

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr | ./pronounce.py -l fr-fr
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --wav bonjour.wav
```

Voir [Prononciation](#fr-pronunciation).

## Installation

La cible principale est GNU/Linux/POSIX. L'ensemble complet demande Python 3.9 ou plus récent.

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --check
```

Dépendances Python de `requirements.txt` :

```text
googletrans==4.0.2
phonemizer>=3.4,<4
piper-tts[alignment]>=1.7,<2
```

`ffplay`, généralement fourni avec FFmpeg, sert à la lecture sur le périphérique par défaut. CUDA est facultatif et exige en plus `onnxruntime-gpu`.

## Pipelines complets

Traduire de l'espagnol vers le français, produire l'IPA français puis le prononcer :

```bash
./trans.py es fr "La casa es azul." | \
    ./phonem.py -l fr-fr | \
    ./pronounce.py -l fr-fr
```

Traduire un fichier :

```bash
./trans.py auto fr -i notes.txt > notes-fr.txt
```

Sauvegarder l'IPA puis le synthétiser :

```bash
./phonem.py "Bonjour tout le monde." -l fr-fr > phrase.ipa
./pronounce.py -l fr-fr -i phrase.ipa --wav phrase.wav
```

Le profil uruguayen déjà réglé reste simple :

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

## Référence détaillée

<a id="fr-translation"></a>
### Traduction

`trans.py` 0.9.5 conserve l'interface historique `SRC DEST` et accepte aussi le texte positionnel, `-t/--text`, `-i/--input` ou stdin. Le paquet fournit `trans -> trans.py` pour garder l'ancien nom de commande.

```bash
./trans.py en fr "Hello world"
./trans.py en fr -t "Hello world"
echo "Hello world" | ./trans.py en fr
./trans.py auto fr -i notes.txt
```

Les séquences de contrôle du terminal sont supprimées par défaut avant traduction :

```bash
ls --color=always -1 | ./trans.py en fr
```

`--keep-ansi` désactive ce filtre. Si la langue source et la langue cible sont identiques, la requête de traduction est évitée mais le filtrage ANSI reste actif :

```bash
ls --color=always -1 | ./trans.py en en
```

Les longs textes sont découpés à des limites utiles, par blocs de 5000 caractères par défaut. `--chunk-size` permet d'aller jusqu'à 15000. Une seule session asynchrone `Translator` est réutilisée.

`googletrans` utilise l'interface web non officielle de Google. Une panne réseau ou de service est donc signalée comme une erreur normale d'exécution, sans faux fallback de traduction.

```bash
./trans.py --list-languages
./trans.py --version
./trans.py -v en fr "Texte"
```

<a id="fr-phonemization"></a>
### Phonémisation

`phonem.py` accepte le texte positionnel, `-t/--text`, `-i/--input` ou stdin. L'IPA normal va sur `stdout`; les diagnostics `-v` vont sur `stderr`.

```bash
./phonem.py "1 2 3" -l fr-fr
./phonem.py -t "1 2 3" -l en-ca
cat phrases.txt | ./phonem.py -l es-uy
```

La ponctuation est conservée par défaut. `--strip-punctuation` la retire lorsqu'un flux IPA sans signes est nécessaire; `-p/--preserve-punctuation` reste accepté pour les scripts explicites ou anciens.

La détection automatique distingue prudemment l'anglais, le français et l'espagnol, avec les profils par défaut suivants :

```text
Anglais   -> en-ca
Français  -> fr-ca
Espagnol  -> es-uy
```

Pour un texte très court ou ambigu, il vaut mieux préciser `-l`.

Les hypothèses du profil restent exportables et modifiables :

```bash
./phonem.py --export-exceptions phonem-exceptions.json
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

Le JSON contient les backends candidats, les profils/échelles numériques, les remplacements de texte, les remplacements IPA littéraux et les règles IPA contextuelles par expressions régulières.

<a id="fr-pronunciation"></a>
### Prononciation

`pronounce.py` accepte l'IPA positionnel, via `-i/--input` ou stdin. Sans option de sortie il lit via `ffplay`; il peut aussi écrire WAV, OGG ou MP3.

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --mp3 bonjour.mp3
```

La résolution pratique du modèle donne priorité à `--model`, puis `--voice`, à l'ancienne voix configurée, à la voix du profil et enfin à la voix globale par défaut.

Les paramètres de synthèse suivent `CLI > profil JSON > profil intégré`. `length_scale`, volume et mode de pauses peuvent ainsi rester dans le JSON tout en étant remplacés temporairement en ligne de commande.

Tous les profils intégrés utilisent par défaut le rythme propre à Piper. L'expérience de silences déterministes après synthèse reste disponible avec `--extra-pauses`, mais elle n'est pas activée par défaut car les essais d'écoute ont montré qu'un silence numérique dur pouvait rendre les fins de mots artificielles.

| Limite | Silence supplémentaire | Option |
|---|---:|---|
| espace entre mots | 0.04 s | `--word-pause` |
| virgule `,` | 0.16 s | `--comma-pause` |
| deux-points/point-virgule `:` `;` | 0.24 s | `--clause-pause` |
| point/interrogation/exclamation `.?!` | 0.40 s | `--sentence-pause` |

`--no-extra-pauses` force explicitement le rythme de Piper seul.

<a id="fr-language-profiles"></a>
### Profils linguistiques

Un profil logique d'étude n'est pas forcément une voix native eSpeak ou Piper. Les approximations restent annoncées comme telles.

#### Profils de phonémisation

| Profil | Variété d'étude | Backend eSpeak préféré | État |
|---|---|---|---|
| `en-us` | anglais US | `en-us` | direct si installé |
| `en-ca` | anglais canadien | `en-us`, puis replis | approximation |
| `en-gb` | anglais britannique | `en-gb`, puis replis | direct/repli |
| `en-rp` | Received Pronunciation | `en-gb-x-rp` | direct si installé |
| `en-lancashire` | Lancashire | `en-gb-x-gbclan` | direct si installé |
| `en-nyc` | New York City | `en-us-nyc` | direct si installé |
| `fr-fr` | France | `fr-fr`, puis `fr` | direct/repli |
| `fr-ca` | profil Québec | `fr-be`, puis France | approximation |
| `fr-be` | Belgique | `fr-be` | direct si installé |
| `fr-ch` | Suisse, profil `huitante` | `fr-ch` | profil d'étude |
| `fr-ch-qv` | Suisse, `quatre-vingts` | `fr-ch` | couche d'étude |
| `es-es` | Espagne | `es` | profil Espagne |
| `es-uy` | espagnol uruguayen formel | `es-419`, puis ancien `es-la` | approximation + couche IPA |

#### Voix Piper par défaut

| Profil(s) | Modèle | Rythme | État |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, rythme Piper | testé par l'utilisateur |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, rythme Piper | point de départ |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, rythme Piper | point de départ |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, rythme Piper | approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, rythme Piper | RP reste approximatif |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, rythme Piper | approximation régionale |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, rythme Piper | point de départ |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, rythme Piper | approximation acoustique |

`es-uy` est le premier profil acoustique réglé à l'écoute dans ce projet. Daniela constitue la cible Piper rioplatense disponible la plus proche, mais reste un modèle acoustique argentin, et non une voix native `es_UY`.

Au niveau IPA, le profil uruguayen formel conserve le seseo et le `/s/` final, ne simplifie pas `ct`, n'impose pas de remplacement madrilène du `d` final et oriente le `y`/`ll` consonantique vers la cible rehilada sourde `[ʃ]`. Le `y` vocalique n'est pas remplacé globalement.

<a id="fr-configuration"></a>
### Configuration

#### `phonem.py`

Exporter les hypothèses d'étude :

```bash
./phonem.py --export-exceptions phonem-exceptions.json
```

Utiliser une copie modifiée :

```bash
./phonem.py --exceptions phonem-exceptions.json "lluvia y yo" -l es-uy
```

#### `pronounce.py`

Chemin par défaut :

```text
${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json
```

Créer une configuration propre :

```bash
./pronounce.py --init-config
```

Pour une mise à niveau, utiliser la fusion conservatrice :

```bash
./pronounce.py --update-config
```

Si le JSON n'existe pas, il est créé. Si des clés/profils manquent, une sauvegarde horodatée est créée avant d'ajouter les nouveaux défauts sous les valeurs existantes. Les réglages utilisateur et clés inconnues sont conservés. Si rien ne change, la commande affiche `status=unchanged` sans créer de nouvelle sauvegarde.

Un autre fichier peut être mis à jour explicitement :

```bash
./pronounce.py --config ./mon-pronounce.json --update-config
```

Le JSON contient `schema_version` et `generated_by` pour les migrations futures.

<a id="fr-number-normalization"></a>
### Normalisation des nombres

Les entiers sont développés avant phonémisation lorsque la forme lexicale est importante. L'espagnol et le français utilisent l'échelle longue; l'anglais moderne des États-Unis, du Canada et du Royaume-Uni utilise l'échelle courte.

| Puissance | Espagnol | Français | Anglais moderne |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

Profils français 70/80/90 :

| Profil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

Le normaliseur ne cherche pas à deviner tous les contextes numériques. Les décimaux, dates, heures et numéros de téléphone clairement formatés restent inchangés :

```text
3.14
2026-08-19
17:30
514 555-1234
```

La comparaison courante peut être générée directement par le même code :

```bash
./phonem.py --number-table
```

<a id="fr-audio-models"></a>
### Audio et modèles Piper

Commandes d'inventaire :

```bash
./pronounce.py --list-profiles
./pronounce.py --list-catalog-languages
./pronounce.py --list-voices es-uy
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

Terminologie du projet :

- **profil logique** : cible d'étude telle que `es-uy` ou `fr-ca`;
- **locale du catalogue Piper** : variante acoustique publiée telle que `es_AR`, `es_ES`, `fr_FR`;
- **voix** : locuteur/jeu de données, par exemple `daniela`;
- **modèle vocal** : variante ONNX concrète, par exemple `es_AR-daniela-high`;
- **modèle installé** : fichier `.onnx` réellement présent dans un répertoire configuré.

Installer une voix :

```bash
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
```

Installer tous les modèles par défaut effectifs sans doublons :

```bash
./pronounce.py --download-defaults
```

La configuration actuelle produit six modèles uniques :

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

Les modèles déjà installés sont ignorés. `--force-download` force un nouveau téléchargement; `--auto-download` peut télécharger automatiquement une voix choisie dans le catalogue.

Chaque voix Piper nécessite son `.onnx` et son `.onnx.json`. Les licences des voix peuvent différer de celle du projet; il faut consulter le `MODEL_CARD` avant redistribution.

## Licence

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Ce projet est distribué sous la **GNU General Public License version 2 ou, à votre choix, toute version ultérieure** (`GPL-2.0-or-later`). Voir `COPYING`.

## Sources

- Liste des langues eSpeak NG : <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **números** : <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **y** : <https://www.rae.es/dpd/y>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **yeísmo** : <https://www.rae.es/dpd/ye%C3%ADsmo>
- RAE/ASALE, *Diccionario de la lengua española*, **billón** : <https://dle.rae.es/bill%C3%B3n>
- RAE/ASALE, *Diccionario de la lengua española*, **trillón** : <https://dle.rae.es/trill%C3%B3n>
- Office québécois de la langue française, **Écriture des grands nombres** : <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library, **What is a billion? And other large numbers** : <https://commonslibrary.parliament.uk/research-briefings/sn04440/>
- US NIST, **Metric (SI) Prefixes** : <https://www.nist.gov/pml/owm/metric-si-prefixes>
- Piper CLI : <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md>
- Voix/modèles Piper : <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
- Catalogue des voix Piper : <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- Projet Piper : <https://github.com/OHF-Voice/piper1-gpl>
- PyPI `piper-tts` : <https://pypi.org/project/piper-tts/>
- Phonemizer : <https://github.com/bootphon/phonemizer>
- googletrans : <https://github.com/ssut/py-googletrans>
- FFmpeg / ffplay : <https://ffmpeg.org/>

---

<p align="center"><b>- oOo -</b></p>

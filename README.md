# phonem.py 1.5.0 / pronounce.py 0.5.0

Small GPL-2.0-or-later command-line study tool for comparing pronunciation and number vocabulary across English, French and Spanish varieties.

Herramienta pequeña de línea de comandos, GPL-2.0-or-later, para estudiar y comparar pronunciación y vocabulario numérico entre variantes del inglés, francés y español.

Petit outil d'étude en ligne de commande, sous GPL-2.0-or-later, pour comparer la prononciation et le vocabulaire des nombres entre plusieurs variétés d'anglais, de français et d'espagnol.

- [English](#english)
- [Español](#español)
- [Français](#français)
- [Shared number reference / Referencia numérica / Référence numérique](#shared-number-reference--referencia-numérica--référence-numérique)
- [Sources / Fuentes / Sources](#sources--fuentes--sources)

---

## English

### What this is

`phonem.py` is a study tool built around `phonemizer` and eSpeak/eSpeak NG. It accepts text from a positional argument, `-t/--text`, `-i/--input`, or standard input, normalizes dialect-sensitive cardinal numbers, and writes IPA to standard output.

The modest claim matters: a **logical study profile is not necessarily a native eSpeak voice**. The program keeps both concepts separate and reports the actual backend with `-v` or `--list-languages`.

Examples:

```bash
./phonem.py "Bonjour, comment allez-vous ?" -l fr-ca
./phonem.py -t "Do you want a poutine?" -l en-ca
./phonem.py "Lluvia, yo, pacto, verdad, casas." -l es-uy
./phonem.py -i phrases.txt -l es-es
cat phrases.txt | ./phonem.py -l fr-fr
```

Normal output contains only IPA. Diagnostics go to `stderr`, so pipes remain useful:

```bash
./phonem.py "1 2 3" -l fr-fr | another-program
```

`pronounce.py` 0.5.0 is the second half of the Unix pipeline. It consumes IPA and uses Piper to synthesize audio. Keeping the two programs separate is intentional: `phonem.py` answers “which phonemes?”, while `pronounce.py` answers “which acoustic voice should render those phonemes?”.

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

The short form needs a configured default Piper voice. IPA describes phonemes, but it does not carry a language/profile or a speaker identity, so reproducible scripts should normally pass `-l` or `--voice` to `pronounce.py` as well.

### Language profiles

| Profile | Intended study variety | Default eSpeak backend | Status |
|---|---|---|---|
| `en-us` | US English | `en-us` | direct when installed |
| `en-ca` | Canadian English | `en-us`, then fallbacks | approximation |
| `en-gb` | British English | `en-gb`, then fallbacks | direct/fallback |
| `en-rp` | Received Pronunciation | `en-gb-x-rp` | direct when installed |
| `en-lancashire` | Lancashire | `en-gb-x-gbclan` | direct when installed |
| `en-nyc` | New York City English | `en-us-nyc` | direct when installed |
| `fr-fr` | France | `fr-fr`, then `fr` | direct/fallback |
| `fr-ca` | Quebec study profile | `fr-be`, then France fallbacks | **approximation, not a native Quebec voice** |
| `fr-be` | Belgium | `fr-be` | direct when installed |
| `fr-ch` | Swiss French, `huitante` study profile | `fr-ch` | study profile |
| `fr-ch-qv` | Swiss French, `quatre-vingts` profile | `fr-ch` | study overlay |
| `es-es` | Spain | `es` | logical alias to eSpeak Spanish (Spain) |
| `es-uy` | formal Uruguayan Spanish | `es-419`, then legacy `es-la` | **approximation with IPA overlay** |

Upstream eSpeak NG currently exposes `es` for Spain and `es-419` for Latin America, but not a native `es-uy` voice. The same general limitation applies to our `fr-ca` and `en-ca` study aliases: the aliases are ours; the backend is reported rather than hidden.

### Formal Uruguayan Spanish profile

`es-uy` is deliberately conservative. It is meant to approximate a careful/formal Uruguayan pronunciation, not every social or regional realization in Uruguay.

The profile starts with the Latin-American Spanish backend, which gives us **seseo** (`c/z` before `e/i` use /s/, not Castilian /θ/), and applies a very small IPA post-processing layer:

```json
"es-uy": {
  "ɟʝ": "ʃ",
  "ʝ": "ʃ",
  "ʎ": "ʃ"
}
```

This targets consonantal `y`/`ll` and gives the requested voiceless rehilated realization `[ʃ]`. It does **not** replace vocalic `y` such as the conjunction *y* or the final sound in *hoy*.

For this formal study profile:

- **seseo is retained**: *cena, cinco, zapato* use /s/, not Castilian /θ/;
- final `/s/` is kept; no aspiration or deletion rule is added;
- consonant groups such as `ct` are not simplified by this project (`pacto` is intended to retain `/kt/`);
- no Madrid-style final-`d` substitution is introduced. The Latin-American backend may represent Spanish `/d/` with an allophone such as `[ð]`; the project does not turn it into `/s/` or `/θ/`.

RAE/ASALE explicitly describes strongly fricated `[ʒ]` and `[ʃ]` realizations of consonantal `y` as characteristic of Argentina and Uruguay, and notes that `ll` participates in widespread yeísmo. This project chooses `[ʃ]` for the `es-uy` profile because that is the target of this study profile, not because every Uruguayan speaker must use the same realization.

### Cardinal numbers and scales

Integer tokens are expanded before phonemization. This is important because the name of a number is lexical information; asking the wrong fallback voice to read raw digits can silently teach the wrong word.

French profiles use the French long scale. Spanish uses the Spanish long scale. Modern US, Canadian and British English use the short scale.

Consequently:

```text
10^9   es: mil millones   fr: un milliard   en: one billion
10^12  es: un billón      fr: un billion    en: one trillion
10^18  es: un trillón     fr: un trillion   en: one quintillion
```

This is not a translation trick. The similar-looking words `billón`, `billion` (French) and `billion` (English) represent different powers depending on the scale.

Modern British English is short-scale too. Historical British English used the long-scale meaning of *billion*, but UK government usage changed officially in 1974; current UK official statistics use `billion = 10^9`. Canadian English also uses the short scale.

The English profiles additionally use a small style distinction for `and`:

```text
en-us: 101 -> one hundred one
en-ca: 101 -> one hundred and one
en-gb: 101 -> one hundred and one
```

This is a study/style default, not a claim that every speaker in those countries follows one rigid rule.

### French 70/80/90

| Profile | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

`fr-ca` is the reason number normalization was added in the first place: if its approximate pronunciation backend is `fr-be`, raw `70`/`90` must not accidentally become Belgian *septante/nonante*. The program writes the Quebec/France lexical form first and only then asks the selected backend for IPA.

### Useful commands

```bash
./phonem.py --help
./phonem.py --version
./phonem.py --list-languages
./phonem.py --number-table

./phonem.py --normalize-only "70 80 90 1000000000" -l fr-ca
./phonem.py --normalize-only "1000000000 1000000000000" -l es-uy
./phonem.py --normalize-only "1000000000 1000000000000" -l en-ca

./phonem.py --export-exceptions phonem-exceptions.json
./phonem.py --exceptions phonem-exceptions.json "lluvia y yo" -l es-uy
```

### Editable JSON

The exported JSON intentionally keeps study assumptions visible. It contains:

- `backend_candidates`: ordered eSpeak backends for each logical profile;
- `number_profiles`: French 70/80/90 construction rules;
- `number_scales`: long/short scale and English `and` style;
- `replacements`: literal text preprocessing corrections;
- `ipa_replacements`: small literal IPA overlays such as the `es-uy` `[ʃ]` rule.

Export:

```bash
./phonem.py --export-exceptions phonem-exceptions.json
```

Edit and reuse:

```bash
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

A manual correction is preferable to a clever hidden heuristic when the dialect evidence is uncertain.

### Number parsing boundaries

The cardinal normalizer intentionally does not guess every numeric context. Structured decimals, dates, times and clearly formatted phone numbers remain untouched, for example:

```text
3.14
2026-08-19
17:30
514 555-1234
```

Thousands can be grouped with narrow/non-breaking spaces, underscores or apostrophes. Ordinary spaces are not interpreted as grouping because `70 80 90` must remain three numbers.

### System and Python requirements

The project currently targets a GNU/Linux/POSIX command-line environment. Other systems may work, but they are not the primary tested target of this project.

Minimum runtime for the complete `phonem.py` + `pronounce.py` toolchain:

| Component | Requirement | Used by |
|---|---|---|
| Python | **3.9 or newer** | both programs |
| `phonemizer` | `>=3.4,<4` | `phonem.py` |
| eSpeak NG | system installation | `phonem.py` / phonemizer backend |
| `piper-tts[alignment]` | `>=1.7,<2` | `pronounce.py` |
| FFmpeg | system installation | OGG/MP3 output |
| `ffplay` | usually provided with FFmpeg | default-device playback |

Piper 1.7 requires Python 3.9 or newer, so Python 3.9 is the project-wide floor even though phonemizer itself can run on older supported Python releases. Piper accepts raw eSpeak-NG IPA/phoneme blocks using `[[ ... ]]`, which is why it fits this pipeline without translating IPA back into orthographic text.

On Debian/Ubuntu-like systems, a practical installation is:

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Check the local installation without synthesizing audio:

```bash
./pronounce.py --check
```

CUDA is optional. `--cuda` additionally needs `onnxruntime-gpu`; it is deliberately not part of the default requirements. Voice models are separate downloads and have their own licenses, which should be checked before redistribution.

### `pronounce.py`: IPA to audio with Piper

The audio path is deliberately simple:

```text
phonem.py -> IPA -> pronounce.py -> Piper -> WAV -> speaker / FFmpeg -> OGG or MP3
```

`pronounce.py` accepts IPA as a positional argument, from `-i/--input`, or from `stdin`. Output defaults to the normal audio device through `ffplay`; alternatively:

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /path/to/voice.onnx --mp3 bonjour.mp3
```

#### Study pauses and punctuation

`phonem.py` 1.5.0 preserves punctuation by default because punctuation is part of the pipeline's prosodic information. Use `--strip-punctuation` only when a punctuation-free IPA stream is specifically wanted. `-p/--preserve-punctuation` remains accepted for explicit/backward-compatible scripts.

`pronounce.py` 0.5.0 can add deterministic **extra** silence after aligned word and punctuation boundaries without resynthesizing every word separately. The pause durations below remain available, but **all built-in profiles now keep extra pauses disabled by default** because hard post-synthesis silence can make word endings sound unnatural. Enable them explicitly with `--extra-pauses`:

| Boundary | Extra silence | Option |
|---|---:|---|
| word space | 0.04 s | `--word-pause` |
| comma `,` | 0.16 s | `--comma-pause` |
| colon/semicolon `:` `;` | 0.24 s | `--clause-pause` |
| period/question/exclamation `.?!` | 0.40 s | `--sentence-pause` |

These values are added **after** Piper's own duration model, so they are independent of `--length-scale`. For the current Uruguayan study experiment, for example:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1
```

Tune only the spacing without changing phoneme duration:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1 \
    --word-pause .06 --comma-pause .20 --clause-pause .30 --sentence-pause .50
```

`--no-extra-pauses` forces Piper-only timing; this is also the built-in default for every profile in 0.5.0. `--extra-pauses` enables the deterministic silence experiment. Precise pause insertion uses Piper phoneme/audio alignments, which is why `piper-tts[alignment]` is needed when that feature is used.

Piper voices are ONNX models accompanied by a matching `.onnx.json` file. Piper can list and download available voices:

```bash
python3 -m piper.download_voices
python3 -m piper.download_voices VOICE_NAME --data-dir ~/.local/share/piper
```

Create the local configuration template:

```bash
./pronounce.py --init-config
```

By default it is written to `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`. Models are searched first in explicitly supplied `--data-dir` paths, then configured directories, then `${XDG_DATA_HOME:-~/.local/share}/piper`, and finally the current directory. An example file is included as `pronounce.example.json`.

#### Built-in voice and timing profiles (0.5.0)

`pronounce.py` now ships conservative per-language defaults. CLI options always override the JSON profile, and a non-empty legacy `voices[LANG]` entry also overrides the built-in profile voice. The Uruguayan profile is the first one calibrated by listening in this project; the others are **starting points or explicit approximations**, not claims that Piper natively implements every dialect.

| Logical profile(s) | Default Piper model | Timing | Status |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, Piper-only pauses | user-tested |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, Piper-only pauses | starting point |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, Piper-only pauses | starting point |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, Piper-only pauses | approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, Piper-only pauses | RP remains approximate |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, Piper-only pauses | regional approximation |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, Piper-only pauses | starting point |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, Piper-only pauses | acoustic approximation |

With the installed Daniela model, the calibrated Uruguayan pipeline is therefore reduced to:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

The same values are exported by `--init-config` into `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`. `--list-languages` prints the resolved default voice, length scale, volume, pause mode and validation status for every profile. `--list-profiles` is an alias for the same table.

#### Updating the JSON configuration and downloading default voices

A new package can update an existing configuration without replacing local tuning:

```bash
./pronounce.py --update-config
```

If the file does not exist, it is created. If it already exists, `pronounce.py` first creates a timestamped backup such as `pronounce.json.bak-20260820-103000`, then merges the current shipped defaults **under** the existing file. Existing user values and unknown custom keys win; new profiles and new keys are added. If nothing needs changing, it reports `status=unchanged` and does not create another backup. The file also records `schema_version` and `generated_by` so later migrations can be handled explicitly. A different file can be updated with:

```bash
./pronounce.py --config ./my-pronounce.json --update-config
```

For a first installation, `--init-config` remains useful when a clean file is wanted. For upgrades, `--update-config` is normally the safer command.

The default acoustic models can now be installed without repeating shared voices:

```bash
./pronounce.py --download-defaults
```

The command reads the **resolved configuration**, deduplicates the effective profile voices, and skips models already installed. With the current shipped profiles this means six unique models rather than one download per logical language:

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

Use `--force-download` only when an installed model should deliberately be downloaded again. The same flag also applies to `--download-voice`.

A practical fresh-install/update sequence is therefore:

```bash
python3 -m pip install -r requirements.txt
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

After mapping a logical profile to a local Piper voice, the intended pipe works directly:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

For scripts where reproducibility matters, make the acoustic choice explicit:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py -l fr-fr --voice VOICE_NAME
```

This distinction matters for dialect study: the IPA stream and the Piper voice are two different layers. A Quebec study profile, for example, does not become a native Quebec acoustic model merely because the phonemes came from `fr-ca`.

### Piper languages, voices and local models

The vocabulary is worth keeping precise:

- a **logical profile** is a study target such as `es-uy` or `fr-ca`;
- a Piper **catalogue locale** is a locale for which Piper publishes acoustic models, such as `es_AR`, `es_ES` or `fr_FR`;
- a **voice** is the recorded/trained speaker or dataset name, such as `daniela`;
- a **voice model** is the concrete ONNX model including quality, such as `es_AR-daniela-high`;
- an **installed model** is an `.onnx` file that actually exists in one of the configured data directories.

`pronounce.py` now exposes those layers separately:

```bash
# Study profiles known by this project and their preferred Piper locales
./pronounce.py --list-languages

# Language locales currently published in Piper's catalogue
./pronounce.py --list-catalog-languages

# Catalogue models suitable for a study profile
./pronounce.py --list-voices es-uy
./pronounce.py --list-voices fr-ca

# Only models already installed locally
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

The catalogue is read from Piper's public `voices.json` and cached under `${XDG_CACHE_HOME:-~/.cache}/phonem/piper-voices.json` for 24 hours. `--refresh-catalog` forces a new copy; `--offline` uses only the cache; `--catalog FILE_OR_URL` allows an explicit catalogue for reproducible/offline work.

For the current `es-uy` study profile, `es_AR` is the preferred Piper catalogue locale because it is the closest available Rioplatense acoustic target. `--list-voices` lists the **remote catalogue and local installation status**; `STATUS=remote` means that the model exists in Piper's catalogue but is not yet installed. `--list-models` lists only models that are actually present on disk.

A practical sequence is:

```bash
./pronounce.py --list-voices es-uy
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
./pronounce.py --list-models es-uy
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high
```

Version 0.3.0 also accepts a unique catalogue speaker name, so `--voice daniela` resolves to `es_AR-daniela-high` for `-l es-uy`. It still does **not** download silently. Use `--auto-download` when that behavior is explicitly wanted:

```bash
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice daniela --auto-download
```

If a selected catalogue voice is not installed, the error now prints the exact `--download-voice` command instead of merely saying that the model was not found.

This is still an approximation of formal Uruguayan Spanish, not a native `es_UY` Piper model. The raw IPA from `phonem.py` remains the authoritative study layer; the acoustic model is selected separately and visibly.

Piper's catalogue downloader is used for `--download-voice`, and the downloaded voice consists of both the `.onnx` model and its matching `.onnx.json` configuration. Voice/model licences are not necessarily the same as this project's GPL-2.0-or-later licence; check the model's `MODEL_CARD` before redistribution.

### Automatic language detection

Automatic detection now distinguishes English, French and Spanish using conservative lexical and orthographic evidence. The default study targets are:

```text
English -> en-ca
French  -> fr-ca
Spanish -> es-uy
```

If the text is too short or ambiguous, the program asks for `-l` instead of making a confident-looking guess from no evidence.

### License

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

This program is free software under the **GNU General Public License, version 2 or (at your option) any later version** (`GPL-2.0-or-later`). See `COPYING`.

---

## Español

### Qué es

`phonem.py` es una herramienta de estudio construida sobre `phonemizer` y eSpeak/eSpeak NG. Puede recibir texto como argumento posicional, con `-t/--text`, desde `-i/--input` o por entrada estándar. Antes de obtener el IPA expande los enteros cardinales cuando eso evita diferencias léxicas entre dialectos o escalas numéricas.

La idea central es sencilla: **perfil de estudio y voz instalada no son la misma cosa**. Cuando no existe una voz nativa, el programa lo llama aproximación y muestra qué backend terminó usando.

```bash
./phonem.py "Je voudrais travailler au Canada." -l fr-ca
./phonem.py "I have 1000000000 records." -l en-ca
./phonem.py "Lluvia, yo, pacto, verdad, casas." -l es-uy
./phonem.py "Quiero 1000000000 registros." -l es-uy
```

### `es-es` y `es-uy`

`es-es` usa la voz `es` que eSpeak NG identifica como español de España.

`es-uy` **no es una voz uruguaya real de eSpeak**, porque upstream no ofrece `es-uy`. Es un perfil formal de estudio que toma primero `es-419` (español latinoamericano; `es-la` como fallback legado) y agrega solamente unas correcciones IPA visibles y exportables. No cae hacia `es` de España: preferimos fallar antes que introducir una distinción /s/–/θ/ que no corresponde al español uruguayo.

Para este perfil decidimos:

- conservar el **seseo**: *cena, cinco, zapato* llevan /s/, no el /θ/ castellano;
- `ll` y la `y` consonántica rehiladas se llevan a `[ʃ]`;
- la `y` vocálica no se toca;
- las `s` finales se conservan: no agregamos aspiración ni pérdida de `/s/`;
- `ct` se conserva como grupo consonántico; el programa no transforma *pacto* en algo parecido a *pasto*;
- no agregamos una sustitución especial para la `d` final. El backend latinoamericano puede realizar el fonema `/d/` con un alófono como `[ð]`, cosa normal en español; lo que no hacemos es imponerle una pronunciación madrileña en `/θ/` ni convertirlo en `/s/`.

RAE/ASALE documenta para Argentina y Uruguay realizaciones rehiladas `[ʒ]` y `[ʃ]` de la `y` consonántica, y también explica que `ll` participa del yeísmo. Elegimos `[ʃ]` porque ése es el español uruguayo formal que queremos usar como objetivo de esta herramienta de estudio. No pretende afirmar que todos los uruguayos hablen idéntico.

### Billones, trillones y la trampa del inglés

Tu sospecha era correcta: **el inglés moderno de Estados Unidos, Canadá y Reino Unido usa la escala corta**.

| Potencia | Español | Francés | Inglés moderno |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

El falso amigo es especialmente peligroso:

```text
English billion = 10^9
Español billón  = 10^12
Français billion = 10^12
```

La RAE mantiene para el español la escala larga. La OQLF explica la escala larga francesa y, además, señala explícitamente que Estados Unidos y Canadá inglés usan la corta y que Gran Bretaña la adoptó posteriormente. La House of Commons Library confirma que las estadísticas oficiales británicas actuales usan `billion = 1 000 million` y que el gobierno británico oficializó ese uso en 1974.

Por eso el programa no entrega los dígitos grandes directamente a eSpeak. Primero los convierte a palabras en el idioma lógico y después obtiene el IPA.

```bash
./phonem.py --normalize-only "1000000000 1000000000000 1000000000000000000" -l es-uy
# mil millones un billón un trillón

./phonem.py --normalize-only "1000000000 1000000000000 1000000000000000000" -l fr-ca
# un milliard un billion un trillion

./phonem.py --normalize-only "1000000000 1000000000000 1000000000000000000" -l en-ca
# one billion one trillion one quintillion
```

### Diferencias francesas

| Perfil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

`fr-ca` sigue siendo una **aproximación**: actualmente no tenemos una voz quebequense real en eSpeak NG. La normalización corrige el vocabulario antes de usar `fr-be`; no convierte mágicamente la voz belga en quebequense.

### Excepciones exportables

```bash
./phonem.py --export-exceptions phonem-exceptions.json
```

El JSON contiene tanto las cadenas de fallback como las reglas numéricas y las pequeñas correcciones IPA. Se puede editar y volver a cargar:

```bash
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

Esto es deliberado. Si encontramos una pronunciación regional mejor documentada, se puede corregir el perfil sin esconder la decisión dentro de una función.

### CLI y pipes

Además de `-t`, ahora se acepta texto posicional:

```bash
./phonem.py "1 2 3" -l fr-fr
./phonem.py -t "1 2 3" -l fr-fr
```

La salida IPA normal queda limpia en `stdout`; `-v` escribe los diagnósticos en `stderr`. `pronounce.py` ya implementa la segunda mitad del pipeline:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

Sigue siendo otra herramienta, no una función incrustada en `phonem.py`. Esa separación permite hablar por el dispositivo de audio por defecto o escribir `--wav`, `--ogg` o `--mp3` sin mezclar fonemización y síntesis acústica.

### Requisitos del sistema y de Python

El objetivo primario del proyecto es una línea de comandos GNU/Linux/POSIX. Puede funcionar en otros sistemas, pero no los presentamos como plataforma principal mientras no estén probados de la misma manera.

Requisitos mínimos para el conjunto `phonem.py` + `pronounce.py`:

| Componente | Requisito | Lo usa |
|---|---|---|
| Python | **3.9 o posterior** | ambos programas |
| `phonemizer` | `>=3.4,<4` | `phonem.py` |
| eSpeak NG | instalación del sistema | `phonem.py` / backend de phonemizer |
| `piper-tts[alignment]` | `>=1.7,<2` | `pronounce.py` |
| FFmpeg | instalación del sistema | salida OGG/MP3 |
| `ffplay` | normalmente incluido con FFmpeg | reproducción por el dispositivo por defecto |

Piper 1.7 requiere Python 3.9 o posterior, por eso adoptamos 3.9 como piso para todo el proyecto aunque phonemizer admita versiones anteriores de Python. Piper puede recibir bloques de fonemas IPA de eSpeak NG con `[[ ... ]]`; eso nos permite alimentar directamente el resultado fonético sin volver a reconstruir texto ortográfico.

Ejemplo para Debian/Ubuntu y derivados:

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Chequeo local sin sintetizar:

```bash
./pronounce.py --check
```

CUDA es opcional. `--cuda` requiere además `onnxruntime-gpu` y por eso no se instala como dependencia normal. Las voces Piper se descargan por separado y cada modelo puede tener su propia licencia; conviene comprobarla antes de redistribuirlo.

### `pronounce.py`: de IPA a audio

La cadena queda deliberadamente simple:

```text
phonem.py -> IPA -> pronounce.py -> Piper -> WAV -> parlantes / FFmpeg -> OGG o MP3
```

`pronounce.py` acepta IPA como argumento posicional, desde `-i/--input` o por `stdin`. Sin opción de salida reproduce por el dispositivo normal mediante `ffplay`; también puede guardar:

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /ruta/voz.onnx --mp3 bonjour.mp3
```

#### Pausas de estudio y puntuación

`phonem.py` 1.5.0 conserva la puntuación por defecto porque, dentro del pipeline, los signos también llevan información prosódica. `--strip-punctuation` la elimina cuando se quiere una salida IPA sin signos; `-p/--preserve-punctuation` sigue aceptándose para scripts explícitos o antiguos.

`pronounce.py` 0.5.0 agrega silencio **extra** y determinista después de límites alineados de palabra y puntuación, sin sintetizar cada palabra por separado. Las duraciones siguientes siguen disponibles, pero **todos los perfiles internos dejan las pausas extra desactivadas por defecto** porque el silencio duro añadido después de sintetizar puede deformar las terminaciones de las palabras. Se activan de forma explícita con `--extra-pauses`:

| Límite | Silencio extra | Opción |
|---|---:|---|
| espacio entre palabras | 0.04 s | `--word-pause` |
| coma `,` | 0.16 s | `--comma-pause` |
| dos puntos/punto y coma `:` `;` | 0.24 s | `--clause-pause` |
| punto/interrogación/exclamación `.?!` | 0.40 s | `--sentence-pause` |

Estos valores se suman **después** de la duración calculada por Piper y, por tanto, no dependen de `--length-scale`. Para la prueba uruguaya actual:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1
```

Si se quiere separar un poco más las palabras y las frases sin alargar las letras:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1 \
    --word-pause .06 --comma-pause .20 --clause-pause .30 --sentence-pause .50
```

`--no-extra-pauses` fuerza el ritmo puro de Piper; además, ése es el valor predeterminado de todos los perfiles en 0.5.0. `--extra-pauses` activa el experimento de silencios deterministas. La inserción precisa usa los alineamientos fonema/audio de Piper, por lo que `piper-tts[alignment]` se necesita cuando se usa esa función.

Piper usa modelos ONNX con su archivo `.onnx.json` correspondiente. Sus herramientas permiten listar y descargar voces:

```bash
python3 -m piper.download_voices
python3 -m piper.download_voices VOICE_NAME --data-dir ~/.local/share/piper
```

Para crear una configuración local:

```bash
./pronounce.py --init-config
```

Por defecto queda en `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`. Se incluye `pronounce.example.json` como ejemplo.

#### Perfiles predeterminados de voz y ritmo (0.5.0)

`pronounce.py` incluye ahora valores conservadores por perfil lógico. Las opciones de línea de comandos siempre tienen prioridad sobre el JSON, y una entrada antigua no vacía en `voices[LANG]` también prevalece sobre la voz interna. `es-uy` es el primer perfil calibrado escuchándolo en este proyecto; los demás son **puntos de partida o aproximaciones explícitas**, no afirmaciones de que Piper implemente de forma nativa cada dialecto.

| Perfil(es) lógico(s) | Modelo Piper predeterminado | Ritmo | Estado |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, pausas de Piper | probado por el usuario |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, pausas de Piper | punto de partida |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, pausas de Piper | punto de partida |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, pausas de Piper | aproximación |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, pausas de Piper | RP sigue siendo aproximado |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, pausas de Piper | aproximación regional |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, pausas de Piper | punto de partida |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, pausas de Piper | aproximación acústica |

Con Daniela instalada, el pipeline uruguayo que acabamos de calibrar queda reducido a:

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

`--init-config` exporta estos mismos valores a `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`. `--list-languages` muestra para cada perfil la voz, `length_scale`, volumen, modo de pausas y estado de validación. `--list-profiles` es un alias de la misma tabla.

#### Actualizar el JSON y descargar las voces predeterminadas

Al bajar una versión nueva se puede actualizar la configuración existente sin perder la calibración local:

```bash
./pronounce.py --update-config
```

Si el archivo no existe, se crea. Si ya existe, primero se genera un backup con fecha, por ejemplo `pronounce.json.bak-20260820-103000`, y después se mezclan los nuevos valores predeterminados **por debajo** del JSON existente. Los valores del usuario y las claves personalizadas se conservan; sólo se agregan perfiles o claves que faltaban. Si no hay nada que cambiar, informa `status=unchanged` y no genera otro backup. El archivo guarda además `schema_version` y `generated_by` para que futuras migraciones sean explícitas. Para actualizar otro archivo:

```bash
./pronounce.py --config ./mi-pronounce.json --update-config
```

`--init-config` sigue sirviendo para crear una configuración limpia. Para actualizar una instalación existente, normalmente conviene `--update-config`.

Las voces predeterminadas se pueden instalar ahora sin repetir las que comparten varios perfiles:

```bash
./pronounce.py --download-defaults
```

La orden usa la **configuración resuelta**, elimina duplicados y omite los modelos ya instalados. Con los perfiles actuales son seis modelos únicos:

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

`--force-download` fuerza una nueva descarga cuando eso sea realmente necesario; también funciona con `--download-voice`.

Una secuencia práctica después de bajar o actualizar el paquete es:

```bash
python3 -m pip install -r requirements.txt
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

Después de asociar un perfil lógico con una voz Piper local, funciona el pipe corto:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

Para scripts reproducibles prefiero hacer explícita también la voz acústica:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py -l fr-fr --voice VOICE_NAME
```

Esto es particularmente importante en este proyecto: **IPA, dialecto lógico y voz acústica son capas diferentes**. Que `phonem.py` produzca un perfil aproximado de Quebec no significa que Piper tenga mágicamente una voz nativa quebequense.

### Idiomas, voces y modelos de Piper

Conviene mantener separados los términos:

- un **perfil lógico** es un objetivo de estudio como `es-uy` o `fr-ca`;
- un **locale del catálogo Piper** es una variante para la que Piper publica modelos acústicos, por ejemplo `es_AR`, `es_ES` o `fr_FR`;
- una **voz** es el hablante o conjunto de datos entrenado, por ejemplo `daniela`;
- un **modelo de voz** es el ONNX concreto con su calidad, por ejemplo `es_AR-daniela-high`;
- un **modelo instalado** es un archivo `.onnx` que realmente existe en alguno de los directorios configurados.

`pronounce.py` presenta esas capas por separado:

```bash
# Perfiles de estudio conocidos por el proyecto y locales Piper preferidos
./pronounce.py --list-languages

# Locales publicados actualmente en el catálogo de Piper
./pronounce.py --list-catalog-languages

# Modelos del catálogo adecuados para un perfil de estudio
./pronounce.py --list-voices es-uy
./pronounce.py --list-voices fr-ca

# Modelos ONNX que ya están instalados localmente
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

El catálogo se obtiene desde el `voices.json` público de Piper y se guarda durante 24 horas en `${XDG_CACHE_HOME:-~/.cache}/phonem/piper-voices.json`. `--refresh-catalog` fuerza una actualización, `--offline` trabaja sólo con la caché y `--catalog FILE_OR_URL` permite indicar un catálogo explícito.

Para nuestro perfil `es-uy`, `es_AR` es el locale Piper preferido porque es la aproximación acústica rioplatense disponible más cercana. `--list-voices` muestra el **catálogo remoto y el estado de instalación local**; `STATUS=remote` significa que el modelo existe en el catálogo de Piper pero todavía no está instalado. `--list-models` muestra únicamente modelos realmente presentes en disco.

El flujo práctico queda así:

```bash
./pronounce.py --list-voices es-uy
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
./pronounce.py --list-models es-uy
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high
```

La versión 0.3.0 también acepta un nombre de hablante único del catálogo: con `-l es-uy`, `--voice daniela` resuelve `es_AR-daniela-high`. Aun así, no descarga nada silenciosamente. Si se desea explícitamente ese comportamiento se usa `--auto-download`:

```bash
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice daniela --auto-download
```

Si la voz seleccionada existe en el catálogo pero no está instalada, el error ahora muestra el comando exacto `--download-voice` que hay que ejecutar.

Sigue siendo una **aproximación** al español uruguayo formal, no un modelo Piper nativo `es_UY`. El IPA generado por `phonem.py` sigue siendo la capa de estudio que controlamos; la voz acústica se elige aparte y queda visible.

`--download-voice` delega la descarga al módulo oficial de Piper. Cada voz necesita el `.onnx` y su `.onnx.json`. Las licencias de las voces/modelos pueden ser distintas de la GPL-2.0-or-later de este proyecto; antes de redistribuir una voz hay que comprobar su `MODEL_CARD`.

### Licencia

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Este programa se distribuye bajo **GNU General Public License versión 2 o, a elección del usuario, cualquier versión posterior** (`GPL-2.0-or-later`). Véase `COPYING`.

---

## Français

### Objetif

`phonem.py` est un petit outil d'étude fondé sur `phonemizer` et eSpeak/eSpeak NG. Il accepte le texte comme argument positionnel, avec `-t/--text`, depuis `-i/--input` ou via l'entrée standard. Il normalise certains nombres cardinaux avant la phonémisation afin de ne pas confondre vocabulaire dialectal et voix de synthèse.

Le principe essentiel est de séparer **le profil logique d'étude** de **la voix eSpeak réellement installée**. Lorsqu'une voix native n'existe pas, le programme parle explicitement d'approximation.

```bash
./phonem.py "Bonjour, comment allez-vous ?" -l fr-ca
./phonem.py "Do you want a poutine?" -l en-ca
./phonem.py "Lluvia, yo, pacto, verdad, casas." -l es-uy
```

### Profils espagnols

`es-es` correspond à la voix `es` qu'eSpeak NG décrit comme espagnol d'Espagne.

`es-uy` n'est **pas** une véritable voix uruguayenne d'eSpeak. C'est un profil formel d'étude basé d'abord sur `es-419` (espagnol d'Amérique latine; ancien `es-la` en repli), avec une couche IPA très limitée et modifiable. Il ne se replie pas sur la voix `es` d'Espagne : mieux vaut échouer que d'introduire une distinction /s/–/θ/ étrangère à l'espagnol uruguayen.

Dans ce profil :

- le **seseo** est conservé : *cena, cinco, zapato* utilisent /s/, et non le /θ/ castillan;
- `ll` et `y` consonantique sont ramenés à la réalisation rehilada sourde `[ʃ]`;
- le `y` vocalique n'est pas modifié;
- les `/s/` finales sont conservées; le projet n'ajoute ni aspiration ni élision;
- les groupes comme `ct` ne sont pas simplifiés par le projet;
- aucune substitution madrilène particulière n'est imposée au `d` final. Le backend peut représenter `/d/` par un allophone tel que `[ð]`, sans que nous le transformions en `/s/` ou `/θ/`.

RAE/ASALE décrit les réalisations rehiladas `[ʒ]` et `[ʃ]` de `y` comme caractéristiques de l'Argentine et de l'Uruguay, et rappelle le rapport avec le yeísmo de `ll`. Le choix de `[ʃ]` est ici celui de notre profil d'étude; ce n'est pas une affirmation selon laquelle tous les Uruguayens ont une prononciation identique.

### Échelles des grands nombres

Le français et l'espagnol utilisent ici l'échelle longue; l'anglais moderne des États-Unis, du Canada et du Royaume-Uni utilise l'échelle courte.

| Puissance | Espagnol | Français | Anglais moderne |
|---|---|---|---|
| `10^6` | un millón | un million | one million |
| `10^9` | mil millones | un milliard | one billion |
| `10^12` | un billón | un billion | one trillion |
| `10^15` | mil billones | un billiard | one quadrillion |
| `10^18` | un trillón | un trillion | one quintillion |

Ainsi, le français *billion* et l'anglais *billion* sont de faux amis numériques : le premier vaut `10^12`, le second `10^9` dans l'usage anglais moderne.

L'OQLF décrit explicitement ces deux échelles et indique que l'échelle courte est utilisée aux États-Unis et au Canada anglais, puis plus récemment en Grande-Bretagne. La House of Commons Library confirme que les statistiques officielles britanniques utilisent aujourd'hui `billion = 10^9` et rappelle l'adoption gouvernementale de 1974.

### 70, 80 et 90 en français

| Profil | 70 | 80 | 90 |
|---|---|---|---|
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix |
| `fr-be` | septante | quatre-vingts | nonante |
| `fr-ch` | septante | huitante | nonante |
| `fr-ch-qv` | septante | quatre-vingts | nonante |

Le profil `fr-ca` reste volontairement qualifié d'**approximation**. eSpeak NG ne nous fournit pas actuellement une véritable voix québécoise. Nous corrigeons les formes lexicales des nombres avant d'utiliser le backend approximatif; cela ne transforme pas une voix belge en voix québécoise.

### JSON modifiable

```bash
./phonem.py --export-exceptions phonem-exceptions.json
./phonem.py --exceptions phonem-exceptions.json "Yo llegué ayer." -l es-uy
```

Le fichier exporté expose les backends candidats, les profils français 70/80/90, les échelles numériques, les remplacements de texte et les petites corrections IPA. Le but est de pouvoir corriger une hypothèse manuellement lorsqu'une meilleure donnée dialectale apparaît.

### Pipes

Le texte positionnel est accepté :

```bash
./phonem.py "1 2 3" -l fr-fr
```

L'IPA normal est écrit sur `stdout`; les diagnostics de `-v` vont sur `stderr`. `pronounce.py` implémente maintenant la seconde moitié du pipeline :

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

Il reste volontairement un programme séparé afin de pouvoir envoyer le son vers le périphérique par défaut ou produire `--wav`, `--ogg` ou `--mp3` sans mélanger phonémisation et synthèse acoustique.

### Prérequis système et Python

La cible principale du projet est un environnement de ligne de commande GNU/Linux/POSIX. D'autres systèmes peuvent fonctionner, mais ils ne sont pas présentés comme cible principale tant qu'ils ne sont pas testés de la même manière.

Prérequis minimaux pour l'ensemble `phonem.py` + `pronounce.py` :

| Composant | Prérequis | Utilisé par |
|---|---|---|
| Python | **3.9 ou plus récent** | les deux programmes |
| `phonemizer` | `>=3.4,<4` | `phonem.py` |
| eSpeak NG | installation système | `phonem.py` / backend phonemizer |
| `piper-tts[alignment]` | `>=1.7,<2` | `pronounce.py` |
| FFmpeg | installation système | sortie OGG/MP3 |
| `ffplay` | généralement fourni avec FFmpeg | lecture sur le périphérique par défaut |

Piper 1.7 exige Python 3.9 ou plus récent; nous adoptons donc Python 3.9 comme minimum pour l'ensemble du projet, même si phonemizer accepte des versions de Python antérieures. Piper accepte des blocs de phonèmes IPA/eSpeak NG sous la forme `[[ ... ]]`, ce qui permet d'utiliser directement notre sortie phonétique.

Exemple sous Debian/Ubuntu et dérivés :

```bash
sudo apt install python3 python3-venv espeak-ng ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Diagnostic local sans synthèse :

```bash
./pronounce.py --check
```

CUDA est facultatif. `--cuda` nécessite en plus `onnxruntime-gpu`; cette dépendance n'est donc pas installée par défaut. Les voix Piper sont téléchargées séparément et chaque modèle peut avoir sa propre licence, à vérifier avant redistribution.

### `pronounce.py` : de l'API vers l'audio

La chaîne reste volontairement simple :

```text
phonem.py -> IPA -> pronounce.py -> Piper -> WAV -> haut-parleurs / FFmpeg -> OGG ou MP3
```

`pronounce.py` accepte l'IPA comme argument positionnel, via `-i/--input` ou par `stdin`. Sans option de sortie il lit le son sur le périphérique normal via `ffplay`; il peut aussi écrire :

```bash
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --wav bonjour.wav
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --ogg bonjour.ogg
./pronounce.py "bɔ̃ʒuʁ" --model /chemin/voix.onnx --mp3 bonjour.mp3
```

#### Pauses d’étude et ponctuation

`phonem.py` 1.5.0 conserve désormais la ponctuation par défaut, car les signes transportent aussi une information prosodique dans le pipeline. `--strip-punctuation` permet d'obtenir un flux IPA sans ponctuation ; `-p/--preserve-punctuation` reste accepté pour les scripts explicites ou anciens.

`pronounce.py` 0.5.0 ajoute un silence **supplémentaire** et déterministe après les limites alignées des mots et de la ponctuation, sans resynthétiser chaque mot séparément. Les durées ci-dessous restent disponibles, mais **tous les profils intégrés désactivent désormais les pauses supplémentaires par défaut**, car un silence numérique ajouté après synthèse peut rendre les fins de mots artificielles. Elles s’activent explicitement avec `--extra-pauses` :

| Limite | Silence supplémentaire | Option |
|---|---:|---|
| espace entre mots | 0.04 s | `--word-pause` |
| virgule `,` | 0.16 s | `--comma-pause` |
| deux-points/point-virgule `:` `;` | 0.24 s | `--clause-pause` |
| point/interrogation/exclamation `.?!` | 0.40 s | `--sentence-pause` |

Ces valeurs sont ajoutées **après** la durée calculée par Piper ; elles sont donc indépendantes de `--length-scale`. Exemple pour l'expérience uruguayenne actuelle :

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1
```

Pour espacer davantage les mots et les phrases sans rallonger les phonèmes :

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high \
    --length-scale 2 --volume 1 \
    --word-pause .06 --comma-pause .20 --clause-pause .30 --sentence-pause .50
```

`--no-extra-pauses` force le rythme de Piper seul ; c'est aussi la valeur par défaut de tous les profils en 0.5.0. `--extra-pauses` active l'expérience de silences déterministes. L'insertion précise repose sur les alignements phonème/audio de Piper ; `piper-tts[alignment]` est donc nécessaire lorsque cette fonction est utilisée.

Piper utilise des modèles ONNX accompagnés de leur fichier `.onnx.json`. Ses outils permettent de lister et télécharger les voix :

```bash
python3 -m piper.download_voices
python3 -m piper.download_voices VOICE_NAME --data-dir ~/.local/share/piper
```

Créer la configuration locale :

```bash
./pronounce.py --init-config
```

Elle est écrite par défaut dans `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`; `pronounce.example.json` est fourni comme exemple.

#### Profils vocaux et rythmiques par défaut (0.5.0)

`pronounce.py` fournit maintenant des valeurs prudentes par profil logique. Les options CLI ont toujours priorité sur le JSON, et une ancienne entrée non vide `voices[LANG]` remplace aussi la voix intégrée. `es-uy` est le premier profil réellement réglé à l'écoute dans ce projet ; les autres restent **des points de départ ou des approximations explicites**, et non l'affirmation que Piper implémente nativement chaque dialecte.

| Profil(s) logique(s) | Modèle Piper par défaut | Rythme | État |
|---|---|---|---|
| `es-uy` | `es_AR-daniela-high` | `length_scale=2.0`, `volume=1.0`, pauses Piper | testé par l'utilisateur |
| `es`, `es-es` | `es_ES-davefx-medium` | `1.0`, `1.0`, pauses Piper | point de départ |
| `en`, `en-us` | `en_US-lessac-high` | `1.0`, `1.0`, pauses Piper | point de départ |
| `en-ca`, `en-nyc` | `en_US-lessac-high` | `1.0`, `1.0`, pauses Piper | approximation |
| `en-gb`, `en-rp` | `en_GB-cori-high` | `1.0`, `1.0`, pauses Piper | RP reste approximatif |
| `en-lancashire` | `en_GB-northern_english_male-medium` | `1.0`, `1.0`, pauses Piper | approximation régionale |
| `fr`, `fr-fr` | `fr_FR-siwis-medium` | `1.0`, `1.0`, pauses Piper | point de départ |
| `fr-ca`, `fr-be`, `fr-ch`, `fr-ch-qv` | `fr_FR-siwis-medium` | `1.0`, `1.0`, pauses Piper | approximation acoustique |

Avec Daniela installée, le pipeline uruguayen réglé empiriquement devient simplement :

```bash
./phonem.py "La casa de ella es azul y verde. No creas que no lo sabe." -l es-uy | \
    ./pronounce.py -l es-uy
```

`--init-config` exporte ces mêmes valeurs vers `${XDG_CONFIG_HOME:-~/.config}/phonem/pronounce.json`. `--list-languages` affiche la voix, `length_scale`, le volume, le mode de pauses et l'état de validation de chaque profil. `--list-profiles` est un alias de la même table.

#### Mettre à jour le JSON et télécharger les voix par défaut

Après le téléchargement d'une nouvelle version, la configuration existante peut être mise à jour sans perdre les réglages locaux :

```bash
./pronounce.py --update-config
```

Si le fichier n'existe pas, il est créé. S'il existe déjà, `pronounce.py` crée d'abord une sauvegarde horodatée, par exemple `pronounce.json.bak-20260820-103000`, puis fusionne les nouvelles valeurs intégrées **sous** le JSON existant. Les valeurs utilisateur et les clés personnalisées sont conservées ; seuls les profils ou champs absents sont ajoutés. Si aucune modification n'est nécessaire, il affiche `status=unchanged` sans créer une nouvelle sauvegarde. Le fichier contient aussi `schema_version` et `generated_by` afin de rendre les migrations futures explicites. Pour mettre à jour un autre fichier :

```bash
./pronounce.py --config ./mon-pronounce.json --update-config
```

`--init-config` reste utile pour créer une configuration propre. Pour une mise à niveau, `--update-config` est normalement le choix le plus prudent.

Les voix par défaut peuvent maintenant être installées sans télécharger plusieurs fois les modèles partagés :

```bash
./pronounce.py --download-defaults
```

La commande utilise la **configuration résolue**, déduplique les voix effectives et ignore les modèles déjà installés. Avec les profils actuels, cela représente six modèles uniques :

```text
en_US-lessac-high
en_GB-cori-high
en_GB-northern_english_male-medium
es_ES-davefx-medium
es_AR-daniela-high
fr_FR-siwis-medium
```

`--force-download` permet de forcer un nouveau téléchargement lorsqu'il est réellement souhaité ; l'option s'applique aussi à `--download-voice`.

Une séquence pratique après téléchargement ou mise à niveau du paquet est :

```bash
python3 -m pip install -r requirements.txt
./pronounce.py --update-config
./pronounce.py --download-defaults
./pronounce.py --list-models
```

Une fois un profil logique associé à une voix Piper locale, le pipeline court fonctionne :

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

Pour un script reproductible, il vaut mieux rendre explicite la voix acoustique :

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py -l fr-fr --voice VOICE_NAME
```

Cette séparation est essentielle pour l'étude dialectale : **IPA, profil logique et voix acoustique sont trois couches différentes**. Un profil québécois approximatif en entrée ne crée pas une véritable voix québécoise dans Piper.

### Langues, voix et modèles Piper

Il est utile de garder les termes séparés :

- un **profil logique** est une cible d'étude telle que `es-uy` ou `fr-ca` ;
- une **locale du catalogue Piper** est une variante pour laquelle Piper publie des modèles acoustiques, comme `es_AR`, `es_ES` ou `fr_FR` ;
- une **voix** est le locuteur ou le jeu de données entraîné, par exemple `daniela` ;
- un **modèle vocal** est le modèle ONNX concret avec son niveau de qualité, par exemple `es_AR-daniela-high` ;
- un **modèle installé** est un fichier `.onnx` réellement présent dans l'un des répertoires configurés.

`pronounce.py` affiche ces couches séparément :

```bash
# Profils d'étude du projet et locales Piper préférées
./pronounce.py --list-languages

# Locales actuellement publiées dans le catalogue Piper
./pronounce.py --list-catalog-languages

# Modèles du catalogue adaptés à un profil d'étude
./pronounce.py --list-voices es-uy
./pronounce.py --list-voices fr-ca

# Modèles ONNX déjà installés localement
./pronounce.py --list-models
./pronounce.py --list-models es-uy
```

Le catalogue est lu depuis le `voices.json` public de Piper et mis en cache pendant 24 heures dans `${XDG_CACHE_HOME:-~/.cache}/phonem/piper-voices.json`. `--refresh-catalog` force sa mise à jour, `--offline` n'utilise que le cache et `--catalog FILE_OR_URL` permet de choisir explicitement un catalogue.

Pour notre profil `es-uy`, `es_AR` est la locale Piper préférée, car c'est l'approximation acoustique rioplatense disponible la plus proche. `--list-voices` affiche le **catalogue distant ainsi que l'état d'installation locale** ; `STATUS=remote` signifie que le modèle existe dans le catalogue Piper mais n'est pas encore installé. `--list-models` n'affiche que les modèles réellement présents sur disque.

Le flux pratique devient :

```bash
./pronounce.py --list-voices es-uy
./pronounce.py -l es-uy --download-voice es_AR-daniela-high
./pronounce.py --list-models es-uy
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice es_AR-daniela-high
```

La version 0.3.0 accepte aussi un nom de locuteur unique du catalogue : avec `-l es-uy`, `--voice daniela` résout `es_AR-daniela-high`. Aucun téléchargement silencieux n'est toutefois effectué. Utilisez `--auto-download` si ce comportement est explicitement souhaité :

```bash
./phonem.py "La casa de ella" -l es-uy | \
    ./pronounce.py -l es-uy --voice daniela --auto-download
```

Si une voix existe dans le catalogue mais n'est pas installée, le message d'erreur fournit désormais la commande `--download-voice` exacte à exécuter.

Cela reste une **approximation** de l'espagnol uruguayen formel, et non un modèle Piper natif `es_UY`. L'IPA produit par `phonem.py` reste la couche d'étude contrôlée ; le modèle acoustique est choisi séparément et explicitement.

`--download-voice` délègue le téléchargement au module officiel de Piper. Chaque voix nécessite le fichier `.onnx` et son `.onnx.json`. Les licences des voix/modèles peuvent différer de la GPL-2.0-or-later de ce projet ; il faut vérifier le `MODEL_CARD` avant redistribution.

### Licence

Copyright 2018- William Martinez Bas `<metfar@gmail.com>`.

Ce programme est distribué sous la **GNU General Public License version 2 ou, à votre choix, toute version ultérieure** (`GPL-2.0-or-later`). Voir `COPYING`.

---

## Shared number reference / Referencia numérica / Référence numérique

The command below generates the comparison from the same code that performs normalization, rather than from a second handwritten table:

La siguiente orden genera la comparación usando el mismo código que normaliza los números, no una segunda tabla escrita a mano:

La commande suivante génère la comparaison à partir du même code que celui qui normalise les nombres, et non d'un second tableau manuel :

```bash
./phonem.py --number-table
```

Current core comparison:

| Profile | 70 | 80 | 90 | `10^9` | `10^12` | `10^18` |
|---|---|---|---|---|---|---|
| `en-us` | seventy | eighty | ninety | one billion | one trillion | one quintillion |
| `en-ca` | seventy | eighty | ninety | one billion | one trillion | one quintillion |
| `en-gb` | seventy | eighty | ninety | one billion | one trillion | one quintillion |
| `fr-fr` | soixante-dix | quatre-vingts | quatre-vingt-dix | un milliard | un billion | un trillion |
| `fr-ca` | soixante-dix | quatre-vingts | quatre-vingt-dix | un milliard | un billion | un trillion |
| `fr-be` | septante | quatre-vingts | nonante | un milliard | un billion | un trillion |
| `fr-ch` | septante | huitante | nonante | un milliard | un billion | un trillion |
| `fr-ch-qv` | septante | quatre-vingts | nonante | un milliard | un billion | un trillion |
| `es-es` | setenta | ochenta | noventa | mil millones | un billón | un trillón |
| `es-uy` | setenta | ochenta | noventa | mil millones | un billón | un trillón |

---

## Sources / Fuentes / Sources

The project uses these references to keep the study assumptions checkable rather than mysterious:

- eSpeak NG language list: <https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **números**: <https://www.rae.es/dpd/n%C3%BAmeros>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **y**: <https://www.rae.es/dpd/y>
- RAE/ASALE, *Diccionario panhispánico de dudas*, **yeísmo**: <https://www.rae.es/dpd/ye%C3%ADsmo>
- RAE/ASALE, *Diccionario de la lengua española*, **billón**: <https://dle.rae.es/bill%C3%B3n>
- RAE/ASALE, *Diccionario de la lengua española*, **trillón**: <https://dle.rae.es/trill%C3%B3n>
- Office québécois de la langue française, **Écriture des grands nombres**: <https://vitrinelinguistique.oqlf.gouv.qc.ca/24445/la-typographie/nombres/ecriture-des-grands-nombres>
- UK House of Commons Library, **What is a billion? And other large numbers**: <https://commonslibrary.parliament.uk/research-briefings/sn04440/>
- US NIST, **Metric (SI) Prefixes**: <https://www.nist.gov/pml/owm/metric-si-prefixes>
- Piper, **Command Line Interface**: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md>
- Piper, **Voices and models**: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
- Piper voice catalogue (`voices.json`): <https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json>
- PyPI, **piper-tts**: <https://pypi.org/project/piper-tts/>
- Piper (Open Home Foundation), project and CLI/Python API: <https://github.com/OHF-Voice/piper1-gpl>
- Phonemizer project: <https://github.com/bootphon/phonemizer>
- FFmpeg / ffplay documentation: <https://ffmpeg.org/>

The references describe language usage; the approximations and study-profile choices remain this project's responsibility.

---

<p align="center"><b>- oOo -</b></p>

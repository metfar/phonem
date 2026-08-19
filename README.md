# phonem.py 1.4.0

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

This is intentional groundwork for a separate `pronounce.py` that can later consume IPA and send audio to the default device or files. `pronounce.py` is not part of this release yet.

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

La salida IPA normal queda limpia en `stdout`; `-v` escribe los diagnósticos en `stderr`. Eso deja preparada la arquitectura para el próximo programa:

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

`pronounce.py` será otra herramienta, no una función incrustada aquí. Así podrá hablar por el dispositivo de audio por defecto o escribir `--wav`, `--ogg` o `--mp3` sin mezclar responsabilidades.

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

L'IPA normal est écrit sur `stdout`; les diagnostics de `-v` vont sur `stderr`. Cela prépare directement le futur pipeline :

```bash
./phonem.py "1 2 3" -l fr-fr | ./pronounce.py
```

Le futur `pronounce.py` restera un programme séparé afin de pouvoir envoyer le son vers le périphérique par défaut ou produire `--wav`, `--ogg` ou `--mp3` sans mélanger phonémisation et synthèse audio.

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

The references describe language usage; the approximations and study-profile choices remain this project's responsibility.

---

<p align="center"><b>- oOo -</b></p>

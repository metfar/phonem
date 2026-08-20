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

"""pronounce.py - Speak or export IPA phonemes with Piper.

EN: pronounce.py consumes IPA from a positional argument, a file, or stdin. Piper
    is used as the phoneme-to-audio engine because current Piper releases accept
    raw eSpeak/IPA phoneme blocks. A Piper voice is still required: IPA describes
    sounds, but it does not identify the intended speaker, language model, or
    acoustic voice. The voice may be selected explicitly or through a small JSON
    configuration file.
ES: pronounce.py consume IPA desde un argumento posicional, un archivo o stdin.
    Piper se usa como motor fonema-a-audio porque las versiones actuales aceptan
    bloques de fonemas eSpeak/IPA crudos. Sigue siendo necesaria una voz Piper:
    el IPA describe sonidos, pero no identifica por sí solo el hablante, el modelo
    lingüístico ni la voz acústica. La voz puede elegirse explícitamente o mediante
    un pequeño archivo JSON de configuración.
FR: pronounce.py lit l'API depuis un argument positionnel, un fichier ou stdin.
    Piper sert de moteur phonèmes-vers-audio car les versions actuelles acceptent
    des blocs de phonèmes eSpeak/API bruts. Une voix Piper reste nécessaire :
    l'API décrit les sons, mais n'identifie ni le locuteur, ni le modèle linguistique,
    ni la voix acoustique. La voix peut être choisie explicitement ou via un petit
    fichier JSON de configuration.

EN: License: GNU GPL version 2 or (at your option) any later version.
ES: Licencia: GNU GPL versión 2 o, a elección del usuario, cualquier versión posterior.
FR: Licence : GNU GPL version 2 ou, à votre choix, toute version ultérieure.
"""

import argparse;
import json;
import os;
import shutil;
import subprocess;
import sys;
import tempfile;
import time;
import urllib.error;
import urllib.request;
import wave;
from pathlib import Path;

from language_profiles import (
    CANONICAL_PROJECT_LANGUAGES,
    SHORT_LANGUAGE_ALIASES,
    canonical_language,
    short_alias_for,
);

# EN: Program metadata and logical-language keys.
# ES: Metadatos del programa y claves de idiomas lógicos.
# FR: Métadonnées du programme et clés de langues logiques.
PROGRAM = "pronounce.py";
VERSION = "0.6.0";
CONFIG_SCHEMA_VERSION = 2;
PIPER_CATALOG_URL = "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json";
PIPER_CATALOG_MAX_AGE = 24 * 60 * 60;
QUALITY_ORDER = {"high": 0, "medium": 1, "low": 2, "x_low": 3};

# EN: Extra study pauses are added after Piper synthesis, in seconds.
# ES: Las pausas extra de estudio se agregan después de sintetizar, en segundos.
# FR: Les pauses d’étude supplémentaires sont ajoutées après la synthèse, en secondes.
DEFAULT_WORD_PAUSE = 0.04;
DEFAULT_COMMA_PAUSE = 0.16;
DEFAULT_CLAUSE_PAUSE = 0.24;
DEFAULT_SENTENCE_PAUSE = 0.40;
PUNCTUATION_PHONEMES = set(",;:.!?");
SUPPORTED_LOGICAL_LANGUAGES = (
    "en-ca", "en-us", "en-gb", "en-rp", "en-lancashire", "en-nyc",
    "es-uy", "es-es",
    "fr-fr", "fr-ca", "fr-be", "fr-ch", "fr-ch-qv",
);

# EN: Logical study profiles are intentionally separated from Piper catalogue locales.
# ES: Los perfiles lógicos de estudio se separan deliberadamente de los locales de Piper.
# FR: Les profils logiques d’étude sont volontairement séparés des locales du catalogue Piper.
PIPER_PROFILE_LOCALES = {
    "en-ca": ("en_US", "en_GB"),
    "en-us": ("en_US",),
    "en-gb": ("en_GB",),
    "en-rp": ("en_GB",),
    "en-lancashire": ("en_GB",),
    "en-nyc": ("en_US",),
    "es-es": ("es_ES",),
    "es-uy": ("es_AR",),
    "fr-fr": ("fr_FR",),
    "fr-ca": ("fr_FR",),
    "fr-be": ("fr_FR",),
    "fr-ch": ("fr_FR",),
    "fr-ch-qv": ("fr_FR",),
};

PIPER_PROFILE_NOTES = {
    "en-ca": "approximation: Piper currently has no en_CA catalogue locale",
    "en-rp": "approximation: uses a British acoustic model",
    "en-lancashire": "approximation: uses a British acoustic model",
    "en-nyc": "approximation: uses a US acoustic model",
    "es-uy": "approximation: es_AR is the closest current Rioplatense catalogue locale",
    "fr-ca": "approximation: Piper currently has no fr_CA catalogue locale",
    "fr-be": "approximation: Piper currently has no fr_BE catalogue locale",
    "fr-ch": "approximation: Piper currently has no fr_CH catalogue locale",
    "fr-ch-qv": "approximation: Piper currently has no fr_CH catalogue locale",
};

# EN: Built-in profile defaults are conservative starting points. Only es-uy has been
#     empirically tuned in this project so far. Users may override every value in JSON.
# ES: Los valores predeterminados son puntos de partida conservadores. Por ahora sólo
#     es-uy fue calibrado empíricamente en este proyecto. Todo se puede sobrescribir en JSON.
# FR: Les valeurs par défaut sont des points de départ prudents. Pour l'instant, seul
#     es-uy a été réglé empiriquement dans ce projet. Tout peut être remplacé via JSON.
PROFILE_DEFAULTS = {
    "en-ca": {"voice": "en_US-lessac-high", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "en-us": {"voice": "en_US-lessac-high", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "starting-point"},
    "en-gb": {"voice": "en_GB-cori-high", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "starting-point"},
    "en-rp": {"voice": "en_GB-cori-high", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "en-lancashire": {"voice": "en_GB-northern_english_male-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "en-nyc": {"voice": "en_US-lessac-high", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "es-es": {"voice": "es_ES-davefx-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "starting-point"},
    "es-uy": {"voice": "es_AR-daniela-high", "length_scale": 2.0, "volume": 1.0, "extra_pauses": False, "validation": "user-tested"},
    "fr-fr": {"voice": "fr_FR-siwis-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "starting-point"},
    "fr-ca": {"voice": "fr_FR-siwis-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "fr-be": {"voice": "fr_FR-siwis-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "fr-ch": {"voice": "fr_FR-siwis-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
    "fr-ch-qv": {"voice": "fr_FR-siwis-medium", "length_scale": 1.0, "volume": 1.0, "extra_pauses": False, "validation": "approximation"},
};


# EN: Configuration and model discovery.
# ES: Configuración y descubrimiento de modelos.
# FR: Configuration et recherche des modèles.
def default_config_path():
    """EN: Return the XDG-aware configuration path.
    ES: Devuelve la ruta de configuración respetando XDG.
    FR: Renvoie le chemin de configuration en respectant XDG.""";
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME");
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / "phonem" / "pronounce.json";
    return Path.home() / ".config" / "phonem" / "pronounce.json";


def default_catalog_cache_path():
    """EN: Return the XDG-aware Piper catalogue cache path.
    ES: Devuelve la ruta XDG de caché del catálogo de Piper.
    FR: Renvoie le chemin XDG du cache du catalogue Piper.""";
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME");
    if xdg_cache_home:
        return Path(xdg_cache_home).expanduser() / "phonem" / "piper-voices.json";
    return Path.home() / ".cache" / "phonem" / "piper-voices.json";


def default_data_dirs():
    """EN: Return XDG-aware Piper model search directories.
    ES: Devuelve los directorios XDG donde buscar modelos Piper.
    FR: Renvoie les répertoires XDG où chercher les modèles Piper.""";
    result = [];
    xdg_data_home = os.environ.get("XDG_DATA_HOME");
    if xdg_data_home:
        result.append(Path(xdg_data_home).expanduser() / "piper");
    else:
        result.append(Path.home() / ".local" / "share" / "piper");
    result.append(Path.cwd());
    return result;


def _copy_profile_defaults():
    """EN: Return JSON-safe copies of profile defaults.
    ES: Devuelve copias seguras para JSON de los perfiles predeterminados.
    FR: Renvoie des copies sérialisables JSON des profils par défaut.""";
    return {language: dict(values) for language, values in PROFILE_DEFAULTS.items()};


def migrate_legacy_alias_config(data):
    """EN: Normalize schema-1 short language aliases without deleting old keys.
    ES: Normaliza alias cortos del esquema 1 sin borrar claves antiguas.
    FR: Normalise les alias courts du schéma 1 sans supprimer les anciennes clés.""";
    if not isinstance(data, dict):
        return data;
    migrated = dict(data);
    default_language = migrated.get("default_language");
    if isinstance(default_language, str):
        normalized = canonical_language(default_language);
        if normalized:
            migrated["default_language"] = normalized;
    # EN: Old files may contain generic en/es/fr entries. Canonical entries win.
    # ES: Archivos viejos pueden contener en/es/fr. Las entradas canónicas ganan.
    # FR: Les anciens fichiers peuvent contenir en/es/fr. Les entrées canoniques gagnent.
    voices = migrated.get("voices");
    if isinstance(voices, dict):
        voices = dict(voices);
        for alias, canonical in SHORT_LANGUAGE_ALIASES.items():
            if canonical not in voices and alias in voices:
                voices[canonical] = voices[alias];
            voices.pop(alias, None);
        migrated["voices"] = voices;
    profiles = migrated.get("profiles");
    if isinstance(profiles, dict):
        profiles = dict(profiles);
        for alias, canonical in SHORT_LANGUAGE_ALIASES.items():
            if canonical not in profiles and alias in profiles:
                profiles[canonical] = profiles[alias];
            profiles.pop(alias, None);
        migrated["profiles"] = profiles;
    return migrated;


def config_template():
    """EN: Return the complete configuration template with per-language defaults.
    ES: Devuelve la configuración completa con valores predeterminados por idioma.
    FR: Renvoie la configuration complète avec des valeurs par langue.""";
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "generated_by": f"{PROGRAM} {VERSION}",
        "default_language": "fr-fr",
        "default_voice": "",
        "data_dirs": [],
        "voices": {language: "" for language in SUPPORTED_LOGICAL_LANGUAGES},
        "profiles": _copy_profile_defaults(),
    };


def deep_merge(base, override):
    """EN: Recursively merge a user JSON object over built-in defaults.
    ES: Mezcla recursivamente el JSON del usuario sobre los valores internos.
    FR: Fusionne récursivement le JSON utilisateur sur les valeurs intégrées.""";
    if isinstance(base, dict) and isinstance(override, dict):
        result = dict(base);
        for key, value in override.items():
            result[key] = deep_merge(result.get(key), value) if key in result else value;
        return result;
    return override;


def validate_config_schema(data, path=None):
    """EN: Reject malformed or newer configuration schemas before merging them.
    ES: Rechaza esquemas inválidos o más nuevos antes de mezclar la configuración.
    FR: Refuse les schémas invalides ou plus récents avant de fusionner la configuration.""";
    schema = data.get("schema_version", 0);
    if not isinstance(schema, int) or schema < 0:
        location = f" '{path}'" if path is not None else "";
        raise RuntimeError(f"configuration{location} has an invalid schema_version: {schema!r}");
    if schema > CONFIG_SCHEMA_VERSION:
        location = f" '{path}'" if path is not None else "";
        raise RuntimeError(
            f"configuration{location} uses schema_version={schema}, newer than supported "
            f"schema_version={CONFIG_SCHEMA_VERSION}; refusing to downgrade it"
        );
    return schema;


def profile_settings(config, language):
    """EN: Return resolved synthesis settings for one logical profile.
    ES: Devuelve los ajustes de síntesis resueltos para un perfil lógico.
    FR: Renvoie les réglages de synthèse résolus pour un profil logique.""";
    language = canonical_language(language);
    profiles = config.get("profiles", {});
    if isinstance(profiles, dict):
        profile = profiles.get(language, {});
        if isinstance(profile, dict):
            return profile;
    return {};


def expand_path(value):
    """EN: Expand environment variables and a leading tilde.
    ES: Expande variables de entorno y la tilde inicial.
    FR: Développe les variables d’environnement et le tilde initial.""";
    return Path(os.path.expandvars(os.path.expanduser(str(value))));


def load_config(path):
    """EN: Load JSON overrides over safe built-in defaults.
    ES: Carga overrides JSON sobre valores internos seguros.
    FR: Charge les surcharges JSON sur des valeurs intégrées sûres.""";
    defaults = config_template();
    if not path.exists():
        return defaults;
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle);
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read configuration '{path}': {exc}") from exc;
    if not isinstance(data, dict):
        raise RuntimeError(f"configuration '{path}' must contain a JSON object");
    validate_config_schema(data, path);
    data = migrate_legacy_alias_config(data);
    return deep_merge(defaults, data);


def write_config_template(path, force=False):
    """EN: Write a fresh configuration template.
    ES: Escribe una plantilla de configuración nueva.
    FR: Écrit un nouveau modèle de configuration.""";
    if path.exists() and not force:
        raise RuntimeError(f"configuration already exists: {path} (use --force)");
    _write_json_atomic(path, config_template());


# EN: Piper catalogue and local-model inventory.
# ES: Catálogo de Piper e inventario de modelos locales.
# FR: Catalogue Piper et inventaire des modèles locaux.
def _read_json_file(path):
    """EN: Read a JSON object from disk.
    ES: Lee un objeto JSON desde disco.
    FR: Lit un objet JSON depuis le disque.""";
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle);
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON '{path}': {exc}") from exc;
    if not isinstance(data, dict):
        raise RuntimeError(f"JSON '{path}' must contain an object");
    return data;


def _write_json_atomic(path, data):
    """EN: Atomically write UTF-8 JSON beside the destination before replacing it.
    ES: Escribe JSON UTF-8 de forma atómica antes de reemplazar el destino.
    FR: Écrit le JSON UTF-8 de façon atomique avant de remplacer la destination.""";
    path = Path(path);
    path.parent.mkdir(parents=True, exist_ok=True);
    temporary = None;
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name);
            json.dump(data, handle, ensure_ascii=False, indent=2);
            handle.write("\n");
            handle.flush();
            os.fsync(handle.fileno());
        os.replace(temporary, path);
    except OSError as exc:
        raise RuntimeError(f"cannot write configuration '{path}': {exc}") from exc;
    finally:
        if temporary is not None and temporary.exists():
            try:
                temporary.unlink();
            except OSError:
                pass;


def _config_backup_path(path):
    """EN: Return a non-destructive timestamped backup path.
    ES: Devuelve una ruta de backup con fecha sin pisar backups anteriores.
    FR: Renvoie un chemin de sauvegarde horodaté sans écraser les précédentes.""";
    stamp = time.strftime("%Y%m%d-%H%M%S");
    base = path.with_name(f"{path.name}.bak-{stamp}");
    candidate = base;
    counter = 1;
    while candidate.exists():
        candidate = path.with_name(f"{base.name}-{counter}");
        counter += 1;
    return candidate;


def update_config_file(path):
    """EN: Add new shipped defaults while preserving every existing user value.
    ES: Agrega defaults nuevos conservando todos los valores existentes del usuario.
    FR: Ajoute les nouvelles valeurs intégrées sans écraser les valeurs utilisateur.""";
    path = Path(path);
    defaults = config_template();
    if not path.exists():
        _write_json_atomic(path, defaults);
        return "created", None;
    existing = _read_json_file(path);
    validate_config_schema(existing, path);
    migrated = migrate_legacy_alias_config(existing);
    merged = deep_merge(defaults, migrated);
    merged["schema_version"] = CONFIG_SCHEMA_VERSION;
    merged["generated_by"] = f"{PROGRAM} {VERSION}";
    if merged == existing:
        return "unchanged", None;
    backup = _config_backup_path(path);
    try:
        shutil.copy2(path, backup);
    except OSError as exc:
        raise RuntimeError(f"cannot back up configuration '{path}' to '{backup}': {exc}") from exc;
    try:
        _write_json_atomic(path, merged);
    except RuntimeError:
        try:
            shutil.copy2(backup, path);
        except OSError:
            pass;
        raise;
    return "updated", backup;


def _write_catalog_cache(path, data):
    """EN: Write the fetched Piper catalogue cache.
    ES: Escribe la caché descargada del catálogo de Piper.
    FR: Écrit le cache téléchargé du catalogue Piper.""";
    try:
        path.parent.mkdir(parents=True, exist_ok=True);
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False);
            handle.write("\n");
    except OSError:
        return;


def _fetch_catalog(url):
    """EN: Fetch Piper voices.json with only the Python standard library.
    ES: Descarga voices.json de Piper usando sólo la biblioteca estándar.
    FR: Télécharge voices.json de Piper avec la bibliothèque standard seulement.""";
    request = urllib.request.Request(url, headers={"User-Agent": f"{PROGRAM}/{VERSION}"});
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read();
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError(f"cannot download Piper catalogue '{url}': {exc}") from exc;
    try:
        data = json.loads(payload.decode("utf-8"));
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Piper catalogue from '{url}': {exc}") from exc;
    if not isinstance(data, dict):
        raise RuntimeError(f"Piper catalogue from '{url}' must contain a JSON object");
    return data;


def load_catalog(args):
    """EN: Load a local/remote Piper catalogue with an XDG cache fallback.
    ES: Carga el catálogo Piper local/remoto con fallback a una caché XDG.
    FR: Charge le catalogue Piper local/distant avec repli sur un cache XDG.""";
    if args.catalog:
        source = str(args.catalog);
        if source.startswith("http://") or source.startswith("https://"):
            return _fetch_catalog(source), source;
        return _read_json_file(expand_path(source)), source;
    cache = default_catalog_cache_path();
    if cache.is_file() and not args.refresh_catalog:
        try:
            age = time.time() - cache.stat().st_mtime;
        except OSError:
            age = PIPER_CATALOG_MAX_AGE + 1;
        if args.offline or age <= PIPER_CATALOG_MAX_AGE:
            return _read_json_file(cache), str(cache);
    if args.offline:
        raise RuntimeError(f"offline mode requested and Piper catalogue cache is absent/stale: {cache}");
    try:
        data = _fetch_catalog(PIPER_CATALOG_URL);
        _write_catalog_cache(cache, data);
        return data, PIPER_CATALOG_URL;
    except RuntimeError as exc:
        if cache.is_file():
            print(f"{PROGRAM}: warning: {exc}; using cached catalogue {cache}", file=sys.stderr);
            return _read_json_file(cache), str(cache);
        raise;


def profile_locales(profile):
    """EN: Return preferred Piper catalogue locales for a logical study profile.
    ES: Devuelve los locales Piper preferidos para un perfil lógico de estudio.
    FR: Renvoie les locales Piper préférées pour un profil logique d’étude.""";
    return PIPER_PROFILE_LOCALES.get(canonical_language(profile), ());


def print_logical_languages(config):
    """EN: Print study profiles, default voices and synthesis settings.
    ES: Imprime perfiles, voces predeterminadas y ajustes de síntesis.
    FR: Affiche les profils, voix par défaut et réglages de synthèse.""";
    print(f"{'PROFILE':15} {'SHORT':5} {'PIPER LOCALE(S)':18} {'DEFAULT VOICE':38} {'LEN':5} {'VOL':5} {'PAUSE':6} STATUS");
    for profile in SUPPORTED_LOGICAL_LANGUAGES:
        locales = ",".join(profile_locales(profile)) or "-";
        settings = profile_settings(config, profile);
        voice = str(settings.get("voice", "")) or "-";
        length_scale = float(settings.get("length_scale", 1.0));
        volume = float(settings.get("volume", 1.0));
        pauses = "extra" if bool(settings.get("extra_pauses", False)) else "piper";
        validation = str(settings.get("validation", "starting-point"));
        short = short_alias_for(profile) or "-";
        print(f"{profile:15} {short:5} {locales:18} {voice[:38]:38} {length_scale:<5g} {volume:<5g} {pauses:6} {validation}");


def _catalog_language(info):
    """EN: Return the normalized language object from a catalogue entry.
    ES: Devuelve el objeto de idioma normalizado de una entrada del catálogo.
    FR: Renvoie l’objet langue normalisé d’une entrée du catalogue.""";
    language = info.get("language", {}) if isinstance(info, dict) else {};
    return language if isinstance(language, dict) else {};


def print_catalog_languages(catalog):
    """EN: Print Piper catalogue locales and model counts.
    ES: Imprime locales del catálogo Piper y cantidad de modelos.
    FR: Affiche les locales du catalogue Piper et le nombre de modèles.""";
    languages = {};
    for info in catalog.values():
        if not isinstance(info, dict):
            continue;
        language = _catalog_language(info);
        code = str(language.get("code", "")).strip();
        if not code:
            continue;
        row = languages.setdefault(code, {
            "native": str(language.get("name_native", "")),
            "english": str(language.get("name_english", "")),
            "country": str(language.get("country_english", "")),
            "count": 0,
        });
        row["count"] += 1;
    print(f"{'LOCALE':10} {'LANGUAGE':22} {'COUNTRY':24} MODELS");
    for code in sorted(languages):
        row = languages[code];
        language_name = row["native"] or row["english"] or "-";
        print(f"{code:10} {language_name[:22]:22} {row['country'][:24]:24} {row['count']}");


def _voice_matches(key, info, selector):
    """EN: Match a catalogue model against a logical profile, locale, family or name.
    ES: Filtra un modelo por perfil lógico, locale, familia o nombre.
    FR: Filtre un modèle par profil logique, locale, famille ou nom.""";
    if not selector or selector == "*":
        return True;
    language = _catalog_language(info);
    code = str(language.get("code", ""));
    family = str(language.get("family", ""));
    canonical_selector = canonical_language(selector);
    if canonical_selector in PIPER_PROFILE_LOCALES:
        return code in profile_locales(canonical_selector);
    if selector == code or selector == family:
        return True;
    needle = selector.lower();
    name = str(info.get("name", "")).lower();
    return needle in key.lower() or needle in name;


def resolve_catalog_voice(catalog, requested, language=""):
    """EN: Resolve an exact catalogue model key or a unique human voice name.
    ES: Resuelve una clave exacta del catálogo o un nombre humano de voz único.
    FR: Résout une clé exacte du catalogue ou un nom de voix humain unique.""";
    requested = str(requested or "").strip();
    if not requested:
        return None;
    normalized = requested[:-5] if requested.endswith(".onnx") else requested;
    if normalized in catalog and isinstance(catalog.get(normalized), dict):
        return normalized;
    language = canonical_language(language);
    locales = set(profile_locales(language)) if language in PIPER_PROFILE_LOCALES else set();
    matches = [];
    for key, info in catalog.items():
        if not isinstance(info, dict):
            continue;
        name = str(info.get("name", "")).strip();
        if name.lower() != normalized.lower():
            continue;
        locale = str(_catalog_language(info).get("code", ""));
        matches.append((str(key), locale));
    if locales:
        scoped = [item for item in matches if item[1] in locales];
        if scoped:
            matches = scoped;
    if len(matches) == 1:
        return matches[0][0];
    if len(matches) > 1:
        choices = ", ".join(key for key, _locale in sorted(matches));
        raise RuntimeError(
            f"Piper voice name '{requested}' is ambiguous; choose one model: {choices}"
        );
    return None;


def catalogue_install_hint(model_key, data_dir=None):
    """EN: Return a copy/paste installation command for one catalogue model.
    ES: Devuelve un comando copiable para instalar un modelo del catálogo.
    FR: Renvoie une commande prête à copier pour installer un modèle du catalogue.""";
    command = f"{PROGRAM} --download-voice {model_key}";
    if data_dir is not None:
        command += f" --download-dir {data_dir}";
    return command;


def scan_local_models(data_dirs):
    """EN: Discover local Piper ONNX models and inspect their companion JSON files.
    ES: Descubre modelos ONNX locales e inspecciona sus JSON asociados.
    FR: Découvre les modèles ONNX locaux et inspecte leurs JSON associés.""";
    result = [];
    seen = set();
    for directory in data_dirs:
        if not directory.is_dir():
            continue;
        try:
            candidates = directory.rglob("*.onnx");
            for model in candidates:
                try:
                    key = str(model.resolve());
                except OSError:
                    key = str(model);
                if key in seen:
                    continue;
                seen.add(key);
                config_path = Path(f"{model}.json");
                config = {};
                if config_path.is_file():
                    try:
                        config = _read_json_file(config_path);
                    except RuntimeError:
                        config = {};
                language = config.get("language", {});
                locale = language.get("code", "") if isinstance(language, dict) else "";
                espeak = config.get("espeak", {});
                espeak_voice = espeak.get("voice", "") if isinstance(espeak, dict) else "";
                speakers = config.get("num_speakers", "");
                quality = model.stem.rsplit("-", 1)[-1];
                if quality not in QUALITY_ORDER:
                    quality = "";
                result.append({
                    "key": model.stem,
                    "path": model,
                    "locale": str(locale),
                    "espeak": str(espeak_voice),
                    "speakers": str(speakers),
                    "quality": quality,
                });
        except OSError:
            continue;
    return sorted(result, key=lambda row: (row["locale"], row["key"], str(row["path"])));


def _model_matches(row, selector):
    """EN: Match an installed model against a logical profile, locale or name.
    ES: Filtra un modelo instalado por perfil lógico, locale o nombre.
    FR: Filtre un modèle installé par profil logique, locale ou nom.""";
    if not selector or selector == "*":
        return True;
    canonical_selector = canonical_language(selector);
    if canonical_selector in PIPER_PROFILE_LOCALES:
        return row.get("locale", "") in profile_locales(canonical_selector);
    needle = selector.lower();
    return needle in row.get("key", "").lower() or needle == row.get("locale", "").lower();


def print_local_models(rows, selector=None):
    """EN: Print locally installed Piper models.
    ES: Imprime modelos Piper instalados localmente.
    FR: Affiche les modèles Piper installés localement.""";
    selected = [row for row in rows if _model_matches(row, selector)];
    if not selected:
        print("No matching local Piper models found.");
        return;
    print(f"{'MODEL':38} {'LOCALE':9} {'QUALITY':8} {'SPK':4} PATH");
    for row in selected:
        print(f"{row['key'][:38]:38} {row['locale'][:9]:9} {row['quality'][:8]:8} {row['speakers'][:4]:4} {row['path']}");


def print_catalog_voices(catalog, selector, local_rows):
    """EN: Print catalogue voice models, sorted by locale/voice/quality.
    ES: Imprime modelos de voz del catálogo, ordenados por locale/voz/calidad.
    FR: Affiche les modèles vocaux du catalogue, triés par locale/voix/qualité.""";
    installed = {row["key"] for row in local_rows};
    rows = [];
    for key, info in catalog.items():
        if not isinstance(info, dict) or not _voice_matches(key, info, selector):
            continue;
        language = _catalog_language(info);
        rows.append({
            "key": str(key),
            "locale": str(language.get("code", "")),
            "voice": str(info.get("name", "")),
            "quality": str(info.get("quality", "")),
            "speakers": str(info.get("num_speakers", "")),
            "installed": "installed" if str(key) in installed else "remote",
        });
    rows.sort(key=lambda row: (
        row["locale"],
        row["voice"].lower(),
        QUALITY_ORDER.get(row["quality"], 99),
        row["key"],
    ));
    if not rows:
        raise RuntimeError(f"no Piper catalogue voices match '{selector or '*'}'");
    print(f"{'VOICE MODEL':40} {'LOCALE':9} {'VOICE':22} {'QUALITY':8} {'SPK':4} STATUS");
    for row in rows:
        print(f"{row['key'][:40]:40} {row['locale'][:9]:9} {row['voice'][:22]:22} {row['quality'][:8]:8} {row['speakers'][:4]:4} {row['installed']}");
    print(f"# remote = listed by Piper but not installed; install with: {PROGRAM} --download-voice MODEL");


def download_voice(voice, destination):
    """EN: Delegate voice downloading to Piper's official downloader module.
    ES: Delega la descarga de la voz al módulo oficial de Piper.
    FR: Délègue le téléchargement de la voix au module officiel de Piper.""";
    destination.mkdir(parents=True, exist_ok=True);
    command = [sys.executable, "-m", "piper.download_voices", voice, "--data-dir", str(destination)];
    try:
        completed = subprocess.run(command, check=False);
    except OSError as exc:
        raise RuntimeError(f"cannot start Piper voice downloader: {exc}") from exc;
    if completed.returncode != 0:
        raise RuntimeError(f"Piper voice downloader failed with exit status {completed.returncode}");


def configured_voice_for_language(config, language):
    """EN: Return the effective configured voice name for one logical profile.
    ES: Devuelve la voz configurada efectiva para un perfil lógico.
    FR: Renvoie la voix configurée effective pour un profil logique.""";
    language = canonical_language(language);
    voices = config.get("voices", {});
    if isinstance(voices, dict):
        legacy = str(voices.get(language, "") or "").strip();
        if legacy:
            return legacy;
    return str(profile_settings(config, language).get("voice", "") or "").strip();


def download_default_voices(args, config, data_dirs):
    """EN: Download unique configured profile voices, skipping installed models by default.
    ES: Descarga las voces únicas de los perfiles y omite las ya instaladas por defecto.
    FR: Télécharge les voix uniques des profils et ignore par défaut celles déjà installées.""";
    desired = {};
    catalog = None;
    catalog_source = None;
    for language in SUPPORTED_LOGICAL_LANGUAGES:
        requested = configured_voice_for_language(config, language);
        if not requested:
            continue;
        local_model = resolve_named_voice(requested, data_dirs);
        if local_model is not None:
            canonical = local_model.stem;
        else:
            if catalog is None:
                catalog, catalog_source = load_catalog(args);
                if args.verbose:
                    print(f"catalog={catalog_source}", file=sys.stderr);
            canonical = resolve_catalog_voice(catalog, requested, language=language);
            if canonical is None:
                raise RuntimeError(
                    f"configured voice '{requested}' for profile '{language}' was not found in the Piper catalogue"
                );
        desired.setdefault(canonical, []).append(language);

    if not desired:
        raise RuntimeError("no default/profile voices are configured");

    destination = args.download_dir or (data_dirs[0] if data_dirs else default_data_dirs()[0]);
    downloaded = 0;
    installed = 0;
    for canonical, profiles in desired.items():
        local_model = resolve_named_voice(canonical, data_dirs);
        profile_text = ",".join(profiles);
        if local_model is not None and not args.force_download:
            installed += 1;
            print(f"voice={canonical}");
            print("status=already-installed");
            print(f"profiles={profile_text}");
            print(f"path={local_model}");
            continue;
        download_voice(canonical, destination);
        downloaded += 1;
        print(f"voice={canonical}");
        print("status=downloaded");
        print(f"profiles={profile_text}");
        print(f"directory={destination}");

    print(f"summary=unique:{len(desired)} downloaded:{downloaded} already-installed:{installed}");


# EN: IPA input and voice/model resolution.
# ES: Entrada IPA y resolución de voz/modelo.
# FR: Entrée API et résolution de la voix/du modèle.
def read_ipa(args):
    """EN: Read IPA from one and only one input source.
    ES: Lee IPA desde una única fuente de entrada.
    FR: Lit l’API depuis une seule source d’entrée.""";
    sources = int(args.ipa is not None) + int(args.input is not None);
    stdin_has_data = not sys.stdin.isatty();
    if sources > 1:
        raise RuntimeError("use only one IPA input source: positional text or --input");
    if args.ipa is not None:
        value = args.ipa;
    elif args.input is not None:
        try:
            value = Path(args.input).read_text(encoding="utf-8");
        except OSError as exc:
            raise RuntimeError(f"cannot read IPA input '{args.input}': {exc}") from exc;
    elif stdin_has_data:
        value = sys.stdin.read();
    else:
        raise RuntimeError("no IPA input; provide an argument, --input FILE, or pipe stdin");
    value = value.strip();
    if not value:
        raise RuntimeError("IPA input is empty");
    return value;


def collect_data_dirs(args, config):
    """EN: Build an ordered, duplicate-free model search path.
    ES: Construye una ruta ordenada de búsqueda de modelos, sin duplicados.
    FR: Construit un chemin ordonné de recherche des modèles, sans doublons.""";
    values = [];
    for item in args.data_dir or []:
        values.append(expand_path(item));
    for item in config.get("data_dirs", []):
        values.append(expand_path(item));
    values.extend(default_data_dirs());
    result = [];
    seen = set();
    for path in values:
        key = str(path.resolve(strict=False));
        if key not in seen:
            seen.add(key);
            result.append(path);
    return result;


def resolve_named_voice(name, data_dirs):
    """EN: Resolve a Piper voice name or path to an ONNX model.
    ES: Resuelve un nombre o ruta de voz Piper hacia un modelo ONNX.
    FR: Résout un nom ou chemin de voix Piper vers un modèle ONNX.""";
    if not name:
        return None;
    candidate = expand_path(name);
    if candidate.is_file():
        return candidate;
    variants = [name];
    if not str(name).endswith(".onnx"):
        variants.append(f"{name}.onnx");
    for directory in data_dirs:
        for variant in variants:
            candidate = directory / variant;
            if candidate.is_file():
                return candidate;
    return None;


def resolve_model(args, config):
    """EN: Resolve the model; explicit CLI values take precedence.
    ES: Resuelve el modelo; los valores explícitos de CLI tienen prioridad.
    FR: Résout le modèle; les valeurs CLI explicites sont prioritaires.""";
    data_dirs = collect_data_dirs(args, config);
    language = canonical_language(args.language or config.get("default_language") or "");
    requested = "";
    source = "";
    if args.model:
        requested = args.model;
        source = "--model";
    elif args.voice:
        requested = args.voice;
        source = "--voice";
    elif language:
        voices = config.get("voices", {});
        if isinstance(voices, dict):
            requested = voices.get(language, "") or "";
            if requested:
                source = f"config voices[{language}]";
        if not requested:
            profile = profile_settings(config, language);
            requested = str(profile.get("voice", "") or "");
            if requested:
                source = f"config profiles[{language}].voice";
    if not requested:
        requested = config.get("default_voice", "") or "";
        if requested:
            source = "config default_voice";
    if not requested:
        raise RuntimeError(
            "no Piper voice selected; use --model PATH, --voice NAME, or configure "
            f"{args.config}"
        );
    model = resolve_named_voice(requested, data_dirs);
    if model is None and source != "--model":
        catalogue_error = None;
        try:
            catalog, _catalog_source = load_catalog(args);
            canonical = resolve_catalog_voice(catalog, requested, language=language);
        except RuntimeError as exc:
            catalog = None;
            canonical = None;
            catalogue_error = exc;
        if canonical:
            model = resolve_named_voice(canonical, data_dirs);
            if model is None and args.auto_download:
                destination = args.download_dir or (data_dirs[0] if data_dirs else default_data_dirs()[0]);
                if args.verbose:
                    print(f"voice_download={canonical}", file=sys.stderr);
                    print(f"download_dir={destination}", file=sys.stderr);
                download_voice(canonical, destination);
                model = resolve_named_voice(canonical, data_dirs);
            if model is None:
                destination = args.download_dir or (data_dirs[0] if data_dirs else default_data_dirs()[0]);
                hint = catalogue_install_hint(canonical, destination);
                raise RuntimeError(
                    f"Piper voice '{requested}' resolves to catalogue model '{canonical}', "
                    f"but it is not installed locally. Run: {hint}; or add --auto-download"
                );
        elif catalogue_error is not None and args.verbose:
            print(f"catalog_warning={catalogue_error}", file=sys.stderr);
    if model is None:
        search = ", ".join(str(path) for path in data_dirs);
        raise RuntimeError(
            f"Piper voice/model '{requested}' from {source} was not found locally; searched: {search}. "
            f"Use {PROGRAM} --list-voices {language or '*'} to inspect catalogue voices."
        );
    model_config = Path(f"{model}.json");
    if not model_config.is_file():
        raise RuntimeError(f"Piper model config not found: {model_config}");
    return model, language, source;


def apply_profile_synthesis_settings(args, config, language):
    """EN: Apply CLI > JSON profile > built-in synthesis precedence.
    ES: Aplica precedencia CLI > perfil JSON > valores internos de síntesis.
    FR: Applique la priorité CLI > profil JSON > valeurs intégrées de synthèse.""";
    profile = profile_settings(config, language);
    args.length_scale = args.length_scale if args.length_scale is not None else float(profile.get("length_scale", 1.0));
    args.volume = args.volume if args.volume is not None else float(profile.get("volume", 1.0));
    args.word_pause = args.word_pause if args.word_pause is not None else float(profile.get("word_pause", DEFAULT_WORD_PAUSE));
    args.comma_pause = args.comma_pause if args.comma_pause is not None else float(profile.get("comma_pause", DEFAULT_COMMA_PAUSE));
    args.clause_pause = args.clause_pause if args.clause_pause is not None else float(profile.get("clause_pause", DEFAULT_CLAUSE_PAUSE));
    args.sentence_pause = args.sentence_pause if args.sentence_pause is not None else float(profile.get("sentence_pause", DEFAULT_SENTENCE_PAUSE));
    if args.extra_pauses is None:
        args.extra_pauses = bool(profile.get("extra_pauses", False));
    return profile;


# EN: Piper synthesis and audio output.
# ES: Síntesis Piper y salida de audio.
# FR: Synthèse Piper et sortie audio.
def prepare_ipa_for_synthesis(ipa):
    """EN: Normalize whitespace and map unsupported punctuation to pause-bearing symbols.
    ES: Normaliza espacios y mapea puntuación no soportada a símbolos con pausa.
    FR: Normalise les espaces et mappe la ponctuation non prise en charge vers des symboles de pause.""";
    ipa = ipa.replace("\r\n", "\n").replace("\r", "\n");
    ipa = ipa.replace("…", ".").replace("—", ";").replace("–", ";");
    ipa = ipa.replace("¿", "").replace("¡", "");
    lines = [" ".join(line.split()) for line in ipa.split("\n") if line.strip()];
    if not lines:
        return "";
    result = lines[0];
    for line in lines[1:]:
        if result and result[-1] in PUNCTUATION_PHONEMES:
            result += " ";
        else:
            result += ". ";
        result += line;
    return result;


def raw_phoneme_block(ipa):
    """EN: Wrap raw IPA in Piper’s explicit phoneme syntax.
    ES: Envuelve el IPA crudo con la sintaxis explícita de fonemas de Piper.
    FR: Encadre l’API brut avec la syntaxe explicite de phonèmes de Piper.""";
    if "[[" in ipa or "]]" in ipa:
        raise RuntimeError("IPA input must not contain Piper [[...]] delimiters");
    prepared = prepare_ipa_for_synthesis(ipa);
    if not prepared:
        raise RuntimeError("IPA input is empty after normalization");
    return f"[[ {prepared} ]]";


def pause_after_phoneme(phoneme, previous_phoneme, args):
    """EN: Return extra silence after one aligned phoneme, in seconds.
    ES: Devuelve el silencio extra después de un fonema alineado, en segundos.
    FR: Renvoie le silence supplémentaire après un phonème aligné, en secondes.""";
    if not args.extra_pauses:
        return 0.0;
    if phoneme == " ":
        if (not previous_phoneme) or previous_phoneme == " " or previous_phoneme in PUNCTUATION_PHONEMES:
            return 0.0;
        return args.word_pause;
    if phoneme == ",":
        return args.comma_pause;
    if phoneme in {";", ":"}:
        return args.clause_pause;
    if phoneme in {".", "!", "?"}:
        return args.sentence_pause;
    return 0.0;


def silence_bytes(seconds, sample_rate, sample_width, sample_channels):
    """EN: Build zero-valued PCM silence. ES: Construye silencio PCM. FR: Construit un silence PCM.""";
    frames = max(0, int(round(seconds * sample_rate)));
    return bytes(frames * sample_width * sample_channels);


def write_aligned_chunk(wav_file, audio_chunk, args):
    """EN: Write a Piper chunk and inject deterministic silence at aligned boundaries.
    ES: Escribe un bloque Piper e inyecta silencio determinista en los límites alineados.
    FR: Écrit un bloc Piper et injecte un silence déterministe aux limites alignées.""";
    alignments = audio_chunk.phoneme_alignments;
    if not alignments:
        raise RuntimeError(
            "Piper returned no phoneme alignments; install the alignment extra with: "
            "python3 -m pip install 'piper-tts[alignment]>=1.7,<2'"
        );
    raw_audio = audio_chunk.audio_int16_bytes;
    bytes_per_frame = audio_chunk.sample_width * audio_chunk.sample_channels;
    cursor = 0;
    previous = "";
    for alignment in alignments:
        frame_count = max(0, int(alignment.num_samples));
        byte_count = frame_count * bytes_per_frame;
        next_cursor = min(len(raw_audio), cursor + byte_count);
        if next_cursor > cursor:
            wav_file.writeframesraw(raw_audio[cursor:next_cursor]);
        cursor = next_cursor;
        pause = pause_after_phoneme(alignment.phoneme, previous, args);
        if pause > 0:
            wav_file.writeframesraw(silence_bytes(
                pause,
                audio_chunk.sample_rate,
                audio_chunk.sample_width,
                audio_chunk.sample_channels,
            ));
        if alignment.phoneme not in {"^", "$"}:
            previous = alignment.phoneme;
    if cursor < len(raw_audio):
        wav_file.writeframesraw(raw_audio[cursor:]);


def import_piper():
    """EN: Import Piper lazily so --help/--check work when it is absent.
    ES: Importa Piper tarde para que --help/--check funcionen si falta.
    FR: Importe Piper tardivement afin que --help/--check fonctionnent s’il manque.""";
    try:
        from piper import PiperVoice, SynthesisConfig;
    except ImportError as exc:
        raise RuntimeError(
            "Python package 'piper-tts' is not installed; run: "
            "python3 -m pip install -r requirements.txt"
        ) from exc;
    return PiperVoice, SynthesisConfig;


def synthesize_wav(ipa, model, destination, args):
    """EN: Synthesize IPA and optionally inject deterministic study pauses.
    ES: Sintetiza IPA e inyecta opcionalmente pausas de estudio deterministas.
    FR: Synthétise l’API et injecte éventuellement des pauses d’étude déterministes.""";
    PiperVoice, SynthesisConfig = import_piper();
    syn_config = SynthesisConfig(
        speaker_id=args.speaker,
        length_scale=args.length_scale,
        volume=args.volume,
        normalize_audio=not args.no_normalize,
    );
    use_alignments = bool(args.extra_pauses) and any((
        args.word_pause > 0,
        args.comma_pause > 0,
        args.clause_pause > 0,
        args.sentence_pause > 0,
    ));
    try:
        voice = PiperVoice.load(model, use_cuda=args.cuda, include_alignments=use_alignments);
    except TypeError as exc:
        if use_alignments:
            raise RuntimeError(
                "installed Piper does not expose alignment support; upgrade with: "
                "python3 -m pip install --upgrade 'piper-tts[alignment]>=1.7,<2'"
            ) from exc;
        raise RuntimeError(f"cannot load Piper voice '{model}': {exc}") from exc;
    except Exception as exc:
        raise RuntimeError(f"cannot load Piper voice '{model}': {exc}") from exc;
    try:
        with wave.open(str(destination), "wb") as wav_file:
            if not use_alignments:
                voice.synthesize_wav(raw_phoneme_block(ipa), wav_file, syn_config=syn_config);
                return;
            first_chunk = True;
            chunk_count = 0;
            for audio_chunk in voice.synthesize(
                raw_phoneme_block(ipa),
                syn_config=syn_config,
                include_alignments=True,
            ):
                chunk_count += 1;
                if first_chunk:
                    wav_file.setframerate(audio_chunk.sample_rate);
                    wav_file.setsampwidth(audio_chunk.sample_width);
                    wav_file.setnchannels(audio_chunk.sample_channels);
                    first_chunk = False;
                write_aligned_chunk(wav_file, audio_chunk, args);
            if chunk_count == 0:
                raise RuntimeError("Piper produced no audio chunks");
    except RuntimeError:
        raise;
    except Exception as exc:
        raise RuntimeError(f"Piper synthesis failed: {exc}") from exc;


def run_checked(command, purpose):
    """EN: Run an audio tool and turn failures into readable diagnostics.
    ES: Ejecuta una herramienta de audio y convierte fallos en diagnósticos legibles.
    FR: Exécute un outil audio et transforme les erreurs en diagnostics lisibles.""";
    try:
        completed = subprocess.run(command, check=False);
    except OSError as exc:
        raise RuntimeError(f"cannot start {purpose}: {exc}") from exc;
    if completed.returncode != 0:
        raise RuntimeError(f"{purpose} failed with exit status {completed.returncode}");


def play_wav(path, player=None):
    """EN: Play WAV audio through the default audio device.
    ES: Reproduce WAV por el dispositivo de audio predeterminado.
    FR: Lit le WAV sur le périphérique audio par défaut.""";
    executable = player or shutil.which("ffplay");
    if not executable:
        raise RuntimeError("ffplay was not found; install FFmpeg or use --wav FILE");
    run_checked(
        [str(executable), "-nodisp", "-autoexit", "-loglevel", "error", str(path)],
        "audio playback",
    );


def transcode_wav(source, destination):
    """EN: Convert WAV to a compressed format with FFmpeg.
    ES: Convierte WAV a un formato comprimido con FFmpeg.
    FR: Convertit le WAV vers un format compressé avec FFmpeg.""";
    ffmpeg = shutil.which("ffmpeg");
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found; it is required for --ogg and --mp3");
    run_checked(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), str(destination)],
        "audio conversion",
    );


# EN: Diagnostics and command-line interface.
# ES: Diagnóstico e interfaz de línea de comandos.
# FR: Diagnostic et interface en ligne de commande.
def dependency_status(args, config):
    """EN: Return dependency/configuration diagnostics without synthesis.
    ES: Devuelve diagnósticos de dependencias/configuración sin sintetizar.
    FR: Renvoie le diagnostic dépendances/configuration sans synthèse.""";
    status = [];
    status.append(("python", sys.version_info >= (3, 9), sys.version.split()[0], ">= 3.9"));
    try:
        import piper;
        version = getattr(piper, "__version__", "installed");
        status.append(("piper-tts", True, str(version), ">= 1.7, < 2"));
    except ImportError:
        status.append(("piper-tts", False, "not installed", ">= 1.7, < 2"));
    try:
        import onnx;
        version = getattr(onnx, "__version__", "installed");
        status.append(("onnx", True, str(version), "Piper alignment extra for study pauses"));
    except ImportError:
        status.append(("onnx", False, "not installed", "install piper-tts[alignment] for study pauses"));
    ffmpeg = shutil.which("ffmpeg");
    ffplay = shutil.which("ffplay");
    status.append(("ffmpeg", bool(ffmpeg), ffmpeg or "not found", "needed for OGG/MP3"));
    status.append(("ffplay", bool(ffplay), ffplay or "not found", "needed for default playback"));
    config_exists = args.config.is_file();
    status.append(("config", config_exists, str(args.config), "optional if --model/--voice is used"));
    if config_exists:
        try:
            model, language, source = resolve_model(args, config);
            detail = f"{model} ({language or 'no language'}, {source})";
            status.append(("voice", True, detail, "Piper ONNX + .json"));
        except RuntimeError as exc:
            status.append(("voice", False, str(exc), "configure before synthesis"));
    return status;


def print_status(status):
    """EN: Print dependency status in a shell-friendly table.
    ES: Imprime el estado de dependencias en una tabla apta para shell.
    FR: Affiche l’état des dépendances dans un tableau pratique en shell.""";
    for name, ok, found, expected in status:
        marker = "OK" if ok else "MISSING";
        print(f"{marker:7} {name:10} {found} [{expected}]");


def build_parser():
    """EN: Build the command-line parser.
    ES: Construye el analizador de línea de comandos.
    FR: Construit l’analyseur de ligne de commande.""";
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Speak IPA phonemes with Piper or export WAV/OGG/MP3 audio.",
    );
    parser.add_argument("ipa", nargs="?", help="IPA phonemes; stdin is used when omitted");
    parser.add_argument("-i", "--input", help="read IPA phonemes from UTF-8 file");
    parser.add_argument("-l", "--language", metavar="LANG", help="project language/profile; en=en-ca, es=es-uy, fr=fr-fr");
    parser.add_argument("--model", help="explicit Piper .onnx model path");
    parser.add_argument("--voice", help="installed Piper model key/path or unique catalogue voice name; use --list-voices");
    parser.add_argument("--data-dir", action="append", help="additional Piper model directory; may be repeated");
    parser.add_argument("--config", type=expand_path, default=default_config_path(), help="configuration JSON path");
    parser.add_argument("--catalog", help="Piper voices.json path or URL; default uses the official catalogue with XDG cache");
    parser.add_argument("--offline", action="store_true", help="do not access the network when reading the Piper catalogue");
    parser.add_argument("--refresh-catalog", action="store_true", help="force refreshing the cached Piper catalogue");
    inventory = parser.add_mutually_exclusive_group();
    inventory.add_argument("--list-languages", "--list-profiles", dest="list_languages", action="store_true", help="list logical study profiles, default voices and preferred Piper locales");
    inventory.add_argument("--list-catalog-languages", action="store_true", help="list language locales currently present in the Piper catalogue");
    inventory.add_argument("--list-voices", nargs="?", const="*", metavar="LANG", help="list Piper catalogue voice models; optionally filter by profile/locale/family/name");
    inventory.add_argument("--list-models", nargs="?", const="*", metavar="LANG", help="list locally installed ONNX models; optionally filter by profile/locale/name");
    inventory.add_argument("--download-voice", metavar="VOICE", help="download one Piper voice model with Piper's official downloader");
    inventory.add_argument("--download-defaults", action="store_true", help="download each unique voice referenced by the resolved language profiles");
    parser.add_argument("--download-dir", type=expand_path, help="destination for downloaded voices; defaults to the first model data directory");
    parser.add_argument("--force-download", action="store_true", help="download again even when a selected/default voice is already installed");
    parser.add_argument("--auto-download", action="store_true", help="download a catalogue voice automatically when --voice/config selects one that is not installed");
    config_action = parser.add_mutually_exclusive_group();
    config_action.add_argument("--init-config", action="store_true", help="write a fresh configuration template and exit");
    config_action.add_argument("--update-config", action="store_true", help="merge new shipped defaults into the configuration without overwriting existing user values");
    parser.add_argument("--force", action="store_true", help="allow --init-config to overwrite an existing file");
    output = parser.add_mutually_exclusive_group();
    output.add_argument("--wav", metavar="FILE", help="write WAV audio");
    output.add_argument("--ogg", metavar="FILE", help="write OGG audio through FFmpeg");
    output.add_argument("--mp3", metavar="FILE", help="write MP3 audio through FFmpeg");
    parser.add_argument("--player", help="ffplay-compatible executable for default playback");
    parser.add_argument("--length-scale", type=float, default=None, help="Piper phoneme length scale; default comes from the selected language profile");
    parser.add_argument("--volume", type=float, default=None, help="Piper output volume multiplier; default comes from the selected language profile");
    parser.add_argument("--word-pause", type=float, default=None, help="extra seconds after a word boundary when extra pauses are enabled");
    parser.add_argument("--comma-pause", type=float, default=None, help="extra seconds after ',' when extra pauses are enabled");
    parser.add_argument("--clause-pause", type=float, default=None, help="extra seconds after ';' or ':' when extra pauses are enabled");
    parser.add_argument("--sentence-pause", type=float, default=None, help="extra seconds after '.', '!' or '?' when extra pauses are enabled");
    pause_mode = parser.add_mutually_exclusive_group();
    pause_mode.add_argument("--extra-pauses", dest="extra_pauses", action="store_true", help="enable deterministic post-synthesis study pauses");
    pause_mode.add_argument("--no-extra-pauses", dest="extra_pauses", action="store_false", help="use Piper timing only; overrides the language profile");
    parser.set_defaults(extra_pauses=None);
    parser.add_argument("--speaker", type=int, help="speaker id for multi-speaker Piper models");
    parser.add_argument("--no-normalize", action="store_true", help="disable Piper audio normalization");
    parser.add_argument("--cuda", action="store_true", help="use CUDA; requires onnxruntime-gpu");
    parser.add_argument("--check", action="store_true", help="check Python/Piper/FFmpeg/configuration and exit");
    parser.add_argument("-v", "--verbose", action="store_true", help="show selected language, model and output on stderr");
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}");
    return parser;


def main():
    """EN: Program entry point.
    ES: Punto de entrada del programa.
    FR: Point d’entrée du programme.""";
    parser = build_parser();
    args = parser.parse_args();
    if args.language:
        args.language = canonical_language(args.language);
    try:
        if args.init_config:
            write_config_template(args.config, force=args.force);
            print(f"config={args.config}");
            print("status=created");
            return 0;
        if args.update_config:
            status, backup = update_config_file(args.config);
            print(f"config={args.config}");
            print(f"status={status}");
            if backup is not None:
                print(f"backup={backup}");
            return 0;
        config = load_config(args.config);
        if args.check:
            print_status(dependency_status(args, config));
            return 0;
        data_dirs = collect_data_dirs(args, config);
        if args.list_languages:
            print_logical_languages(config);
            return 0;
        if args.list_catalog_languages:
            catalog, source = load_catalog(args);
            if args.verbose:
                print(f"catalog={source}", file=sys.stderr);
            print_catalog_languages(catalog);
            return 0;
        if args.list_voices is not None:
            selector = args.list_voices if args.list_voices != "*" else (args.language or "*");
            catalog, source = load_catalog(args);
            if args.verbose:
                print(f"catalog={source}", file=sys.stderr);
            print_catalog_voices(catalog, selector, scan_local_models(data_dirs));
            return 0;
        if args.list_models is not None:
            selector = args.list_models if args.list_models != "*" else (args.language or "*");
            print_local_models(scan_local_models(data_dirs), selector);
            return 0;
        if args.download_defaults:
            download_default_voices(args, config, data_dirs);
            return 0;
        if args.download_voice:
            requested = args.download_voice;
            canonical = requested;
            local_requested = resolve_named_voice(requested, data_dirs);
            if local_requested is not None and not args.force_download:
                print(f"voice={local_requested.stem}");
                print("status=already-installed");
                print(f"path={local_requested}");
                return 0;
            try:
                catalog, source = load_catalog(args);
                resolved = resolve_catalog_voice(catalog, requested, language=args.language or "");
                if resolved:
                    canonical = resolved;
                elif requested not in catalog:
                    raise RuntimeError(f"Piper catalogue voice '{requested}' was not found");
                if args.verbose:
                    print(f"catalog={source}", file=sys.stderr);
            except RuntimeError:
                if "-" not in requested and "_" not in requested:
                    raise;
            destination = args.download_dir or (data_dirs[0] if data_dirs else default_data_dirs()[0]);
            local_model = resolve_named_voice(canonical, data_dirs);
            if local_model is not None and not args.force_download:
                print(f"voice={canonical}");
                print("status=already-installed");
                print(f"path={local_model}");
                return 0;
            download_voice(canonical, destination);
            print(f"voice={canonical}");
            print("status=downloaded");
            print(f"directory={destination}");
            return 0;
        ipa = read_ipa(args);
        model, language, source = resolve_model(args, config);
        profile = apply_profile_synthesis_settings(args, config, language);
        if args.length_scale <= 0:
            raise RuntimeError("--length-scale must be greater than zero");
        if args.volume < 0:
            raise RuntimeError("--volume cannot be negative");
        for option_name, option_value in (
            ("--word-pause", args.word_pause),
            ("--comma-pause", args.comma_pause),
            ("--clause-pause", args.clause_pause),
            ("--sentence-pause", args.sentence_pause),
        ):
            if option_value < 0:
                raise RuntimeError(f"{option_name} cannot be negative");
        if args.verbose:
            print(f"language={language or '(not specified)'}", file=sys.stderr);
            print(f"model={model}", file=sys.stderr);
            print(f"model_source={source}", file=sys.stderr);
            print(f"profile_validation={profile.get('validation', 'starting-point')}", file=sys.stderr);
            print(f"length_scale={args.length_scale}", file=sys.stderr);
            print(f"volume={args.volume}", file=sys.stderr);
            print(f"extra_pauses={args.extra_pauses}", file=sys.stderr);
            print(f"word_pause={args.word_pause if args.extra_pauses else 0.0}", file=sys.stderr);
            print(f"comma_pause={args.comma_pause if args.extra_pauses else 0.0}", file=sys.stderr);
            print(f"clause_pause={args.clause_pause if args.extra_pauses else 0.0}", file=sys.stderr);
            print(f"sentence_pause={args.sentence_pause if args.extra_pauses else 0.0}", file=sys.stderr);
        direct_wav = Path(args.wav).expanduser() if args.wav else None;
        compressed = args.ogg or args.mp3;
        if direct_wav is not None:
            direct_wav.parent.mkdir(parents=True, exist_ok=True);
            synthesize_wav(ipa, model, direct_wav, args);
            if args.verbose:
                print(f"output={direct_wav}", file=sys.stderr);
            return 0;
        with tempfile.TemporaryDirectory(prefix="pronounce-") as tmpdir:
            temporary_wav = Path(tmpdir) / "speech.wav";
            synthesize_wav(ipa, model, temporary_wav, args);
            if compressed:
                destination = Path(compressed).expanduser();
                destination.parent.mkdir(parents=True, exist_ok=True);
                transcode_wav(temporary_wav, destination);
                if args.verbose:
                    print(f"output={destination}", file=sys.stderr);
            else:
                if args.verbose:
                    print("output=default-audio-device", file=sys.stderr);
                play_wav(temporary_wav, player=args.player);
        return 0;
    except RuntimeError as exc:
        parser.exit(2, f"{PROGRAM}: error: {exc}\n");


if __name__ == "__main__":
    raise SystemExit(main());

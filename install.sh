#!/usr/bin/env bash
# -*- mode: sh; sh-shell: bash -*-
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
# EN: Install the toolkit in a private virtual environment and expose the four
#     commands in ~/.local/bin. The normal installation also prepares Piper
#     voices and the default faster-whisper model.
# ES: Instala el toolkit en un entorno virtual privado y expone los cuatro
#     comandos en ~/.local/bin. La instalación normal también prepara las voces
#     Piper y el modelo predeterminado de faster-whisper.
# FR: Installe le toolkit dans un environnement virtuel privé et expose les
#     quatre commandes dans ~/.local/bin. L'installation normale prépare aussi
#     les voix Piper et le modèle faster-whisper par défaut.

set -euo pipefail

PROGRAM="install.sh"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
XDG_DATA_HOME_VALUE="${XDG_DATA_HOME:-${HOME}/.local/share}"
VENV_DIR="${PHONEM_VENV:-${XDG_DATA_HOME_VALUE}/phonem/venv}"
BIN_DIR="${PHONEM_BIN_DIR:-${HOME}/.local/bin}"
WHISPER_MODEL="small"
MINIMAL=0
INSTALL_PIPER=1
INSTALL_WHISPER=1
UPDATE_MODE=0
DRY_RUN=0

usage() {
    cat <<'USAGE'
Usage: ./install.sh [OPTIONS]

Install phonem/trans/pronounce/transcribe in a private Python virtual environment.
The default installation also downloads the configured Piper voices and the
faster-whisper "small" model.

Options:
  --minimal                install code/dependencies only; do not download models
  --update                 update an existing installation in place
  --no-piper               do not download Piper voices
  --no-whisper             do not download a faster-whisper model
  --whisper-model MODEL    model to preload (default: small)
  --venv DIR               virtual environment directory
  --bin-dir DIR            directory for phonem/pronounce/trans/transcribe links
  --dry-run                 show the main actions without changing anything
  -h, --help               show this help

Environment:
  PHONEM_VENV               default virtual environment directory
  PHONEM_BIN_DIR            default command-link directory
  PHONEM_PIP_ARGS           extra arguments appended to "pip install"

System programs are checked but never installed with sudo automatically.
On Debian/Ubuntu, the usual system dependencies are:
  sudo apt install python3 python3-venv espeak-ng ffmpeg
USAGE
}

log() {
    printf '%s: %s\n' "$PROGRAM" "$*"
}

warn() {
    printf '%s: warning: %s\n' "$PROGRAM" "$*" >&2
}

fail() {
    printf '%s: error: %s\n' "$PROGRAM" "$*" >&2
    exit 1
}

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '+ '
        printf '%q ' "$@"
        printf '\n'
        return 0
    fi
    "$@"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --minimal)
            MINIMAL=1;
            INSTALL_PIPER=0;
            INSTALL_WHISPER=0;
            shift;
            ;;
        --update)
            UPDATE_MODE=1;
            shift;
            ;;
        --no-piper)
            INSTALL_PIPER=0;
            shift;
            ;;
        --no-whisper)
            INSTALL_WHISPER=0;
            shift;
            ;;
        --whisper-model)
            [[ $# -ge 2 ]] || fail "--whisper-model requires a value";
            WHISPER_MODEL="$2";
            shift 2;
            ;;
        --venv)
            [[ $# -ge 2 ]] || fail "--venv requires a directory";
            VENV_DIR="$2";
            shift 2;
            ;;
        --bin-dir)
            [[ $# -ge 2 ]] || fail "--bin-dir requires a directory";
            BIN_DIR="$2";
            shift 2;
            ;;
        --dry-run)
            DRY_RUN=1;
            shift;
            ;;
        -h|--help)
            usage;
            exit 0;
            ;;
        *)
            fail "unknown option: $1";
            ;;
    esac
done

command -v python3 >/dev/null 2>&1 || fail "python3 was not found in PATH";

# EN/ES/FR: System dependencies are checked, not installed behind the user's back.
missing_system=();
for command_name in espeak-ng ffmpeg ffplay; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        missing_system+=("$command_name");
    fi
done
if [[ ${#missing_system[@]} -gt 0 ]]; then
    warn "missing system command(s): ${missing_system[*]}";
    warn "phonem/pronounce features that need them will not work until they are installed";
fi

if [[ "$UPDATE_MODE" -eq 1 ]]; then
    log "updating installation in $VENV_DIR";
else
    log "installing into $VENV_DIR";
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "creating virtual environment";
    run mkdir -p "$(dirname -- "$VENV_DIR")";
    run python3 -m venv "$VENV_DIR";
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    VENV_PYTHON="$VENV_DIR/bin/python";
    VENV_PIP="$VENV_DIR/bin/python";
else
    [[ -x "$VENV_DIR/bin/python" ]] || fail "could not create virtual environment: $VENV_DIR";
    VENV_PYTHON="$VENV_DIR/bin/python";
    VENV_PIP="$VENV_DIR/bin/python";
fi

log "updating pip/setuptools";
run "$VENV_PIP" -m pip install --upgrade pip setuptools;

pip_extra=();
if [[ -n "${PHONEM_PIP_ARGS:-}" ]]; then
    # shellcheck disable=SC2206
    pip_extra=( ${PHONEM_PIP_ARGS} );
fi

log "installing phonem-toolkit and Python dependencies";
project_install_args=(--upgrade --no-build-isolation);
if [[ "$UPDATE_MODE" -eq 1 ]]; then
    project_install_args+=(--force-reinstall);
fi
run "$VENV_PIP" -m pip install "${project_install_args[@]}" "${pip_extra[@]}" "$SCRIPT_DIR";

run mkdir -p "$BIN_DIR";
for command_name in phonem pronounce trans transcribe; do
    source_path="$VENV_DIR/bin/$command_name";
    destination="$BIN_DIR/$command_name";
    if [[ "$DRY_RUN" -eq 1 ]]; then
        run ln -sfn "$source_path" "$destination";
        continue;
    fi
    [[ -x "$source_path" ]] || fail "installed entry point is missing: $source_path";
    if [[ -e "$destination" && ! -L "$destination" ]]; then
        warn "$destination already exists and is not a symlink; leaving it unchanged";
        continue;
    fi
    ln -sfn "$source_path" "$destination";
done

PRONOUNCE="$VENV_DIR/bin/pronounce";
TRANSCRIBE="$VENV_DIR/bin/transcribe";
PHONEM="$VENV_DIR/bin/phonem";
TRANS="$VENV_DIR/bin/trans";

log "creating or migrating Piper configuration";
run "$PRONOUNCE" --update-config;

if [[ "$INSTALL_PIPER" -eq 1 ]]; then
    log "downloading configured default Piper voices (already installed voices are skipped)";
    run "$PRONOUNCE" --download-defaults;
else
    log "Piper voice download skipped";
fi

if [[ "$INSTALL_WHISPER" -eq 1 ]]; then
    log "preloading faster-whisper model: $WHISPER_MODEL";
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '+ %q -c %q %q\n' "$VENV_PYTHON" \
            'from faster_whisper import download_model; import sys; print(download_model(sys.argv[1]))' \
            "$WHISPER_MODEL";
    else
        "$VENV_PYTHON" -c \
            'from faster_whisper import download_model; import sys; path=download_model(sys.argv[1]); print("whisper_model=" + str(path))' \
            "$WHISPER_MODEL";
    fi
else
    log "faster-whisper model download skipped";
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
    log "checking installed commands";
    "$PHONEM" --version;
    "$PRONOUNCE" --version;
    "$TRANS" --version;
    "$TRANSCRIBE" --version;
    "$PRONOUNCE" --check || true;
fi

case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) warn "$BIN_DIR is not currently in PATH; add it to your shell PATH to use the short commands" ;;
esac

printf '\n';
log "installation complete";
printf '  venv:     %s\n' "$VENV_DIR";
printf '  commands: %s/{phonem,pronounce,trans,transcribe}\n' "$BIN_DIR";
if [[ "$MINIMAL" -eq 1 ]]; then
    printf '  models:   skipped (--minimal)\n';
else
    printf '  Piper:    %s\n' "$([[ "$INSTALL_PIPER" -eq 1 ]] && printf prepared || printf skipped)";
    printf '  Whisper:  %s\n' "$([[ "$INSTALL_WHISPER" -eq 1 ]] && printf '%s' "$WHISPER_MODEL" || printf skipped)";
fi
printf '\nTry:\n  phonem "Bonjour tout le monde." -l fr\n';

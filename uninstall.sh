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
# EN: Remove the private toolkit environment and command links. User tuning and
#     third-party model caches are preserved unless the project-owned config/cache
#     purge is explicitly requested.
# ES: Elimina el entorno privado y los enlaces de comandos. La configuración del
#     usuario y las cachés de modelos de terceros se conservan salvo pedido expreso.
# FR: Supprime l'environnement privé et les liens de commandes. La configuration
#     utilisateur et les caches de modèles tiers sont conservés sauf demande expresse.

set -euo pipefail

PROGRAM="uninstall.sh"
XDG_DATA_HOME_VALUE="${XDG_DATA_HOME:-${HOME}/.local/share}"
XDG_CONFIG_HOME_VALUE="${XDG_CONFIG_HOME:-${HOME}/.config}"
XDG_CACHE_HOME_VALUE="${XDG_CACHE_HOME:-${HOME}/.cache}"
VENV_DIR="${PHONEM_VENV:-${XDG_DATA_HOME_VALUE}/phonem/venv}"
BIN_DIR="${PHONEM_BIN_DIR:-${HOME}/.local/bin}"
PURGE=0
DRY_RUN=0

usage() {
    cat <<'USAGE'
Usage: ./uninstall.sh [OPTIONS]

Options:
  --purge       also remove project configuration and project cache
  --venv DIR    virtual environment directory used by install.sh
  --bin-dir DIR command-link directory used by install.sh
  --dry-run     show what would be removed
  -h, --help    show this help

The default uninstall intentionally preserves:
  * ~/.config/phonem
  * ~/.cache/phonem
  * Piper models in ~/.local/share/piper
  * faster-whisper/Hugging Face model caches

--purge removes the first two project-owned directories, but still preserves
third-party model caches because they may be shared by other applications.
USAGE
}

fail() {
    printf '%s: error: %s\n' "$PROGRAM" "$*" >&2;
    exit 1;
}

run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '+ ';
        printf '%q ' "$@";
        printf '\n';
        return 0;
    fi
    "$@";
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --purge) PURGE=1; shift ;;
        --venv)
            [[ $# -ge 2 ]] || fail "--venv requires a directory";
            VENV_DIR="$2"; shift 2 ;;
        --bin-dir)
            [[ $# -ge 2 ]] || fail "--bin-dir requires a directory";
            BIN_DIR="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) fail "unknown option: $1" ;;
    esac
done

for command_name in phonem pronounce trans transcribe; do
    destination="$BIN_DIR/$command_name";
    if [[ -L "$destination" ]]; then
        target="$(readlink -- "$destination" || true)";
        case "$target" in
            "$VENV_DIR"/*) run rm -f -- "$destination" ;;
            *) printf '%s: preserving unrelated symlink: %s -> %s\n' "$PROGRAM" "$destination" "$target" >&2 ;;
        esac
    fi
done

if [[ -d "$VENV_DIR" ]]; then
    run rm -rf -- "$VENV_DIR";
fi

# Remove the parent only when it became empty. Never recurse above the venv here.
venv_parent="$(dirname -- "$VENV_DIR")";
if [[ "$DRY_RUN" -eq 0 && -d "$venv_parent" ]]; then
    rmdir -- "$venv_parent" 2>/dev/null || true;
fi

if [[ "$PURGE" -eq 1 ]]; then
    run rm -rf -- "$XDG_CONFIG_HOME_VALUE/phonem";
    run rm -rf -- "$XDG_CACHE_HOME_VALUE/phonem";
fi

printf '%s: uninstall complete\n' "$PROGRAM";
if [[ "$PURGE" -eq 0 ]]; then
    printf '%s: configuration and model caches were preserved\n' "$PROGRAM";
else
    printf '%s: project configuration/cache removed; third-party model caches preserved\n' "$PROGRAM";
fi

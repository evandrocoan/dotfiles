#!/bin/bash
set -x
set -euo pipefail

# ---------------------------------------------------------------------------
# All available packages (build order matters; see https://docs.xfce.org/xfce/building)
# Each entry is "name|upstream_url"
# ---------------------------------------------------------------------------
declare -a PACKAGES=(
    "xfce4-dev-tools|https://gitlab.xfce.org/xfce/xfce4-dev-tools.git"
    "xfce4-libxfce4util|https://gitlab.xfce.org/xfce/libxfce4util.git"
    "xfce4-libxfce4ui|https://gitlab.xfce.org/xfce/libxfce4ui.git"
    "xfce4-exo|https://gitlab.xfce.org/xfce/exo.git"
    "xfce4-thunar|https://gitlab.xfce.org/xfce/thunar.git"
    "xfce4-thunar-archive-plugin|https://gitlab.xfce.org/thunar-plugins/thunar-archive-plugin.git"
    "xfce4-panel|https://gitlab.xfce.org/xfce/xfce4-panel.git"
    "xfce4-xfwm4|https://gitlab.xfce.org/xfce/xfwm4.git"
    "xfce4-whiskermenu-plugin|https://gitlab.xfce.org/panel-plugins/xfce4-whiskermenu-plugin.git"
    "xf86-input-libinput|https://gitlab.freedesktop.org/xorg/driver/xf86-input-libinput.git"
)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
# PREFIX cannot contain spaces (xfce build scripts assumes this!)
export PREFIX=$HOME/.local
export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export ACLOCAL_PATH="${PREFIX}/share/aclocal:${ACLOCAL_PATH:-}"
export CFLAGS=""
export LD_LIBRARY_PATH=$PREFIX/lib

declare -a PACKAGES_TO_BUILD=()
DO_CONFIGURE=0
DO_BUILD=0
DO_INSTALL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Looks up the full "name|url" tuple for a given package name.
function lookup_package() {
    local name="$1"
    for entry in "${PACKAGES[@]}"; do
        if [[ "${entry%%|*}" == "$name" ]]; then
            echo "$entry"
            return 0
        fi
    done
    printf 'Error: Unknown package "%s".\n' "$name" >&2
    printhelp
}

function invalidargument() {
    printf 'Error: Invalid argument "%s" for option "%s".\n' "${2}" "${1}" >&2
    printhelp
    exit 1
}

function checkargsvalid() {
    if [[ "${2:-}" == '-'* ]]; then
        invalidargument "${1}" "${2}"
    fi
}

function check_expected_args() {
    if [[ "${2:-}" != '-'* ]] && [[ -n "${2:-}" ]]; then
        printf 'Error: The option "%s" does not expect any arguments, but got "%s".\n' "${1}" "${2}" >&2
        printhelp
        exit 1
    fi
}

function printhelp() {
cat >&1 <<EOF

Usage: bash ${0} [options] [PACKAGE...]

Required apt packages:
sudo apt install \
  gtk-doc-tools \
  libcairo2-dev \
  libexo-2-dev \
  libgarcon-1-0-dev \
  libgarcon-gtk3-1-dev \
  libglib2.0-dev \
  libgtk-3-dev \
  libinput-dev \
  libwnck-3-dev \
  libx11-dev \
  libxfce4ui-2-dev \
  libxfce4util-dev \
  libxfconf-0-dev \
  x11proto-dev \
  xfce4-battery-plugin \
  xfce4-cpugraph-plugin \
  xfce4-dev-tools \
  xfce4-fsguard-plugin \
  xfce4-genmon-plugin \
  xfce4-netload-plugin \
  xserver-xorg-dev \
  xutils-dev

Clones or pulls one or more XFCE4 packages. Optionally builds and installs them.

Positional:
  PACKAGE               Name(s) of the package(s) to process. May be specified multiple times. Available packages:
                        multiple times. Available packages:
$(for entry in "${PACKAGES[@]}"; do printf '                          %s\n' "${entry%%|*}"; done)

Options:
  -h | --help           Show this help and exit.
       --all            Process all packages in dependency order.
  -p | --package NAME   Package to process. May be specified multiple times.
       --configure      Run autogen.sh only (implies clone/pull).
       --build          Run make only (implies --configure).
       --install        Run make install (implies --build).

EOF
    exit 1
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [[ "$#" -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            printhelp
        ;;
        --all)
            PACKAGES_TO_BUILD=("${PACKAGES[@]}")
        ;;
        --configure)
            DO_CONFIGURE=1
        ;;
        --build)
            DO_CONFIGURE=1
            DO_BUILD=1
        ;;
        --install)
            DO_CONFIGURE=1
            DO_BUILD=1
            DO_INSTALL=1
        ;;
        -p|--package)
            checkargsvalid "$1" "${2:-}"
            PACKAGES_TO_BUILD+=("$(lookup_package "${2}")")
            shift
        ;;
        -*)
            printf 'Error: Unknown option "%s".\n' "${1}" >&2
            printhelp
        ;;
        *)
            PACKAGES_TO_BUILD+=("$(lookup_package "${1}")")
        ;;
    esac
    shift
done

# If no packages specified, show help
if [[ "${#PACKAGES_TO_BUILD[@]}" -eq 0 ]]; then
    printhelp
fi

mkdir xfce4 -p
cd xfce4

function main {
    # For building order see: https://docs.xfce.org/xfce/building
    for entry in "${PACKAGES_TO_BUILD[@]}"; do
        libname="${entry%%|*}"
        upstream="${entry##*|}"

        if git clone https://github.com/evandroforks/$libname 2>/dev/null; then
            echo "Cloned ${libname}."
            git -C "${libname}" remote add upstream "${upstream}"
            echo "Added upstream remote: ${upstream}"
        fi;

        pushd "${libname}"

        if [[ "$DO_CONFIGURE" -eq 1 ]]; then
            # Cannot compile any XFCE 4.14 project with `./configure --enable-debug=full`
            # https://gitlab.xfce.org/xfce/xfce4-panel/-/issues/351
            ./autogen.sh --prefix=$PREFIX --enable-debug=no
        fi;

        if [[ "$DO_BUILD" -eq 1 ]]; then
            make -j"$(nproc)" || make -j"$(nproc)"

        fi;

        if [[ "$DO_INSTALL" -eq 1 ]]; then
            make install
        fi;

        popd
    done
}

time main

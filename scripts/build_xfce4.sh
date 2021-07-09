#!/bin/bash
set -x
set -eo pipefail

# PREFIX cannot contain spaces (xfce build scripts assumes this!)
export PREFIX=$HOME/.local
export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig:$PKG_CONFIG_PATH"
export CFLAGS=""
export LD_LIBRARY_PATH=$PREFIX/lib

declare -a projects_to_build=(
    "xfce4-libxfce4util"
    "xfce4-libxfce4ui"
    "xfce4-exo"
    "xfce4-thunar"
    "xfce4-thunar-archive-plugin"
    "xfce4-panel"
    "xfce4-xfwm4"
)
projects_to_buildlength="${#projects_to_build[@]}"

mkdir xfce4 -p
cd xfce4

function main {
    # For building order see: https://docs.xfce.org/xfce/building
    for (( index = 0; index < projects_to_buildlength; index++ ));
    do
        libname="${projects_to_build[$index]}"
        git clone https://github.com/evandroforks/$libname || echo Skpping because it already exists...
        pushd "${libname}"

        # Cannot compile any XFCE 4.14 project with `./configure --enable-debug=full`
        # https://gitlab.xfce.org/xfce/xfce4-panel/-/issues/351
        ./autogen.sh --prefix=$PREFIX --enable-debug=no \
                && make \
                && make install || { \
            ./autogen.sh --prefix=$PREFIX --enable-debug=no \
                && make \
                && make install
            }
        popd
    done
}

time main

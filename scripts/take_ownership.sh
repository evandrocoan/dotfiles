#!/bin/bash
(
    set -ex
    dir="$1"
    [[ -z "$dir" ]] && echo "No directory provided." && exit 1
    cd "$dir" || exit 1
    read -p "Run: chown -R $USER:$USER . in \"$dir\" [y/N]? " ans

    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo chown -R "$USER:$USER" .
        echo "Done!"
    else
        echo "Cancelled."
    fi
)
read -p ""

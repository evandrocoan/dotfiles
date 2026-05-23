#!/bin/bash
(
    set -ex
    dir="$1"
    [[ -z "$dir" ]] && echo "No directory provided." && exit 1
    cd "$dir" || exit 1
    set +x
    echo "This will change ownership of all files in: "
    echo "Run: chown -R $USER:$USER . in \"$dir\""
    echo ""
    echo "$dir"
    echo ""
    read -p "[y/N]? " ans

    set -x
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo chown -R "$USER:$USER" .
        echo "Done!"
    else
        echo "Cancelled."
    fi
)
read -p ""

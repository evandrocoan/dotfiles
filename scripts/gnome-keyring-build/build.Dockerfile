ARG BASE_IMAGE=ubuntu:24.04@sha256:24737cef17f4e22b1977df7d9a05e77c4e28b7da5b8911f8d8ccda136bf3573c
FROM ${BASE_IMAGE} AS dependencies

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential debhelper dh-sequence-gnome ca-certificates dbus dbus-daemon \
    xsltproc docbook-xml docbook-xsl libgck-1-dev libgcr-3-dev libgcrypt20-dev \
    libglib2.0-dev libp11-kit-dev libpam0g-dev libselinux1-dev libsystemd-dev \
    libtasn1-6-dev libtasn1-bin libglib2.0-doc openssh-client python3 systemd-dev \
    autoconf automake libtool pkg-config \
    && rm -rf /var/lib/apt/lists/*

FROM dependencies AS build
RUN install -d -o 1000 -g 1000 /build/gnome-keyring
WORKDIR /build/gnome-keyring
COPY --chown=1000:1000 . .
USER 1000:1000
ENV HOME=/tmp/keyring-build-home DEB_BUILD_OPTIONS=parallel=2
ENV DEB_BUILD_MAINT_OPTIONS=hardening=+all DEB_LDFLAGS_MAINT_APPEND="-Wl,-O1 -Wl,-z,defs"
RUN --network=none dpkg-checkbuilddeps && dh_autoreconf && dh_auto_configure -- \
    --with-pam-dir=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/security --without-libcap-ng \
    --enable-docs --enable-ssh-agent --with-systemd \
    && dh_auto_build --max-parallel=2
CMD ["/bin/true"]

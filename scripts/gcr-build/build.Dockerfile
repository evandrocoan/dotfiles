ARG KEYRING_DEPS_IMAGE=local/keyring-rebuild:dependencies
FROM ${KEYRING_DEPS_IMAGE} AS dependencies

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    dh-sequence-gir gi-docgen gnupg libgirepository1.0-dev libgtk-3-doc libsecret-1-dev meson valac \
    && rm -rf /var/lib/apt/lists/*

FROM dependencies AS build
RUN install -d -o 1000 -g 1000 /build/gcr
WORKDIR /build/gcr
COPY --chown=1000:1000 . .
USER 1000:1000
ENV HOME=/tmp/gcr-build-home DEB_BUILD_OPTIONS=parallel=2
ENV DEB_BUILD_MAINT_OPTIONS=hardening=+all DEB_LDFLAGS_MAINT_APPEND="-Wl,-O1 -Wl,-z,defs" DEB_LDFLAGS_MAINT_STRIP=-Wl,-Bsymbolic-functions
RUN --network=none dpkg-checkbuilddeps && dh_auto_configure -- \
    -Dauto_features=enabled -Dgtk_doc=true -Dintrospection=true \
    -Dgtk=true -Dsystemd=disabled -Dssh_agent=false \
    && dh_auto_build --max-parallel=2
CMD ["/bin/true"]

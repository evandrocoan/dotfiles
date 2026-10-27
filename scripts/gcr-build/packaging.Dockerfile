ARG SOURCE_IMAGE=local/keyring-rebuild:gcr
FROM ${SOURCE_IMAGE} AS packages
ARG SOURCE_PACKAGE=gcr
ARG BASE_VERSION=3.41.2-1build3
ARG PACKAGE_VERSION=3.41.2-1build3+keyringfix1
USER root
COPY package_changelog.py /build/package_changelog.py
RUN python3 /build/package_changelog.py "${SOURCE_PACKAGE}" "${BASE_VERSION}" "${PACKAGE_VERSION}" \
    && DEB_BUILD_OPTIONS="parallel=2 nocheck" dpkg-buildpackage -b -us -uc -nc
COPY export_packages.py /build/export_packages.py
RUN python3 /build/export_packages.py
USER 1000:1000
CMD ["/bin/true"]

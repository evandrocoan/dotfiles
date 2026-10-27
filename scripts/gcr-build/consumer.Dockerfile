ARG GCR_IMAGE=local/keyring-rebuild:gcr
ARG KEYRING_IMAGE=local/keyring-rebuild:keyring
FROM ${GCR_IMAGE} AS gcr
FROM ${KEYRING_IMAGE}
COPY --from=gcr /build/gcr/obj-x86_64-linux-gnu/gcr /opt/gcr/gcr
COPY --from=gcr /build/gcr/obj-x86_64-linux-gnu/gck /opt/gcr/gck
ENV LD_LIBRARY_PATH=/opt/gcr/gcr:/opt/gcr/gck

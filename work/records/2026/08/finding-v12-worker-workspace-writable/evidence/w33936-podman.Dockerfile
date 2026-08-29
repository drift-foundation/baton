# W33936 — a COMPATIBLE PODMAN deployment, because this host cannot have one.
#
# M34630 requires the applied-group matrix on Docker AND compatible Podman, and
# the review is right that a skip cannot satisfy it. Podman cannot be installed
# on this host: `sudo` here is not setuid, and ROOTLESS podman needs
# `newuidmap`/`newgidmap`, which this host does not carry. So the deployment
# moves again, exactly as it did for the dedicated group: podman is provisioned
# in an image, and the manager runs inside it ROOTLESS as a non-root account
# holding the dedicated non-authority group.
#
# The workers are podman containers inside this one rather than siblings on a
# host daemon -- which is the honest shape for podman, since podman has no
# daemon to be a sibling of. Everything the matrix touches is one filesystem,
# so the bind paths the manager composes are the paths the engine resolves.
FROM quay.io/podman/stable

RUN dnf install -y python3 python3-pip >/dev/null 2>&1 \
 && pip3 install --no-cache-dir --quiet jsonschema \
 && groupadd -g 8291 baton-workspace \
 && useradd -u 4000 -m -G baton-workspace batonmgr \
 && echo 'batonmgr:100000:65536' >> /etc/subuid \
 && echo 'batonmgr:100000:65536' >> /etc/subgid \
 && mkdir -p /run/user/4000 && chown batonmgr /run/user/4000

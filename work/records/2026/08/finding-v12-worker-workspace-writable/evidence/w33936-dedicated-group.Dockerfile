# W33936 — a deployment that really has a dedicated non-authority workspace
# group, because this host cannot be given one.
#
# The reviewer's standing requirement is engine evidence from "an actual
# dedicated non-authority group". This workstation has no such group and this
# manager may not create one: `sudo` is not setuid here, `newgidmap` is absent,
# and creating a host group is exactly what approver ruling M34630 forbids the
# manager to do. So the DEPLOYMENT is the thing that moves: the manager runs
# inside a provisioned image where gid 8291 `baton-workspace` exists, owns
# nothing, and names nobody but the manager account -- and it launches its
# workers as SIBLINGS on the same real host daemon, over the same socket, with
# the same bind paths.
FROM python:3.13-slim
RUN groupadd -g 8291 baton-workspace \
 && groupadd -g 1000 batonmgr \
 && echo 'batonmgr:x:1000:1000:baton worker manager:/nonexistent:/usr/sbin/nologin' >> /etc/passwd \
 && sed -i 's/^baton-workspace:x:8291:.*$/baton-workspace:x:8291:batonmgr/' /etc/group \
 && groupadd -g 119 enginesocket \
 && sed -i 's/^enginesocket:x:119:.*$/enginesocket:x:119:batonmgr/' /etc/group
# The manager's own dependency, installed in the image rather than mounted:
# a proof that ran against the host's site-packages would be proving the host.
RUN pip install --no-cache-dir jsonschema

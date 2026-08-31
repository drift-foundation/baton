# W39364 run 1 — network policy

Egress is granted, on the Docker `bridge` network, because a provider-backed
worker is a network client and the milestone is a real provider turn. The
value is an operator grant (M50427) and is named explicitly in the grants
file; this deployment infers no default and `oci._network` refuses anything
that is not one engine network name.

Nothing else about egress is granted: no published port, no host networking,
no added capability, and no second network. The consent posture mounts nothing
and is unaffected.

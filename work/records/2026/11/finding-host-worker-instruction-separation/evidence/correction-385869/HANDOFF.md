# Interactive R1/R2 correction — W385853

Owner explicitly selected this interactive correction instead of codexpc. No claim borrowed. Assignment returned to decide via E385869 while unclaimed.

Manifest: 8800f7f05eec75bab04793a3aac23f9b927e9c770ab60ed794cfb3212762b951
Base and original packet preserved unchanged at consolidation-385856. Full corrected bytes in candidate/; delta.patch contains only R1 exception paragraph and R2 builds → image builds. HOST-INTEGRATION.md is byte-identical. Non-blocking suggestions were not included.

R1 restores the governing exception permission, scope/lifetime, revalidation, no sibling/successor extension, and relocation semantics. Matrix JSON and addendum point to the actual paragraph. R2 preserves ordinary worker compilation freedom.

Verification: 14/14 static checks, no failures/skips; no product or provider tests. Root is 20570 bytes, above the soft 20 KiB target but below the required 32 KiB loader budget. The size check explicitly changed from the soft target to the real loader budget; no rule was removed to meet a size goal. Prior 12 checks retained otherwise, with two direct R1/R2 checks added. Static checks do not replace K semantic review.

No host import, Git mutation or runtime delivery change. Request K narrow delta review. Overall Work remains unfinished through native delivery proof.

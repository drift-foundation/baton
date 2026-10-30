# Restore the expanded candidate

The two expanded candidate copies were redundant. Their 1,196 files each
matched the retained archive exactly at cleanup on 2026-10-30. Preserve
`candidate-338472.tar.gz` and `CANDIDATE-338472.json` in the owner checkpoint.
This archive is currently local; cleanup does not establish an off-machine backup.

From this dossier directory, verify the archive before extraction:

```sh
printf '%s  %s\n' c2bcbadbb141bf4ffbecbbd346a5d185205c7c4cc795b6c295f3dfad3f3395e6 candidate-338472.tar.gz | sha256sum -c -
```

For ordinary inspection, extract into a new disk-backed scratch directory.
If historical scripts require the original paths, restore each copy below.
Run each command separately, after successful digest verification. `mkdir`
refuses an existing destination, preventing an accidental overlay.

```sh
mkdir candidate-338472
```

```sh
tar -xzf candidate-338472.tar.gz -C candidate-338472
```

```sh
mkdir review-338596/candidate
```

```sh
tar -xzf candidate-338472.tar.gz -C review-338596/candidate
```

These exact expanded paths are ignored as reproducible copies. Review-only
reports and composition evidence outside them remain preserved normally.

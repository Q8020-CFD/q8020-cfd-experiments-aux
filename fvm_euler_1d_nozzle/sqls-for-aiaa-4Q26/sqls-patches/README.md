# sqls patches — superseded by a commit

The sampler port (`UNCOMMITTED-sampler-port.diff`, 6099 bytes) is committed as
`187a7a5` on branch `sqls-aiaa-4q26` of https://github.com/Q8020-CFD/sqls
(2026-10-15), on top of upstream `9a4346a`. The fvm `pyproject.toml` pins that
rev. The diff file was removed 2026-10-18 after checking it is byte-identical
to the commit.

Runs made while the port was uncommitted record
`code_versions.sqls.diff_sha256 = c8425988ddc64d72385dcf026eb5125c665fdbe3d0c1a7b85a9e4b6250090752`
(earlier runs: `2d4c5a7c...`, an older revision of the same port). Reproduce
the current one from git:

    git -C /Users/agallojr/proj/src/q8020/sqls diff 9a4346a 187a7a5 | shasum -a 256

ORNL hand-off: `git format-patch 9a4346a..187a7a5`.

# Package stacks for the fvm April reruns

Each `<stack>/requirements.lock.txt` is a fully pinned package set for `fvm_euler_1d_solver`.
`submit_fvm_april.sh <stack>` passes it to `docker/submit.sh --reqs`, which installs it
exactly (`--no-deps`) at job start.

| stack | fvm code | HHL (quantum_linear_solvers) | other packages |
|---|---|---|---|
| old | 9e76e398 | Q8020-CFD@66eadf0 | April 2026 Frontier versions (qiskit 2.3.1), Python 3.12.9 |
| new | 38a41e52 | Q8020-CFD@99231b8 (+ sqls@67057e4) | latest releases (qiskit 2.6.1) |
| code-new_pkgs-old | 38a41e52 | 99231b8 | April versions |
| code-old_pkgs-new | 9e76e398 | 66eadf0 | latest releases |

April's HHL commit was established by iteration-0 gate counts: Q8020-CFD@66eadf0 reproduces
April's transpiled counts exactly (649089 / 604520); the agallojr fork named in 9e76e398's
requirements.txt is always +56.

## Regenerating a lock
From inside the stack folder (uv; `SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt` behind Zscaler):

    # old: April's recorded versions as constraints, nothing newer than the sweep start
    uv pip compile requirements.in -c april-constraints.txt --python-version 3.12.9 \
      --python-platform x86_64-manylinux_2_28 --exclude-newer 2026-04-05T00:10:19Z \
      --no-header --annotation-style line -o requirements.lock.txt

    # new: latest releases; overrides.txt lifts sqls's hard pins
    uv pip compile requirements.in --override overrides.txt --python-version 3.12 \
      --python-platform x86_64-manylinux_2_28 --no-header --annotation-style line \
      -o requirements.lock.txt

`april-constraints.txt` holds the 85 versions April's sweep recorded (q8020_env_before of
2026-04-05/_52d087d1 trial b9da8a4e). The new stack needs a GitHub token for the private
sqls repo when compiling (e.g. `GIT_CONFIG_*` insteadOf with `gh auth token`).

Generated per-case TOMLs (one per Batch job) land in `<stack>/cases/<sweep>/`
(`<stack>/cases-opt<N>/` with QISKIT_OPT_LEVEL); they are rewritten on every submit.

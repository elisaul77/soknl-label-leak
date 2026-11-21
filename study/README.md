# Full study (P-SOKNL-1)

Everything needed to re-run and re-audit the 29-stream study. Comments and variable names are in Spanish; a glossary is at the end.

| File | Role |
|---|---|
| `PROTOCOL_PSOKNL1.md` | Protocol, committed before the code (Spanish) |
| `INFORME_PSOKNL1.md` | Original report (Spanish) |
| `config_frozen.json` | Seeds, ensemble size, stream list, SHA-256 of code and data |
| `soknl1.py` | Study code: loader, the two arms, evaluation, verdict |
| `audit_soknl1.py` | Independent audit; imports nothing from `soknl1.py` |
| `results/eval.json` | Per-stream and per-seed RMSE, flips, control |
| `Dockerfile` | Environment pins (see note) |

## Data

Not redistributed. The study expects the `original_data` folder of the KDD'25 drift-simulation collection at `../ext/KDD25-DriftSimulation/original_data` relative to this folder (five `.arff` files and `NZEP_datasets/`). Hashes of the exact files are in `config_frozen.json`.

## Run

```bash
docker build -t soknl-study .
docker run --rm --network none -v "$PWD/..":/w -w /w soknl-study python study/soknl1.py evalua
docker run --rm --network none -v "$PWD/..":/w -w /w soknl-study python study/audit_soknl1.py
```

The audit needs `results/predicciones.npz` (114 MB, not in the repository). Regenerate it with the study's run step, or ask the author.

> [!NOTE]
> The `Dockerfile` here is a standalone equivalent of the image used for the formal run (same pins: CapyMOA 0.11.0, NumPy 1.26.4, Python 3.12, headless JRE). The original image was built on a private base layer. This standalone file has not itself been used for a formal run.

## Glossary

| Spanish | English |
|---|---|
| `habitual` | usual arm (label visible to `predict`) |
| `tapado` | label-hidden arm (weight 0) |
| `flujo` | stream |
| `semilla` | seed |
| `inflado` | relative RMSE reduction from reading the label |
| `vuelco` | flip (SOKNL beats ARF-Reg only when it reads the label) |
| `veredicto` | verdict |
| `no depende` | "does not depend" |

# Report to the maintainers — SENT on 2026-11-21

Filed as [adaptive-machine-learning/CapyMOA#491](https://github.com/adaptive-machine-learning/CapyMOA/issues/491). The text below is the draft; the filed version is slightly longer.
Checked on 2026-11-21 before filing: no existing issue in the CapyMOA or MOA trackers mentioned this.

---

**Title:** SOKNL uses the true label of the instance being predicted (self-optimising k is scored inside `getVotesForInstance`)

**Summary**

With self-optimising k enabled, `SelfOptimisingKNearestLeaves.getVotesForInstance` calls `selfOptimisingEvaluators[i].addResult(example, …)` for every candidate k using the instance it is currently predicting, then returns the prediction of the k with the lowest squared error. In a test-then-train loop that instance carries its true label, so the returned prediction depends on the label it is supposed to predict. `trainOnInstanceImpl` scores the same stored predictions again when the label arrives.

The effect is small but systematic. It does not change the conclusions we could check.

**How we checked**

- CapyMOA 0.11.0, `SOKNL(ensemble_size=30)`, 5 seeds, plain test-then-train.
- Two arms that differ only in the weight of the instance passed to `predict`: weight 1 (usual) and weight 0. `BasicRegressionPerformanceEvaluator.addResult` ignores weight-0 instances, so the label cannot enter the k selection; attributes, label value and training instances are unchanged.
- Control: `AdaptiveRandomForestRegressor` under the same two arms.

**Results (29 streams: abalone, bike, diamonds, House8L, superconductivity, 24 NZEP files)**

- ARF-Reg predictions are bit-identical in both arms on all 29 streams.
- SOKNL predictions differ on all 29 streams and all 5 seeds.
- RMSE is lower with the label visible in 145 of 145 stream–seed pairs.
- Size: 0.00 %–0.31 % on the five tabular streams; 0.02 %–1.55 % on NZEP (median about 0.5 %).
- SOKNL beats ARF-Reg on 21 of 29 streams in the usual loop and on 16 of 29 with the label hidden. The 5 flips are NZEP files where the two methods are within 2 % of each other.

**Reproduction**

`reproduce/minimal_repro.py` in this repository (synthetic data, no download).

**Suggested fix**

Drop the `addResult` call in `getVotesForInstance` and choose k from the errors accumulated by `trainOnInstanceImpl`.

**Limits**

One version tested; part of the datasets from the SOKNL papers; one run.

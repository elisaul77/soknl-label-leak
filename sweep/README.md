# Follow-up: the same test on every CapyMOA learner

After SOKNL, the label test was run on all 37 learners exported by `capymoa.regressor` and `capymoa.classifier` (CapyMOA 0.11.0, default parameters, synthetic data). Protocols were registered before the code; both studies passed an independent audit (304 and 91 checks).

## The test

Training always uses the true instance. The instance handed to `predict` is varied:

| Arm | Instance given to `predict` |
|---|---|
| U | the usual labelled instance |
| U2 | exact repeat of U (determinism check) |
| L | same attributes, a different label |
| W | true label, weight 0 |

A learner is **clean** when all four arms give bit-identical predictions.

## Result

| Class | Learners |
|---|---|
| **Clean (34)** | Regression: ARFFIMTDD, AdaptiveRandomForestRegressor, FIMTDD, FadingTargetMean, KNNRegressor, NoChange, ORTO, PassiveAggressiveRegressor, SGDRegressor, SOKNLBT, ShrubsRegressor, StreamingGradientBoostedRegression, TargetMean. Classification: AdaptiveRandomForestClassifier, CSMOTE, DynamicWeightedMajority, EFDT, HoeffdingAdaptiveTree, HoeffdingTree, KNN, LeveragingBagging, MajorityClass, NaiveBayes, NoChange, OnlineAdwinBagging, OnlineBagging, OnlineSmoothBoost, OzaBoost, PassiveAggressiveClassifier, SGDClassifier, ShrubsClassifier, StreamingGradientBoostedTrees, StreamingRandomPatches, WeightedkNN |
| **Reads the label inside `predict` (2)** | SOKNL, SAMkNN |
| Not tested (1) | Finetune (needs a model argument) |

No learner was non-deterministic, and none depended on the weight alone.

## SOKNL and SAMkNN are different cases

| | SOKNL | SAMkNN |
|---|---|---|
| What `predict` does with the label | scores every k against it, then chooses k for **this** prediction | after choosing its vote, records whether each memory would have been right, for **later** predictions |
| Effect in ordinary test-then-train | measured RMSE is slightly too low (≤ 1.55 %) | none: the bookkeeping would happen one step later anyway |
| Effect when the instance given to `predict` has no label | — | memory selection silently stops (all histories stay at zero, short-term memory is always used) |
| Effect when it carries a placeholder label | — | accuracy drops |

SAMkNN, `getVotesForInstance` on MOA `master`:

```java
int correctSTM = historySum(this.stmHistory);        // histories of PAST instances choose the memory
...
this.stmHistory.add((predClassSTM==inst.classValue()) ? 1 : 0);   // then THIS instance's label is recorded
this.ltmHistory.add((predClassLTM==inst.classValue()) ? 1 : 0);
this.cmHistory.add((predClassCM==inst.classValue()) ? 1 : 0);
```

## SAMkNN: how much it matters

Mean accuracy over 5 data seeds (%), training always on the true instance:

| Label slot of the instance given to `predict` | Stationary stream | Recurring-concept stream |
|---|---|---|
| true label (ordinary evaluation) | 55.45 | 46.38 |
| **no label** (`Instance.from_array`) | **53.96** | **46.72** |
| a random class | 52.17 | 44.19 |
| always class 0 | 47.33 | 42.78 |
| always another class | 45.94 | 42.60 |
| reference: CapyMOA `KNN` | 54.49 | 45.45 |

- With **no label** the cost is small: −1.5 points on the stationary stream (5 of 5 seeds), nothing on the recurring-concept stream. The pre-registered verdict was "does not lose".
- With a **placeholder label** the cost is 2 to 10 points.
- No published figure is affected: in ordinary evaluation SAMkNN behaves as intended.

## Limits

- "Clean" means the predictions did not change on these data with default parameters. It is not a proof.
- Synthetic data, 3,000–4,000 rows, numeric attributes, one library version, one run.
- The registered class "reads the label" does not separate the SOKNL case from the SAMkNN case; that distinction was made afterwards by reading the MOA source.
- Delayed labels were not measured.

## Files

| Folder | Contents |
|---|---|
| `all_learners/` | protocol, frozen config, code, audit, per-learner predictions and `eval.json` |
| `samknn/` | protocol, frozen config, code, audit, predictions and `eval.json` |

Protocols and reports are in Spanish (`PROTOCOL_*.md`, `INFORME_*.md`).

"""Minimal reproduction: SOKNL's prediction depends on the label of the instance it is predicting.

No dataset needed (synthetic stream). Requires capymoa (tested with 0.11.0) and a Java runtime.

Two arms that differ ONLY in the weight of the instance handed to predict():
  usual  -> weight 1 (what a normal test-then-train loop does)
  hidden -> weight 0 (MOA's BasicRegressionPerformanceEvaluator.addResult ignores weight-0 instances,
                      so the label cannot enter SOKNL's choice of k; attributes and label value are untouched)
Training always uses the normal weight-1 instances.
"""
import numpy as np
from capymoa.stream import NumpyStream
from capymoa.regressor import SOKNL, AdaptiveRandomForestRegressor


def instances(X, y, weight):
    stream = NumpyStream(X, y, target_type="numeric")
    out = []
    while stream.has_more_instances():
        inst = stream.next_instance()
        if weight == 0:
            inst.java_instance.getData().setWeight(0.0)
        out.append(inst)
    return stream.get_schema(), out


def run(model_cls, X, y, hide_label, seed=1):
    schema, train = instances(X, y, 1)
    pred = instances(X, y, 0)[1] if hide_label else train
    model = model_cls(schema=schema, ensemble_size=30, random_seed=seed)
    p = np.zeros(len(y))
    last = 0.0
    for t in range(len(y)):
        v = model.predict(pred[t])
        p[t] = last if v is None or not np.isfinite(v) else float(v)
        model.train(train[t])
        last = float(y[t])
    return p


def rmse(p, y):
    return float(np.sqrt(np.mean((p - y) ** 2)))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n, d = 4000, 6
    X = rng.normal(size=(n, d))
    y = np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * rng.normal(size=n)

    for name, cls in (("SOKNL", SOKNL), ("ARF-Reg (control)", AdaptiveRandomForestRegressor)):
        usual, hidden = run(cls, X, y, False), run(cls, X, y, True)
        print(f"{name:18s} identical predictions: {np.array_equal(usual, hidden)!s:5s} | "
              f"RMSE usual {rmse(usual, y):.5f} | RMSE label hidden {rmse(hidden, y):.5f}")
    print("Expected: SOKNL -> False (and a lower RMSE in the usual arm); ARF-Reg -> True.")

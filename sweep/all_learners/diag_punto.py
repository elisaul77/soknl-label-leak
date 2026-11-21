"""Diagnóstico posterior a P-BARRIDO-1 (no registrado): separa dos cosas que el brazo L mezcla.
 (a) la predicción del dato t depende de SU PROPIA respuesta (fuga en la evaluación habitual);
 (b) predecir deja en el modelo una huella que depende de la respuesta y solo afecta a predicciones POSTERIORES.
Para cada sonda tau: se pasa el flujo verdadero hasta tau-1 y en tau se predice una vez con la respuesta cambiada.
Si esa predicción coincide con la del brazo U guardado, la predicción no depende de su propia respuesta."""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_barrido1 import fabrica
from capymoa.stream import NumpyStream
import capymoa.regressor as R, capymoa.classifier as C
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results'); SONDAS = list(range(299, 3000, 300))
def lista(X, y, tipo):
    s = NumpyStream(X, y, target_type='numeric' if tipo == 'reg' else 'categorical'); out = []
    while s.has_more_instances(): out.append(s.next_instance())
    return s.get_schema(), out
out = {}
for tipo, n, mod in (('reg', 'SOKNL', R), ('clf', 'SAMkNN', C), ('reg', 'KNNRegressor', R)):
    X, y, yl = fabrica(tipo); U = np.load(os.path.join(RES, f'{tipo}_{n}.npz'))['U']; dif = []
    for tau in SONDAS:
        sc, Tr = lista(X, y, tipo); Al = lista(X, yl, tipo)[1]
        try: m = getattr(mod, n)(schema=sc, random_seed=1)
        except Exception: m = getattr(mod, n)(schema=sc)
        for t in range(tau): m.predict(Tr[t]); m.train(Tr[t])
        p = m.predict(Al[tau]); p = np.nan if p is None else float(p); dif.append(not (p == U[tau] or (np.isnan(p) and np.isnan(U[tau]))))
    out[f'{tipo}|{n}'] = {'sondas': len(SONDAS), 'prediccion_propia_cambia': int(sum(dif))}; print(f'{tipo}|{n}: en {sum(dif)} de {len(SONDAS)} sondas la predicción del dato cambia al cambiarle SU respuesta', flush=True)
json.dump(out, open(os.path.join(RES, 'diag_punto.json'), 'w'), indent=1)

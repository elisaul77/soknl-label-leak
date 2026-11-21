"""Auditoría independiente de P-BARRIDO-1. No importa el código del estudio: datos, comparación, clases y bucle propios."""
import os, json, hashlib
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(AQUI, 'results'); N = [0]; FALLOS = []
def ok(c, msg):
    N[0] += 1
    if not c: FALLOS.append(msg); print('  FALLA:', msg)
def fabrica(tipo):
    r = np.random.default_rng(20261121); X = r.normal(size=(3000, 6)); base = np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * r.normal(size=3000)
    if tipo == 'reg': return X, base, base + 5 * np.std(base)
    c1, c2 = np.quantile(base, [1 / 3, 2 / 3]); y = (base >= c1).astype(int) + (base >= c2).astype(int); return X, y, (y + 1) % 3
def mismo(a, b): return bool(np.all((a == b) | (np.isnan(a) & np.isnan(b))))
def clase(P): return 'no determinista' if not mismo(P['U'], P['U2']) else 'lee la respuesta' if not mismo(P['U'], P['L']) else 'depende del peso' if not mismo(P['U'], P['W']) else 'limpio'

if __name__ == '__main__':
    Fz = json.load(open(os.path.join(AQUI, 'config_frozen.json'))); E = json.load(open(os.path.join(RES, 'eval.json'))); T = json.load(open(os.path.join(RES, 'lista.json')))
    ok(hashlib.sha256(open(os.path.join(AQUI, 'barrido1.py'), 'rb').read()).hexdigest() == Fz['hashes']['barrido1.py'], 'hash del código'); ok(len(T) == len(E['metodos']) == json.load(open(os.path.join(RES, 'corrida.json')))['n'], 'número de métodos'); rec = {}
    import capymoa.regressor as R, capymoa.classifier as C, inspect
    for tipo, mod in (('reg', R), ('clf', C)): ok(sorted(n for t, n in T if t == tipo) == sorted(n for n, o in vars(mod).items() if inspect.isclass(o)), f'{tipo}: la lista cubre todas las clases exportadas')
    for tipo, n in T:
        k = f'{tipo}|{n}'; q = E['metodos'][k]; est = json.load(open(os.path.join(RES, f'{tipo}_{n}.json')))
        if est['estado'] != 'hecho': ok(q['clase'] == 'no probada' and not os.path.exists(os.path.join(RES, f'{tipo}_{n}.npz')), f'{k}: no probada'); rec['no probada'] = rec.get('no probada', 0) + 1; continue
        P = dict(np.load(os.path.join(RES, f'{tipo}_{n}.npz'))); X, y, yl = fabrica(tipo); ok(all(len(P[b]) == 3000 for b in ('U', 'U2', 'L', 'W')), f'{k}: cuatro brazos completos'); c = clase(P); ok(c == q['clase'], f'{k}: clase'); rec[c] = rec.get(c, 0) + 1
        for b in ('U2', 'L', 'W'): ok(int(np.sum(~((P['U'] == P[b]) | (np.isnan(P['U']) & np.isnan(P[b]))))) == q['cambian_' + b], f'{k}: cambian {b}')
        for b in ('U', 'L', 'W'):
            m = float(np.sqrt(np.mean((P[b][np.isfinite(P[b])] - y[np.isfinite(P[b])]) ** 2))) if tipo == 'reg' and np.isfinite(P[b]).any() else float(np.mean(P[b] == y)) if tipo == 'clf' else float('nan')
            ok((np.isnan(m) and np.isnan(q['medida'][b])) or abs(m - q['medida'][b]) <= 1e-12 * max(1.0, abs(m)), f'{k}: medida {b}')
    ok(rec == E['recuento'], 'recuento'); ok(E['valida'] == (E['metodos']['reg|SOKNL']['clase'] == 'lee la respuesta' and E['metodos']['reg|AdaptiveRandomForestRegressor']['clase'] == 'limpio'), 'controles de validez'); print('recuento recalculado:', rec, '| válida:', E['valida'])
    # tres métodos repetidos con bucle propio
    from capymoa.stream import NumpyStream
    def lista(X, y, tipo, peso=1):
        s = NumpyStream(X, y, target_type='numeric' if tipo == 'reg' else 'categorical'); out = []
        while s.has_more_instances():
            i = s.next_instance()
            if peso == 0: i.java_instance.getData().setWeight(0.0)
            out.append(i)
        return s.get_schema(), out
    for tipo, n, mod in (('reg', 'SOKNL', R), ('reg', 'KNNRegressor', R), ('clf', 'HoeffdingTree', C)):
        if json.load(open(os.path.join(RES, f'{tipo}_{n}.json')))['estado'] != 'hecho': continue
        X, y, yl = fabrica(tipo); G = np.load(os.path.join(RES, f'{tipo}_{n}.npz'))
        for b in ('U', 'L', 'W'):
            sc, Tr = lista(X, y, tipo); Pr = Tr if b == 'U' else lista(X, yl, tipo)[1] if b == 'L' else lista(X, y, tipo, 0)[1]
            try: m = getattr(mod, n)(schema=sc, random_seed=1)
            except Exception: m = getattr(mod, n)(schema=sc)
            out = np.full(3000, np.nan)
            for t in range(3000):
                p = m.predict(Pr[t]); out[t] = np.nan if p is None else float(p); m.train(Tr[t])
            ok(mismo(out, G[b]), f'{tipo}|{n} con bucle propio, brazo {b}')
    print(f'{N[0]} comprobaciones, {len(FALLOS)} fallos →', 'PASA' if not FALLOS else 'NO PASA')

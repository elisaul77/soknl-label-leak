"""Auditoría independiente de P-SAM-1. No importa el código del estudio: datos, recuento, veredicto y bucle propios."""
import os, json, hashlib
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(AQUI, 'results'); N = [0]; FALLOS = []
def ok(c, msg):
    N[0] += 1
    if not c: FALLOS.append(msg); print('  FALLA:', msg)
def terc(s): a, b = np.quantile(s, [1 / 3, 2 / 3]); return (s >= a).astype(int) + (s >= b).astype(int)
def fabrica(d, sem):
    r = np.random.default_rng(1000 * sem + (1 if d == 'C' else 0)); n = 4000 if d == 'C' else 3000; X = r.normal(size=(n, 6)); a = terc(np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * r.normal(size=n))
    if d == 'E': return X, a
    b = (terc(np.sin(2 * X[:, 3]) + X[:, 4] * X[:, 5] + 0.5 * r.normal(size=n)) + 1) % 3; return X, np.array([a[i] if (i // 500) % 2 == 0 else b[i] for i in range(n)])

if __name__ == '__main__':
    Fz = json.load(open(os.path.join(AQUI, 'config_frozen.json'))); E = json.load(open(os.path.join(RES, 'eval.json')))
    ok(hashlib.sha256(open(os.path.join(AQUI, 'sam1.py'), 'rb').read()).hexdigest() == Fz['hashes']['sam1.py'], 'hash del código'); ok(json.load(open(os.path.join(RES, 'corrida.json')))['n'] == 10, 'diez corridas'); pierde = {}; toca = False
    for d in ('E', 'C'):
        q = E['datos'][d]; dif = []
        for k, s in enumerate([1, 2, 3, 4, 5]):
            P = np.load(os.path.join(RES, f'{d}_{s}.npz')); X, y = fabrica(d, s); ok(all(len(P[b]) == len(y) for b in ('U', 'N', 'Z', 'A', 'L', 'KNN')), f'{d}/{s}: brazos completos')
            for b in ('U', 'N', 'Z', 'A', 'L', 'KNN'): ok(abs(float(np.mean(P[b] == y)) - q['acierto'][b][k]) < 1e-12, f'{d}/{s}: acierto {b}')
            c = int(np.sum(~((P['U'] == P['N']) | (np.isnan(P['U']) & np.isnan(P['N']))))); ok(c == q['predicciones_que_cambian_N'][k], f'{d}/{s}: cambian'); toca |= c > 0; dif.append(float(np.mean(P['N'] == y)) - float(np.mean(P['U'] == y)))
        pierde[d] = bool(np.mean(dif) <= -0.01 and sum(x < 0 for x in dif) >= 4); ok(pierde[d] == q['pierde'] and abs(np.mean(dif) - q['N_menos_U_media']) < 1e-12, f'{d}: pierde')
    v = 'no evaluable' if not toca else 'pierde fuera del examen' if pierde['E'] and pierde['C'] else 'pierde donde hay cambio' if pierde['C'] else 'no pierde'; ok(v == E['veredicto'], 'veredicto'); print('veredicto recalculado:', v, '| pierde:', pierde)
    from capymoa.stream import NumpyStream
    from capymoa.instance import Instance
    from capymoa.classifier import SAMkNN
    for d, s in (('E', 1), ('C', 3)):
        X, y = fabrica(d, s); G = np.load(os.path.join(RES, f'{d}_{s}.npz'))
        for b in ('U', 'N'):
            st = NumpyStream(X, y, target_type='categorical'); Tr = []
            while st.has_more_instances(): Tr.append(st.next_instance())
            sc = st.get_schema(); m = SAMkNN(schema=sc, random_seed=1); out = np.full(len(y), np.nan)
            for t in range(len(y)):
                i = Tr[t] if b == 'U' else Instance.from_array(sc, X[t])
                if b == 'N' and t == 0: ok(bool(i.java_instance.getData().classIsMissing()), f'{d}/{s}: el dato sin respuesta tiene la clase ausente')
                p = m.predict(i); out[t] = np.nan if p is None else float(p); m.train(Tr[t])
            ok(bool(np.all((out == G[b]) | (np.isnan(out) & np.isnan(G[b])))), f'{d}/{s} con bucle propio, brazo {b}')
    print(f'{N[0]} comprobaciones, {len(FALLOS)} fallos →', 'PASA' if not FALLOS else 'NO PASA')

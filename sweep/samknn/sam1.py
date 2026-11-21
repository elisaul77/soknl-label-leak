"""P-SAM-1: SAMkNN al predecir datos sin la respuesta verdadera. Protocolo: PROTOCOL_PSAM1.md."""
import os, sys, json, hashlib, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(AQUI, 'results'); SEMS = [1, 2, 3, 4, 5]; DATOS = ('E', 'C'); BRAZOS = ('U', 'N', 'Z', 'A', 'L'); D = 6
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def tres(s): return np.digitize(s, np.quantile(s, [1 / 3, 2 / 3])).astype(int)
def datos(dato, sem):
    g = np.random.default_rng(1000 * sem + (0 if dato == 'E' else 1)); n = 3000 if dato == 'E' else 4000; X = g.normal(size=(n, D)); ya = tres(np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * g.normal(size=n))
    if dato == 'E': return X, ya
    yb = (tres(np.sin(2 * X[:, 3]) + X[:, 4] * X[:, 5] + 0.5 * g.normal(size=n)) + 1) % 3; tramo = (np.arange(n) // 500) % 2; return X, np.where(tramo == 0, ya, yb)

def relleno(y, brazo, sem):
    if brazo == 'Z': return np.zeros(len(y), dtype=int)
    if brazo == 'A': return np.random.default_rng(77 + sem).integers(0, 3, size=len(y))
    if brazo == 'L': return (y + 1) % 3
    raise ValueError(brazo)

def pasa(modelo, Pr, Tr):
    out = np.full(len(Tr), np.nan)
    for t in range(len(Tr)):
        p = modelo.predict(Pr[t])
        if p is not None: out[t] = float(p)
        modelo.train(Tr[t])
    return out

def uno(dato, sem):
    from capymoa.stream import NumpyStream
    from capymoa.instance import Instance
    from capymoa.classifier import SAMkNN, KNN
    X, y = datos(dato, sem); P = {}
    def lista(yy):
        s = NumpyStream(X, yy, target_type='categorical'); out = []
        while s.has_more_instances(): out.append(s.next_instance())
        return s.get_schema(), out
    for b in BRAZOS:
        sc, Tr = lista(y); Pr = Tr if b == 'U' else [Instance.from_array(sc, X[t]) for t in range(len(y))] if b == 'N' else lista(relleno(y, b, sem))[1]; P[b] = pasa(SAMkNN(schema=sc, random_seed=1), Pr, Tr)
    sc, Tr = lista(y); P['KNN'] = pasa(KNN(schema=sc), Tr, Tr); np.savez_compressed(os.path.join(RES, f'{dato}_{sem}.npz'), **P)

def lanza(ds):
    d, s = ds; t0 = time.time(); r = subprocess.run([sys.executable, os.path.abspath(__file__), 'uno', d, str(s)], capture_output=True, text=True); print(f'  {d} semilla {s}: {"hecho" if os.path.exists(os.path.join(RES, f"{d}_{s}.npz")) else "FALLA " + r.stderr.strip()[-300:]} ({time.time() - t0:.0f} s)', flush=True)

def corre():
    os.makedirs(RES, exist_ok=True)
    with ThreadPoolExecutor(4) as ex: list(ex.map(lanza, [(d, s) for d in DATOS for s in SEMS]))
    json.dump({'n': len(DATOS) * len(SEMS)}, open(os.path.join(RES, 'corrida.json'), 'w'))

def veredicto(pierde, toca):
    return 'no evaluable' if not toca else 'pierde fuera del examen' if pierde['E'] and pierde['C'] else 'pierde donde hay cambio' if pierde['C'] else 'no pierde'

def evalua():
    R = {'datos': {}}; toca = False; pierde = {}
    for d in DATOS:
        ac = {b: [] for b in BRAZOS + ('KNN',)}; cambian = []
        for s in SEMS:
            P = np.load(os.path.join(RES, f'{d}_{s}.npz')); X, y = datos(d, s)
            for b in ac: ac[b].append(float(np.mean(P[b] == y)))
            cambian.append(int(np.sum(~((P['U'] == P['N']) | (np.isnan(P['U']) & np.isnan(P['N'])))))); toca |= cambian[-1] > 0
        dif = [n - u for n, u in zip(ac['N'], ac['U'])]; pierde[d] = bool(np.mean(dif) <= -0.01 and sum(x < 0 for x in dif) >= 4)
        R['datos'][d] = {'acierto': ac, 'media': {b: float(np.mean(v)) for b, v in ac.items()}, 'N_menos_U': dif, 'N_menos_U_media': float(np.mean(dif)), 'N_peor_en': int(sum(x < 0 for x in dif)), 'predicciones_que_cambian_N': cambian, 'pierde': pierde[d]}
    R['veredicto'] = veredicto(pierde, toca); json.dump(R, open(os.path.join(RES, 'eval.json'), 'w'), ensure_ascii=False, indent=1); print('veredicto:', R['veredicto'])
    for d, q in R['datos'].items(): print(f"  {d}: " + ' '.join(f"{b} {100 * q['media'][b]:.2f}" for b in BRAZOS + ('KNN',)) + f" | N−U {100 * q['N_menos_U_media']:+.2f} puntos, peor en {q['N_peor_en']}/5 | cambian {q['predicciones_que_cambian_N']}")

def prueba():
    X, y = datos('E', 1); assert X.shape == (3000, D) and set(y) == {0, 1, 2}; X, y = datos('C', 1); assert X.shape == (4000, D) and set(y) == {0, 1, 2}
    X2, y2 = datos('C', 2); assert not np.array_equal(y, y2) and np.array_equal(datos('C', 1)[1], y)
    assert (relleno(y, 'L', 1) != y).all() and (relleno(y, 'Z', 1) == 0).all() and set(relleno(y, 'A', 1)) == {0, 1, 2} and np.array_equal(relleno(y, 'A', 1), relleno(y, 'A', 1))
    assert veredicto({'E': True, 'C': True}, True) == 'pierde fuera del examen' and veredicto({'E': False, 'C': True}, True) == 'pierde donde hay cambio' and veredicto({'E': True, 'C': False}, True) == 'no pierde' and veredicto({'E': True, 'C': True}, False) == 'no evaluable'
    class M:
        def __init__(s): s.u = 0
        def predict(s, d): return s.u
        def train(s, d): s.u = d
    assert np.array_equal(pasa(M(), [9, 9, 9], [1, 2, 3]), [0, 1, 2]); print('pruebas inventadas: bien')

def congela():
    json.dump({'semillas': SEMS, 'datos': DATOS, 'brazos': BRAZOS, 'hashes': {'sam1.py': sha(os.path.abspath(__file__))}}, open(os.path.join(AQUI, 'config_frozen.json'), 'w'), indent=1); print('congelado')

if __name__ == '__main__':
    o = sys.argv[1] if len(sys.argv) > 1 else 'prueba'
    if o == 'uno': uno(sys.argv[2], int(sys.argv[3]))
    else:
        if o == 'corre': assert json.load(open(os.path.join(AQUI, 'config_frozen.json')))['hashes']['sam1.py'] == sha(os.path.abspath(__file__)), 'el código cambió tras congelar'; assert not os.path.exists(os.path.join(RES, 'corrida.json')), 'ya hay una corrida'
        {'prueba': prueba, 'congela': congela, 'corre': corre, 'evalua': evalua}[o]()

"""P-BARRIDO-1: ¿qué métodos de CapyMOA usan la respuesta del dato que predicen? Protocolo: PROTOCOL_PBARRIDO1.md."""
import os, sys, json, hashlib, inspect, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(AQUI, 'results'); SEM = 20261121; N = 3000; D = 6; TOPE = 600; BRAZOS = ('U', 'U2', 'L', 'W')
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def datos(tipo):
    g = np.random.default_rng(SEM); X = g.normal(size=(N, D))
    if tipo == 'reg': y = np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * g.normal(size=N); return X, y, y + 5 * y.std()
    s = np.sin(2 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.5 * g.normal(size=N); y = np.digitize(s, np.quantile(s, [1 / 3, 2 / 3])).astype(int); return X, y, (y + 1) % 3

def clases(tipo):
    import capymoa.regressor as r, capymoa.classifier as c
    m = r if tipo == 'reg' else c; return sorted(n for n, o in vars(m).items() if inspect.isclass(o))

def instancias(X, y, tipo, peso):
    from capymoa.stream import NumpyStream
    st = NumpyStream(X, y, target_type='numeric' if tipo == 'reg' else 'categorical'); L = []
    while st.has_more_instances():
        i = st.next_instance()
        if peso == 0: i.java_instance.getData().setWeight(0.0)
        L.append(i)
    return st.get_schema(), L

def construye(cls, sc):
    err = None
    for kw in (dict(schema=sc, random_seed=1), dict(schema=sc)):
        try: return cls(**kw), None
        except Exception as e: err = f'{type(e).__name__}: {e}'
    return None, err

def pasa(modelo, Pr, Tr):
    """Prueba y luego entrena: predice con Pr[t], entrena con Tr[t]. Devuelve las predicciones (NaN si no hay)."""
    out = np.full(len(Tr), np.nan)
    for t in range(len(Tr)):
        p = modelo.predict(Pr[t])
        if p is not None:
            try: out[t] = float(p)
            except Exception: pass
        modelo.train(Tr[t])
    return out

def uno(tipo, nombre):
    import capymoa.regressor as r, capymoa.classifier as c
    cls = getattr(r if tipo == 'reg' else c, nombre); X, y, yl = datos(tipo); P = {}
    for b in BRAZOS:
        sc, Tr = instancias(X, y, tipo, 1); Pr = Tr if b in ('U', 'U2') else instancias(X, yl, tipo, 1)[1] if b == 'L' else instancias(X, y, tipo, 0)[1]; m, err = construye(cls, sc)
        if m is None: json.dump({'estado': 'no construye', 'motivo': err[:300]}, open(os.path.join(RES, f'{tipo}_{nombre}.json'), 'w')); return
        P[b] = pasa(m, Pr, Tr)
    np.savez_compressed(os.path.join(RES, f'{tipo}_{nombre}.npz'), **P); json.dump({'estado': 'hecho'}, open(os.path.join(RES, f'{tipo}_{nombre}.json'), 'w'))

def clasifica(P):
    ig = lambda a, b: bool(np.array_equal(P[a], P[b], equal_nan=True))
    return 'no determinista' if not ig('U', 'U2') else 'lee la respuesta' if not ig('U', 'L') else 'depende del peso' if not ig('U', 'W') else 'limpio'

def medida(tipo, p, y):
    if tipo == 'reg': k = np.isfinite(p); return float(np.sqrt(np.mean((p[k] - y[k]) ** 2))) if k.any() else float('nan')
    return float(np.mean(p == y))

def lanza(tn):
    tipo, nombre = tn; t0 = time.time(); f = os.path.join(RES, f'{tipo}_{nombre}.json')
    try:
        r = subprocess.run([sys.executable, os.path.abspath(__file__), 'uno', tipo, nombre], capture_output=True, text=True, timeout=TOPE)
        if not os.path.exists(f): json.dump({'estado': 'falla', 'motivo': (r.stderr or r.stdout).strip().splitlines()[-1][:300] if (r.stderr or r.stdout).strip() else 'sin salida'}, open(f, 'w'))
    except subprocess.TimeoutExpired: json.dump({'estado': 'agota el tiempo', 'motivo': f'más de {TOPE} s'}, open(f, 'w'))
    print(f'  {tipo} {nombre}: {json.load(open(f))["estado"]} ({time.time() - t0:.0f} s)', flush=True)

def corre():
    os.makedirs(RES, exist_ok=True); T = [(t, n) for t in ('reg', 'clf') for n in clases(t)]; json.dump(T, open(os.path.join(RES, 'lista.json'), 'w'))
    with ThreadPoolExecutor(3) as ex: list(ex.map(lanza, T))
    json.dump({'n': len(T)}, open(os.path.join(RES, 'corrida.json'), 'w'))

def evalua():
    T = json.load(open(os.path.join(RES, 'lista.json'))); R = {'metodos': {}, 'recuento': {}}
    for tipo, n in T:
        e = json.load(open(os.path.join(RES, f'{tipo}_{n}.json'))); k = f'{tipo}|{n}'
        if e['estado'] != 'hecho': R['metodos'][k] = {'clase': 'no probada', 'motivo': e['estado'] + ': ' + e.get('motivo', '')}; continue
        P = dict(np.load(os.path.join(RES, f'{tipo}_{n}.npz'))); X, y, yl = datos(tipo); c = clasifica(P); q = {'clase': c, 'sin_prediccion': int(np.isnan(P['U']).sum()), 'medida': {b: medida(tipo, P[b], y) for b in ('U', 'L', 'W')}}
        for b in ('U2', 'L', 'W'): q['cambian_' + b] = int(np.sum(~((P['U'] == P[b]) | (np.isnan(P['U']) & np.isnan(P[b])))))
        R['metodos'][k] = q
    for q in R['metodos'].values(): R['recuento'][q['clase']] = R['recuento'].get(q['clase'], 0) + 1
    R['controles'] = {'soknl_lee': R['metodos'].get('reg|SOKNL', {}).get('clase') == 'lee la respuesta', 'arf_limpio': R['metodos'].get('reg|AdaptiveRandomForestRegressor', {}).get('clase') == 'limpio'}; R['valida'] = all(R['controles'].values())
    json.dump(R, open(os.path.join(RES, 'eval.json'), 'w'), ensure_ascii=False, indent=1); print('válida:', R['valida'], R['controles'], '| recuento:', R['recuento'])
    for k, q in R['metodos'].items(): print(f"  {k:44s} {q['clase']:18s}", '' if q['clase'] in ('limpio', 'no probada') else f"cambian L {q['cambian_L']} W {q['cambian_W']} U2 {q['cambian_U2']} | medida U {q['medida']['U']:.5f} L {q['medida']['L']:.5f} W {q['medida']['W']:.5f}", q.get('motivo', '')[:90])

def prueba():
    """Pruebas con métodos de mentira: comprueban el bucle y la clasificación sin tocar CapyMOA."""
    class Dato:
        def __init__(s, x, y, w=1.0): s.x, s.y, s.w = x, y, w
    class Limpio:
        def __init__(s): s.m = 0.0; s.n = 0
        def predict(s, d): return s.m
        def train(s, d): s.n += 1; s.m += (d.y - s.m) / s.n
    class Tramposo(Limpio):
        def predict(s, d): return 0.5 * s.m + 0.5 * d.y
    class PorPeso(Limpio):
        def predict(s, d): return s.m * d.w
    class Azar(Limpio):
        g = np.random.default_rng()
        def predict(s, d): return s.m + float(Azar.g.normal())
    g = np.random.default_rng(1); y = g.normal(size=200); Tr = [Dato(0, v) for v in y]; Lr = [Dato(0, v + 5) for v in y]; Wr = [Dato(0, v, 0.0) for v in y]
    for cls, esp in ((Limpio, 'limpio'), (Tramposo, 'lee la respuesta'), (PorPeso, 'depende del peso'), (Azar, 'no determinista')):
        P = {'U': pasa(cls(), Tr, Tr), 'U2': pasa(cls(), Tr, Tr), 'L': pasa(cls(), Lr, Tr), 'W': pasa(cls(), Wr, Tr)}; assert clasifica(P) == esp, (cls.__name__, clasifica(P))
    X, y, yl = datos('clf'); assert set(y) == {0, 1, 2} and (yl != y).all() and abs(np.mean(y == 0) - 1 / 3) < 0.01; X, y, yl = datos('reg'); assert np.allclose(yl - y, 5 * y.std()) and X.shape == (N, D)
    assert medida('clf', np.array([0., 1, np.nan]), np.array([0, 2, 1])) == 1 / 3; print('pruebas inventadas: bien')

def congela():
    json.dump({'semilla': SEM, 'n': N, 'd': D, 'tope_s': TOPE, 'brazos': BRAZOS, 'hashes': {'barrido1.py': sha(os.path.abspath(__file__))}}, open(os.path.join(AQUI, 'config_frozen.json'), 'w'), indent=1); print('congelado')

if __name__ == '__main__':
    o = sys.argv[1] if len(sys.argv) > 1 else 'prueba'
    if o == 'uno': uno(sys.argv[2], sys.argv[3])
    else:
        if o == 'corre': assert json.load(open(os.path.join(AQUI, 'config_frozen.json')))['hashes']['barrido1.py'] == sha(os.path.abspath(__file__)), 'el código cambió tras congelar'; assert not os.path.exists(os.path.join(RES, 'corrida.json')), 'ya hay una corrida'
        {'prueba': prueba, 'congela': congela, 'corre': corre, 'evalua': evalua}[o]()

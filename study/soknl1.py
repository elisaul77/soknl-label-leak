"""P-SOKNL-1: ¿la ventaja publicada de SOKNL sobre ARF-Reg depende de leer la respuesta al predecir? Modos: tests | freeze | corre | evalua."""
import sys, os, json, hashlib
import multiprocessing as mp
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, 'results'); EXT = os.path.join(HERE, '..', 'ext', 'KDD25-DriftSimulation', 'original_data')
TAB = ('abalone', 'bike', 'diamonds', 'House8L', 'superconductivity'); NODOS = ('ALB0331', 'HAM0331', 'ISL0661', 'SDN0331', 'STK0331', 'WIL0331'); RET = ('0.5hr', '4hr', '6hr', '24hr')
NZ = tuple(f'{n}|{r}' for n in NODOS for r in RET); FLUJOS = TAB + NZ; SEMILLAS = (1, 2, 3, 4, 5); MIEMBROS = 30
def ruta(sid): return os.path.join(EXT, sid + '.arff') if sid in TAB else os.path.join(EXT, 'NZEP_datasets', sid.split('|')[0], '{}_avg_{}.csv'.format(*sid.split('|')))
def hashes(): return dict({'soknl1.py': hashlib.sha256(open(os.path.join(HERE, 'soknl1.py'), 'rb').read()).hexdigest()}, **{s: hashlib.sha256(open(ruta(s), 'rb').read()).hexdigest() for s in FLUJOS})
def fuente(sid): return sid if sid in TAB else 'NZEP'

def carga(sid):
    """X, y en el orden del archivo; la última columna es el objetivo. Los atributos nominales del arff se codifican por su posición en la lista declarada."""
    if sid not in TAB: M = np.loadtxt(ruta(sid), delimiter=',', skiprows=1); return M[:, :-1], M[:, -1]
    L = open(ruta(sid)).read().splitlines(); i = next(k for k, l in enumerate(L) if l.strip().lower() == '@data'); nom = []
    for l in L[:i]:
        if l.strip().lower().startswith('@attribute'): r = l.strip(); nom.append([v.strip().strip("'\"") for v in r[r.index('{') + 1:r.rindex('}')].split(',')] if '{' in r else None)
    F = [[(nom[j].index(v.strip().strip("'\"")) if nom[j] else float(v)) for j, v in enumerate(l.rstrip().rstrip(',').split(','))] for l in L[i + 1:] if l.strip() and not l.startswith('%')]
    M = np.array(F, dtype=float); assert nom[-1] is None, 'el objetivo es numérico'; return M[:, :-1], M[:, -1]

def instancias(X, y, peso=None):
    from capymoa.stream import NumpyStream
    st = NumpyStream(X, y, target_type='numeric'); L = []
    while st.has_more_instances():
        ins = st.next_instance()
        if peso is not None: ins.java_instance.getData().setWeight(peso)
        L.append(ins)
    assert len(L) == len(y); return st.get_schema(), L
def corre(args):
    """brazo: 'habitual' (el dato lleva la respuesta y cuenta al predecir) o 'tapado' (al predecir el dato va con peso 0: el evaluador interno lo ignora)."""
    sid, metodo, brazo, sem, XY = args; X, y = XY if XY is not None else carga(sid)
    from capymoa.regressor import AdaptiveRandomForestRegressor, SOKNL
    sc, Tr = instancias(X, y); Pr = Tr if brazo == 'habitual' else instancias(X, y, 0.0)[1]; m = (SOKNL if metodo == 'soknl' else AdaptiveRandomForestRegressor)(schema=sc, ensemble_size=MIEMBROS, random_seed=sem); P = np.zeros(len(y)); ult = 0.0
    for t in range(len(y)):
        p = m.predict(Pr[t]); P[t] = ult if p is None or not np.isfinite(p) else float(p); m.train(Tr[t]); ult = float(y[t])
    return f'{sid}|{metodo}|{brazo}|{sem}', P
def trabajos(flujos): return [(s, 'soknl', b, k, None) for s in flujos for b in ('habitual', 'tapado') for k in SEMILLAS] + [(s, 'arf', 'habitual', k, None) for s in flujos for k in SEMILLAS] + [(s, 'arf', 'tapado', 1, None) for s in flujos]

def rmse(p, y, desde=0): return float(np.sqrt(((p - y)[desde:] ** 2).mean()))
def evalua_flujo(sid, Pn, y):
    q = {}
    for nom, d in (('todo', 0), ('final', int(0.2 * len(y)))):
        R = {f'{m}|{b}': [rmse(Pn[f'{sid}|{m}|{b}|{k}'], y, d) for k in SEMILLAS] for m, b in (('soknl', 'habitual'), ('soknl', 'tapado'), ('arf', 'habitual'))}; M = {k: float(np.mean(v)) for k, v in R.items()}
        q[nom] = dict(rmse=M, por_semilla=R, inflado=1 - M['soknl|habitual'] / M['soknl|tapado'], inflado_semillas_positivo=int(sum(a < b for a, b in zip(R['soknl|habitual'], R['soknl|tapado']))),
                      gana_habitual=bool(M['soknl|habitual'] < M['arf|habitual']), gana_tapado=bool(M['soknl|tapado'] < M['arf|habitual']), ventaja_habitual=1 - M['soknl|habitual'] / M['arf|habitual'], ventaja_tapado=1 - M['soknl|tapado'] / M['arf|habitual'])
        q[nom]['vuelco'] = bool(q[nom]['gana_habitual'] and not q[nom]['gana_tapado'])
    q['control_arf'] = bool(np.array_equal(Pn[f'{sid}|arf|habitual|1'], Pn[f'{sid}|arf|tapado|1'])); return q
def veredicto(F):
    ctrl = all(q['control_arf'] for q in F.values()); v = {s: F[s]['todo']['vuelco'] for s in F}; nz = [v[s] for s in F if fuente(s) == 'NZEP']; fu = {s: v[s] for s in F if fuente(s) != 'NZEP'}
    if nz: fu['NZEP'] = bool(sum(nz) > len(nz) / 2)
    n = int(sum(fu.values())); fr = 'no evaluable: falla el control de ARF-Reg' if not ctrl else 'la ventaja publicada depende de leer la respuesta' if n >= 3 else 'depende en parte' if n >= 1 else 'no depende'
    return dict(fuentes=fu, vuelcan=n, control=ctrl, veredicto=fr, nzep_vuelcan=int(sum(nz)), gana_habitual=int(sum(F[s]['todo']['gana_habitual'] for s in F)), gana_tapado=int(sum(F[s]['todo']['gana_tapado'] for s in F)), flujos=len(F))
def show(F, V):
    for s, q in F.items():
        t = q['todo']; print(f"{s:22s} RMSE SOKNL habitual {t['rmse']['soknl|habitual']:.4g} | tapado {t['rmse']['soknl|tapado']:.4g} | ARF-Reg {t['rmse']['arf|habitual']:.4g} | inflado {100 * t['inflado']:+.2f} % ({t['inflado_semillas_positivo']}/5 semillas) | ventaja sobre ARF {100 * t['ventaja_habitual']:+.2f} → {100 * t['ventaja_tapado']:+.2f} % {'VUELCO' if t['vuelco'] else ''} | final: inflado {100 * q['final']['inflado']:+.2f} %, {'vuelco' if q['final']['vuelco'] else ''}")
    print(V)

def tests():
    rng = np.random.default_rng(0); n = 1500; X = rng.normal(size=(n, 5)); y = np.sin(2 * X[:, 0]) * 3 + X[:, 1] * X[:, 2] + 0.3 * rng.normal(size=n); Pn = {}
    for a in [('s', 'soknl', b, k, (X, y)) for b in ('habitual', 'tapado') for k in SEMILLAS] + [('s', 'arf', 'habitual', k, (X, y)) for k in SEMILLAS] + [('s', 'arf', 'tapado', 1, (X, y))]: k, p = corre(a); Pn[k] = p
    assert np.array_equal(Pn['s|soknl|tapado|1'], corre(('s', 'soknl', 'tapado', 1, (X, y)))[1]) and all(np.isfinite(v).all() for v in Pn.values()), 'repetible y finito'
    assert not np.array_equal(Pn['s|soknl|habitual|1'], Pn['s|soknl|tapado|1']), 'tapar cambia a SOKNL'; q = evalua_flujo('s', Pn, y); assert q['control_arf'], 'tapar no cambia a ARF-Reg'
    V = veredicto({'abalone': q, 'ALB0331|4hr': q}); assert V['control'] and V['vuelcan'] in (0, 2) and abs(q['todo']['inflado'] - (1 - q['todo']['rmse']['soknl|habitual'] / q['todo']['rmse']['soknl|tapado'])) < 1e-12
    q2 = json.loads(json.dumps(q)); q2['control_arf'] = False; assert veredicto({'abalone': q2})['veredicto'].startswith('no evaluable')
    print('  sintético: inflado', round(100 * q['todo']['inflado'], 2), '% | ventaja sobre ARF', round(100 * q['todo']['ventaja_habitual'], 2), '→', round(100 * q['todo']['ventaja_tapado'], 2))
    for s in TAB + NZ[:1] + NZ[-1:]: Xs, ys = carga(s); assert np.isfinite(Xs).all() and np.isfinite(ys).all(); print(' ', s, Xs.shape, 'objetivo: media', round(float(ys.mean()), 3), 'desv.', round(float(ys.std()), 3))
    assert len(trabajos(FLUJOS)) == 29 * 16; print('PRUEBAS OK')

if __name__ == '__main__':
    mode = sys.argv[1]; os.makedirs(RES, exist_ok=True); cf = os.path.join(HERE, 'config_frozen.json')
    if mode == 'tests': tests()
    elif mode == 'freeze': json.dump(dict(semillas=SEMILLAS, miembros=MIEMBROS, flujos=FLUJOS, hashes=hashes()), open(cf, 'w'), indent=1); print('CONGELADO')
    elif mode == 'corre':
        Fz = json.load(open(cf)); assert Fz['hashes'] == hashes(), 'algo cambió tras congelar'; out = os.path.join(RES, 'corrida.json'); assert not os.path.exists(out), 'la corrida formal ya existe: es única'
        import capymoa
        J = sorted(trabajos(FLUJOS), key=lambda a: -os.path.getsize(ruta(a[0])))
        with mp.get_context('spawn').Pool(int(os.environ.get('SOKNL_PROCS', '4'))) as pool: O = pool.map(corre, J, chunksize=1)
        np.savez_compressed(os.path.join(RES, 'predicciones.npz'), **dict(O)); json.dump(dict(n=len(O), capymoa=capymoa.__version__), open(out, 'w')); print('FORMAL HECHA', len(O))
    elif mode == 'evalua':
        Pn = np.load(os.path.join(RES, 'predicciones.npz')); F = {s: evalua_flujo(s, Pn, carga(s)[1]) for s in FLUJOS}; V = veredicto(F); json.dump(dict(flujos=F, resumen=V), open(os.path.join(RES, 'eval.json'), 'w'), indent=1); show(F, V)

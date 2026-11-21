"""Auditoría independiente de P-SOKNL-1. No importa el código del estudio: lector, cuentas y bucle propios."""
import os, json, hashlib, re
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); DAT = os.path.join(AQUI, '..', 'ext', 'KDD25-DriftSimulation', 'original_data'); N = [0]; FALLOS = []
def ok(c, msg):
    N[0] += 1
    if not c: FALLOS.append(msg); print('  FALLA:', msg)
def donde(s): return os.path.join(DAT, s + '.arff') if '|' not in s else os.path.join(DAT, 'NZEP_datasets', s.split('|')[0], s.split('|')[0] + '_avg_' + s.split('|')[1] + '.csv')
def lee(s):
    if '|' in s:
        f = open(donde(s)); f.readline(); M = np.array([[float(v) for v in l.split(',')] for l in f if l.strip()]); return M[:, :-1], M[:, -1]
    cat = []; filas = []; datos = False
    for l in open(donde(s)):
        l = l.strip()
        if not l or l.startswith('%'): continue
        if not datos:
            if l.lower().startswith('@attribute'): m = re.search(r'\{(.*)\}', l); cat.append([v.strip().strip('\'"') for v in m.group(1).split(',')] if m else None)
            datos = l.lower() == '@data'; continue
        v = [x.strip().strip('\'"') for x in l.split(',')]; v = v[:len(cat)]; filas.append([cat[j].index(x) if cat[j] else float(x) for j, x in enumerate(v)])
    M = np.array(filas, dtype=float); return M[:, :-1], M[:, -1]

if __name__ == '__main__':
    Fz = json.load(open(os.path.join(AQUI, 'config_frozen.json'))); Ev = json.load(open(os.path.join(AQUI, 'results', 'eval.json'))); Pn = np.load(os.path.join(AQUI, 'results', 'predicciones.npz')); C = json.load(open(os.path.join(AQUI, 'results', 'corrida.json')))
    ok(hashlib.sha256(open(os.path.join(AQUI, 'soknl1.py'), 'rb').read()).hexdigest() == Fz['hashes']['soknl1.py'], 'hash del código'); FL = list(Fz['flujos']); ok(len(FL) == 29 and len(Pn.files) == 29 * 16 == C['n'], 'número de flujos y de predicciones'); SEM = [1, 2, 3, 4, 5]; ok(Fz['semillas'] == SEM and Fz['miembros'] == 30, 'configuración')
    vuel = {}; gh = gt = 0; ctrl = True
    for s in FL:
        ok(hashlib.sha256(open(donde(s), 'rb').read()).hexdigest() == Fz['hashes'][s], f'{s}: hash del dato'); X, y = lee(s); q = Ev['flujos'][s]
        for k in [f'{s}|soknl|{b}|{i}' for b in ('habitual', 'tapado') for i in SEM] + [f'{s}|arf|habitual|{i}' for i in SEM] + [f'{s}|arf|tapado|1']: ok(k in Pn.files and len(Pn[k]) == len(y) and np.isfinite(Pn[k]).all(), f'{k}: completo y finito')
        for nom, d in (('todo', 0), ('final', int(0.2 * len(y)))):
            r = lambda m, b: float(np.mean([np.sqrt(np.mean((Pn[f'{s}|{m}|{b}|{i}'][d:] - y[d:]) ** 2)) for i in SEM])); h, t, a = r('soknl', 'habitual'), r('soknl', 'tapado'), r('arf', 'habitual'); z = q[nom]
            ok(abs(h - z['rmse']['soknl|habitual']) < 1e-9 * h and abs(t - z['rmse']['soknl|tapado']) < 1e-9 * t and abs(a - z['rmse']['arf|habitual']) < 1e-9 * a, f'{s}/{nom}: RMSE'); ok(abs((1 - h / t) - z['inflado']) < 1e-9, f'{s}/{nom}: inflado'); v = bool(h < a and not t < a); ok(v == z['vuelco'], f'{s}/{nom}: vuelco')
            if nom == 'todo': vuel[s] = v; gh += h < a; gt += t < a
        c = bool(np.array_equal(Pn[f'{s}|arf|habitual|1'], Pn[f'{s}|arf|tapado|1'])); ok(c == q['control_arf'], f'{s}: control'); ctrl &= c
        ok(all(not np.array_equal(Pn[f'{s}|soknl|habitual|{i}'], Pn[f'{s}|soknl|tapado|{i}']) for i in SEM), f'{s}: tapar cambia las predicciones de SOKNL en las 5 semillas')
    nz = [vuel[s] for s in FL if '|' in s]; fu = {s: vuel[s] for s in FL if '|' not in s}; fu['NZEP'] = sum(nz) > len(nz) / 2; n = sum(fu.values()); fr = 'no evaluable: falla el control de ARF-Reg' if not ctrl else 'la ventaja publicada depende de leer la respuesta' if n >= 3 else 'depende en parte' if n >= 1 else 'no depende'
    R = Ev['resumen']; ok(fr == R['veredicto'] and n == R['vuelcan'] and sum(nz) == R['nzep_vuelcan'] and gh == R['gana_habitual'] and gt == R['gana_tapado'], 'veredicto y recuentos'); print('veredicto recalculado:', fr, '| vuelcan', n, 'fuentes | NZEP', sum(nz), 'de', len(nz), '| SOKNL gana a ARF: habitual', gh, 'tapado', gt)
    # un flujo con bucle propio
    from capymoa.stream import NumpyStream
    from capymoa.regressor import SOKNL
    X, y = lee('abalone')
    def lista(peso):
        st = NumpyStream(X, y, target_type='numeric'); L = []
        while st.has_more_instances():
            i = st.next_instance()
            if peso == 0: i.java_instance.getData().setWeight(0.0)
            L.append(i)
        return st.get_schema(), L
    for br in ('habitual', 'tapado'):
        sc, Tr = lista(1); Pr = Tr if br == 'habitual' else lista(0)[1]; m = SOKNL(schema=sc, ensemble_size=30, random_seed=1); out = np.zeros(len(y)); u = 0.0
        for t in range(len(y)):
            p = m.predict(Pr[t]); out[t] = u if p is None or not np.isfinite(p) else float(p); m.train(Tr[t]); u = float(y[t])
        ok(np.array_equal(out, Pn[f'abalone|soknl|{br}|1']), f'abalone con bucle propio, {br}')
    # el peso 0 no cambia el dato que ve el modelo: mismas entradas y misma respuesta guardada
    a = lista(1)[1][5].java_instance.getData(); b = lista(0)[1][5].java_instance.getData(); ok(a.classValue() == b.classValue() and all(a.value(j) == b.value(j) for j in range(X.shape[1])) and b.weight() == 0.0 and a.weight() == 1.0, 'el dato tapado solo difiere en el peso')
    print(f'{N[0]} comprobaciones, {len(FALLOS)} fallos →', 'PASA' if not FALLOS else 'NO PASA')

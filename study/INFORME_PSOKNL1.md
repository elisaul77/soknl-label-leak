# INFORME P-SOKNL-1 — SOKNL lee la respuesta al predecir: existe, es pequeño y no cambia la conclusión publicada

2026-11-21. Protocolo `PROTOCOL_PSOKNL1.md`, registrado antes del código. Una sola corrida (29 flujos, 464 pasadas, CapyMOA 0.11.0). Auditoría independiente (`audit_soknl1.py`): **PASA** (732 comprobaciones; lector y cuentas propios; abalone repetido con bucle propio, idéntico bit a bit).

## Veredicto registrado
**«no depende».** Ninguna de las 6 fuentes vuelca. El fallo existe, pero la ventaja publicada de SOKNL sobre ARF-Reg no descansa en él.

## 1. Medido
- **Control:** tapar la respuesta no cambia ni un bit de ARF-Reg en los 29 flujos. A SOKNL le cambia las predicciones en los 29 y en las 5 semillas.
- **El inflado va siempre en el mismo sentido:** leer la respuesta baja el RMSE de SOKNL en los 29 flujos y en las 5 semillas de cada uno (145 de 145).
- **Tamaño:**

| Fuente | Inflado del RMSE | Ventaja sobre ARF-Reg: habitual → tapado |
|---|---|---|
| abalone | 0,31 % | +4,6 → +4,3 % |
| bike | 0,13 % | −2,3 → −2,4 % |
| diamonds | 0,00 % | +23,1 → +23,1 % |
| House8L | 0,17 % | +0,8 → +0,6 % |
| superconductivity | 0,03 % | +0,6 → +0,5 % |
| NZEP (24 flujos) | 0,02 a 1,55 %, mediana ≈ 0,5 % | vuelcan 5 de 24 |

- SOKNL gana a ARF-Reg en 21 de 29 flujos con el bucle habitual y en 16 de 29 tapado.
- Los 5 vuelcos son todos de NZEP (cuatro a 4 h, uno a 24 h), donde los dos métodos están a menos de un 2 % uno del otro. NZEP es una sola fuente y vuelca menos de la mitad: no cuenta.

## 2. Lo que queda establecido
1. En CapyMOA 0.11.0, SOKNL usa la respuesta del dato que está prediciendo. Comprobado de dos maneras: leyendo el código público de MOA y midiendo (control con ARF-Reg incluido).
2. El efecto es sistemático pero pequeño: leer la respuesta baja el RMSE medido como mucho un 1,55 % (cambio relativo del RMSE, no puntos de ventaja), casi siempre menos de un 1 %.
3. Donde SOKNL gana con claridad (diamonds, abalone) sigue ganando igual. Solo cambian los empates.
4. Mi predicción: «depende en parte» 55 %, «no depende» 30 %. Fallé, aunque acerté que en los tabulares sería menor del 1 %.

## 3. Corrección que esto obliga a hacer en P-RELOJ-1
Allí el brazo «limpio» de SOKNL llevaba, en el hueco de la respuesta, el último valor conocido. Eso no solo le tapa la respuesta: le mete errores falsos en su elección de k. Por eso allí SOKNL caía un 7 % en luz a 4 h, y aquí, tapado sin ensuciar, cae un 1,5 %. **La frase «SOKNL es el que más pierde» de P-RELOJ-1 es en parte un artefacto de mi método.** El veredicto de P-RELOJ-1 no cambia (los ganadores anunciados en los dos casos principales eran vecinos, no SOKNL), pero las cifras de SOKNL «limpio» de aquel informe están castigadas de más.

## 4. Lectura (mía, posterior)
- Es un fallo de implementación real y, que yo haya encontrado, no avisado. Merece un aviso corto a los mantenedores, con la prueba de control. Nada más.
- No es un resultado que cambie una conclusión publicada. La objeción del revisor («¿qué conclusión publicada cambia?») se contesta: ninguna de las que hemos podido mirar.

## 5. Límites
- No sé si las cifras publicadas se sacaron con este mismo código; 30 miembros, 5 semillas.
- Solo parte de los conjuntos de los artículos; la clasificación pública que señaló Codex (StreamArena) no se ha repetido.
- Tapar con peso 0 es mi forma de corregirlo sin tocar el Java.
- Un autor, una corrida.

## 6. Archivos
`results/predicciones.npz`, `results/corrida.json`, `results/eval.json`, `config_frozen.json`, `soknl1.py`, `audit_soknl1.py`.

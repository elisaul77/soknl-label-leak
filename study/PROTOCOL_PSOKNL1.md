# PROTOCOLO P-SOKNL-1 — ¿la ventaja publicada de SOKNL sobre ARF-Reg depende de leer la respuesta?

2026-11-21. Registrado antes del código del estudio. Antes de escribirlo solo hice una sonda con datos **sintéticos** para saber si la medida es posible (ver §3).

## 1. De dónde sale
- Leyendo el código público de MOA (`SelfOptimisingKNearestLeaves.getVotesForInstance`, rama principal, consultado hoy): con la autooptimización activa (por defecto), al **predecir** SOKNL apunta el error de cada k candidato usando la respuesta que viaja en el dato, y **después** elige el k de menor error acumulado y devuelve su predicción. La respuesta del propio paso influye en la predicción de ese paso.
- En el bucle habitual de evaluación (predecir y luego entrenar con el mismo dato) el dato lleva la respuesta. Así se evaluó en los trabajos que lo comparan con ARF-Reg.
- En P-QUE-1 y P-RELOJ-1 medimos que SOKNL, y solo SOKNL, cambia de resultado según el dato lleve o no la respuesta.
- No he encontrado un aviso público de esto (búsqueda corta; Codex tampoco lo halló).

## 2. Pregunta
Repitiendo el protocolo habitual y cambiando **solo** que SOKNL no pueda leer la respuesta al predecir: ¿sigue ganando a ARF-Reg?

## 3. Cómo se le tapa la respuesta
El evaluador interno de MOA ignora los datos de peso cero. Brazo **TAPADO**: al predecir se le da el mismo dato con peso 0; al entrenar, el dato normal. Así el k se elige solo con errores de pasos anteriores, sin meter ruido. Brazo **HABITUAL**: el dato normal en los dos momentos.
Sonda sintética previa: con peso 0, ARF-Reg da predicciones idénticas bit a bit (control) y SOKNL cambia; es repetible con la misma semilla.

## 4. Datos (todo lo que hay en local de los bancos donde se publicó la comparación)
| Fuente | Flujos |
|---|---|
| abalone, bike, diamonds, House8L, superconductivity (repositorio DriftSimulation, `original_data`) | 5, una fuente cada uno |
| Precios de Nueva Zelanda (NZEP), 6 nodos × 4 horizontes, archivos `_avg_` | 24, **una sola fuente** |

Orden del archivo, sin tipificar, todas las columnas tal cual, como en el bucle publicado (incluida la actualización inmediata en NZEP: aquí se replica el protocolo publicado, no se corrige el reloj).

## 5. Brazos
SOKNL HABITUAL, SOKNL TAPADO y ARF-Reg, 30 miembros, resto por defecto de CapyMOA 0.11.0, semillas 1–5. Control: ARF-Reg con peso 0, semilla 1, debe ser idéntico al normal en todos los flujos.

## 6. Medida
RMSE sobre el flujo entero (como se publica); también sobre el 80 % final, descriptivo. Por flujo, con la media de RMSE de las 5 semillas:
- **Inflado** = 1 − RMSE_habitual / RMSE_tapado.
- **Vuelco** = SOKNL habitual gana a ARF-Reg y SOKNL tapado no.
Se informa también del signo del inflado semilla a semilla y de en cuántos flujos SOKNL gana a ARF-Reg en cada brazo.
NZEP cuenta como una fuente: «vuelca» si vuelcan más de la mitad de sus 24 flujos.

## 7. Criterio
- Vuelcan ≥ 3 de 6 fuentes: **«la ventaja publicada depende de leer la respuesta»**.
- Vuelcan 1 o 2: **«depende en parte»**.
- Ninguna: **«no depende»** (el fallo existe pero no cambia la conclusión publicada).
Si el control de ARF-Reg falla en algún flujo, «no evaluable».

## 8. Mi predicción
«Depende en parte» 55 %, «no depende» 30 %, «depende» 15 %. Espero vuelco en NZEP (70 %) e inflado pequeño (< 1 %) en los tabulares.

## 9. Método
Imagen `pfuera:env` sin red, 4 procesos. Pruebas, congelar, corrida única guardando predicciones, auditoría con lector propio que recalcula todo y repite un flujo con bucle propio, informe.

## 10. Límites conocidos de antemano
- CapyMOA 0.11.0 y su MOA empaquetado: no sé si las cifras publicadas se sacaron con este mismo código.
- 30 miembros y 5 semillas; los trabajos originales usan más de lo uno o lo otro.
- TAPADO es mi forma de corregirlo sin tocar el Java; los autores podrían corregirlo de otra manera.
- Seis fuentes, y solo parte de los conjuntos del artículo original de SOKNL.
- (Añadido antes de congelar, al escribir el lector.) En `diamonds` hay tres atributos de categorías; los paso como números por su posición en la lista declarada, no como categorías. Afecta igual a los tres brazos.
- Un autor, una corrida.

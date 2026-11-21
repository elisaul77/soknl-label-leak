# INFORME P-SAM-1 — sin respuesta al predecir, SAMkNN pierde poco o nada; con un relleno en el hueco pierde de 2 a 10 puntos

2026-11-21. Protocolo `PROTOCOL_PSAM1.md`, registrado antes del código. Una sola corrida (2 corrientes fabricadas × 5 semillas × 5 brazos, CapyMOA 0.11.0). Auditoría independiente (`audit_sam1.py`): **PASA** (91 comprobaciones; datos, recuento y veredicto propios; dos corridas repetidas con bucle propio).

## Veredicto registrado
**«no pierde».** En la corriente con conceptos que vuelven (C), predecir datos sin respuesta no baja el acierto. La regla exigía perder en C.

En la corriente estable (E) sí pierde, 1,49 puntos y en las 5 semillas; el protocolo dejaba ese caso sin nombre.

## 1. Medido
Acierto medio en 5 semillas (%), entrenando siempre con el dato verdadero:

| Qué lleva el hueco de la respuesta al predecir | Estable (E) | Conceptos que vuelven (C) |
|---|---|---|
| U — la respuesta verdadera (examen habitual) | 55,45 | 46,38 |
| **N — nada (dato sin respuesta)** | **53,96** | **46,72** |
| A — una clase al azar | 52,17 | 44,19 |
| Z — siempre la clase 0 | 47,33 | 42,78 |
| L — siempre otra clase | 45,94 | 42,60 |
| Referencia: KNN de CapyMOA | 54,49 | 45,45 |

| | E | C |
|---|---|---|
| N − U, por semilla (puntos) | −1,07; −1,47; −2,70; −0,67; −1,53 | +0,52; −0,17; +0,57; +0,30; +0,50 |
| N − U, media | −1,49 | +0,34 |
| Predicciones que cambian entre U y N | 92 a 645 de 3 000 | 311 a 601 de 4 000 |

## 2. Lo que queda establecido
1. El mecanismo es real: sin respuesta al predecir cambian entre el 3 % y el 21 % de las predicciones de SAMkNN.
2. **Sin respuesta, el efecto es pequeño.** En E pierde 1,5 puntos y queda por debajo del KNN corriente (53,96 frente a 54,49). En C no pierde; sale 0,3 puntos mejor.
3. **Con un valor de relleno en el hueco, el daño es claro:** entre 2,2 y 9,5 puntos según el relleno, en las dos corrientes.
4. Por qué N es benigno (lectura del código, no medida): con la clase ausente ninguna memoria «acierta», los tres historiales quedan a cero y el método usa siempre su memoria corta. No se estropea: deja de elegir.
5. Mi predicción: «no pierde» 40 % (era la que más peso tenía; salió). Fallé en el detalle: esperaba que perdiera donde hay cambio y no en la estable, y fue al revés.

## 3. Lectura (mía, posterior)
- La caída de 7 puntos de P-BARRIDO-1 era el peor caso. El caso real (dato sin respuesta) cuesta como mucho 1,5 puntos en estos datos.
- En mi corriente C, SAMkNN apenas supera al KNN corriente (46,4 frente a 45,5), así que hay poco que perder ahí. No es una buena corriente para ver el valor de sus memorias; una con cambios más marcados podría dar otro resultado.
- Lo que sigue siendo un defecto es de diseño: predecir cambia el estado del modelo según la respuesta que lleve el dato. Quien pase un relleno pierde varios puntos sin aviso, y quien no pase respuesta pierde la selección de memorias sin aviso.

## 4. Límites
- Dos corrientes fabricadas, 3 clases, valores por defecto.
- No se mide el caso de respuestas retardadas.
- «U equivale al método corregido» se apoya en leer el código.
- Una versión, una corrida, un autor.

## 5. Archivos
`results/eval.json`, `results/*.npz`, `config_frozen.json`, `sam1.py`, `audit_sam1.py`.

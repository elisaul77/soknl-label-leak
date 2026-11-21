# INFORME P-BARRIDO-1 — de 37 métodos de CapyMOA, 34 no tocan la respuesta al predecir; SOKNL y SAMkNN sí, y de dos maneras distintas

2026-11-21. Protocolo `PROTOCOL_PBARRIDO1.md`, registrado antes del código. Una sola corrida (CapyMOA 0.11.0, datos fabricados, valores por defecto). Auditoría independiente (`audit_barrido1.py`): **PASA** (304 comprobaciones; datos, comparación y clases propios; SOKNL, vecinos y árbol de Hoeffding repetidos con bucle propio).

La prueba es válida según el protocolo: SOKNL sale «lee la respuesta» y ARF-Reg sale «limpio».

## 1. Medido
| Clase | Métodos |
|---|---|
| **limpio** (34) | Regresión: ARFFIMTDD, AdaptiveRandomForestRegressor, FIMTDD, FadingTargetMean, KNNRegressor, NoChange, ORTO, PassiveAggressiveRegressor, SGDRegressor, SOKNLBT, ShrubsRegressor, StreamingGradientBoostedRegression, TargetMean. Clasificación: AdaptiveRandomForestClassifier, CSMOTE, DynamicWeightedMajority, EFDT, HoeffdingAdaptiveTree, HoeffdingTree, KNN, LeveragingBagging, MajorityClass, NaiveBayes, NoChange, OnlineAdwinBagging, OnlineBagging, OnlineSmoothBoost, OzaBoost, PassiveAggressiveClassifier, SGDClassifier, ShrubsClassifier, StreamingGradientBoostedTrees, StreamingRandomPatches, WeightedkNN |
| **lee la respuesta** (2) | SOKNL (regresión), **SAMkNN** (clasificación) |
| depende del peso | ninguno |
| no determinista | ninguno |
| no probada (1) | Finetune: necesita un modelo como argumento y no se construye por defecto |

| Método | Predicciones que cambian con la respuesta cambiada (L) | Con peso cero (W) | Medida: habitual → L → W |
|---|---|---|---|
| SOKNL | 1 730 de 3 000 | 31 de 3 000 | RMSE 1,0639 → 1,0877 → 1,0675 |
| SAMkNN | 1 082 de 3 000 | 0 | acierto 56,07 % → 48,67 % → 56,07 % |

## 2. Son dos fallos distintos (diagnóstico posterior, no registrado: `diag_punto.py` y lectura del código público de MOA)
El brazo L mezcla dos cosas: que la predicción de un dato dependa de **su propia** respuesta, y que predecir deje en el modelo una huella que depende de la respuesta y solo afecte a predicciones **posteriores**.

- **SOKNL: su propia respuesta.** Ya establecido en P-SOKNL-1. Aquí lo confirma el brazo W: quitar el dato de predicción de su evaluador interno cambia 31 predicciones y sube el RMSE un 0,34 %.
- **SAMkNN: huella al predecir.** En `SAMkNN.getVotesForInstance` (líneas 206–221 de MOA `master`) el método elige entre sus tres memorias con el historial de aciertos **anterior**, devuelve el voto, y después apunta en ese historial si cada memoria habría acertado **este** dato, comparando con `inst.classValue()`. La predicción del dato no usa su propia respuesta. Lo que pasa es que el aprendizaje de «qué memoria acierta más» se hace al predecir y no al entrenar.
- La sonda de un solo punto (10 sondas) no ve cambio en la predicción propia en ninguno de los dos. En SAMkNN concuerda con el código. En SOKNL no demuestra nada: con W solo cambia un 1 % de las predicciones, así que 10 sondas no bastan.

## 3. Qué implica lo de SAMkNN
1. **En la evaluación habitual (probar y luego entrenar, respuesta inmediata) no cambia ninguna cifra.** El apunte se haría igual un paso después. No hay cifras publicadas en duda por esto.
2. **Si el dato que se da a predecir no lleva la respuesta verdadera, el método se estropea.** Con respuestas equivocadas al predecir y entrenamiento correcto, el acierto baja de 56,1 % a 48,7 % en estos datos. Es el caso de cualquier uso real (se predice lo que aún no se sabe) y de quien rellene la respuesta con un valor cualquiera.
3. **Con respuestas retardadas, usa antes de tiempo la respuesta del dato** para elegir memoria en los pasos siguientes, si el evaluador le pasa el dato con su respuesta verdadera.
4. Llamar a predecir dos veces sobre el mismo dato apunta dos veces en el historial.
5. No he encontrado ningún aviso previo en MOA ni en CapyMOA (búsqueda en sus incidencias el 2026-11-21).

El punto 2 mide el peor caso (todas las respuestas cambiadas a otra clase, de forma sistemática), en un solo conjunto fabricado. No se ha medido con respuesta ausente ni con retardo.

## 4. Lo que queda establecido
1. Con esta prueba, 34 de los 36 métodos probados no cambian ni una predicción cuando se altera la respuesta o el peso del dato que predicen.
2. SOKNL y SAMkNN leen la respuesta dentro de la función de predecir. SOKNL la usa para la predicción de ese mismo dato; SAMkNN, para las siguientes.
3. SOKNLBT, la variante de SOKNL, sale limpia.
4. Mi predicción: SOKNL sí (acerté); SOKNLBT también (fallé: sale limpia); «algún otro método» 30 % (ocurrió: SAMkNN); «algún no determinista» 50 % (no hubo ninguno).

## 5. Límites
- Que la prueba no salte no certifica limpieza: datos fabricados, 3 000 filas, entradas numéricas, valores por defecto, una semilla.
- La clase «lee la respuesta» del protocolo no distingue los dos casos del apartado 2; la distinción es posterior y se apoya en leer el código.
- No se ha comprobado SOKNLBT leyendo su código.
- Una versión, una corrida, un autor.

## 6. Archivos
`results/eval.json`, `results/*.npz` (predicciones de cada método y brazo), `results/diag_punto.json`, `config_frozen.json`, `barrido1.py`, `audit_barrido1.py`, `diag_punto.py`.

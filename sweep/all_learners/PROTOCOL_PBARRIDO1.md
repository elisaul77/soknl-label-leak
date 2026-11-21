# PROTOCOLO P-BARRIDO-1 — ¿qué otros métodos de CapyMOA usan la respuesta del dato que están prediciendo?

Registrado el 2026-11-21, antes del código. Sigue a P-SOKNL-1 (`soknl/INFORME_PSOKNL1.md`).

## 1. Pregunta
En CapyMOA 0.11.0, además de SOKNL, ¿la predicción de algún regresor o clasificador depende de la respuesta que lleva el dato que se le da a predecir?

## 2. Antecedentes
Una búsqueda (extendida, una consulta) no encontró ninguna revisión sistemática de este tipo en MOA, CapyMOA ni River. Es una búsqueda corta: «no encontrado», no «no existe».

## 3. Alcance
Todas las clases que exporta `capymoa.regressor` (14) y `capymoa.classifier` (23) en la imagen `pfuera:env`, construidas con sus valores por defecto y `random_seed=1` cuando lo admiten. La que no se pueda construir así, o falle, o tarde más de 10 minutos, se anota como «no probada» con el motivo; no se le buscan parámetros.

## 4. Datos
Fabricados, sin descargas, semilla 20261121:
- Regresión: 3 000 filas, 6 entradas numéricas, y = sen(2·x0) + x1·x2 + ruido.
- Clasificación: 3 000 filas, 6 entradas numéricas, 3 clases por umbrales de una combinación no lineal más ruido.

## 5. Brazos (se entrena siempre con el dato verdadero y peso 1)
- **U (habitual):** se predice con el mismo dato con el que luego se entrena.
- **U2:** repetición exacta de U. Mide si el método es determinista.
- **L (respuesta cambiada):** el dato de predicción lleva las mismas entradas y otra respuesta (regresión: y + 5 desviaciones típicas; clasificación: la clase siguiente, cíclicamente).
- **W (peso cero):** el dato de predicción lleva la respuesta verdadera y peso 0.

## 6. Clasificación de cada método (fijada ahora)
- **no determinista:** U ≠ U2. No se puede juzgar.
- **lee la respuesta:** U = U2 y L ≠ U.
- **depende del peso:** U = U2, L = U y W ≠ U. Se informa aparte; no es por sí solo leer la respuesta.
- **limpio:** U = U2 = L = W, bit a bit.
- **no probada:** no se construye, falla o agota el tiempo.

«Igual» es igualdad exacta de todas las predicciones (las ausentes cuentan como iguales entre sí).

## 7. Controles de validez
- SOKNL debe salir «lee la respuesta». Si no, la prueba no vale.
- ARF-Reg debe salir «limpio». Si no, la prueba no vale.

## 8. Qué se informa
Tabla por método con su clase; para los que lean la respuesta, cuántas predicciones cambian y cuánto cambia la medida (RMSE o acierto) entre U y W, y entre U y L. Sin veredicto global más allá del recuento.

## 9. Límites conocidos de antemano
- Una prueba que no salta no certifica limpieza: solo dice que en estos datos y con estos parámetros la predicción no cambió.
- Datos fabricados y pequeños; solo entradas numéricas; valores por defecto.
- El brazo L ensucia el estado de un método que lea la respuesta, así que el tamaño medido con L no es el tamaño del fallo; para eso está W, y solo sirve si el método usa los evaluadores de MOA.
- Una versión, una corrida, un autor.

## 10. Mi predicción
SOKNL y SOKNLBT leen la respuesta (95 %). Algún otro método además de esos dos: 30 %. Algún método «no determinista»: 50 %.

## 11. Auditoría
Guion independiente que reconstruye los datos, recompara las predicciones guardadas, recalcula las clases y repite con bucle propio dos métodos (uno limpio y SOKNL).

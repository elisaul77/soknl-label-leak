# PROTOCOLO P-SAM-1 — ¿cuánto pierde SAMkNN cuando el dato que predice no lleva la respuesta verdadera?

Registrado el 2026-11-21, antes del código. Sigue a P-BARRIDO-1 (`barrido/INFORME_PBARRIDO1.md`), donde se vio que SAMkNN apunta en su historial de memorias dentro de la función de predecir, comparando con la respuesta que lleve el dato.

## 1. Pregunta
P-BARRIDO-1 midió solo el peor caso (respuesta cambiada siempre a otra clase). Aquí se mide el caso de uso real: predecir un dato **sin respuesta**, que es lo que hace cualquiera que use el modelo fuera de un examen.

Comprobado antes de registrar (solo la interfaz, sin correr SAMkNN): en CapyMOA 0.11.0, `Instance.from_array(schema, x)` crea un dato sin respuesta y su valor de clase es «ausente» (NaN).

## 2. Brazos (se entrena siempre con el dato verdadero, respuesta inmediata)
- **U (habitual):** se predice con el dato etiquetado. Equivale a lo que haría un SAMkNN corregido.
- **N (sin respuesta):** se predice con `Instance.from_array(schema, x)`. **Brazo principal.**
- **Z (relleno fijo):** se predice con la clase 0 en el hueco.
- **A (relleno al azar):** clase al azar, semilla fija.
- **L (otra clase):** la clase siguiente, como en P-BARRIDO-1.

## 3. Datos (fabricados, sin descargas; 5 semillas de datos cada uno)
- **E (estable):** 3 000 filas, 6 entradas, 3 clases por umbrales de sen(2·x0) + x1·x2 + ruido.
- **C (conceptos que vuelven):** 4 000 filas, 6 entradas, 3 clases; tramos de 500 filas que alternan dos reglas (la de E y otra con las clases rotadas y otras entradas). Es el tipo de corriente para la que SAMkNN se diseñó.

## 4. Medidas
Acierto de cada brazo y diferencia N − U por semilla. Además, como referencia, el clasificador `KNN` de CapyMOA en el brazo U.

## 5. Veredicto (fijado ahora, sobre el brazo N)
Para cada dato, «pierde» si la media de N − U es ≤ −1 punto y N < U en al menos 4 de 5 semillas.
- **«pierde fuera del examen»:** pierde en E y en C.
- **«pierde donde hay cambio»:** pierde solo en C.
- **«no pierde»:** no pierde en C. (Si pierde solo en E se informa tal cual, sin nombre.)
- **«no evaluable»:** si U y N dan predicciones idénticas en todas las corridas (la prueba no estaría tocando el mecanismo) o falla la auditoría.

## 6. Límites conocidos de antemano
- Datos fabricados; dos corrientes; valores por defecto de SAMkNN.
- No se mide el caso de respuestas retardadas: para compararlo haría falta un SAMkNN corregido, y no se toca el código Java.
- U como «lo que haría el método corregido» es un argumento por lectura del código, no una medida con el código corregido.
- Una versión, una corrida, un autor.

## 7. Mi predicción
N pierde en C: 60 %. N pierde en E: 30 %. Veredictos: «pierde donde hay cambio» 35 %, «pierde fuera del examen» 25 %, «no pierde» 40 %.

## 8. Auditoría
Guion independiente: datos propios, recuento propio de aciertos y veredicto, y dos corridas repetidas con bucle propio.

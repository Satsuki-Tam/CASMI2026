# El Espejismo del Leaderboard: Cómo pasar de 0.133 a 0.094 (y por qué es una gran noticia)
topic 750491 | by **Manuel lasarte León** (https://www.kaggle.com/manuellasarte) | posted 2026-10-18 | votes 1 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750491

El Espejismo del Leaderboard: Por qué limpiar fugas de datos redujo mi score público de 0.133 a 0.094 (Y qué nos sugiere esto sobre el test set)
Hola a todos,

Durante el desarrollo de nuestro pipeline para la identificación molecular en esta competición, nos hemos topado con una dinámica interesante: corregir errores metodológicos en nuestro pipeline hizo que nuestra puntuación en el Leaderboard público descendiera, pasando de un 0.133 a un 0.094.

Analizar este descenso ofrece una perspectiva útil sobre cómo las fugas de datos (data leaks) interactúan con la evaluación pública y por qué un score más bajo puede reflejar un modelo que ya no depende de atajos en sus características.

- La autopsia: ¿Dónde estaban las inconsistencias metodológicas?
Nuestras primeras iteraciones alcanzaban scores más altos en el LB público, pero un análisis profundo destapó dos factores críticos en la ingeniería de características:

La auto-referencia de Tanimoto: Al buscar vecinos con FAISS sobre el índice de entrenamiento (index_train), las moléculas pertenecientes a train encontraban su propia huella exacta (Tanimoto = 1.0). El modelo aprendió a priorizar esa señal explícita, ventaja con la que no contaban los candidatos externos de COCONUT.

Contaminación del Banco Espectral global (spec_bank): Los espectros de referencia se construían de manera combinada, filtrando indirectamente cierta información en la validación.

- Una hipótesis sobre el Leaderboard Público
Un modelo con fugas en las características de entrenamiento se infla internamente en la validación local, pero en teoría no debería mejorar el score de un test set independiente a menos que exista una relación específica entre ambos conjuntos.

Si un pipeline con estas fugas puntuaba más alto en el Leaderboard público (0.133 frente a 0.094), esto sugiere como hipótesis que el conjunto de test público podría contener cierto solapamiento (overlap) con las estructuras de entrenamiento. Si ese solapamiento existe, el modelo anterior lograba aprovecharlo para obtener mejor puntuación.

- Cambios en la versión limpia y composición de predicciones
Al aislar los bancos de referencia y corregir la auto-referencia (cambios que también se ejecutaron en paralelo junto con la incorporación de soporte multi-aducto para evaluar candidatos adicionales):

El modelo dejó de utilizar el acceso directo de la auto-coincidencia.

La distribución de las predicciones cambió: el 34% de las predicciones Top-1 pasaron a ser candidatos externos de COCONUT.

El score público cambió a 0.094, probablemente al reducirse la capacidad del modelo para aprovechar eventuales solapamientos con el conjunto de entrenamiento.

Conclusión
Aunque en un Leaderboard público la memorización o el uso de atajos puede traducirse en una métrica superior cuando existe solapamiento, en el conjunto de test privado (donde la distribución suele primar estructuras no vistas) este tipo de dependencias podría penalizar el rendimiento final.

¿Habéis observado patrones similares o indicios de solapamiento en vuestros pipelines? ¡Será muy interesante leer vuestras observaciones en los comentarios!

## Comments (0 top-level)


# Rondas Claude 042–044: barrido del ancho del parásito Wp en US3_PS4

- **IDs:** US3_PS4_2_OPENEMS_042 (Wp 10 mm), US3_PS4_3_OPENEMS_043 (Wp 9 mm), US3_PS4_4_OPENEMS_044 (Wp 8 mm). Este informe cubre las tres rondas.
- **Fecha:** 2026-11-16, rondas 42–44/50.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «US3_PS4_1 no mejora como yo esperaba; prueba en lugar de Wp = 7 mm con los 3 valores entre medias, 10, 9 y 8 mm. Muéstralo en una gráfica aparte en el artifact».
- **Variantes:** `variants/US3_PS4_2.json`, `US3_PS4_3.json` y `US3_PS4_4.json`, generadas por el orquestador a partir de US3_PS4_1. Solo cambia Wp (parásito centrado en x, y −2,98…4,48, z 1,035). Hints de malla y [−0,215, −2,99], igual que en 040. Antes de simular se hizo `prepare` en malla base y fina para cada una, y las seis pasan el gradado de 1,5.
- **FDTD:** 3, una por ronda y en secuencia, todas en malla base con `--max-timesteps 60000`, 2 hilos y afinidad 0,1.
  - Un primer intento de 042 se lanzó dentro de un monitor que tenía un tope de 30 minutos. Se detuvo a los pocos segundos y se borró la carpeta. Las tres rondas se relanzaron desde cero.
  - Cada carpeta contiene un solo run: `prepare` y `solve` en la misma carpeta, con `launcher.json` escrito entre ambos.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.
- **Referencias del barrido:** US3_PS4 (036, Wp 11 mm) y US3_PS4_1 (040, Wp 7 mm), con el mismo comando y el mismo perfil de malla base. Las líneas efectivas difieren: 036 no lleva el hint y −2,99; la malla en x cambia con Wp (157–163 líneas, desplazamientos de décimas de mm entre ±5 y ±13 mm); el paso temporal varía entre 2,18e-13 y 2,26e-13 s. Las diferencias finas entre puntos vecinos (≈ 0,1 dB, profundidad del mínimo) no son interpretables; los efectos grandes del barrido sí.
- **Trazabilidad:** `solver_log.txt` y `nf2ff_raw_dumps.sha256` de las tres carpetas se escribieron juntos al final del barrido (13:22 UTC), como copias de `solver.log` y hashes a posteriori. `prepared.json` conserva `status: PREPARED_NOT_RUN`, como en 036 y 040; el estado real está en `run_numeric.json`.

## Ejecución
- **042:** −50,71 dB en 37 152 pasos, 620 s de solver, pico RSS 464 188 KiB.
- **043:** −50,22 dB en 36 623 pasos, 731 s de solver, pico RSS 478 876 KiB.
- **044:** −52,17 dB en 37 692 pasos, 803 s de solver, pico RSS 469 132 KiB.
- La energía de parada fluctúa unos 5 dB en los últimos muestreos (p. ej. 043: −45,1 → −50,2 dB), así que el −50 dB se cumple en una muestra; el truncado temporal es una fuente de error no cuantificada, compartida con 036 y 040.
- `port_validity` OK en las tres. openEMS v0.37.0-40-g5fecbb5. Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256.

## Resultados (malla base; S11 en rejilla de 1 MHz salvo que se indique)

| Wp | Mínimos de S11 (picos de Re(Zin) entre paréntesis en el texto) | Peor S11 en el canal | Canal ≤ −10 dB | Bordes 7,7376 / 8,2368 | η mín. (frecuencia) | Puntos con η < 0,55 | Ganancia realizada mín. |
|---|---|---|---|---|---|---|---|
| 11 mm (036) | 7,826 (−30,2) y 8,158 GHz (−32,2) | −10,66 dB | 100 % | −16,6 / −10,7 | 0,244 (8,137) | 5 | −0,48 dBi |
| **10 mm (042)** | **7,868 (−28,9) y 8,098 GHz (−27,3)** | **−8,56 dB (8,2368)** | 93,2 % | −13,4 / −8,6 | 0,301 (8,087) | 6 | 0,43 dBi |
| **9 mm (043)** | **mínimo ancho en 7,932 GHz (−23,8) con meseta hasta 8,00 GHz** (el «segundo mínimo» de 7,999 GHz tiene 0,008 dB de prominencia: no es un mínimo físico) | **−7,87 dB (8,2368)** | 85,6 % | −10,7 / −7,9 | 0,389 (8,037) | 4 | 1,65 dBi |
| **8 mm (044)** | **uno: 7,972 GHz (−15,4)** | **−7,97 dB (8,2368)** | 75,2 % | −8,8 / −8,0 | 0,496 (7,987) | 2 | 2,51 dBi |
| 7 mm (040) | uno: 7,972 GHz (−19,6) | −7,71 dB (7,7376) | 75,0 % | −7,7 / −8,8 | 0,517 (7,887) | 2 | 2,54 dBi |

η es P_rad / P_aceptada en las 11 frecuencias del NF2FF, con un paso de 49,92 MHz. La frecuencia del valle de η está limitada a esa rejilla.

## Hipótesis pre-registradas (iguales en las tres variantes)
- **H0, falla en parte.**
  - Se cumple el orden monótono. Con el criterio de picos de Re(Zin) (más robusto aquí que los mínimos de S11): 7,76/8,17 GHz (11 mm) → 7,80/8,12 (10) → 7,853/8,056 (9) → un solo pico en 7,971 (8) → 7,876 GHz (7 mm). Los mínimos de S11 se separan 332 MHz (11 mm) y 230 MHz (10 mm); con 9 mm ya hay un solo mínimo ancho con meseta.
  - No se cumple dónde se funden: los mínimos de S11 se funden entre 10 y 9 mm y los picos de Re(Zin) entre 9 y 8 mm, no entre 8 y 7 mm como se había escrito.
- **H1 falla en los tres anchos.** Con 10 mm el mínimo inferior sube +42 MHz, como pedía el propietario, pero el superior baja −60 MHz. El borde superior del canal pierde la adaptación: −8,56 dB.
- **H2 falla en los tres:** hay 6, 4 y 2 puntos con η < 0,55. Aun así, el valle se hace menos profundo a medida que Wp baja, como se esperaba.

## Lectura (observaciones; sin identificar el mecanismo)
- **Con este parámetro no se puede subir solo el mínimo inferior.** En todo el barrido, al subir el inferior también baja el superior, y el peor caso pasa del borde superior del canal (10 a 8 mm) al inferior (7 mm).
- **El valle de η se mueve con Wp.** Baja de frecuencia (8,137 → 8,087 → 8,037 → 7,987 → 7,887 GHz) y se hace menos profundo (0,24 → 0,52). En 10 y 9 mm queda cerca del mínimo superior de S11 o del segundo pico de Re(Zin) (8,12 y 8,055 GHz). Que el modo poco radiante sea el que baja con Wp es compatible con los datos, pero sin un mapa de campo no queda demostrado.
- **No hay ningún ancho intermedio que mejore a US3_PS4 en S11 y a US3_PS6 en eficiencia a la vez.**
  - Wp 10 mm conserva el S11 de doble mínimo con el inferior más centrado, pero pierde 2,1 dB en el borde superior frente a PS4. Su valle de η sigue siendo profundo (0,30).
  - US3_PS6, en la misma malla base (038), sigue siendo mejor en conjunto: peor caso −8,16 dB y η de 0,59 a 0,68 sin valle.
- **Para subir el inferior sin bajar el superior**, el barrido indica que hace falta un segundo grado de libertad. Por ejemplo, Wp 10 mm junto con un patch_L algo menor, para desplazar el par entero hacia arriba, como se hizo de PS1 a PS4. Es una hipótesis que habría que contrastar, y solo con el consentimiento del propietario.

## Gráfica
En el artifact «U-slot con parche parásito · openEMS» hay un apartado propio, «Barrido del ancho del parásito Wp en US3_PS4», con |S11|, η y ganancia realizada para Wp de 11 a 7 mm.

## Auditoría
`validator` (2026-11-16): **OK con observaciones** en las tres rondas. Variantes, run único por carpeta, hashes, energía y todas las cifras de la tabla confirmados. Sus reservas (falso segundo mínimo en 043, mallas efectivas distintas, trazabilidad, fluctuación de la energía de parada) están incorporadas arriba. Las rondas 042 y 043 no tienen informe propio: este informe las cubre.

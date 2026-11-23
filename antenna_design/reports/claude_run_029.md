# Ronda Claude 029: US3_MS4, U más ancha (u_Wu 4,4 → 7,0 mm)

- **ID del experimento:** US3_MS4_OPENEMS_029.
- **Fecha:** 2026-11-13, ronda 29/40, en la sesión del propietario (petición tras su barrido HFSS de `patch_L`).
- **Orquestador:** `claude-opus-5-5` (comprobado con `get_session`).
- **FDTD:** 1, malla base.
- **Evidencia:** `EM_SIMULATED`.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS** (números comprobados contra los CSV; tests 57 OK).

## Contexto: barrido HFSS de `patch_L` (propietario)
Datos: [`hfss/results_2026-11-13/S Parameter US3_MS3 parametric patch_L.csv`](../hfss/results_2026-11-13/), 12 valores de 6,402 a 6,502 mm, 1 MHz. Análisis: [`hfss/hfss_parametric_patch_L.py`](../hfss/hfss_parametric_patch_L.py) → [`hfss_parametric_patch_L_2026-11-13.json`](../hfss/hfss_parametric_patch_L_2026-11-13.json).
- El ancho de −10 dB **no cambia**: 349–359 MHz en todos los valores. El de −6 dB, 699–713 MHz.
- El centro de la banda de −10 dB se mueve unos **−7 MHz por cada +0,01 mm** (ajuste lineal; residuo RMS 9 MHz, máximo 18 MHz, no monótono; atribuido sin verificar a la malla adaptativa de cada punto).
- Mejor peor caso en el canal: −7,94 dB con L = 6,432 mm. Ningún valor llega a −10 dB en todo el canal, porque la banda de −10 dB (~350 MHz) es más estrecha que el canal (499,2 MHz).
- Solo hay un mínimo de S11 y ningún lazo en la carta de Smith, ni en HFSS ni en openEMS (023/024). En openEMS no hay ningún pico de Re(Zin) por debajo de 10,52 GHz salvo el del parche, aunque Re(Zin) ya sube a ~56 Ω en ese borde. **En el canal la respuesta es la de un parche de una sola resonancia**; la U no aporta una segunda resonancia cerca del canal.

## Propuesta
[`variants/US3_MS4.json`](../variants/US3_MS4.json): US3_MS3 con **una sola variable cambiada, u_Wu de 4,4 a 7,0 mm** (polígono de la ranura ±2,2 → ±3,5 mm; Lu 2,65, t 0,8, y0 −0,7 sin cambios).
- Márgenes: 2,21 mm de cobre a cada lado de la U, isla central de 5,4 mm, 1,30 mm de la parte alta de la U al borde del parche.
- Parche (6,502 × 11,421 mm), alimentación (línea 50 Ω + transformador 0,80 × 6,60 mm), FR4 provisional (εr 4,4, tanδ 0,017, 2,07 mm), cobre 35 µm / 5,8e7 S/m, placa 26 × 26 mm y puerto concentrado de 50 Ω en el borde: iguales a US3_MS3.
- **Estimación guía (GUIDE_MODEL, no EM):** escalado de un solo punto desde US2 (modo alto en 10,36 GHz con una U de 9,2 mm de longitud media). Con Wu 7,0 la longitud media pasa de 8,1 a 10,7 mm, lo que situaría el modo de la U hacia **8,9 GHz**.
- **Hipótesis pre-registradas** (en la variante, antes del run):
  - H1: aparece una segunda resonancia (máximo local de Re(Zin) ≥ 20 Ω o lazo) entre 8,24 y 10,5 GHz.
  - H2: la banda contigua de −10 dB es más ancha que la de US3_MS3 en la misma malla (023: 7,800–8,170 GHz, 370 MHz).
  - Regla: H1 y H2 → recentrar con `patch_L`. H1 sin H2 → probar Lu o y0. Sin H1 → el escalado falla y se abandona la vía Wu.

## Ejecución
- **Solver:** openEMS/CSXCAD del entorno (`em/runtime_env.sh`), mismo comando y mismo perfil de malla que 023 salvo la variante: `python em/patch_openems.py solve --variant variants/US3_MS4.json --out em/US3_MS4_OPENEMS_029 --mesh base --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9`, con `timeout 1500s` y `taskset -c 0,1` ([`launcher.json`](../em/US3_MS4_OPENEMS_029/launcher.json)).
- **Malla:** 2 227 680 celdas (156 × 170 × 84); gradación máx. 1,41 (límite 1,5). La línea guía y = −0,215 mm de US3_MS3 sigue dentro de la base de la U, que no se mueve. **No es la misma malla que 023:** 3 celdas en el ancho de la ranura (023: 4) y límite de gradación usado 1,5 (023: 1,4); 2 199 120 celdas en 023.
- **Estimación previa:** 500–810 s, 0,45–0,8 GB. **Real:** 261 s de pared, 460 s de CPU, RSS 0,45 GB, 2 CPU.
- **Fin:** energía −50,08 dB respecto al máximo de las muestras de `openEMS_run_stats.txt`, 14 280 pasos (corrección de la ronda 030: openEMS normaliza con su máximo interno, mayor que el de las muestras, así que el valor de su `solver.log`, no conservado, sería más bajo; −50,08 dB es una cota superior). `port_validity` OK (|S11| máx. 0,89).
- **Incidencia:** el primer lanzamiento falló al instante porque `/usr/bin/time` no existe en el contenedor (exit 127, el solver no llegó a arrancar). Se relanzó sin él; el `started_utc` del `launcher.json` corresponde a ese primer intento (segundos antes).
- Los volcados NF2FF brutos se borraron tras guardar sus hashes en [`nf2ff_raw_dumps.sha256`](../em/US3_MS4_OPENEMS_029/nf2ff_raw_dumps.sha256). `solver.log` está en `.gitignore`.

## Resultados (malla base)
| | US3_MS3 (023) | **US3_MS4 (029)** |
|---|---|---|
| Peor S11 en el canal | −8,18 dB | **−1,37 dB** (8,2368 GHz) |
| Mejor S11 en el canal | −16,39 dB | −1,55 dB |
| Pico de Re(Zin) del modo del parche | 70 Ω en 7,92 GHz | **129 Ω en 6,83 GHz** |
| Mínimo de S11 cerca del modo del parche | −16,4 dB en 7,98 GHz | −7,8 dB en 6,74 GHz |
| Segundo pico de Re(Zin) en 5,5–10,5 GHz | ninguno (S11 −9,0 dB en 10,5 GHz, subiendo) | 61 Ω en 10,30 GHz; S11 −13,0 dB en 10,52 GHz (borde del rango) |
| Eficiencia de radiación en el canal | 0,65–0,67 (024, fina) | 0,27–0,28 |
| Ganancia realizada en broadside | 3,2–4,0 dBi | −8,5 a −11,9 dBi |

En el canal la antena está fuera de resonancia: no cumple −6 dB y el campo lejano del canal no tiene interés de diseño.

## Hipótesis
- **H1:** **cumplida solo formalmente, sin atribución de modo** (máximo de Re(Zin) de 61 Ω en 10,30 GHz, con X = +39 Ω; X no cruza cero entre 8,1 y 10,52 GHz). El pico ya se intuía en 023 justo por encima de 10,52 GHz (Re(Zin) 56 Ω en el borde) y solo ha bajado 0,2–0,3 GHz, frente a los ~2,9 GHz del modelo guía. Está además en el borde de validez de la excitación (u_inc −19,8 dB frente al límite de −20 dB). **No está identificado:** puede ser un modo de orden superior del parche (por ejemplo con variación en x) o de la U; harían falta volcados de campo para atribuirlo.
- **H2:** **no evaluable**: la banda de −10 dB (10,34–10,52 GHz, ≥180 MHz) está truncada por el borde del rango. Con H1 formal y H2 indeterminado, el árbol de decisión pre-registrado no aplica limpiamente. En cualquier caso no hay banda útil cerca del canal.
- **Escalado guía:** **no verificado** (no se puede decir que "falle por el modo de la U" sin identificar ese modo). Lo que sí muestra el run: ensanchar la U baja el **modo del parche** unos −1,1 GHz (de 7,92 a 6,83 GHz, malla base sin convergencia; la magnitud exacta no está acotada) y el pico alto apenas se mueve.

## Decisión
- La regla pre-registrada no aplica limpiamente (H2 indeterminado). **No recomiendo seguir con Lu o y0**: esta variante empeora el canal, ensanchar la U actúa sobre todo como un alargamiento efectivo del parche, y no hay evidencia de que acerque una segunda resonancia al canal.
- **Recomendación:** cerrar la vía de ancho de banda con U-slot en microstrip sobre FR4 de 2,07 mm, y priorizar **P01_MS2** (−10 dB en todo el canal en openEMS, pendiente de HFSS). Si el propietario quiere insistir con la U, la siguiente prueba con más información sería un barrido corto en HFSS de `u_Wu` (4,4–5,6 mm, paso 0,2) con `patch_L` compensado, mirando si aparece un lazo en la carta de Smith.
- US3_MS4 queda como **experimento negativo**, no como candidato.

## Reservas
1. **El pico de 10,3 GHz no está identificado** como modo de la U (ya existía en 023 por encima de 10,52 GHz y se ha movido poco).
2. **H1 solo formal**; el pico está a 0,2 GHz del límite de la hipótesis y en el borde de validez de la excitación.
3. **H2 no evaluable** (banda truncada por el borde del rango).
4. **Malla no idéntica a 023**: mismo perfil, pero 3 celdas en la ranura (antes 4) y gradación 1,41 con límite 1,5. Sin malla fina: el −1,1 GHz y la posición de los picos son de una sola malla.
5. **η_rad 0,27–0,28 y ganancia realizada −8,5 a −11,9 dBi** describen una antena desadaptada fuera de resonancia (pérdida por desadaptación 5,2–5,7 dB); no son una propiedad intrínseca de la U ancha ni un argumento contra ella.
6. **Pendiente del barrido HFSS** (−7 MHz por 0,01 mm) válida como orden de magnitud: el residuo (rms 9, máx. 18 MHz) es comparable a un paso.
7. **Energía final −50,08 dB**, justo por debajo del criterio de −50 dB, con un pico de Q alto en 6,83 GHz.
8. **Evidencia**: `solver.log` ignorado por `*.log`; energía y tiempos están en `openEMS_run_stats.txt` y `run_numeric.json` (versionados). Volcados NF2FF brutos borrados, solo hashes.
9. **La recomendación de parar** se apoya en que esta variante empeora el canal y en la adaptación ya lograda con P01_MS2, no en una atribución de modos.
10. FR4 provisional, sin conector (puerto concentrado en el borde), metal como lámina ideal.

## Estado
- Ronda 29/40. La campaña sigue en **READY_FOR_HFSS_REVIEW** con P01_MS2 como candidato.

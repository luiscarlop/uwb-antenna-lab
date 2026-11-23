# HFSS del array 1×5 de US3_PS4_2_1 con convergencia ΔS 0,01 (2026-11-21)

- **Fuente:** exportación del propietario (Drive, 21-11) con nuestros scripts, en `hfss/results/results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/`. Diseño `ARR1x5_US3_PS4_2_1_dparam`, `arr_d` paramétrico.
  - 15 pasos (13,5–20,5 mm cada 0,5 mm, más 18,2 mm), cada uno con su `.s5p` y su `convergence.conv`.
  - El paso de 20 mm no se resolvió en HFSS. Los logs solo dicen «no está resuelto», sin la causa.
  - Campos lejanos `ff_P1..P5.csv` en 5 frecuencias (7,7376 / 7,8624 / 7,9872 / 8,112 / 8,2368 GHz) a 13,5, 17, 18,2 y 20,5 mm.
  - `export_log.txt` y `export_fields_log.txt` son acumulativos: para este array solo valen las dos últimas tandas de cada log.
- **Datos anteriores:** el barrido del 20-11 (8 pasos de 16,5 a 19,5 mm, sin convergencia: 15 de 15 pasadas, ΔS 0,012–0,021), los zips y sus análisis están en `legacy_2026-11-20/`.
- **Geometría:** la variación coincide con `variants/US3_PS4_2_1.json` y con el barrido anterior. Material FR4 εr 4,4, tanδ 0,017, h 2,07 mm, cobre 35 µm; puerto lumped de 50 Ω por elemento; puertos apagados a 50 Ω.

## Convergencia
- **Criterio:** ΔS 0,01 en 2 pasadas consecutivas, máximo 25. Los 15 pasos convergen en 17–23 pasadas, con ΔS final 0,0039–0,0095 y 128 000–409 000 tetraedros.
- **Continuación, no re-simulación independiente:** en los 8 pasos del barrido anterior, las pasadas 1–15 son idénticas (mismos tetraedros y ΔS). HFSS continuó el refinamiento adaptativo a partir del límite anterior de 15 pasadas.
- **Las S cambian más que el ΔS residual:** de la solución anterior a la nueva, |ΔS| máx 0,05–0,08 por paso, mientras su ΔS residual era 0,012–0,021. El ΔS es un criterio de parada, no una cota del error.
- **18,2 mm está menos refinado que sus vecinos:** 17 pasadas y 150 000 tetraedros, frente a 316 000–409 000 en 16,5–19,5 mm. Su `.conv` declara Target 0,02, pero las dos últimas pasadas (0,0078 y 0,0087) cumplen 0,01 y el solver no paró al cruzar 0,02, así que el criterio efectivo fue 0,01. Su peor Sii (−10,49 dB) queda unos 0,4 dB por encima de la tendencia de 18 y 18,5 mm (−10,88 y −10,92 dB).

## Resultados a 18,2 mm (canal 7,738–8,236 GHz; campos a 7,9872 GHz)

| | Anterior (sin converger) | **Convergido** |
|---|---|---|
| Peor Sii | −10,30 dB | **−10,49 dB** |
| Acoplamiento vecino (peor) | −18,27 dB | **−18,25 dB** |
| Activo 0°: peor puerto / TARC | −10,0 dB | **−10,25 / −10,50 dB** (los 5 ≤ −10 dB) |
| Activo 15° / 30° / 45°: peor puerto | | −10,41 / −9,12 / −9,32 dB |
| HPBW xz físico | 20,8° | **20,7°** |
| HPBW virtual (a) 1 TX + 2 RX | 16,5° | **16,4°** |
| HPBW virtual (b) con monostáticos | 12,0° | **11,9°** |
| A 30°: (a) / (b), lóbulo (b) | 18,8° / 13,8°, −8,2 dB | 18,75° / 13,76°, −8,2 dB (cuasi-lóbulo 2d a −32°) |
| Pico físico | 11,04 dBi | 11,05 dBi |

- **η radiada sobre aceptada por puerto:** 0,71–0,74 a 7,7376 GHz, 0,65–0,67 a f0, **0,37–0,38 a 8,112 GHz** (mínimo en banda) y 0,48–0,49 a 8,2368 GHz. Es el valle de la familia PS4: en el elemento aislado, 0,32 a 8,137 GHz.
- **τ_g físico en broadside (5 frecuencias):** 337 / 350 / 330 / 33 / −232 ps. Con 5 puntos a 124,8 MHz es orientativo; el salto coincide con el valle de η, aunque la atribución no está demostrada con tan pocas frecuencias.

## Otros pasos

| Paso | Peor Sii | Vecino | Activo 0° (peor) | HPBW físico / (a) / (b) a f0 |
|---|---|---|---|---|
| 13,5 mm | −9,26 dB | −11,32 dB | −7,32 dB | 26,8 / 22,4 / 15,2° |
| 17 mm | −10,46 dB | −16,32 dB | −9,86 dB | 21,6 / 17,4 / 12,6° |
| 20,5 mm | −10,85 dB | −22,85 dB | −10,48 dB | 18,5 / 14,8 / 10,9° |

La mejora del peor Sii frente al barrido anterior es de 0,19 a 0,72 dB entre 16,5 y 19,5 mm.

## Lectura
- **La convergencia mejora la adaptación del array, pero no los haces.** El peor Sii mejora entre 0,2 y 0,7 dB, y los anchos de haz cambian menos de 0,1°: los fija la apertura.
- **«Todos los puertos ≤ −10 dB a 0°» no es robusto.** El margen es de 0,25 dB, y el paso de 18,2 mm está menos refinado (unos 0,4 dB por encima de la tendencia de sus vecinos). Se cita como «≈ −10 dB a 0°, ±0,4 dB de malla». A 30° y 45° no se cumple; −6 dB se cumple en todos los ángulos.
- **El punto débil sigue siendo la eficiencia en la mitad alta del canal** (0,37 a 8,112 GHz), como en el elemento aislado.
- **El paso de 20 mm** no afecta a ninguna cifra de los cuatro pasos analizados. Solo deja un hueco de 1 mm en el barrido.

## Estado de evidencia
- **S, campos y parámetros de array:** `EM_SIMULATED`. HFSS convergido con ΔS 0,01, puerto lumped sin wave port, FR4 provisional, versión de resolución no confirmada.
- **Haces virtuales (a) y (b):** `GUIDE_MODEL` sobre campos `EM_SIMULATED`.
- Falta el registro de CPU, RAM y tiempo (no hay profile del array).

## Auditoría
`validator` (2026-11-21): **OK con observaciones**.
- **Comprobaciones:**
  - Mapeo de los 15 pasos y de las 20 ff, y geometría frente a la variante.
  - Asignación P1..P5 verificada por el centro de fase: −36,6 / −18,5 / 0,0 / +18,6 / +36,8 mm a 18,2 mm.
  - JSON regenerados idénticos byte a byte, y cifras recalculadas con código propio. Pasan 224 tests.
- **Reservas:**
  1. 18,2 mm menos refinado que sus vecinos (alta).
  2. Continuación de la malla anterior; ΔS no acota el error (media).
  3. `artifacts/summary/build.py` pedía 16p5 (media; corregido).
  4. Documentación desactualizada (media; actualizada aquí, en `campaign_state.json` y en `hfss/results/README.md`).
  5. Causa del fallo de 20 mm desconocida (media-baja).
  6. El mínimo de η en banda (0,37 a 8,112 GHz) no aparece en el análisis de 3 frecuencias (media-baja).
  7. Logs acumulativos (baja).
  8. Etiqueta Target 0,02 a 18,2 mm (baja).
  9. Caso (b) con monostáticos: modelo guía con hardware TX/RX en el mismo elemento (baja).
- **Siguiente paso opcional:** 2–4 pasadas más a 18,2 mm (ΔS ≤ 0,005) para cerrar la reserva 1.

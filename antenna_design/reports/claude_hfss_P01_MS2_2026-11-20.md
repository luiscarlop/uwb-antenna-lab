# HFSS de P01_MS2: elemento y array 1×4 (2026-11-20)

- **Fuente:** resimulación y exportación del propietario con los scripts actuales (HFSS 2025.1.0, Drive), en `hfss/results/results_P01_MS2/P01_MS2/` y `hfss/results/results_P01_MS2/ARR1x4_P01_MS2_dparam/`.
- **Geometría:** la de `variants/P01_MS2.json` (parche 11,421 × 7,322 mm, transformador 0,8 × 7,1 mm, línea de 50 Ω de 3,92 mm; FR4 εr 4,4, tanδ 0,017, h 2,07 mm; cobre 58 MS/m, 35 µm). Puerto lumped de 50 Ω en el borde.
- **Criterio de convergencia (más laxo que el de US3_PS6_4):** ΔS ≤ 0,02 con 1 pasada consecutiva.
  - Elemento: 10 pasadas (máx. 15), ΔS final 0,0156, 15 964 tetraedros. 4 núcleos, 907 MB por proceso, 1 min 4 s.
  - Array 1×4: 16 pasos (13,5–20,5 mm cada 0,5 y 18,2 mm), máx. 25 pasadas, ΔS final 0,0111–0,0196, 39–52 k tetraedros. Sin `profile.prof` ni logs del array.
  - Con ΔS 0,0156, en el borde (|S11| ≈ 0,32) la incertidumbre es unos ±0,4 dB (±20 MHz en el cruce de −10 dB). Diferencias de S11 menores de ~0,4 dB no son resolubles.

## Elemento

| | openEMS base / fina | **HFSS** |
|---|---|---|
| Peor S11 en el canal | −10,42 / −10,36 dB (borde inferior) | **−9,81 dB** (borde superior, 8,236 GHz) |
| Canal ≤ −10 dB | 100 % | 98,2 % (100 % ≤ −6 dB) |
| Mínimo | 7,991 GHz | 7,937 GHz (−22,0 dB) |
| Región ≤ −10 dB | 7,724–8,306 GHz | 7,699–8,227 GHz (528 MHz) |
| η_rad | 0,73–0,76 | 0,813 / 0,839 / 0,853 (3 frecuencias) |
| Ganancia realizada broadside | 4,3–4,8 dBi | 4,92 / 5,21 / 4,66 dBi (pico 5,14 / 5,39 / 4,81, inclinado ≈ 10° hacia −y) |
| τ_g broadside | rizado 47 ps (11 puntos) | pendiente de −43 ps a lo largo del canal (solo 3 puntos: no es un rizado) |

- HFSS desplaza la resonancia −54 MHz respecto a openEMS (≈ −0,7 %), como en US3_PS6 y US3_PS6_4. openEMS fino cubre el canal a −10 dB y HFSS se queda a 0,2 dB, dentro de la incertidumbre: no se confirman mutuamente.
- η y ganancia salen +0,08…+0,10 y +0,4…+0,6 dB mayores en HFSS con la misma directividad (≈ 6,0 dBi). La causa no está identificada (modelo de pérdidas dieléctricas, método de cálculo de potencia radiada, contornos). Se reportan ambos sin promediar.
- Las diferencias de S11, η y ganancia frente a US3_PS6_4 (criterio 0,01 / 2 pasadas) no deben ordenarse si son menores que la incertidumbre de convergencia.

## Array 1×4 y comparación con 1×5

| Paso (mm) | Sii | Acoplo vecino | Activa 0° | Activa 30° | Activa 45° |
|---|---|---|---|---|---|
| 13,5 | −9,18 | −9,87 | −6,14 | −7,87 | −6,88 |
| 18,2 | −10,18 | −16,74 | −10,04 | −8,85 | −7,80 |
| 20,5 | −10,80 | −20,35 | −11,04 | −9,16 | −7,80 |

A 18,2 mm y f0 (xz): HPBW físico 25,7°, virtual 1 TX + 2 RX 22,5° (lóbulo −23,2 dB; 12 adquisiciones, 24 canales, 5 posiciones), con monostáticos 15,2° (−21,5 dB; 7 posiciones).

| HPBW virtual a f0 | 1×4 | 1×5 | Razón |
|---|---|---|---|
| P01_MS2, 17 mm, bistático | 24,4° | 17,7° | 0,73 |
| P01_MS2, 17 mm, con monostáticos | 16,3° | 12,6° | 0,77 |
| P01_MS2, 13,5 mm, bistático | 30,1° | 22,9° | 0,76 |
| 18,2 mm (1×4 P01_MS2 frente a 1×5 US3_PS6_4, elemento distinto) | 22,5° | 16,3° | 0,72 |

**El quinto elemento estrecha el haz virtual un 24–28 %** (razón 0,72–0,76), con el mismo elemento (P01_MS2, 17 mm) y entre elementos distintos (18,2 mm). El elemento apenas influye en el HPBW, que lo fija el factor de array. Comparador 1×5 de P01_MS2 a 17 mm: exportación anterior (HFSS 2024.2.0, sin `convergence.conv`).

## Estado de evidencia
- **Elemento, S11:** `EM_SIMULATED` (puerto lumped, criterio ΔS 0,02 / 1 pasada).
- **Elemento, radiación (η y ganancia):** `HFSS_VALIDATED` con la reserva del puerto lumped y del criterio ΔS 0,02, como la radiación de US3_PS6_4. Decisión del propietario (2026-11-21). Campo lejano en 3 frecuencias; FR4 provisional.
- **Array 1×4:** `EM_SIMULATED`. Haces virtuales y con monostáticos: modelo guía.

## Auditoría
`validator` (2026-11-20): **OK con observaciones**. Reproduce geometría, convergencia, S11, η, ganancia (recalculada desde el campo lejano), barrido, haces y secuencias (N = 4 y N = 5). Reservas incorporadas arriba; además, textos de evidencia obsoletos en `array_hfss_analysis.py` («adaptive convergence data not provided») y en el docstring de `element_hfss_patterns.py` («11 points», «HFSS_VALIDATED if converged»), pendientes de corregir; y se recomienda pedir al propietario el campo lejano del elemento en 11 frecuencias para tener un rizado de τ_g comparable.

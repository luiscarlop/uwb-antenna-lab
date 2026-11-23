# HFSS del array 1×5 de P01_MS2, re-exportado con convergencia (2026-11-21)

- **Fuente:** exportación del propietario con nuestros scripts (Drive, 20-11), en `hfss/results/results_P01_MS2/ARR1x5_P01_MS2_dparam/`. Diseño `ARR1x5_P01_MS2_dparam`, `arr_d` paramétrico.
  - 16 pasos (13,5–20,5 mm cada 0,5 mm, más 18,2 mm), cada uno con su `.s5p` y su `convergence.conv`.
  - Campos lejanos `ff_P1..P5.csv` (3 frecuencias, rejilla de 5°) a 13,5, 17, 18,2 y 20,5 mm.
- **Datos anteriores:** los del 15-11 (sin `.conv`), el run manual de 17 mm (HFSS 2024.2.0) y sus análisis están en `legacy_2026-11-15/`. Los `.s5p` y campos por paso del 15-11 quedan en el historial de git (commit `5ef1507^`).
- **Elemento y material:** P01_MS2, FR4 εr 4,4, tanδ 0,017, h 2,07 mm, cobre 35 µm. Puerto lumped de 50 Ω por elemento, sin wave port. Puertos apagados a 50 Ω.
- **Análisis:** `array_pitch_sweep_hfss.py`, `array_hfss_analysis.py`, `array_virtual_3d.py` y `array_virtual_monostatic.py`.

## Procedencia: es la misma solución, no una re-simulación
El validator comparó los 16 `.s5p` nuevos con los del 15-11. Difieren como máximo 3e-13 en módulo, y los campos de 13,5 mm unos 1e-14 en relativo. El `.s5p` manual de 17 mm (HFSS 2024.2.0) difiere 1,8e-13.
- Se ha re-exportado la solución almacenada en el proyecto. «HFSS 2025.1.0» es la versión del exportador, y la versión con la que se resolvió sigue sin confirmar.
- Lo que aporta la re-exportación es el registro de convergencia del mismo solve.
- No es una reproducción independiente.

## Convergencia
- **Criterio:** ΔS máx 0,02 con 1 pasada consecutiva, máximo 15 pasadas, adaptación a 7,9872 GHz. Los 16 pasos convergen en 10–12 pasadas, con ΔS final entre 0,0114 y 0,0197 y entre 30 641 y 68 075 tetraedros.
  - A 18,2 mm: 12 pasadas, ΔS 0,0180, 51 057 tetraedros.
  - En todos los pasos, la pasada anterior estaba en ΔS ≥ 0,02: paran en cuanto cruzan el umbral.
- **Comparación:**
  - El 1×4 de P01_MS2 usa el mismo criterio, con 11–12 pasadas.
  - El 1×5 de US3_PS6_4 usa ΔS 0,01 con 2 pasadas consecutivas: 14–17 pasadas y unas 3 veces más tetraedros. Su `d18p2mm/convergence.conv` declara Target 0,02, aunque el valor final (0,0095) cumple 0,01.
- **Incertidumbre:** ΔS 0,02 equivale a unos ±0,5 dB cuando |S| ≈ 0,31 (−10 dB). Sii frente al paso oscila ±0,2–0,3 dB entre pasos vecinos (18,5 → 19 → 19,5 mm: −10,47 / −10,30 / −10,85 dB), coherente con ruido de malla.
- ΔS solo se controla a f0; los bordes del canal salen del barrido interpolante.

## Resultados a 18,2 mm (canal 7,738–8,236 GHz; campos a 7,9872 GHz)

| | 1×4 P01_MS2 | **1×5 P01_MS2** | 1×5 US3_PS6 | 1×5 US3_PS6_4 |
|---|---|---|---|---|
| Peor Sii | −10,18 dB | **−10,25 dB** | −8,64 | −10,73 |
| Acoplamiento vecino (peor) | −16,74 dB | **−16,90 dB** | −18,25 | −16,28 |
| No vecino (peor) | −27,09 dB | **−27,27 dB** | | |
| ECC por S (máx) | 0,0094 | **0,0099** | | |
| Activo 0°: peor puerto / TARC | −10,04 dB / — | **−9,27 / −10,16 dB** | −9,62 | −9,23 |
| HPBW xz físico | 25,7° | **20,6°** | 20,6° | 20,5° |
| HPBW virtual (a), 1 TX + 2 RX | 22,5° (12 adq.) | **16,4° (30 adq., 7 posiciones)** | 16,4° | 16,3° |
| HPBW virtual (b), con monostáticos | 15,2° (7 posiciones) | **11,9° (20 adq., 9 posiciones)** | 11,9° | 11,8° |
| Lóbulo lateral máx. (b) a 0° / a 30° | −21,5 / −9,5 dB | **−21,8 / −8,1 dB** | | |
| Pico físico | 10,9 dBi | **11,79 dBi** (θ 10°, φ 270°; 11,67 dBi en broadside) | | |

- **Activo con haz a 15 / 30 / 45°:** peor puerto −9,80 / −8,05 / −8,26 dB y TARC −10,56 / −10,71 / −9,06 dB. Todos los puertos ≤ −6 dB a todos los ángulos, pero ninguno de los ángulos con todos ≤ −10 dB.
- **η radiada sobre aceptada por puerto:** 0,82–0,85 a f0 (0,78–0,81 a 7,7376 GHz y 0,86–0,88 a 8,2368 GHz). Es un control de orden de magnitud.
- **τ_g físico en broadside:** 238,9 / 222,7 / 206,6 ps en las 3 frecuencias. Es una pendiente de unos −65 ps/GHz, no un rizado: con 3 puntos no se puede medir el rizado.

## Otros pasos (a f0)

| Paso | HPBW físico 1×4 / 1×5 | Virtual (a) 1×4 / 1×5 | (b) 1×4 / 1×5 | Peor Sii 1×5 | Vecino 1×5 |
|---|---|---|---|---|---|
| 13,5 mm | 33,6 / 27,5° | 30,1 / 22,9° | 20,5 / 15,7° | −9,57 dB | −10,28 dB |
| 17 mm | 27,8 / 21,7° | 24,4 / 17,7° | 16,3 / 12,6° | −10,00 dB | −15,03 dB |
| 20,5 mm | 22,9 / 18,4° | 20,2 / 14,6° | 13,6 / 10,9° | −10,70 dB | −20,63 dB |

A 20,5 mm aparece el cuasi-lóbulo de rejilla del caso (b): −18,0 dB en el 1×5 y −20,7 dB en el 1×4, a ±62,6°.

## Lectura
- **El quinto elemento estrecha el haz virtual un 27 % en (a) y un 22 % en (b)** (cocientes 1×5/1×4 de 0,73 y 0,78; 0,80 en el físico). La adaptación y el acoplamiento no cambian. Es la primera comparación 1×4 frente a 1×5 con el mismo elemento, sustrato, alimentación y criterio de convergencia.
- **A paso fijo, el haz lo fija la apertura, no el elemento.** Los tres 1×5 a 18,2 mm (P01_MS2, US3_PS6 y US3_PS6_4) dan el mismo HPBW con ±0,1° de diferencia. El elemento decide la adaptación, el acoplamiento y la eficiencia.
- **Adaptación:** el peor Sii (−10,25 dB) cumple −10 dB con un margen (0,25 dB) menor que la incertidumbre de ΔS 0,02. Con todos los puertos activos, el peor puerto baja a −9,27 dB a 0° y a −8,05 dB a 30°. Lo firme es −6 dB; «−10 dB en el canal» no debe darse como resultado.
- **Caso (b):** el haz de 11,9° sale del modelo guía (posiciones ±4d, monostáticos con multiplicidad 4, sin fuga TX→RX ni S_tt). No es un superconjunto del caso (a), porque tiene 20 adquisiciones frente a 30, y no debe venderse como una ganancia real de resolución sin el modelo de fuga. A 30° su lóbulo lateral sube a −8,1 dB.

## Estado de evidencia
- S, campos y parámetros de array: `EM_SIMULATED`.
  - HFSS con convergencia adaptativa exportada (ΔS 0,02, 1 pasada), puerto lumped sin wave port, FR4 provisional, versión de resolución no confirmada.
  - No es `HFSS_VALIDATED`.
- Haces virtuales (a) y (b): `GUIDE_MODEL` sobre campos `EM_SIMULATED`.
- Los textos de evidencia de `array_hfss_analysis.py` y `array_pitch_sweep_hfss.py` se han corregido para leer el `convergence.conv`.

## Auditoría
`validator` (2026-11-21): **OK con observaciones**.
- **Comprobaciones:**
  - Ha comprobado el mapeo de los 52 ficheros (cabecera, DesignVariation y columna arr_d).
  - Ha verificado P1..P5 de forma independiente por el centro de fase de cada puerto: −36,69 / −18,84 / −0,08 / +18,78 / +36,89 mm frente a ±36,4 / ±18,2 / 0. La simetría P1↔P5 y P2↔P4 cuadra.
  - Ha reproducido todas las cifras a 18,2 mm con código propio y con los scripts del repo. Pasan 223 tests.
- **Reservas:**
  1. Procedencia: es una re-exportación y no una re-simulación (media).
  2. Margen de convergencia frente a −10 dB (media).
  3. Textos de evidencia obsoletos (media; corregidos).
  4. Referencias desactualizadas a `manual_d17mm/` en `campaign_state.json`, `hfss/results/README.md`, `hfss/CLAUDE_PYAEDT.md` y en los informes del 15-11 y del 20-11 (media-baja; las cifras siguen valiendo).
  5. Faltan tests de carpeta de resultados para P01_MS2, US3_PS6 y US3_PS4_2_1 (baja).
  6. El artifact solo ofrece 13,5 y 17 mm para P01_MS2 (baja).
  7. Los `.s5p` del 15-11 solo quedan en git (baja).
  8. «Rizado τ_g» de 3 puntos (baja).
  9. Pico fuera de broadside (baja).
  10. El caso (b) es modelo guía (baja).
  11. La rejilla del canal es de 1 MHz (≤ 0,011 dB) (baja).

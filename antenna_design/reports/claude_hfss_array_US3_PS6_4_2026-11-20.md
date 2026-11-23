# HFSS del array 1×5 de US3_PS6_4 (2026-11-20)

- **Fuente:** exportación del propietario (HFSS 2025.1.0, Drive) en `hfss/results/results_US3_PS6_4/ARR1x5_US3_PS6_4_dparam/`: 11 matrices S y `convergence.conv` (`arr_d` 16, 16,5 … 20,5 mm y 18,2 mm; el paso de 16 mm lo añadió el propietario fuera de la rejilla pre-registrada); diagramas embebidos `ff_P1..P5` a 18,2 mm (3 frecuencias). Script `hfss/build/US3_PS6_4/claude_aedt_array1x5_US3_PS6_4_param_ch9.py`, revisado por `design-reviewer`.
- **Pre-registro:** `hfss/results/results_US3_PS6_4/preregistro_hfss.md`, sección R2 (anterior a los resultados).
- **Geometría:** la de `variants/US3_PS6_4.json` en los 11 pasos, con `board_x = 4·arr_d + 26`.
- **Convergencia:** los 11 pasos convergen (14–17 pasadas de 25, ΔS 0,0054–0,0095, dos pasadas consecutivas < 0,01). Convergencia justa en 5 pasos (ΔS 0,0087–0,0095). A 18,2 mm el `.conv` indica «Target 0,02», incoherente con el setup (0,01) y con la historia de pasadas, igual que en US3_PS6: el criterio efectivo fue 0,01. Ruido empírico entre pasos ≈ 0,05 dB (ajuste cúbico frente al paso; simetría S11/S55 ≤ 0,08 dB). Sin `profile.prof` ni logs: RAM, CPU y tiempo no registrados; versión de resolución no confirmada.

## Barrido del paso (peor en el canal)

| Paso (mm) | Sii | Acoplo vecino | Activa 0° | Activa 30° | Activa 45° |
|---|---|---|---|---|---|
| 16,0 | −11,66 | −12,64 | −8,34 | −8,37 | −8,91 |
| 18,2 | −10,73 | −16,28 | −9,23 | −8,63 | −8,60 |
| 19,5 | −11,11 | −18,72 | −10,69 | −9,10 | −8,25 |
| 20,5 | −11,12 | −20,93 | −11,27 | −9,20 | −8,98 |

El acoplo mejora de forma monótona (≈ 1,8 dB/mm). La reflexión activa en broadside solo baja de −10 dB en todos los puertos desde 19 mm (−10,13 dB) y con margen desde 19,5 mm; a 30° y 45° ningún paso llega a −10 dB (mejores −9,21 y −8,98 dB).

## Haces a 18,2 mm y f0 (xz)

| | Físico | Virtual 1 TX + 2 RX | Con monostáticos |
|---|---|---|---|
| Broadside | 20,5° (lóbulo −13,6 dB) | 16,3° (−24,4 dB) | 11,8° (−22,1 dB) |
| Apuntando a 30° | 23,2° (−11,3 dB) | 18,8° (−14,0 dB) | 13,8° (−8,2 dB, cuasi lóbulo de rejilla) |

Pico global en θ = 10°, φ = 270° (squint en elevación, como el elemento). Los haces son iguales a los de US3_PS6 y US3_PS4_2_1 al mismo paso (diferencias < 0,3°, por debajo de la rejilla angular de 5°): los fija la geometría del array, no el elemento.

## Comparación a 18,2 mm

| | US3_PS6_4 | US3_PS6 | US3_PS4_2_1 |
|---|---|---|---|
| Acoplo vecino | −16,28 dB | −18,25 dB | −18,27 dB |
| Sii peor | −10,73 dB | −8,64 dB | −10,3 dB |
| Activa 0° / 30° / 45° | −9,23 / −8,63 / −8,60 | −9,62 / −8,18 / −6,80 | −10,04 / −8,97 / −9,43 |
| η por puerto (f0) | 0,755–0,77 | 0,74–0,75 | 0,64–0,66 |
| Convergencia | 11/11 pasos | 3 de 16 documentados | no convergido |

US3_PS6_4 gana en Sii y eficiencia; en reflexión activa broadside es el peor de los tres. No es «mejor array» en conjunto.

## Contra el pre-registro (R2)
- **Acoplo vecino (≈ −13…−15 dB, refutación si mejor que −15 dB):** **refutado**, −16,28 dB. El acoplo depende sobre todo del paso (d/λ), no del hueco de cobre: al mismo paso solo empeora ≈ 2 dB frente a los parches estrechos.
- **Reflexión activa broadside (≈ −8 dB, −7,5…−9,5):** dentro del rango (−9,23 dB); no llega a −10 dB en todos los puertos (1, 3 y 5 por encima).

## Lectura
- **Sii del array mejor que el elemento aislado** (−10,73 frente a −9,82 dB): no es ruido de malla (≈ 0,05 dB) ni acoplo mutuo (efecto de segundo orden ≈ 0,2 dB; a 20,5 mm el acoplo es −20,9 dB y el Sii sigue en −11,1 dB). La curva se desplaza +21…+39 MHz y la región ≤ −10 dB llega a 8,33–8,38 GHz. Hipótesis sin contraste: efecto de la placa mayor (98,8 × 26 mm frente a 26 × 26 mm). Se cita el −9,82 dB del elemento como referencia conservadora; un control con un elemento en placa de 98,8 × 26 mm lo resolvería (opcional).
- **El barrido no elige 18,2 mm:** es λ/2 en el borde superior del canal (criterio de diseño). Si se quisiera ≤ −10 dB en broadside, apunta a 19–19,5 mm (d/λ ≈ 0,54 en el borde superior). Sin campos a otros pasos, el efecto sobre el haz no está medido.
- **Retardo de grupo del array:** con 3 frecuencias no es comparable con el rizado del elemento (11 puntos) y el valor absoluto incluye la línea de alimentación; no se cita como rizado.

## Estado de evidencia
`EM_SIMULATED` (HFSS convergido, puerto lumped, sin wave port). No se arrastra al array el `HFSS_VALIDATED` de la radiación del elemento. Haces virtuales y con monostáticos: modelo guía.

## Auditoría
`validator` (2026-11-20): **OK con observaciones**. Reproduce todas las cifras desde `.s5p`, `.conv` y `ff`; geometría y `arr_d` correctos; pasivo y recíproco. Reservas incorporadas arriba; además, un test que exigía la carpeta vacía fallaba tras subir los datos (corregido en este commit) y `array_analysis_d18p2mm.json` conserva el texto fijo «adaptive convergence data not provided» de `array_hfss_analysis.py` (pendiente de corregir en el script).

# HFSS del array 1×5 de US3_PS6 (2026-11-20)

- **Fuente:** exportación del propietario (HFSS 2025.1.0, Drive) en `hfss/results/results_US3_PS6/ARR1x5_US3_PS6_dparam/`: 16 matrices S (`arr_d` 13,5–20,5 mm cada 0,5 mm más 18,2 mm); diagramas embebidos `ff_P1..P5` a 18,2 mm (3 frecuencias); `convergence.conv` a 13,5, 18,2 y 20,5 mm. Script `hfss/build/US3_PS6/claude_aedt_array1x5_US3_PS6_param_ch9.py`, revisado por `design-reviewer`.
- **Geometría:** la de `variants/US3_PS6.json` (parche 11,421 × 6,29 mm, parásito 11 × 7,05 mm, transformador 0,8 × 6,6 mm) con `board_x = 4·arr_d + 26` y puertos lumped de 50 Ω.
- **Convergencia:** 15 pasadas, ΔS 0,0051 (13,5 mm), 0,0092 (18,2 mm) y 0,0065 (20,5 mm), dos pasadas consecutivas. Los `.conv` indican «Maximum: 25» (el script fija 15: el propietario amplió el máximo en AEDT) y, a 18,2 mm, «Target 0,02», incoherente con el setup de 0,01 y con la historia de pasadas; con 0,01 también converge. Sin logs de convergencia en los otros 13 pasos ni `profile.prof` (RAM, CPU y tiempo no registrados).
- **Análisis:** `array_pitch_sweep_hfss.json`, `array_analysis_d18p2mm.json`, `virtual_3d/array_virtual_3d_d18p2.json` y `virtual_mono/array_virtual_monostatic_d18p2.json`, con los scripts de `hfss/analysis/`.

## Barrido del paso (peor en el canal, rejilla de 1 MHz)

| Paso (mm) | Sii (dB) | Acoplo vecino (dB) | Activa 0° | Activa 30° | Activa 45° |
|---|---|---|---|---|---|
| 13,5 | −8,48 | −10,91 | −7,21 | −7,17 | −6,65 |
| 16,5 | −8,54 | −15,37 | −8,98 | −7,63 | −6,87 |
| 18,2 | −8,64 | −18,25 | −9,62 | −8,18 | −6,80 |
| 20,5 | −9,19 | −22,29 | −10,31 | −8,33 | −6,75 |

Acoplo y reflexión activa a 0° y 30° mejoran de forma monótona con el paso; a 45° la activa queda entre −6,4 y −7,4 dB en todo el barrido. Diferencias menores de 0,3 dB entre pasos vecinos están dentro del ruido de malla (cada paso se malla por separado). El peor Sii del array (−8,64 dB a 18,2 mm) es coherente con el elemento aislado (−8,72 dB).

## Haces a 18,2 mm y f0 (xz)

| | Físico | Virtual 1 TX + 2 RX | Virtual TX/RX + RX (con monostáticos) |
|---|---|---|---|
| HPBW broadside | 20,6° | 16,4° (lóbulo −24,4 dB) | 11,9° (lóbulo −22,1 dB) |
| HPBW a 30° | 23,2° | 18,8° (−13,9 dB) | 13,8° (−8,1 dB, cuasi lóbulo de rejilla por la periodicidad 2d de los pesos) |

El pico del haz está inclinado unos 10° en el plano yz (θ ≈ 10°, φ = 270°), como el elemento aislado. Los haces son prácticamente iguales a los de US3_PS4_2_1 al mismo paso (16,5° y 12,0°): los fija la geometría del array, no el elemento.

## Lectura
- **18,2 mm (λ/2 en el borde superior del canal)** es un compromiso coherente: sin lóbulos de rejilla, acoplo vecino ≈ −18 dB. No es óptimo en ninguna métrica y no se distingue de los pasos 17,5–19 mm dentro del ruido de malla.
- **US3_PS6 tiene la peor adaptación de los tres arrays** a 18,2 mm: Sii −8,64 dB frente a −10,3 dB (US3_PS4_2_1, sin convergencia completa) y −10,25 dB (P01_MS2, sin datos de convergencia). Cumple −6 dB en toda la banda y en todos los apuntados (0–45°), no −10 dB.
- **Los pares monostáticos** estrechan el haz de 16,4° a 11,9° a cambio de subir el lóbulo lateral a −8,1 dB al apuntar a 30°.

## Estado de evidencia
- Sii, acoplos, reflexión activa y TARC: `EM_SIMULATED` (puerto lumped, sin contraste con wave port; convergencia documentada solo en 3 de 16 pasos).
- Patrones embebidos y haz físico a 18,2 mm: convergidos, con la reserva del puerto lumped.
- Haces virtuales y con monostáticos: `GUIDE_MODEL` sobre campos de HFSS (pesos uniformes, sin fuga TX→RX, rejilla angular de 5°: ±0,5–1° en el HPBW).

## Auditoría
`validator` (2026-11-20): **OK con observaciones**. Reproduce el barrido en los 16 pasos, los haces y la geometría; 223 tests OK. Reservas: cifra con monostáticos a 30° citada con los valores de 8,2368 GHz en lugar de f0 (corregida aquí: 13,8° y −8,1 dB); Target 0,02 incoherente a 18,2 mm; setup resuelto con 25 pasadas máximas no documentado en el script; convergencia solo en 3 de 16 pasos; metadatos erróneos en `array_pitch_sweep_hfss.json` (corregido el nombre del diseño en el script y regenerado); faltan logs de exportación y perfil; redacción sobre el paso; margen de adaptación estrecho; comparación con criterios de convergencia distintos entre diseños; modelo guía y resolución angular de 5°; el retardo de grupo del array incluye la línea de alimentación.

# Ronda Claude 034: US3_PS3, refinamiento 1 del apilado invertido

- **ID del experimento:** US3_PS3_OPENEMS_034.
- **Fecha:** 2026-11-15, ronda 34/40.
- **Orquestador:** `claude-opus-5-5`. La variante la diseñó `rf-designer`.
- **FDTD:** 1, con malla base y `--max-timesteps 60000`.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.
- **Veredicto de `validator`:** **OK con observaciones**.

## Cambio (excepción documentada: dos cambios a la vez)
[`variants/US3_PS3.json`](../variants/US3_PS3.json) parte de US3_PS2.
- **Acoplo:** la capa excitada sube de z_d = 1,29375 a **1,5525 mm**, con lo que el hueco hasta el parásito queda en 0,5175 mm.
- **Transformador:** pasa de 0,5 × 5,7 a **0,5 × 7,8 mm** (≈ 96,6 Ω).
- **Línea de 50 Ω enterrada:** 2,10 → 2,60 mm, como consecuencia de z_d.

El diagnóstico de 033 (GUIDE_MODEL del `rf-designer`) separaba dos modos:
- el de 8,06 GHz, «brillante», dominado por el parásito, que radia bien pero llegaba poco al puerto;
- el de 7,07 GHz, confinado, con Q ≈ Qd.

**Hints de malla:** después de esta ronda, para que pase la malla fina, se cambiaron solo los `mesh_hint_lines_mm` (se quita x ±1,8 y se añade y −2,95). La ronda 034 usó los hints anteriores. La comparación limpia de malla es 035 (base) frente a 036 (fina).

## Resultados (malla base, hints anteriores)
- Converge a −51,5 dB en 18 810 pasos, en 390 s y 0,49 GB.

| | US3_PS3 (034) | US3_MS3 (023) | P01_MS2 (027) |
|---|---|---|---|
| Peor S11 en el canal | **−7,59 dB** | −8,18 dB | −10,42 dB |
| Mejor / medio en el canal | −12,7 / −10,8 dB | −16,4 / −12,4 dB | −22,3 / −16,3 dB |
| Banda de −10 dB | 335 MHz (7,837–8,172 GHz) | 375 MHz | 582 MHz |
| Muestras del canal ≤ −10 dB | 67 % | 75 % | 100 % |
| η | **0,654–0,746** | 0,648–0,673 | 0,728–0,761 |
| Ganancia realizada broadside | 3,6–4,8 dBi | 3,2–4,0 dBi | 4,3–4,8 dBi |
| Rizado pico a pico de τg broadside (diagnóstico) | 120 ps | 67 ps | 47 ps |
| Residuo de fase frente a lineal | 3,5° | 1,8° | 1,4° |

- **Modo confinado** en ≈ 7,005 GHz: Re(Zin) 102 Ω, S11 −9,3 dB, fuera del canal. Su η no está medida (el NF2FF solo cubre el canal). Su falda llega al borde inferior, donde están η 0,654 y el peor S11.
- Dmax 6,5–6,6 dBi en θ 10–15°, φ 270°.

## Hipótesis
- **H1 se cumple** (−7,59 ≤ −6 dB), con 1,6 dB de holgura, unos 60 MHz de deriva.
- **H2 se cumple** (η ≥ 0,654 en los 11 puntos; Dmax < 20°), con 0,054 de holgura en η.
- **H_mecanismo**, con la receta de des-incrustación del JSON:
  - (i) se cumple justo: Re Z_borde del modo brillante pasa de 30 a 40 Ω, ×1,33 frente al ×1,49 predicho;
  - (ii) es marginal: el modo brillante baja 75 MHz, con un límite de ±80;
  - (iii) se cumple: el modo confinado sigue fuera del canal, en 7,005 GHz.
- La adaptación se logra con la reactancia residual y una sección que ya no es λ/4, no por adaptación resistiva.

## Lectura
- US3_PS3 es un diseño de **adaptación aceptable** (−6 dB en el canal, η ≥ 0,65).
- **No es mejor que P01_MS2.** Es peor en adaptación, en ancho de −10 dB, en rizado de retardo de grupo y en dispersión de fase. Mejora a US3_MS3 solo en η y ganancia.
- Las tres capas de cobre, el parásito y la línea interna sin conector resuelto no han comprado ancho de banda.
- No se llama «buen diseño».

## Siguiente paso
- Regla (A): pareja de mallas 035 (base, hints nuevos) y 036 (fina).
- Después, la decisión del propietario sobre HFSS y Fable.
- Queda un refinamiento para este candidato.

## Reservas (validator)
1. η del modo confinado no medida.
2. Holgura pequeña frente a la malla fina.
3. 034 y 035 no comparten hints.
4. Muestreo de 1 MHz.
5. Umbrales de H1/H2 bajos.
6. Conector y transformador de 0,5 mm sensibles al grabado.
7. Todo es EM_SIMULATED con FR4 provisional.

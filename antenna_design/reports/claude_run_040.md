# Ronda Claude 040: US3_PS4_1, parásito más estrecho (petición del propietario)

- **ID del experimento:** US3_PS4_1_OPENEMS_040.
- **Fecha:** 2026-11-16, ronda 40/50.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «en US3_PS4 … solo quiero probar a mover la resonancia que está entre 7,5 y 8 un poco más arriba». `rf-designer` escribió la variante.
- **FDTD:** 1, malla base, `--max-timesteps 60000`, 2 hilos (afinidad 0,1). El primer lanzamiento falló al instante por no haber hecho `prepare` antes (sin coste de CPU; log guardado fuera del repositorio). Se preparó y se relanzó en la misma carpeta.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.

## Cambio
[`variants/US3_PS4_1.json`](../variants/US3_PS4_1.json), con US3_PS4 como base:
- Ancho del parásito enterrado Wp **11,0 → 7,0 mm** (x ±3,5 mm). Lp, y −2,98…4,48, z 1,035, parche, U-slot, alimentación, material y puerto sin cambios.
- Objetivo: reducir el acoplamiento parche-parásito, porque en PS4 la separación de los dos mínimos (≈ 332 MHz) ya estaba en el suelo que fija el acoplamiento.
- Malla: en y solo cambia una línea (hint −2,99 mm en lugar de −2,9843; 5,7 µm); z idéntica. En x la malla se regenera entera (46 líneas cambian frente a 036, hasta ±12,5 mm); los bordes del parásito quedan entre las líneas ±3,4167 y ±3,6667 (regla 1/3–2/3), no hay línea en ±3,5. Esto mezcla algo el efecto de Wp con el de la malla, aunque el cambio observado (146 MHz) es muy superior a la incertidumbre de malla citada (~13 MHz).
- Celdas: 2 311 680 (`total_cells` de `prepared.json`); el solver informa 2 367 505 celdas nodales (`nodal_cells`), no celdas de PML.
- `launcher.json` se escribió antes del primer intento (fallido por falta de `prepare`); el comando es el mismo del relanzamiento válido, que arrancó a las 08:03:45 UTC (`run_started.json`) y no tiene registro de lanzador propio.

## Resultados (malla base)
- **Ejecución:** converge a −50,97 dB en 36 720 pasos, 741 s de solver (754 s de pared), pico RSS 474 220 KiB (≈ 0,45 GiB). `port_validity` OK.

| | US3_PS4 (036) | **US3_PS4_1 (040)** | Previsión de guía (H0) |
|---|---|---|---|
| Mínimos de S11 (1 MHz) | −30,16 dB en 7,826 y −32,18 dB en 8,158 GHz | **uno solo: −19,55 dB en 7,972 GHz** | 7,85–7,92 y 8,12–8,16 GHz |
| Peor S11 en el canal (1 MHz) | −10,66 dB (8,2368) | **−7,71 dB (7,7376)**; −8,77 dB en 8,2368 | |
| Canal ≤ −10 dB | 100 % | **75 %** (376/501) | |
| Banda de −10 dB (rejilla de 5 MHz) | 7,635–8,245 GHz | **7,82–8,19 GHz** | |
| Banda de −6 dB (5 MHz) | 7,49–8,355 GHz | 7,655–8,395 GHz | |
| Pico de Re(Zin) (5 MHz) | 50 Ω (7,76) y 53 Ω (8,17) | 72 Ω en 7,875 GHz | |
| η en el canal | 0,677 → **0,244** (8,137) → 0,373 | 0,605 → **0,517** (7,887) → 0,671 (máx. 0,676 en 8,137) | |
| Ganancia realizada broadside | 4,33 → −0,48 dBi | 2,54–3,88 dBi | |
| Dmax muestreado (θ cada 5°, 4 cortes en φ) | | 6,09–6,53 dBi, θ 15–20° | |

## Hipótesis pre-registradas
- **H0 falla.** Se observa un único mínimo en 7,972 GHz, 146 MHz por encima del mínimo inferior de PS4 (previsión: +25…+95 MHz), y ningún mínimo en 8,10–8,18 GHz.
- **H1 falla:** −7,71 dB frente a ≤ −10 dB.
- **H2 falla, pero de otra forma:** 2 de 11 puntos con η < 0,55 (0,524 en 7,837 y 0,517 en 7,887 GHz) y ganancia realizada ≥ 2,54 dBi en todos. El valle profundo de PS4 en 8,14 GHz (0,244) desaparece, y aparece uno poco profundo en la parte baja del canal.

## Lectura
- **Observación: con Wp 7 mm hay un solo mínimo de S11 (7,972 GHz) y un solo pico de Re(Zin) (7,875 GHz)**, en lugar de los dos de PS4; el valle de η pasa de 8,137 a 7,887 GHz. El resultado se parece más a PS5/PS6 que a PS4.
- **La causa no está identificada.** Son compatibles con los datos una reducción del acoplamiento mayor de la prevista, un cambio de la frecuencia propia del parásito por el ancho, o un cruce de modos (el modo poco radiante bajando hacia 7,89 GHz y el brillante subiendo). Con un solo run y sin mapa de campo no se distinguen. Lo único seguro es que el modelo guía falló (H0).
- **Frente a PS4:** PS4_1 pierde adaptación (−7,71 frente a −10,66 dB) y gana eficiencia en la parte alta del canal (η ≥ 0,64 desde 7,9872 GHz frente a 0,24–0,56 de PS4).
- **Frente a US3_PS6 en la misma malla base (038):** PS4_1 es peor en todo (S11 −7,71 frente a −8,16 dB, η mínimo 0,517 frente a 0,592, ganancia mínima 2,54 frente a 3,10 dBi). La conclusión no cambia frente a la malla fina (039).
- **Frente a P01_MS2:** sin ventaja.
- **Regla de decisión del JSON:** H0 falla porque los modos se fundieron, un caso que la regla no contemplaba. La conclusión práctica es la misma que para «ley k(Wp) no confirmada»: no reducir Wp más. Si se quiere separar los modos un poco menos que en PS4, un ancho intermedio (≈ 9–10 mm) es una hipótesis a contrastar: con dos puntos (11 y 7 mm) no hay base para suponer una respuesta monótona o interpolable. Solo se probaría con consentimiento del propietario y tras recalibrar con 036 y 040.

## Auditoría
`validator` (2026-11-16): **OK con observaciones**. Un solo run válido por carpeta, hashes y cifras recalculadas confirmadas. Sus reservas (mecanismo no respaldado, comparación con malla distinta, celdas nodales, malla en x, `launcher.json`, rejillas, extrapolación de Wp) están corregidas arriba.

## Pendiente
- Ronda 041 (decisión del propietario): scripts HFSS de US3_PS6.

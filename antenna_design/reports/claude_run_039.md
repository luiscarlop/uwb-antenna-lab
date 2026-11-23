# Ronda Claude 039: US3_PS6 en malla fina (comprobación de dos mallas)

- **ID del experimento:** US3_PS6_FINE_OPENEMS_039.
- **Fecha:** 2026-11-16, ronda 39/50 (el propietario subió el límite de 40 a 50 durante esta ronda).
- **Orquestador:** `claude-opus-5-5`.
- **FDTD:** 1, malla fina, `--max-timesteps 60000 --owner-long-convergence`, 2 hilos (afinidad 0,1), tope de pared 3960 s.
- **Geometría:** `variants/US3_PS6.json` sin cambios respecto a 038 (mismos hints de malla).
- **Evidencia:** `EM_SIMULATED`, con dos mallas (base 038, fina 039; refinado ≈ 1,43×). Acuerdo parcial entre mallas; convergencia no demostrada (harían falta más mallas y un criterio pre-registrado).

## Ejecución
- 5 316 960 celdas (`total_cells`; 5 414 247 nodales), 45 140 pasos, 2196 s de solver (2224 s de pared), pico RSS 961 456 KiB (≈ 0,92 GiB). openEMS v0.37.0-40-g5fecbb5, CSXCAD v0.7.0-8.
- Energía final −50,01 dB (`solver.log`), justo en el criterio de −50 dB y sobre una oscilación del decaimiento (−45,0, −43,7 y −50,0 dB en los tres últimos informes). `port_validity` OK.
- Volcados `nf2ff_E/H_*.h5` borrados tras guardar su sha256 en `nf2ff_raw_dumps.sha256`.

## Base frente a fina

| | Base (038) | **Fina (039)** | Diferencia |
|---|---|---|---|
| Peor S11 en el canal (1 MHz) | −8,16 dB (7,7376 GHz) | **−8,14 dB (7,7376 GHz)** | 0,02 dB |
| Mínimo de S11 (rejilla de 5 MHz) | −20,4 dB en 8,005 GHz | −24,7 dB en 8,005 GHz | misma frecuencia |
| Pico de Re(Zin) (5 MHz) | 63 Ω en 7,935 GHz | 59 Ω en 7,94 GHz | 5 MHz |
| Banda de −10 dB (5 MHz; 1 MHz) | 7,80–8,245; 7,797–8,248 GHz | 7,80–8,275; 7,796–8,278 GHz | +30 MHz arriba |
| Banda de −6 dB (5 MHz) | 7,64–8,365 GHz | 7,645–8,39 GHz | |
| Máx. \|ΔΓ\| complejo en el canal (1 MHz) | | 0,056 (0,040 en 7,7376 GHz) | |
| η en el canal | 0,592–0,683 | **0,625–0,690** | +0,033 en 8,2368 GHz |
| Ganancia realizada broadside | 3,10–4,23 dBi | **3,40–4,32 dBi** | +0,4 dB en 8,2368 GHz |
| Dmax muestreado (θ cada 5°, 4 cortes en φ) | 6,06–6,56 dBi, θ 15–20°, φ 270° | 6,17–6,59 dBi, θ 15–20°, φ 270° | |

## Lectura
- **Las dos mallas coinciden dentro de |ΔΓ| ≤ 0,056 en el canal.** Son estables el peor S11 (en 7,7376 GHz), la frecuencia del mínimo (8,003–8,005 GHz) y la banda de −6 dB. No son estables la profundidad del nulo (4,3 dB), el borde superior de la banda de −10 dB (+30 MHz) ni η en 8,2368 GHz (+0,033). Que el peor S11 coincida en 0,02 dB es en parte casual: en ese punto |ΔΓ| = 0,040 y la fase de Γ difiere 5,9°.
- **Hipótesis de US3_PS6 en la malla fina:** H0 se cumple (mínimo en 8,005 GHz, rango 7,95–8,03). H1 se cumple por 0,14 dB, que equivale a Δ|Γ| ≈ 0,0065, seis veces menos que la diferencia entre mallas: **no es robusto**. H2 se cumple (η ≥ 0,625, ganancia ≥ 3,40 dBi); Dmax cae a θ 15–20°, en el límite de 20°, con una rejilla de 5° y solo 4 cortes en φ, así que el máximo real puede estar fuera de la rejilla.
- **El borde superior mejora en la malla fina** (η 0,625, 3,5 dBi en 8,2368 GHz). El aviso del validator sobre ese borde se suaviza, aunque la tendencia descendente de η hacia 8,24 GHz sigue presente en las dos mallas.
- **La confusión de malla 037 → 038** señalada por el validator no se resuelve con esta ronda: 039 compara dos mallas de la misma geometría, no la causa del desplazamiento entre PS5 y PS6.
- **Posición frente a P01_MS2 sin cambios:** US3_PS6 sigue peor en peor S11 (−8,14 frente a −10,42 dB), eficiencia (0,63–0,69 frente a 0,73–0,76) y ganancia (3,4–4,3 frente a 4,3–4,8 dBi). No hay ventaja demostrada.

## Siguiente paso
- El propietario decidió preparar los scripts HFSS de US3_PS6 (ronda 041) y confirmó que se simulará; `design-reviewer` los revisa.
- US3_PS4_1: ronda 040 (`claude_run_040.md`).

## Auditoría
`validator` (2026-11-16): **OK con observaciones**. Run único, hashes y cifras confirmados. Sus reservas (convergencia sobredimensionada, H0/H2 sin evaluar, rejillas, celdas nodales, parada sobre una oscilación) están corregidas arriba.

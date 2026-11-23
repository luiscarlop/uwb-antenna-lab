# Ronda Claude 022: US3 alimentado por el borde (sin muesca), medida de R_edge y Q

- **Experimento:** US3_MS2_OPENEMS_022. Fecha: 2026-11-05, ~15:20–15:45 UTC. Ronda 22/40 (routine programada).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los tipos `rf-designer`/`em-solver` del repo no estaban disponibles: diseño y FDTD en secuencia por el orquestador. La auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Evidencia:** `EM_SIMULATED` (1 FDTD, malla base única → convergencia `NOT_ESTABLISHED`).
- **Veredicto `validator`:** **APROBAR CON RESERVAS**.

## Propuesta
Variante [`variants/US3_MS2.json`](../variants/US3_MS2.json) = US3_MS1 con **un solo cambio**: se elimina la muesca del inset (inset 2,0 → 0 mm, gap 0,5 → 0 mm). El parche vuelve a ser un rectángulo de 11,421 × 6,502 mm con la misma ranura U. La pista de 50 Ω (w 3,92 mm) va del borde de la placa (y = −13 mm) al borde radiante (y = −3,251 mm, 9,749 mm de línea).
- Material igual que US3/US3_MS1: FR4 homogéneo, εr 4,4, tanδ 0,017, h 2,07 mm; cobre 35 µm, 5,8e7 S/m; placa 26 × 26 mm.
- **Puerto** (decisión del propietario): `AddLumpedPort` vertical de R = 50 Ω en el inicio de la línea, con el ancho de la pista. Sin SMA ni sonda. El plano de referencia de S11 es el inicio de línea, sin de-embedding.
- **Objetivo:** el paso de caracterización que pedía el `next_task` de la ronda 21 («edge feed without notch after an R_edge check»). Con el Q ≈ 27,5 de US3_MS1, un λ/4 sobre el inset no podía cumplir −6 dB.
- **Hipótesis pre-registradas** (en la variante):
  - **H1:** Q < 20, η > 0,70 y Dmax a menos de 20° de broadside.
  - **H2:** R_edge entre 150 y 500 Ω.

## Ejecución
- **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f.
- **Comando** ([`launcher.json`](../em/US3_MS2_OPENEMS_022/launcher.json)): `timeout 1500s taskset -c 0,1 python em/patch_openems.py solve --variant variants/US3_MS2.json --out em/US3_MS2_OPENEMS_022 --mesh base --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9`, después de un `prepare` con los mismos argumentos.
- **Malla:** 1 966 020 celdas (2,02 M nodales). Se alcanzó −52,4 dB a los 6232 pasos.
- **Recursos:** **103 s de pared**, 89 s de motor (141 Mcell/s), **RSS 0,41 GB**, 2 CPU. La estimación previa era de 619 s y 0,72 GB.
- Los volcados NF2FF brutos se borraron después de guardar sus hashes en `nf2ff_raw_dumps.sha256`.

## Resultados
Ficheros: [`run_numeric.json`](../em/US3_MS2_OPENEMS_022/run_numeric.json), [`s11_complex.csv`](../em/US3_MS2_OPENEMS_022/s11_complex.csv), [`nf2ff_summary.json`](../em/US3_MS2_OPENEMS_022/nf2ff_summary.json).

| | US3_MS2 (022, sin muesca) | US3_MS1 (021, inset 2 mm) |
|---|---|---|
| Peor S11 en canal (puerto) | **−2,40 dB** (7,7376 GHz) | −1,93 dB |
| Mejor S11 en canal | −3,86 dB (8,2368 GHz) | −4,09 dB |
| Pico Re Zin en el puerto | 256 Ω a 8,12 GHz | 299 Ω a 8,04 GHz |
| Eficiencia de radiación | 0,55–0,59 | 0,50–0,56 |
| Dmax | 6,3 dBi en θ 35–40°, φ 270° (hacia la línea) | 6,7 dBi en θ 40°, φ 270° |
| Ganancia realizada broadside | −2,6 … −1,6 dBi | — |

- **No cumple −6 dB** (era lo esperado: alimentación directa de 50 Ω sobre un borde de alta impedancia). El puerto es válido (max\|S11\| 0,83).
- **Impedancia en el borde del parche:** [`s11_wideband_patchedge_deembedded.csv`](../em/US3_MS2_OPENEMS_022/s11_wideband_patchedge_deembedded.csv). Se obtiene rotando Γ por e^{+2jβl}, con l = 9,749 mm y εeff 3,308 (línea ideal de 50 Ω). Es un producto derivado, no un resultado del solver.
  - **Ajuste de guía** ([`circuit_fits/US3_MS2_OPENEMS_022_fit_7to9GHz_patchedge.json`](../em/circuit_fits/US3_MS2_OPENEMS_022_fit_7to9GHz_patchedge.json)): fr 7,935 GHz, **Q 16,25**, **R 296 Ω**.
  - **Zedge(f0)** = 295 − j14 Ω.
- **Dependencia de εeff** (validator): con la dispersión (Kirschning-Jansen, εeff 3,64 a 8 GHz) el ajuste da fr 8,135 GHz y R 243 Ω, con Q igual (16,0–16,5). **R_edge = 243–296 Ω** según εeff.

## Hipótesis
- **H2 se cumple:** R_edge está entre 243 y 296 Ω para todo εeff de 3,31 a 3,64.
- **H1 no se confirma en conjunto.**
  - Q < 20 en el plano del borde se cumple de forma robusta.
  - η > 0,70 y el apuntamiento a broadside **fallan**.
- **Interpretación del validator** (estimación de guía, no un resultado):
  - La η del propio parche, deducida de Q (1/Q − tanδ − 1/Qc), sería ≈ 0,72.
  - La línea desadaptada (|Γ| ≈ 0,8, 9,75 mm de FR4) daría una eficiencia ≈ 0,79.
  - El producto, 0,72 × 0,79 ≈ 0,57, coincide con lo simulado. La inclinación hacia −y es coherente con radiación de la línea ancha.
  - Por tanto, la η baja se debe sobre todo a la desadaptación y a la línea, no al parche. Hay que volver a medir η y el patrón con la línea adaptada.
- La comparación de Q con US3_MS1 no es justa: 27,5 se midió en el plano del puerto, con otra longitud de línea. Si se de-embebe US3_MS1 igual, sale Q ≈ 19–24 según el rango de ajuste. La mejora frente a US3_MS1 no está cuantificada.

## Guía para el transformador (no es un resultado)
[`circuit_fits/US3_MS2_OPENEMS_022_qw_guide_sweep.txt`](../em/circuit_fits/US3_MS2_OPENEMS_022_qw_guide_sweep.txt): un λ/4 de línea ideal sobre la Zedge de-embebida.
- Con **Zt ≈ 99–103 Ω** (w 0,8–0,9 mm) y unos 5,5 mm, el peor valor en banda es ≈ **−7,4 dB**. No incluye los parásitos de los escalones.
- Con εeff dispersivo, ese largo solo da −6,6 dB. Hace falta ~6,8 mm para recuperar los −7,4 dB.

## Reservas del validator
1. **εeff y dispersión** (media): fr y R_edge dependen de εeff. En US3_MS3 hay que barrer el largo del transformador entre 5 y 7 mm, o sacar β de una ejecución con MSLPort, en lugar de fijarlo en 5,5 mm.
2. **Comparación de Q entre planos distintos** (media), ver arriba.
3. **η de H1** (media): el criterio, tal como está redactado, no aísla el parche.
4. **Malla única** (media): resolución adecuada (bordes de 0,25 mm, ≥ 3 celdas en la ranura), pero la convergencia es `NOT_ESTABLISHED`.
5. (baja) La guía usa la rejilla de 5 MHz, que excluye los extremos exactos. Las cifras «what-if» del ajuste no deben citarse como alcanzables.
6. (heredada de la ronda 21) `prepared.json` → `port.description` sigue hablando de «SMA at the board edge», texto heredado del código. El modelo no incluye SMA.

## Siguiente hipótesis
- **US3_MS3:** US3_MS2 más un transformador λ/4 (`microstrip_edge_qw`) de Zt ≈ 100 Ω (w ≈ 0,85 mm, ≥ 3 celdas de ancho). El largo se elige con εeff dispersivo (~6–6,8 mm, centro del barrido de guía). Línea de 50 Ω hasta el puerto concentrado del borde; malla base.
- Si cumple −6 dB con margen: malla fina (comprobación con dos mallas) y comprobar η > 0,7 y broadside.
- Siguen pendientes de rehacer con esta alimentación P01_R2 y US0. P01_R2 sigue pendiente de revisión HFSS.

## Estado
Ronda 22/40. Campaña ACTIVE. Tests: 54 OK (después de reinstalar `requirements.txt`: faltaba `ezdxf`). **CONTINUE.**

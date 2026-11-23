# Ronda Claude 023: US3_MS3, transformador λ/4 sobre el U-slot alimentado por el borde

- **Experimento:** US3_MS3_OPENEMS_023. Fecha: 2026-11-05, ~16:20–16:50 UTC. Ronda 23/40 (routine programada).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los tipos `rf-designer`/`em-solver` del repo no estaban disponibles: diseño y FDTD los hizo el orquestador en secuencia. La auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Evidencia:** `EM_SIMULATED` (1 FDTD, malla base única → convergencia `NOT_ESTABLISHED`).
- **Veredicto `validator`:** **APROBAR CON RESERVAS** (métricas recalculadas desde los datos brutos; reservas abajo).

## Propuesta
Variante [`variants/US3_MS3.json`](../variants/US3_MS3.json) = US3_MS2 (ronda 22) con **un solo cambio**: los últimos 6,60 mm de la pista de 50 Ω pasan a ser un **transformador λ/4 de w 0,80 mm (Zt ≈ 102,5 Ω, HJ estático)** que toca el borde radiante (y = −3,251 mm). La pista de 50 Ω (w 3,92 mm) queda de y = −13 a y = −9,851 mm (3,149 mm).
- Parche, ranura U, material (FR4 homogéneo, εr 4,4, tanδ 0,017, h 2,07 mm; cobre 35 µm, 5,8e7 S/m), placa 26 × 26 mm y puerto iguales a US3_MS2.
- **Puerto** (decisión del propietario 2026-11-05): `AddLumpedPort` vertical de R = 50 Ω en el inicio de la línea (y = −13, ancho de pista). Sin SMA ni sonda. Plano de referencia de S11 = inicio de línea, sin de-embedding.
- **Diseño guía** ([`em/circuit_fits/US3_MS3_qw_design.py`](../em/circuit_fits/US3_MS3_qw_design.py), `GUIDE_MODEL`): la Zin EM de US3_MS2 en el plano del puerto se lleva al borde por 9,749 mm de línea de 50 Ω con εeff dispersivo (Kirschning-Jansen, 3,64 a f0), después transformador (Z0 estático HJ, εeff KJ 3,197) y la línea de 50 Ω restante. No modela el escalón ni la radiación del transformador.
  - Óptimo: **l = 6,6 mm**, mayor que λg/4 = 5,25 mm porque el transformador absorbe también la inductancia serie del borde (~0,78 nH). Aclara la discrepancia del informe 22: el barrido de guía de la ronda 22 (εeff estático, datos ya des-embebidos) daba ~5,5 mm; con εeff dispersivo, 5,5 mm predecía solo −4,5 dB.
  - Predicción guía del peor caso en banda: −7,55 dB (εeff nominal), −5,6/−5,7 dB con εeff ±5 %. Era un test real, no un resultado asegurado.
- **Malla:** el camino `microstrip_edge_qw` de `patch_openems.py` añade líneas y en la ranura (≤ 0,3 mm) y una línea x central en el transformador (x = −0,317/0/+0,317 mm dentro de una pista de ±0,4 mm: 2 celdas completas más dos fracciones de 1/3, el mínimo práctico; validator). Con eso la gradación y daba 1,507 > 1,5; se añadió una línea dura `mesh_hint_lines_mm: y = −0,215 mm` (dentro de la base de la ranura, sin metal), encontrada con pruebas de `prepare`. Es un confusor menor frente a la malla de US3_MS2.
- **Hipótesis pre-registradas** (en la variante):
  - **H1:** peor S11 en canal ≤ −6,5 dB (margen ≥ 0,5 dB) en malla base.
  - **H2:** η_rad > 0,70 y Dmax a menos de 20° de broadside.

## Ejecución
- **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f (`diagnose_solver.py` OK).
- **Comandos** ([`launcher.json`](../em/US3_MS3_OPENEMS_023/launcher.json)): `python em/patch_openems.py prepare --variant variants/US3_MS3.json --out em/US3_MS3_OPENEMS_023 --mesh base --edge-port lumped --nf2ff --excitation-fc-hz 2.5e9` y después `timeout 1500s taskset -c 0,1 python em/patch_openems.py solve` con los mismos argumentos más `--nf2ff-points 11`.
- **Malla:** 2 199 120 celdas (x 154, y 170, z 84; 2 252 925 nodos según openEMS); paso mínimo y 0,083 mm; gradación máx. 1,40.
- **Recursos:** **494 s de pared**, **RSS 0,45 GB**, 2 CPU (taskset 0,1). Estimación previa 145 s / 0,46 GB: la RAM acertó; el tiempo fue 3,4× mayor Según la auditoría: 11 232 pasos frente a 6 232 (dt 0,226 frente a 0,290 ps y más tiempo físico hasta el mismo endCriteria 1e-5) y motor a 53,2 MC/s frente a 140,7 (variabilidad del host, constante desde el primer paso). Error de método: no se reestimó el número de pasos.
- Los volcados NF2FF brutos se borraron después de guardar sus hashes en `nf2ff_raw_dumps.sha256` (como en la ronda 22).

## Resultados
Ficheros: [`run_numeric.json`](../em/US3_MS3_OPENEMS_023/run_numeric.json), [`s11_complex.csv`](../em/US3_MS3_OPENEMS_023/s11_complex.csv), [`s11_wideband.csv`](../em/US3_MS3_OPENEMS_023/s11_wideband.csv), [`nf2ff_summary.json`](../em/US3_MS3_OPENEMS_023/nf2ff_summary.json), [`nf2ff_group_delay_broadside.csv`](../em/US3_MS3_OPENEMS_023/nf2ff_group_delay_broadside.csv), [`nf2ff_pattern_complex.csv`](../em/US3_MS3_OPENEMS_023/nf2ff_pattern_complex.csv).

| | **US3_MS3 (023, λ/4)** | US3_MS2 (022, directo) |
|---|---|---|
| Peor S11 en canal (puerto) | **−8,18 dB** (7,7376 GHz) | −2,40 dB |
| Mejor S11 en canal | **−16,39 dB** (7,979 GHz) | −3,86 dB |
| Muestras ≤ −10 dB (de 501) | **376** (7,80–8,17 GHz) | 0 |
| Muestras > −6 dB | **0** | 501 |
| Banda −6 dB (barrido ancho) | 7,64–8,38 GHz (~740 MHz) | — |
| Pico Re Zin en el puerto | 69,6 Ω a 7,925 GHz | 256 Ω a 8,12 GHz |
| η_rad (Prad/Pacc) | 0,648–0,673 | 0,55–0,59 |
| Ganancia realizada broadside | **3,2–4,0 dBi** | −2,6 … −1,6 dBi |
| D broadside / Dmax | 5,7–5,9 / 5,9–6,5 dBi, Dmax en θ 15–20°, φ 270° | 6,3 dBi en θ 35–40° |
| Retardo de grupo radiado (broadside, E_φ dominante) | media 0,33 ns, ripple 67 ps pp (57 ps interior), `DIAGNOSTIC` (11 puntos) | — |

- **Cumple −6 dB en las 501 muestras del canal con 2,18 dB de margen; no cumple −10 dB en toda la banda** (falla en los bordes: −8,18 dB a 7,7376 GHz y −8,38 dB a 8,2368 GHz). El puerto es válido (`port_validity: OK`), balance de potencias `ok`.
- **H1: se cumple** (−8,18 ≤ −6,5 dB). La guía predijo −7,55 dB; el EM salió 0,6 dB mejor.
- **H2: no se cumple del todo.** η_rad 0,65–0,67 < 0,70 (FR4 tanδ 0,017 + pérdidas de línea); Dmax a 15–20° de broadside, hacia la línea (φ 270°), justo en el límite.
- El retardo de grupo es el **radiado** (E_far / a_inc en broadside), no la derivada de la fase de S11. Con 11 puntos es solo diagnóstico.

## Comparación con el mejor candidato anterior
- P01_R2 (sonda ideal, ronda 5) tenía −6,29 dB en malla fina, y US0 −6,15/−5,70 dB; todos con sonda ideal, que la decisión del propietario del 2026-11-05 ya no admite como adaptación convergida.
- Con la alimentación del propietario (microstrip + puerto concentrado de 50 Ω), **US3_MS3 es el mejor resultado de la campaña**: −8,18 dB de peor caso frente a −2,40 dB (US3_MS2) y −1,93 dB (US3_MS1).

## Errores y reservas
- **Una sola malla:** convergencia `NOT_ESTABLISHED`. No se declara viable ni se pasa a `READY_FOR_HFSS_REVIEW` hasta la comprobación con dos mallas (regla del propietario).
- La malla del camino `microstrip_edge_qw` difiere de la de US3_MS2 (líneas extra en la ranura, línea central del transformador, hint y = −0,215 mm).
- Tiempo de pared 3,4× sobre la estimación (más pasos y host más lento; ver Ejecución).
- El campo `model` de `nf2ff_summary.json` arrastra texto de los puertos MSL (herencia del script; `power_reference` es correcto).
- Dmax muestreado con 4 cortes φ y pasos de 5° en θ: el apuntamiento real puede superar algo los 20°.
- Material FR4 homogéneo provisional; η < 0,70.
- `ezdxf` faltaba en el entorno: se reinstaló `requirements.txt` y los tests pasaron (54 OK).
- Primer intento de `solve` falló porque se lanzó sin `prepare` previo en el directorio de salida (sin efecto en los datos).

## Siguiente hipótesis
- **US3_MS3 en malla fina** (misma variante, `--mesh fine`, mismo puerto): comprobación con dos mallas. Regla pre-registrada (la de la serie, `claude_run_016.md`, corregida por el validator): peor S11 en canal ≤ −6 dB, cambio del peor caso ≤ 0,5 dB, |ΔΓ| ≤ 0,03 en todo el canal y bordes de −6 dB que no se muevan más de 10 MHz. Antes de lanzar: `prepare`, estimar pasos con el dt real y la tasa de 53 MC/s (el validator estima 5–5,6 M celdas, 600–1650 s) y fijar el timeout dentro del límite de convergencia de `automation_policy.json`.
- Si converge: `READY_FOR_HFSS_REVIEW` con US3_MS3. Después, P01_R2 y US0 con alimentación microstrip.

## Estado
Ronda 23/40. Campaña ACTIVE. Tests: 54 OK. **CONTINUE.**

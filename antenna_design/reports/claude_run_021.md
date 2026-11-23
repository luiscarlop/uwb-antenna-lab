# Ronda Claude 021: US3 con alimentación microstrip de 50 Ω (malla base)

- **Experimento:** US3_MS1_OPENEMS_021. Fecha: 2026-11-05, ~14:20–14:50 UTC. Ronda 21/40 (routine programada).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los subagentes `rf-designer`/`em-solver`/`validator` del repo no estaban disponibles como tipos en esta sesión: diseño y FDTD hechos en secuencia por el orquestador; la auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Evidencia:** `EM_SIMULATED` (1 FDTD, malla única → convergencia `NOT_ESTABLISHED`).
- **Veredicto `validator`:** **APROBAR CON RESERVAS** (resultado negativo válido).

## Propuesta (aplica la decisión del propietario del 2026-11-05)
Variante [`variants/US3_MS1.json`](../variants/US3_MS1.json), derivada de US3:
- **Igual que US3:** FR4 homogéneo εr 4,4, tanδ 0,017, h 2,07 mm, placa 26×26 mm, cobre 35 µm (5,8e7 S/m), W 11,421 mm, ranura U (Wu 4,4, Lu 2,65, t 0,8, y0 −0,7 mm).
- **Alimentación:** pista microstrip de 50 Ω, **w = 3,92 mm** (Hammerstad-Jensen con corrección de espesor: 49,99 Ω, εeff 3,31; el validator obtiene 50,03 Ω de forma independiente), de y = −13 mm (borde) a la punta del inset; inset 2,0 mm, gap de muesca 0,5 mm.
- **Puerto:** `AddLumpedPort` R = 50 Ω, dirección z, de la masa a la pista, en y = −13 mm con el ancho de la pista (x ±1,96). Plano de referencia = inicio de la línea, sin de-embedding (`--edge-port lumped`). Sin SMA ni sonda.
- **L 6,85 → 6,502 mm:** el ajuste circuital de US3 (fr 7,58 GHz, Ls 1,8–2,0 nH) mostraba que su adaptación en banda la ponía la inductancia de la sonda ideal sobre una resonancia por debajo de la banda; sin sonda hay que centrar fr en f0 (escalado L·fr/f0).
- Inset estimado con la ley cos² anclada en R = 142 Ω del ajuste de US3 (estimación ~60 Ω).

## Ejecución
- openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f (`source em/runtime_env.sh`).
- Comando ([`launcher.json`](../em/US3_MS1_OPENEMS_021/launcher.json)): `timeout 1500s taskset -c 0,1 python em/patch_openems.py solve --variant variants/US3_MS1.json --out em/US3_MS1_OPENEMS_021 --mesh base --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9` (tras `prepare` con los mismos argumentos).
- 1 963 840 celdas, 5304 pasos, energía final −51,3 dB (7,5e−6 < 1e−5). **194 s de pared** (motor 180 s, 57,8 Mcell/s), **RSS 0,40 GB**, 2 CPU. Estimación previa: 399 s, 0,71 GB.
- Primer intento abortado antes de arrancar el solver (`/usr/bin/time` no existe en el contenedor; no se creó `run_started.json`); relanzado sin ese envoltorio.
- NF2FF crudos borrados tras guardar sus hashes en `nf2ff_raw_dumps.sha256` (como en 016).

## Resultados ([`run_numeric.json`](../em/US3_MS1_OPENEMS_021/run_numeric.json), [`s11_complex.csv`](../em/US3_MS1_OPENEMS_021/s11_complex.csv), [`nf2ff_summary.json`](../em/US3_MS1_OPENEMS_021/nf2ff_summary.json))
| | US3_MS1 base (021) | US3 sonda ideal fina (016) |
|---|---|---|
| Peor S11 en canal | **−1,93 dB** (7,7376 GHz) | −6,65 dB |
| Mejor S11 en canal | −4,09 dB (8,2368 GHz) | −13,64 dB |
| Pico Re Zin | 299 Ω a 8,04 GHz (Zin(f0) = 267 + j127 Ω) | — |
| Eficiencia de radiación | 0,50–0,56 | 0,79–0,81 |
| D broadside | 2,0–3,1 dBi | ≈ 6,6 dBi |
| Dmax | 6,7 dBi en θ 40°, φ 270° (−y, hacia la línea) | ≈ 6,6 dBi broadside |
| Q ajustada (guía) | 27,5 | 13,75 |

- **No cumple −6 dB ni −10 dB.** Puerto válido (max|S11| 0,834).
- **Lo que sí funcionó:** centrar la resonancia (fr 8,04 GHz, +0,7 % sobre f0).
- **Lo que falló:** la resistencia en el inset es unas 5,8 veces 50 Ω; la ley cos² (que preveía ~60 Ω) no vale con muesca + U.
- Ajuste de guía: [`circuit_fits/US3_MS1_OPENEMS_021_fit_7p5to8p5GHz_portplane.json`](../em/circuit_fits/US3_MS1_OPENEMS_021_fit_7p5to8p5GHz_portplane.json) (GUIDE_MODEL; Ls/R0 son artefactos de ~0,47 λg de línea delante del parche). Con Q ≈ 27 el modelo dice que −10 dB en toda la banda no es alcanzable ni con adaptación ideal.
- Patrón y eficiencia degradados: la Q alta (L más corto y muesca que quita ~43 % del borde radiante) explica η ≈ 1 − Q·tanδ ≈ 0,53. La inclinación hacia −y es coherente con radiación de la línea ancha (h/λ0 = 0,055) con ROE ≈ 6. El retardo de grupo radiado ([`nf2ff_group_delay_broadside.csv`](../em/US3_MS1_OPENEMS_021/nf2ff_group_delay_broadside.csv)) es solo diagnóstico.

## Reservas del validator
1. **Malla del gap de la muesca insuficiente:** 1–2 celdas en 0,5 mm; los bordes ±1,96 / ±2,46 no caen en líneas de malla (gap efectivo 0,3–0,66 mm). El puente de 0,55 mm entre la punta del inset y la U tiene ~2 celdas. `slot_mesh_check` no comprueba la muesca.
2. `prepared.json` → `port.description` aún habla de «SMA at the board edge» (texto heredado de `EDGE_PORT_MODEL`; el modelo real no incluye SMA). Corregir en el código en una ronda futura.
3. Malla única: convergencia `NOT_ESTABLISHED`. No se gasta la segunda malla en un diseño que no cumple.

## Siguiente hipótesis
- **No profundizar el inset:** el cos² recalibrado pediría d ≈ 2,76 mm, que corta la base de la U.
- **Recomendada:** transformador λ/4 entre la línea de 50 Ω y el inset actual: Zt ≈ √(50·288) ≈ 120 Ω, w ≈ 0,53 mm, λg/4 ≈ 5,4 mm (guía, tipo `microstrip_edge_qw` o equivalente). La línea de 50 Ω sigue llegando al puerto concentrado del borde.
- **Alternativa:** alimentación por el borde sin muesca con λ/4 (devolvería borde radiante, menor Q y más eficiencia), pero antes hace falta medir R_edge con EM.
- En ambas: ≥ 3 celdas en el gap/pista estrecha, malla base + fina, y comprobar que Dmax vuelve a broadside con η > 0,7.
- P01_R2 y US0 siguen pendientes de rehacer con esta alimentación; P01_R2 sigue pendiente de revisión HFSS.

## Estado
Ronda 21/40. Campaña ACTIVE. Tests: 54 OK (se reinstaló `requirements.txt` en el venv: faltaba `ezdxf`). **CONTINUE.**

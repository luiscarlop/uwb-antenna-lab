# Claude run 026 — P01_MS1 en malla fina (comprobación con dos mallas)

- **Ronda:** 26/40 (routine programada, 2026-11-05, ~19:18–19:45 UTC).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los tipos `rf-designer`, `em-solver` y `validator` no estaban disponibles como subagentes («Agent type not found»). La preparación y la FDTD las hizo el orquestador. La auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Experimento:** `P01_MS1_FINE_OPENEMS_026`, frente a la base `P01_MS1_OPENEMS_025`.
- **Evidencia:** `EM_SIMULATED` (1 FDTD). Regla de dos mallas: **`BOUNDED_SENSITIVITY_PASS`**, con márgenes muy justos. No es «convergencia».
- **Veredicto `validator`:** **APROBAR CON RESERVAS**. Es legítimo pasar a `READY_FOR_HFSS_REVIEW` como `EM_SIMULATED`, con las reservas por escrito.

## Propuesta y parámetros
- Variante [`variants/P01_MS1.json`](../variants/P01_MS1.json) **sin ningún cambio** (SHA `34ba2d01…`, el mismo en las dos ejecuciones). Solo cambia el perfil de malla: `base` → `fine` (XY 0,35 mm, aire Z 0,6 mm, gradación límite 1,5).
- Material y alimentación iguales a la ronda 25:
  - FR4 εr 4,4, tanδ 0,017, h 2,07 mm; cobre 35 µm, 5,8e7 S/m; placa 26 × 26 mm.
  - Pista de 50 Ω (w 3,92 mm) y transformador λ/4 de 0,80 × 6,60 mm (Zt ≈ 102 Ω) hasta el borde radiante del parche rectangular (W 11,421 mm, L 7,322 mm).
  - `AddLumpedPort` vertical de R = 50 Ω en el inicio de la línea (borde de la placa, ancho de pista). S11 referido a ese plano, sin de-embedding. Sin SMA ni sonda.
- **Regla pre-registrada:** la de [`claude_run_016.md`](claude_run_016.md), aplicada al par base/fina como en la ronda 24. La regla se escribió para el par fina/xfine; aquí se adapta.
  - Ítem 1: peor caso fino ≤ −6 dB y cambio ≤ 0,5 dB.
  - Ítem 2: |ΔΓ| ≤ 0,03 en el canal, y los bordes de −6 dB no se mueven más de 10 MHz.
  - Ítem 3: energía ≤ −50 dB, `port_validity` OK y |S11| ≤ 1,02.
- **Cambio de procedimiento, registrado antes de la FDTD** (commit `4ee4476`, anterior a cualquier resultado de 026): en [`em/mesh_compare.py`](../em/mesh_compare.py), los bordes del ítem 2 son ahora los de la **región contigua de −6 dB que contiene f0**, emparejados lo/hi. Lo recomendó el validator de la ronda 24.
  - Sobre 023/024 reproduce el veredicto `RULE_FAILED`.
  - En 025/026 solo hay dos cruces en todo el barrido, así que la regla antigua por ventana da exactamente lo mismo (comprobado por el validator).

## Ejecución
- **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f. `diagnose_solver.py` OK.
- **Comandos** ([`launcher.json`](../em/P01_MS1_FINE_OPENEMS_026/launcher.json)):
  - `python em/patch_openems.py prepare --variant variants/P01_MS1.json --out em/P01_MS1_FINE_OPENEMS_026 --mesh fine --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9 --owner-long-convergence`
  - después, `timeout 3800s taskset -c 0,1 python em/patch_openems.py solve`, con los mismos argumentos.
  - El timeout de 3800 s cubre los 3763 s que exige `prepared.json` y queda por debajo del límite del propietario de 4000 s.
- **Malla:** 5 202 340 celdas en `prepared.json` (5 298 030 según openEMS); paso mínimo en y de 0,058 mm.
- **Recursos:**
  - **983 s de pared**, 1749 s de CPU, **RSS máx. 0,94 GB** (`peak_rss_kib` 936 596), 2 CPU, a 77–82 MC/s.
  - Estimación previa: 800–1500 s y ~0,93 GB.
- **Fin:** energía −50,85 dB en el paso 14 308 (no fue un timeout).
- Los volcados NF2FF brutos se borraron después de guardar sus hashes en `nf2ff_raw_dumps.sha256`.

## Resultados
Ficheros: [`run_numeric.json`](../em/P01_MS1_FINE_OPENEMS_026/run_numeric.json), [`s11_complex.csv`](../em/P01_MS1_FINE_OPENEMS_026/s11_complex.csv), [`s11_wideband.csv`](../em/P01_MS1_FINE_OPENEMS_026/s11_wideband.csv), [`nf2ff_summary.json`](../em/P01_MS1_FINE_OPENEMS_026/nf2ff_summary.json), [`nf2ff_pattern_complex.csv`](../em/P01_MS1_FINE_OPENEMS_026/nf2ff_pattern_complex.csv), [`nf2ff_group_delay_broadside.csv`](../em/P01_MS1_FINE_OPENEMS_026/nf2ff_group_delay_broadside.csv), [`mesh_comparison.json`](../em/P01_MS1_FINE_OPENEMS_026/mesh_comparison.json).

| | P01_MS1 base (025) | **P01_MS1 fina (026)** | US3_MS3 fina (024) |
|---|---|---|---|
| Peor S11 en canal | −8,34 dB (7,7376 GHz) | **−8,17 dB** (7,7376 GHz) | −8,04 dB |
| Muestras ≤ −10 dB (de 501) | 440 | **434** | 387 |
| Muestras > −6 dB | 0 | 0 | 0 |
| Mínimo | 8,053 GHz | 8,054 GHz | 7,986 GHz |
| Región contigua de −6 dB | 7,6154–8,6407 GHz | **7,6251–8,6346 GHz** | 7,647–8,389 GHz |
| η_rad | 0,720–0,759 | **0,717–0,759** | 0,648–0,677 |
| Ganancia realizada broadside | 3,99–4,80 dBi | **3,94–4,82 dBi** | 3,27–4,10 dBi |
| Dmax (muestreado) | θ 15°, 6,15–6,49 dBi | θ 15°, 6,18–6,51 dBi | θ 15–20° |
| Ripple del retardo de grupo radiado (broadside, E_φ) | 34,6 ps | **35,0 ps** (`DIAGNOSTIC`) | 67 ps |
| Pared / RSS | 336 s / 425 MiB | 983 s / 0,94 GB | 910 s / 0,94 GB |

**Comprobación de la regla:**
1. Peor caso fino −8,17 ≤ −6 dB y cambio 0,18 ≤ 0,5 dB: **pasa**.
2. Máx. |ΔΓ| 0,0291 ≤ 0,03 (a 7,7376 GHz): **pasa por un 3 %**. Bordes contiguos desplazados 9,65 y 6,07 MHz ≤ 10 MHz: **pasa por 0,35 MHz**.
3. Energía −50,85 dB; `port_validity` OK en las dos; |S11| máx. 0,39: **pasa**.

**Veredicto: `BOUNDED_SENSITIVITY_PASS`.** P01_MS1 es el **primer candidato con la alimentación del propietario que supera la regla de dos mallas**. Cumple −6 dB en toda la banda, en las dos mallas, con ~2,2 dB de margen; **no cumple −10 dB**. El validator lo recalculó todo de forma independiente desde los CSV y obtiene los mismos valores.

## Errores y reservas (validator)
1. **Márgenes muy justos.**
   - ΔΓ es casi constante (0,0285–0,0291) en todo el tramo bajo del canal: es un desplazamiento sistemático, no ruido.
   - Con la malla fina, el borde inferior de −6 dB sube hacia el canal.
   - Una tercera malla probablemente no pasaría el ítem 2. Hay que hablar de «sensibilidad acotada», no de convergencia.
2. **El transformador de 0,80 mm no se refina entre mallas.**
   - Tiene ~2,5 celdas a lo ancho en las dos: líneas a 0 y ±0,317 mm en la base, y a 0 y ±0,302 mm en la fina, con una línea relajada 0,04 mm.
   - La regla no acota el Zt absoluto (≈ 102 Ω) ni la sensibilidad a ese ancho, que es lo que domina la adaptación.
3. **Gradación en x de 1,403 en la fina,** dentro del límite de 1,5 pero por encima del objetivo de 1,4. Es otro factor de confusión entre perfiles (ver ronda 24).
4. **Plano de referencia:** el puerto concentrado está en el borde de la placa, sin conector ni de-embedding. −10 dB no se cumple; −6 dB es el mínimo y no garantiza una buena respuesta temporal.
5. **η, Gr y el retardo de grupo** salen de NF2FF en openEMS: son `EM_SIMULATED` y de diagnóstico, no `HFSS_VALIDATED`. El registro es corto (~2,3 ns), con una resolución DTFT de ~440 MHz.
6. **Higiene:** `ezdxf` faltaba otra vez en el venv y se reinstaló `requirements.txt`. Los `.pyc` versionados de `em/__pycache__` siguen modificándose y no se commitean.

## Decisión
- **La campaña pasa a `READY_FOR_HFSS_REVIEW`** con `hfss_review_candidate = P01_MS1`. Sustituye a P01_R2, cuya alimentación por sonda ideal quedó superada por la regla de alimentación del propietario.
- Las rondas de Claude se detienen hasta la revisión humana, como establece `CLAUDE_CYCLE.md`.
- **Qué debe comprobar quien revise en HFSS:**
  - el ancho del transformador (0,80 mm) y la sensibilidad de S11 a ±0,05 mm;
  - el borde inferior de la banda (7,7376 GHz);
  - el sustrato real (FR4 provisional) y un posible lanzador SMA real.

## Siguiente hipótesis (para después de la revisión)
- Recentrar L (−0,8 %) para equilibrar los dos bordes, que ahora están asimétricos (+122/−398 MHz respecto a la banda).
- O bien refinar la malla del transformador (líneas guía declaradas antes y aplicadas a las dos mallas).
- La opción A de la ronda 24 (xfine de US3_MS3) sigue pendiente del propietario. Con este resultado tiene menos prioridad.

## Estado
Ronda 26/40. Campaña **READY_FOR_HFSS_REVIEW** (fase `EM_SIMULATED`). Tests: 54 OK. **PAUSED** (en espera de la revisión humana; el contador de la routine sigue ACTIVE).

# Claude run 025 — P01_MS1: parche rectangular con la alimentación microstrip del propietario (malla base)

- **Ronda:** 25/40 (routine programada, 2026-11-05).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los tipos `rf-designer`/`em-solver` no estaban disponibles como subagentes («Agent type not found»): el diseño, la preparación y la FDTD los hizo el orquestador. La auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Experimento:** `P01_MS1_OPENEMS_025`. Ejecuta la opción B de la ronda 24: rehacer P01 con la alimentación del propietario (2026-11-05).
- **Evidencia:** `EM_SIMULATED` (1 FDTD, una sola malla). Convergencia: `NOT_ESTABLISHED`.
- **Veredicto `validator`:** **APROBAR CON RESERVAS**. No pasa a `READY_FOR_HFSS_REVIEW`.

## Propuesta y parámetros
Variante: [`variants/P01_MS1.json`](../variants/P01_MS1.json) (SHA `34ba2d01…`). Guía: [`em/circuit_fits/P01_MS1_design.py`](../em/circuit_fits/P01_MS1_design.py) y su [`.json`](../em/circuit_fits/P01_MS1_design.json). Toda la guía es `GUIDE_MODEL`.

**Elemento.** Parche rectangular sin ranuras:
- W = 11,421 mm.
- **L = 7,322 mm**, escalando L·fr = cte desde el ajuste EM de US0 (rectángulo con h = 2,07 mm, malla fina, fr = 7,625 GHz con L = 7,67 mm). El mismo escalado llevó US3 → US3_MS2 a −0,65/+0,70 % de f0.
- R_edge del modelo de línea de transmisión (G1 + G12): ≈ 300 Ω. El borde del U-slot medido en EM daba 243–296 Ω.

**Material y alimentación, idénticos a US3_MS3**, de modo que la variable comparada es el elemento:
- FR4 εr 4,4, tanδ 0,017, h 2,07 mm; cobre 35 µm, 5,8e7 S/m; placa 26 × 26 mm.
- Pista de 50 Ω (w 3,92 mm, y −13 → −10,261) y transformador λ/4 de 0,80 × 6,60 mm (Zt ≈ 102 Ω) hasta el borde radiante en y = −3,661.
- `AddLumpedPort` vertical de R = 50 Ω en el inicio de la línea (borde de la placa, ancho de pista). S11 referido a ese plano, sin de-embedding. Sin SMA ni sonda.

**Hipótesis pre-registradas:**
- H1: el mínimo de S11 cae entre 7,85 y 8,15 GHz.
- H2: el peor caso en el canal es peor que el de US3_MS3 base (−8,18 dB).
- Regla: si el peor caso es ≤ −6 dB, la siguiente ronda va en malla fina.

## Ejecución
- **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f. `diagnose_solver.py` OK.
- **Comando** ([`launcher.json`](../em/P01_MS1_OPENEMS_025/launcher.json)): `python em/patch_openems.py prepare|solve --variant variants/P01_MS1.json --out em/P01_MS1_OPENEMS_025 --mesh base --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9`, bajo `timeout 1800s taskset -c 0,1`.
  - El primer lanzamiento falló al instante porque `/usr/bin/time` no existe en el contenedor. Se volvió a preparar y a lanzar.
- **Malla:** 2 055 648 celdas (152 × 161 × 84); paso mínimo en y de 0,083 mm; gradación máx. 1,40.
- **Recursos:** **336 s de pared**, 584 s de CPU, **RSS 425 MiB**, 2 CPU. Estimación previa: 450–900 s y 450 MiB.
- **Fin por criterio de energía:** −50,9 dB en el paso 9894 de 30 000 (no fue un timeout). Los volcados NF2FF brutos se borraron después de guardar sus hashes en `nf2ff_raw_dumps.sha256`.

## Resultados
Ficheros: [`run_numeric.json`](../em/P01_MS1_OPENEMS_025/run_numeric.json), [`s11_complex.csv`](../em/P01_MS1_OPENEMS_025/s11_complex.csv), [`s11_wideband.csv`](../em/P01_MS1_OPENEMS_025/s11_wideband.csv), [`nf2ff_summary.json`](../em/P01_MS1_OPENEMS_025/nf2ff_summary.json), [`nf2ff_pattern_complex.csv`](../em/P01_MS1_OPENEMS_025/nf2ff_pattern_complex.csv), [`nf2ff_group_delay_broadside.csv`](../em/P01_MS1_OPENEMS_025/nf2ff_group_delay_broadside.csv).

| | US3_MS3 base (023) | US3_MS3 fina (024) | **P01_MS1 base (025)** |
|---|---|---|---|
| Peor S11 en canal | −8,18 dB | −8,04 dB | **−8,34 dB** (7,7376 GHz) |
| Muestras ≤ −10 dB (de 501) | 376 | 387 | **440** |
| Muestras > −6 dB | 0 | 0 | 0 |
| Mínimo | 7,979 GHz | 7,986 GHz | 8,053 GHz (Zin 50,25 + j0,01 Ω) |
| Región contigua de −6 dB | 7,638–8,381 GHz | 7,647–8,389 GHz | **7,62–8,64 GHz** |
| Región contigua de −10 dB | 7,798–8,173 GHz | | 7,80–8,345 GHz |
| η_rad | 0,648–0,673 | 0,648–0,677 | **0,720–0,759** |
| Ganancia realizada broadside | 3,21–4,02 dBi | 3,27–4,10 dBi | **3,99–4,80 dBi** |
| Dmax (muestreado) | θ 15–20°, φ 270° | θ 15–20°, φ 270° | θ 15°, φ 270°, 6,2–6,5 dBi |
| Ripple del retardo de grupo radiado (broadside, E_φ) | 67 ps | 67 ps | **35 ps** (`DIAGNOSTIC`) |
| Pared / RSS | 494 s / 439 MiB | 910 s / 941 MiB | 336 s / 425 MiB |

- **H1 se confirma** (mínimo a 8,053 GHz).
- **H2 queda refutada:** sin U-slot, el peor caso no empeora. Lo que más mejora es la eficiencia (+0,07…0,09) y la ganancia realizada (+0,7…0,8 dB). El peor caso cae en el borde inferior porque la resonancia está +0,8 % por encima de f0.
- El mínimo de −52 dB es un cruce suave de Zin por 50 + j0 Ω. Su profundidad no tiene significado físico.

## Errores y reservas (validator)
1. **El transformador de 0,80 mm tiene solo ~2,5 celdas a lo ancho** (líneas a ±0,317 y 0 mm), en las dos mallas. La comparación con 023 es justa porque la malla es idéntica, pero el Zt absoluto no está acotado.
2. **La ventaja en el peor caso (0,16 dB) es del orden de la sensibilidad a la malla de US3_MS3** (0,15 dB, |ΔΓ| 0,045). En adaptación, P01_MS1 es **equivalente**, no demostradamente mejor. La ventaja en η, ganancia y ripple sí es mayor que esa variación.
3. **Resonancia desplazada +0,8 %:** el margen sobre −6 dB en el borde inferior es de ~2,3 dB.
4. **La línea de 50 Ω es 0,41 mm más corta que en 023:** el retardo absoluto no es comparable; solo el ripple.
5. **Registro de 2,28 ns:** la resolución DTFT es de ~440 MHz. El paso de 1 MHz es interpolación.
6. **`ezdxf` faltaba otra vez en el venv:** se reinstaló `requirements.txt` y pasan los 54 tests. Los `.pyc` versionados en `em/__pycache__` siguen en el índice; no se commitean sus cambios.

## Siguiente hipótesis
- **Ronda 26:** P01_MS1 en **malla fina** (prepare de prueba: 5,20 M de celdas, gradación 1,5, ~900 s, < 1 GB), con la regla de dos mallas de [`claude_run_016.md`](claude_run_016.md), emparejando los bordes de la región contigua de −6 dB.
  - Si se añaden líneas guía en x dentro del transformador (±0,2 mm, solo malla), hay que declararlas antes de simular y aplicarlas a las dos mallas. Eso exige repetir la base: no cabe en una sola ronda, así que la regla se aplica sin ellas.
- No recentrar L (−0,8 %) hasta tener la malla fina.
- La opción A de la ronda 24 (xfine de US3_MS3) sigue pendiente de decisión del propietario.

## Estado
Ronda 25/40. Campaña ACTIVE (fase `EM_SIMULATED`). Tests: 54 OK. **CONTINUE.**

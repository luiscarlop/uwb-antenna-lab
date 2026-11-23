# Ronda Claude 024: US3_MS3 en malla fina (comprobación con dos mallas)

- **Experimento:** US3_MS3_FINE_OPENEMS_024. Fecha: 2026-11-05, ~17:20–18:10 UTC. Ronda 24/40 (routine programada).
- **Orquestador:** Opus 5.5 (cabecera de la sesión). Los tipos `rf-designer`/`em-solver` no estaban disponibles como subagentes: preparación y FDTD las hizo el orquestador. La auditoría la hizo un agente general siguiendo `.claude/agents/validator.md`.
- **Evidencia:** `EM_SIMULATED` (1 FDTD). Convergencia: **regla de dos mallas NO superada** (ítem 2).
- **Veredicto `validator`:** **APROBAR CON RESERVAS**. Confirma que es correcto **no** pasar a `READY_FOR_HFSS_REVIEW`.

## Propuesta y parámetros
- Variante [`variants/US3_MS3.json`](../variants/US3_MS3.json) **sin ningún cambio** (SHA `2fcae3de…` idéntico en ambas ejecuciones). Solo cambia el perfil de malla: `base` (ronda 23) → `fine` (XY 0,35 mm, aire Z 0,6 mm, 11 líneas en el sustrato, borde 0,175 mm).
- Material y alimentación iguales a la ronda 23: FR4 homogéneo εr 4,4, tanδ 0,017, h 2,07 mm; cobre 35 µm, 5,8e7 S/m. Pista de 50 Ω (w 3,92 mm) + transformador λ/4 (0,80 × 6,60 mm, Zt ≈ 102 Ω) al borde del parche U-slot. `AddLumpedPort` vertical de R = 50 Ω en el inicio de la línea (borde de la placa, ancho de pista). Plano de referencia de S11 = inicio de línea, sin de-embedding (decisión del propietario 2026-11-05). Placa 26 × 26 mm, PML_8, Gaussiana f0 7,9872 GHz / fc 2,5 GHz, endCriteria 1e-5.
- **Regla pre-registrada** (ronda 23, que remite a [`claude_run_016.md`](claude_run_016.md)): peor S11 en malla fina ≤ −6 dB y cambio del peor caso ≤ 0,5 dB; |ΔΓ| ≤ 0,03 en todo el canal; los bordes de −6 dB no se mueven más de 10 MHz; energía ≤ −50 dB, `port_validity` OK, |S11| ≤ 1,02. Con dos mallas se habla de «sensibilidad acotada», nunca de «convergencia».

## Ejecución
- **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f (`diagnose_solver.py` OK).
- **Comandos** ([`launcher.json`](../em/US3_MS3_FINE_OPENEMS_024/launcher.json)): `python em/patch_openems.py prepare --variant variants/US3_MS3.json --out em/US3_MS3_FINE_OPENEMS_024 --mesh fine --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9 --owner-long-convergence`, y después `timeout 3960s taskset -c 0,1 python em/patch_openems.py solve` con los mismos argumentos.
  - Sin `--owner-long-convergence`, la estimación del script (1975 s) superaba el límite por defecto de 1800 s. Con la bandera aplica el límite de convergencia del propietario (4000 s). El timeout de 3960 s cubre los 3911 s que `prepared.json` exige como límite externo.
- **Malla:** 5 367 120 celdas en `prepared.json` (5 465 085 nodos según openEMS; 215 × 229 × 111); paso mínimo y 0,058 mm; gradación máx. 1,40 (límite usado 1,5, frente a 1,4 en base).
- **Recursos:** **910 s de pared**, 1633 s de CPU, **RSS 0,94 GB**, 2 CPU (taskset 0,1). Motor a 84–98 MC/s. Estimación previa: 1250–2300 s y ~0,9 GB.
- **Fin:** energía −50,68 dB tras 15 836 pasos (registro de 2,54 ns, el mismo que la base). Los volcados NF2FF brutos se borraron después de guardar sus hashes en `nf2ff_raw_dumps.sha256`.

## Resultados
Ficheros: [`run_numeric.json`](../em/US3_MS3_FINE_OPENEMS_024/run_numeric.json), [`s11_complex.csv`](../em/US3_MS3_FINE_OPENEMS_024/s11_complex.csv), [`s11_wideband.csv`](../em/US3_MS3_FINE_OPENEMS_024/s11_wideband.csv), [`nf2ff_summary.json`](../em/US3_MS3_FINE_OPENEMS_024/nf2ff_summary.json), [`nf2ff_group_delay_broadside.csv`](../em/US3_MS3_FINE_OPENEMS_024/nf2ff_group_delay_broadside.csv), [`mesh_comparison.json`](../em/US3_MS3_FINE_OPENEMS_024/mesh_comparison.json) (herramienta nueva [`em/mesh_compare.py`](../em/mesh_compare.py), validada sobre 016/018: reproduce |ΔΓ| 0,078 y −5,78 dB).

| | Base (023) | **Fina (024)** | Δ |
|---|---|---|---|
| Peor S11 en canal | −8,18 dB (7,7376 GHz) | **−8,04 dB** (7,7376 GHz) | 0,15 dB |
| Mejor S11 en canal | −16,39 dB (7,979 GHz) | −18,30 dB (7,986 GHz) | |
| Muestras ≤ −10 dB (de 501) | 376 | 387 | |
| Muestras > −6 dB | 0 | 0 | |
| Bordes −6 dB | 7,6377 / 8,3811 GHz | 7,6472 / 8,3890 GHz | 9,5 / 7,9 MHz |
| máx. \|ΔΓ\| en canal | | | **0,045** (7,7376 GHz; 60 % de las muestras > 0,03) |
| η_rad | 0,648–0,673 | 0,648–0,677 | ≤ 0,006 |
| Ganancia realizada broadside | 3,21–4,02 dBi | 3,27–4,10 dBi | ≤ 0,11 dB |
| Dmax (muestreado) | θ 15–20°, φ 270° | θ 15–20°, φ 270° | |
| Retardo de grupo radiado (broadside, E_φ dominante, 11 puntos) | 0,328 ns, ripple 67 ps | 0,333 ns, ripple 67 ps | `DIAGNOSTIC` |

**Comprobación de la regla:**
1. Peor caso fino −8,04 ≤ −6 dB y cambio 0,15 ≤ 0,5 dB: **pasa**.
2. |ΔΓ| máx. 0,045 > 0,03: **NO pasa**. Bordes de −6 dB 9,5 y 7,9 MHz ≤ 10 MHz: pasa (el margen es de solo 0,45 MHz).
3. Energía −50,7 dB, `port_validity` OK en ambas, |S11| ≤ 0,92: **pasa**.
4. No aplica: el cambio es < 0,5 dB, así que no es «sensible a la malla» en el sentido de la regla.

**Resultado: `RULE_FAILED` (ítem 2).** US3_MS3 sigue siendo el mejor candidato con la alimentación del propietario y cumple −6 dB con ~2 dB de margen en las dos mallas. Aun así, **no se declara viable ni pasa a `READY_FOR_HFSS_REVIEW`**.

### Diagnóstico de la diferencia ΔΓ (sin efecto en el veredicto)
- La mayor parte de la diferencia está en la magnitud: Δ|Γ| máx. 0,031; la fase cambia entre −3,7° y +11,1°.
- Un desplazamiento en frecuencia de +10 MHz de la curva base deja aún |ΔΓ| = 0,031. Es solo un diagnóstico: no está en la regla y no sirve para aprobar.
- Recortar los registros a 2,4/2,2 ns cambia Γ ~0,0015, así que el truncamiento no explica la diferencia: es discretización real.
- Confusores inherentes al cambio de perfil (validator): límite de gradación 1,5 frente a 1,4, PML físicamente más delgada en la fina (~2,8 frente a ~4 mm), caja NF2FF desplazada 1,36 mm y un snapping de polígonos distinto (0,027 frente a 0,040 mm). Este último tiene el orden de magnitud justo para producir un desplazamiento de ~10 MHz.

## Errores y reservas
- **Cambio de procedimiento posterior a ver los datos.** La primera versión de `mesh_compare.py` (commit `b653635`) comparaba todos los cruces de −6 dB. Después de ver los datos se restringió a 7–9 GHz, porque un tercer cruce (modo fuera de banda, ~10,3 GHz) se movía 14 MHz. La ronda 23 ya registraba el ancho de banda de −6 dB como 7,638–8,381 GHz, de modo que «bordes» se refería a la banda adaptada. **El veredicto es `RULE_FAILED` con o sin la ventana.** Mejora pendiente (validator): tomar la región contigua de −6 dB que contiene el canal y emparejar bordes por vecino más cercano.
- `launcher.json` anotó dt 0,205 ps (estimación del script); el dt real fue 0,160 ps. El registro físico es el mismo (2,54 ns).
- `solver.log` está en `.gitignore` (`*.log`); la evidencia de energía está en `openEMS_run_stats.txt` (versionado).
- `em/__pycache__/*.pyc` está versionado en git (higiene; no se toca en esta ronda).
- `ezdxf` faltaba en el venv del solver: se instaló `requirements.txt` y los tests pasaron.
- **El perfil `xfine` no se puede preparar para US3_MS3 tal cual:** gradación y 1,83 > 1,5 cerca de la base de la ranura. Necesita `mesh_hint_lines_mm` (solo malla). Estimación: ≥ 14–15 M celdas y unos 16–22 k pasos, es decir ~4200–6600 s a 53 MC/s, **por encima del límite de 4000 s**.

## Siguiente hipótesis
- **Opción A, decisión del propietario:** autorizar ~6000 s para US3_MS3 en `xfine` (solo S11, sin NF2FF, con líneas guía solo de malla), con la misma regla sobre el par fina/xfine. O bien aceptar HFSS como árbitro de la sensibilidad residual |ΔΓ| ≈ 0,045, con peor caso −8,0 dB y cambio de 0,15 dB.
- **Opción B, la ronda siguiente sin esperar:** rehacer **P01_R2 con la alimentación microstrip del propietario** (pendiente por la decisión del 2026-11-05), en malla base, con el mismo material y el mismo puerto.

## Estado
Ronda 24/40. Campaña ACTIVE (fase `EM_SIMULATED`). Tests: 54 OK. **CONTINUE**: el siguiente paso queda en la opción B. La opción A necesita al propietario.

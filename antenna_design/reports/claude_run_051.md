# Ronda Claude 051: US3_PS6_4 en malla fina

- **ID:** US3_PS6_4_FINE_OPENEMS_051.
- **Fecha:** 2026-11-19, ronda 51/60.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «Sí, lanza la malla fina de US3_PS6_4» (autoriza superar el tope de 1800 s).
- **Geometría:** `variants/US3_PS6_4.json`, la misma que en 050 (sha256 6c9b0c77…). XML `8ce32db1…`, distinto del de 050 solo por la malla.
- **FDTD:** 1, malla fina, `--max-timesteps 60000 --owner-long-convergence`, 2 hilos (afinidad 0,1), tope de pared 4060 s (prepare pedía ≥ 4008 s). `prepare` y `solve` en la misma carpeta.
- **Software:** openEMS 0.37.0-40-g5fecbb5, CSXCAD 0.7.0-8-g626b99f, `em/patch_openems.py` sha256 `2fc739d5…`.
- **Material y puerto:** FR4 homogéneo provisional (εr 4,4, tanδ 0,017, h 2,07 mm), cobre de 35 µm en lámina, placa de 26 × 26 mm, puerto lumped de 50 Ω en y = −13 mm sin de-embedding ni conector.
- **Evidencia:** `EM_SIMULATED` en dos mallas (050 base, 051 fina): `BOUNDED_SENSITIVITY_PASS (two meshes, not convergence)`.

## Ejecución
- 46 546 pasos sobre 5 566 761 celdas nodales (219 × 229 × 111): 3012 s de pared, 5436 s de CPU, pico RSS 985 096 KiB (≈ 1,0 GB). La estimación previa era 2672 s de motor y 1,96 GB con margen ×2.
- **Terminación en un valle de energía:** −50,01 dB en el último muestreo, con una envolvente de picos de ≈ −43 dB que baja de forma monótona. 050 terminó igual (valle −51,3 dB, envolvente ≈ −45 dB). El validator recortó el registro de puerto: quitar el 30 % final cambia |Γ| ≤ 0,006, un orden de magnitud por debajo de la diferencia entre mallas. El efecto del truncamiento sobre η, ganancia y τ_g no se ha medido.
- `port_validity` OK (máx |S11| 0,9126). Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256; las salidas versionadas son `nf2ff.h5`, `nf2ff_summary.json` y `nf2ff_pattern_complex.csv`.

## Base frente a fina (S11 en rejilla de 1 MHz)

| | Base (050) | **Fina (051)** |
|---|---|---|
| Mínimo de S11 | 7,936 GHz (−21,66 dB) | **7,947 GHz (−22,23 dB)** |
| Peor S11 en el canal | −10,92 dB (8,2368) | **−11,24 dB (8,2368)** |
| Bordes 7,7376 / 8,2368 | −11,77 / −10,92 dB | −11,46 / −11,24 dB |
| Canal ≤ −10 dB | 100 % | **100 %** |
| Región ≤ −10 dB | 7,687–8,318 GHz | 7,695–8,380 GHz |
| η_rad (P_rad/P_acept) | 0,654–0,709 | 0,661–0,712 |
| Ganancia realizada broadside | 4,03–4,71 dBi | 4,13–4,71 dBi |
| Ganancia IEEE | 4,40–4,74 dBi | 4,47–4,75 dBi |
| Rizado τ_g (copolar y, broadside, diagnóstico) | 32 ps | 15 ps |
| Máx. \|ΔΓ\| en el canal | | **0,015 (7,866 GHz)**; media 0,013 |

## Lectura
- **Las dos mallas cubren el canal a −10 dB, y la fina con más margen** (1,24 dB frente a 0,92 dB). La reserva 2 del validator en la ronda 50 queda resuelta de forma acotada: el −10 dB no era un artefacto de la malla base.
- **La sensibilidad de malla es baja:** |ΔΓ| máx 0,015, la mitad del umbral de 0,03 de las rondas 026/028, y unas 13 veces menos que en US3_PS4_2_1 (0,20 entre 045 y 047). Es coherente con un mínimo único y suave. El cambio del peor caso (0,32 dB) es mayor que en 024/026, pero en sentido favorable.
- **El borde superior de la región ≤ −10 dB es lo más sensible:** sube 62 MHz con la malla (8,318 → 8,380 GHz). El margen sobre el canal pasa de 81 a 143 MHz.
- **Es un contraste de sensibilidad, no una prueba de convergencia.** El refinamiento es de solo 1,25–1,43×. Además cambian el grosor físico de la PML (4,0 → 2,8 mm) y la posición de la caja NF2FF (≈ 1,2 mm). El transformador de 1,0 mm solo gana ≈ 1,2× de resolución, y la razón entre celdas vecinas llega a 1,457 en la unión transformador-parche. Con dos mallas no se puede extrapolar ni decir cuál es el valor «verdadero».
- **Sin resolver: el escalón de la línea de 50 Ω cerca del puerto** (reserva 3 de 050). Gana resolución en y (0,083 → 0,058 mm), pero no hay prueba aislada ni de-embedding. Lo debe contrastar HFSS con un wave port.
- **τ_g:** la mejora de 32 a 15 ps es del orden de la sensibilidad de malla y de la rejilla de 11 puntos (≈ 50 MHz). Se cita como diagnóstico, no como valor firme.

## Estado
- US3_PS6_4: `EM_SIMULATED` en dos mallas, con sensibilidad acotada y modelo de material provisional. No es `HFSS_VALIDATED` ni `MEASURED`.
- Candidato para HFSS. Si el propietario confirma que lo simula, se lanza `design-reviewer`. Puntos que deben contrastar el revisor y HFSS: el escalón de la línea de 50 Ω, la unión transformador-parche y el borde superior a −10 dB (8,32–8,38 GHz).

## Auditoría
`validator` (2026-11-19): **OK con observaciones**. Trazabilidad, hashes, versiones, cifras de S11, |ΔΓ|, η, ganancias, τ_g y recursos reproducidos; `reanalyze_port_dft.py --check` reproduce `s11_complex.csv` con error de 2,2e-15; 198 tests OK. Sus reservas (sensibilidad y no convergencia, confusores PML/NF2FF/transformador, escalón del puerto, valle de energía, etiquetado de ganancia y τ_g, volcados efímeros, registro de campaña) están incorporadas arriba.

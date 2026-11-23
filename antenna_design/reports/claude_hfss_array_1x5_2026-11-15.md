# Array 1×5 de P01_MS2 en HFSS (propietario), paso 17 mm: análisis

- **Fecha:** 2026-11-15. Análisis del orquestador (`claude-opus-5-5`) sobre la exportación del propietario; auditado por `validator`: **APROBAR CON RESERVAS**.
- **Evidencia:** `EM_SIMULATED`. El `.s5p` manual de 17 mm se exportó con HFSS 2024.2.0 y los 16 del barrido con 2025.1.0; la versión con la que se resolvió no está confirmada. **No es `HFSS_VALIDATED`:** faltan la convergencia adaptativa (`.conv`, pases, ΔS), la frecuencia de adaptación y el tipo de barrido. Hay que pedírselos al propietario.
- **Diseño:** `ARR1x5_P01_MS2_dparam` (script `hfss/claude_aedt_array1x5_param_ch9.py`), `arr_d` = 17 mm. Elemento P01_MS2: parche 11,421 × 7,322 mm, transformador 0,8 × 7,1 mm, FR4 εr 4,4, tanδ 0,017, 2,07 mm. 5 puertos concentrados de 50 Ω, P1…P5 de −x a +x en x = (i − 2)·17 mm.
- **Datos:** [`hfss/results_2026-11-15/ARR1x5_P01_MS2_d17mm/`](../hfss/results_2026-11-15/ARR1x5_P01_MS2_d17mm/): `.s5p` y campos embebidos `ff_P1…P5.csv` (1 W en un puerto y 0 W en los demás). Análisis: [`array_hfss_analysis.py`](../hfss/array_hfss_analysis.py) → `array_analysis_d17mm.json`.
- **Columnas de frecuencia de los CSV:** sin sufijo = 7,9872 GHz, `_1` = 7,7376 GHz y `_2` = 8,2368 GHz. Se comprueba con la pendiente de fase del campo lejano de P1 y P5, que ordena como las frecuencias. La comparación de potencia radiada con potencia aceptada **no** discrimina la asignación.

## Matriz S (canal 7,7376–8,2368 GHz, rejilla de 1 MHz)
| | Peor valor en el canal |
|---|---|
| Adaptación de cada puerto en el array | ≈ −10,0 dB (de −10,00 a −10,69; margen ≤ 0,13 dB en P2, P3 y P4, en 7,738 GHz) |
| Acoplo entre vecinos | −15,0 a −15,4 dB (hacia 7,79–7,83 GHz) |
| Acoplo entre no vecinos | < −24 dB |
| ECC a partir de S | ≤ 0,021 (indicativo: supone antenas sin pérdidas y la eficiencia es ≈ 0,8) |
| S activo, 5 puertos a 1 W | θ0 = 0°: −8,5 dB (P3); 15°: −9,3 dB; 30°: −7,8 dB (P5). El peor caso cae casi siempre en 8,236 GHz |
| TARC | −9,6 a −10,7 dB |

## Diagramas (7,9872 GHz; rejilla de 5°, HPBW interpolado ±0,5°, cortes en φ = 0/180 y 90/270)
| | Ganancia realizada | HPBW xz | Lóbulo secundario xz | Notas |
|---|---|---|---|---|
| Elemento embebido extremo (P1) | 5,1 dBi | ≈ 110° | | pico en θ 10°, φ 285° |
| Elemento embebido central (P3) | 4,6 dBi | ≈ 121° | | más ancho que el aislado (≈ 84°) |
| Array físico, broadside | 11,5 dBi | ≈ 21,7° | −13,6 dB | yz ≈ 89°, pico en −5° hacia la alimentación |
| Array físico, θ0 = 15° / 30° | 11,4 / 11,2 dBi | ≈ 22,6° / 24,5° | −12,5 / −11,8 dB | el pico del corte xz cae en 15° / 30°; el máximo global está ~5° fuera del plano |
| Virtual MIMO, broadside (30 configuraciones 1 TX + 2 RX, apagados a 50 Ω) | ida y vuelta, normalizado | ≈ 17,7° | −24,0 dB | yz ≈ 56° |
| Virtual MIMO, θ0 = 15° / 30° | | ≈ 19,1° / 19,8° | −17,7 / −14,6 dB | |

En 7,7376 y 8,2368 GHz los valores son parecidos (`array_analysis_d17mm.json`).

## Comparación con el modelo
- El cálculo en chat con el elemento **aislado** P01_MS1 × factor de array daba ≈ 22° (físico) y ≈ 18° (virtual). No se guardó como script.
- La reconstrucción del validator con el elemento central **embebido** × factor de array da 21,65° y 17,3°. HFSS da 21,7° y 17,65°.
- La coincidencia se limita al **lóbulo principal**: dentro de 0,3 dB para |θ| ≤ 10°, hasta 1,5–3,3 dB entre 30° y 50°, y los nulos no coinciden.
- En el array, los diagramas embebidos son más anchos que el del elemento aislado. Por eso el error de apuntamiento que predecía el modelo (−5° a 30°) no aparece en el corte xz.

## Corrección de método
`cut_metrics` contaba las muestras ≥ −3 dB sin interpolar: en una rejilla de 5°, el haz virtual salía de 10°. Ahora interpola el cruce en dB. Los anchos que se dieron antes en el chat y en la página visual estaban redondeados por defecto a la rejilla de 5°. `virtual_array_pitch_sweep.py` usa su propia rutina con rejilla de 0,25° y no se ve afectado.

## Pendiente
- Pedir al propietario la convergencia (`.conv`) del array.
- ~~Exportar el resto de pasos del barrido~~: hecho (sección siguiente). Solo hay campos de 13,5 y 17 mm; los pasos intermedios son solo de S.
- Exportar los campos a 18,2 mm (paso recomendado).
- Calcular el ECC a partir de los diagramas (sin hacer).
- El supuesto de 50 Ω en los puertos apagados es una decisión del propietario sobre el hardware; un conmutador real no da Γ_off = 0 exacto.

## Barrido de paso (Optimetrics de `arr_d`, 16 pasos) — añadido 2026-11-15
Datos: [`hfss/results_2026-11-15/ch9_array_export/`](../hfss/results_2026-11-15/ch9_array_export/) (exportados con `claude_aedt_export_array_ch9.py`; véase su `export_log.txt`). Las cabeceras de los 16 `.s5p` coinciden con su paso (`board_x` = 4·`arr_d` + 26 mm). Rejilla de 1 MHz: el canal se evalúa entre 7,738 y 8,236 GHz. Diagramas en rejilla de 5°. Auditado por `validator`: **APROBAR CON RESERVAS**. Análisis: [`array_pitch_sweep_hfss.py`](../hfss/array_pitch_sweep_hfss.py) → `array_pitch_sweep_hfss.json`. Los campos se exportaron solo para 13,5 mm (y 17 mm a mano): `array_analysis_d13p5mm.json`. El `.s5p` de 17 mm del script coincide con el manual (diferencia máxima 3e-13).

Valores en dB; todos son el peor caso en el canal. «S activo» es el de los 5 puertos a 1 W con fase progresiva.

| Paso (mm) | Adaptación pasiva | Acoplo vecinos | Acoplo no vecinos | ECC (S) | S activo 0° | S activo 15° | S activo 30° | S activo 45° |
|---|---|---|---|---|---|---|---|---|
| 13,5 | −9,6 | −10,3 | −16,2 | 0,073 | **−4,9** | −6,3 | −6,6 | −7,4 |
| 15,0 | −9,7 | −12,1 | −19,7 | 0,048 | −7,1 | −7,7 | −7,0 | −8,3 |
| 16,0 | −9,7 | −13,6 | −22,1 | 0,034 | −8,0 | −8,7 | −7,5 | −8,3 |
| 17,0 | −10,0 | −15,0 | −24,6 | 0,021 | −8,5 | −9,3 | −7,8 | −8,4 |
| 18,0 | −10,2 | −16,6 | −26,8 | 0,011 | −8,8 | −9,8 | −8,1 | −8,6 |
| 18,2 | −10,3 | −16,9 | −27,3 | 0,010 | −9,3 | −9,8 | −8,1 | −8,3 |
| 19,0 | −10,3 | −18,1 | −28,1 | 0,005 | −10,0 | −10,2 | −8,4 | −8,1 |
| 20,5 | −10,7 | −20,6 | −30,3 | 0,001 | −11,2 | −10,4 | −8,9 | −7,9 |

Diagramas a 7,9872 GHz, 13,5 frente a 17 mm:

| | 13,5 mm | 17 mm |
|---|---|---|
| Ganancia realizada del array físico | 10,3 dBi | 11,5 dBi |
| HPBW xz del array físico | 27,5° | 21,7° |
| HPBW xz del array virtual | 22,9° | 17,7° |
| Lóbulo secundario virtual (broadside) | −24,9 dB | −24,0 dB |
| Elemento central embebido | 3,5 dBi | 4,6 dBi |

**Lectura:**
- El paso del artículo (13,5 mm) acopla mucho: −10,3 dB entre vecinos y S activo de −4,9 dB en broadside, que **no cumple −6 dB**.
- El cruce de −6 dB del S activo en broadside está hacia 14,3 mm.
- El acoplo entre vecinos y entre no vecinos baja de forma estrictamente monótona con el paso.
- Ángulo máximo de apuntamiento sin lóbulo de rejilla en 8,2368 GHz (factor de array físico): asin(λ/d − 1) = 88,9° a 18,2 mm, ≈78° a 18,5 mm, ≈66° a 19 mm y 50,8° a 20,5 mm. Para ±45° bastaría hasta ≈21,3 mm.
- Se propone **18–18,2 mm** como compromiso: acoplo ≈ −17 dB, ECC (S) ≈ 0,01 y S activo entre −8,1 y −9,8 dB hasta 30°, con d ≤ λ/2 en todo el canal. Es una elección por λ/2 y por acoplo, no porque 19 mm tenga lóbulos de rejilla a ±45°. El código del TFG usa λ/2 en f0 = 18,77 mm, muy cerca.
- A 0°, 15° y 30° el peor S activo cae en ≈8,236 GHz; a 45° cae en 7,738 GHz desde 14,5 mm. El S activo a 30° pasa de −6,6 a −8,9 dB con el paso, y a 45° de −7,4 a −8,6 dB: solo desde ≈18 mm queda en −8 a −9 dB. Lo limita el margen del elemento en los bordes (Sii ≈ −10,3 dB a 18,2 mm), pero el paso también influye a 30°.
- El ECC a partir de S supone antenas sin pérdidas; la eficiencia radiada/aceptada es ≈0,76–0,83.
- Los CSV de 13,5 mm no registran `board_x`. El log indica que se exportaron tras fijar `arr_d` = 13,5 mm como valor del diseño, después del primer intento fallido (variación mezclada, ficheros sobrescritos).

# Pre-registro HFSS de US3_PS6_4

- **Fecha:** 2026-11-19.
- **Estado de este documento:** pre-registro anterior a cualquier resultado HFSS de US3_PS6_4. Debe estar commiteado antes de que exista ningún fichero de resultados en esta carpeta.
- **Origen:** correcciones R1 (elemento) y R2 (array 1x5) de `design-reviewer`, con las cifras recalculadas desde los datos del repositorio.
- **Estado del diseño:** `GEOMETRY_ONLY` en la geometría y `EM_SIMULATED` solo en openEMS (rondas 050 y 051). Nada de lo que sigue es un resultado HFSS: son hipótesis y extrapolaciones.
- **Anclaje temporal:** `variants/US3_PS6_4.json` no se modifica; su sha256 es `6c9b0c774f741e4380d3f194fbddab56ab581fa94f110875f8f7c431e246f75a` y está registrado en `em/US3_PS6_4_OPENEMS_050/` y `em/US3_PS6_4_FINE_OPENEMS_051/` (`prepared.json`, `run_numeric.json`, `solver_log.txt`). Eso prueba que las hipótesis H0, H1 y H2 de la variante son anteriores a HFSS.

## Fuentes

- openEMS: `em/US3_PS6_4_OPENEMS_050/` (malla base) y `em/US3_PS6_4_FINE_OPENEMS_051/` (malla fina): `s11_complex.csv`, `nf2ff_summary.json`.
- Referencias openEMS previas: `em/US3_PS6_OPENEMS_038/`, `em/US3_PS6_FINE_OPENEMS_039/`, `em/US3_PS6_1_OPENEMS_046/`, `em/US3_PS4_2_1_OPENEMS_045/`.
- HFSS previo del elemento: `hfss/results/results_US3_PS6/US3_PS6/` (`US3_PS6.s1p`, `antenna_params.csv`, `ff_P1.csv`, `realized_gain_cuts.csv`) y `hfss/results/results_US3_PS4_2_1/US3_PS4_2_1/`.
- Desfase de la guía: `hfss/results/results_P01_MS1/hfss_vs_openems.json`, `hfss/results/results_US3_MS3/hfss_vs_openems.json`, `reports/claude_hfss_review_2026-11-13.md` y `reports/claude_hfss_elements_2026-11-17.md`.
- Arrays: `hfss/results/results_P01_MS2/ARR1x5_P01_MS2_dparam/array_pitch_sweep_hfss.json` y `hfss/results/results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/array_pitch_sweep_hfss.json` y `array_analysis_d18p2mm.json`.
- Variante: `variants/US3_PS6_4.json`.

## Configuración HFSS prevista (para que la comparación sea justa)

Mismo modelo que US3_PS6: FR4 homogéneo provisional (eps_r 4,4, tan_delta 0,017, h 2,07 mm), cobre de 35 um, **puerto lumped de 50 Ω en el borde de la placa** (y = -13 mm), sin conector y sin de-embedding. Banda 7,7376–8,2368 GHz, f0 7,9872 GHz. El barrido de HFSS llega a 8,236 GHz en la rejilla de 1 MHz del canal (no a 8,2368), y el `.s1p` se exporta hasta 8,5 GHz. Las hipótesis se evalúan sobre la rejilla de 1 MHz del canal y sobre las 11 frecuencias de `Edges_and_f0` (paso de 49,92 MHz) para radiación.

## R1. Elemento aislado

### Base openEMS (sin desplazar)

| Ronda | Mínimo de S11 | S11 mínimo | Peor S11 en el canal | Bordes inf. / sup. | Banda ≤ −10 dB |
|---|---|---|---|---|---|
| 050 (base) | 7,936 GHz | −21,66 dB | −10,92 dB (8,2368 GHz) | −11,77 / −10,92 | 7,687–8,318 GHz |
| 051 (fina) | 7,947 GHz | −22,23 dB | −11,24 dB (8,2368 GHz) | −11,46 / −11,24 | 7,695–8,380 GHz |

Radiación openEMS (11 frecuencias, broadside): η_rad (Prad/Pacc) 0,654–0,709 en 050 y 0,661–0,712 en 051; ganancia realizada broadside 4,03–4,71 dBi en 050 y 4,13–4,71 dBi en 051.

### Desfase HFSS − openEMS: lo que sí está medido

Se mide como diferencia entre las posiciones del mínimo de S11 principal.

| Diseño | Mínimo HFSS | Mínimo openEMS | Desfase |
|---|---|---|---|
| P01_MS1 | 7,991 GHz | 8,053 GHz (025) | −62 MHz |
| US3_MS3 | 7,906 GHz | 7,979 GHz (023) | −73 MHz |
| US3_PS6 | 7,955 GHz | 8,005 GHz (038, base) / 8,003 GHz (039, fina) | **−50 / −48 MHz** (recalculado en este pre-registro) |
| US3_PS4_2_1 | 7,875 y 8,140 GHz | 7,880 y 8,137 GHz (045, base) | **≈ −5 / +3 MHz** (contraejemplo; `reports/claude_hfss_elements_2026-11-17.md`) |

El desfase **no es una constante**: −62/−73 MHz en los diseños de parche sin parásito, −48…−50 MHz en US3_PS6 y ≈ 0 en US3_PS4_2_1. US3_PS6_4 es de la familia de US3_PS6 (misma pila, mismo parásito flotante en z = 1,035 mm, mismo U-slot), así que el desfase de US3_PS6 es la referencia más cercana, y el rango −50…−75 MHz es el pre-registrado. **Que el desfase sea ≈ 0 es el escenario alternativo, y no se descarta.**

### Método de desplazamiento de las curvas openEMS

1. Se carga `s11_complex.csv` de 050 y 051 (1 001 puntos, 1 MHz entre 7,5 y 8,5 GHz).
2. Se desplaza el eje de frecuencia una cantidad fija Δf (−50, −62 y −75 MHz) sin tocar el módulo de S11.
3. Se recalcula el mínimo, el peor S11 en el canal (rejilla desplazada, 7,7376–8,2368 GHz, con interpolación lineal en los bordes), los S11 en los bordes del canal y los bordes de la banda ≤ −10 dB alrededor del mínimo.
4. Prueba retrospectiva sobre US3_PS6 con Δf = −50 MHz: 038 desplazada da peor S11 −8,54 dB (HFSS real −8,72 dB, diferencia 0,18 dB optimista), borde inferior −9,67 dB (HFSS −9,05) y superior −8,51 dB (HFSS −8,70); 039 desplazada da −9,73 dB (diferencia 1,0 dB optimista). En US3_PS4_2_1, sin desplazamiento, 045 da −10,35 dB y HFSS −10,00 dB (0,35 dB optimista). La malla base de openEMS es la que más se parece a HFSS en los dos casos.
5. Conclusión del método: el desplazamiento reproduce la posición del mínimo, pero **la predicción del peor S11 sale entre 0,2 y 1,0 dB más optimista que HFSS**. El desplazamiento solo traslada la curva; no recoge los cambios de forma.

### Curvas desplazadas de US3_PS6_4 (cálculo, no resultado HFSS)

| Curva | Δf | Mínimo | Peor S11 en canal (8,236 GHz) | Bordes inf. / sup. | Borde sup. a −10 dB |
|---|---|---|---|---|---|
| 050 | 0 | 7,936 GHz | −10,92 dB (8,2368) | −11,77 / −10,92 | 8,318 GHz |
| 050 | −50 MHz | 7,886 GHz | −10,43 dB | −13,93 / −10,43 | 8,268 GHz |
| 050 | −62 MHz | 7,874 GHz | −10,30 dB | −14,52 / −10,29 | 8,256 GHz |
| 050 | −75 MHz | 7,861 GHz | −10,13 dB | −15,21 / −10,11 | 8,243 GHz |
| 051 | 0 | 7,947 GHz | −11,24 dB (8,2368) | −11,46 / −11,24 | 8,380 GHz |
| 051 | −50 MHz | 7,897 GHz | −10,87 dB | −13,58 / −10,87 | 8,330 GHz |
| 051 | −62 MHz | 7,885 GHz | −10,86 dB | −14,17 / −10,86 | 8,318 GHz |
| 051 | −75 MHz | 7,872 GHz | −10,85 dB | −14,85 / −10,85 | 8,305 GHz |

Con un sesgo adicional optimista de 0,35 dB (el de US3_PS4_2_1) la base desplazada da un peor S11 de −10,08, −9,95 y −9,78 dB para −50, −62 y −75 MHz; con un sesgo de 1,0 dB (el peor caso de la prueba retrospectiva) da −9,43, −9,30 y −9,13 dB. Para la fina con 0,35 dB: −10,52, −10,51 y −10,50 dB; con 1,0 dB: −9,87, −9,86 y −9,85 dB.

### Hipótesis

- **H_HFSS0 (posición del mínimo):** el mínimo de S11 de HFSS cae en **7,86–7,89 GHz** si HFSS sigue la malla base (050) y en **7,87–7,90 GHz** si sigue la fina (051). Escenario alternativo (desfase ≈ 0, como US3_PS4_2_1): 7,936–7,947 GHz. Se refuta H_HFSS0 si el mínimo cae fuera de 7,85–7,91 GHz.
- **H_HFSS1 (adaptación en el canal):** el **peor S11 del canal está entre −9,1 y −10,9 dB**. La probabilidad de que sea ≤ −10 dB es de **≈ 50 %** (estimación a partir de las cifras anteriores, no un cálculo estadístico): el valor central del desplazamiento sin sesgo es −10,3 dB (base) y −10,9 dB (fina), pero la prueba retrospectiva indica que HFSS suele salir entre 0,2 y 1,0 dB peor. El peor punto se espera en el borde superior (8,236 GHz), no en el inferior (−13,6 a −15,2 dB). El borde superior de la banda ≤ −10 dB se espera en **8,24–8,27 GHz** si HFSS sigue la base y hasta **8,31–8,33 GHz** si sigue la fina; con el sesgo de 0,35 dB baja a 8,22–8,24 GHz (base). El criterio es que ese borde quede por encima de 8,2368 GHz. Se refuta H_HFSS1 si el peor S11 es peor que −10,9 dB o mejor que −9,1 dB, o si el peor punto está en el borde inferior.
- **H_HFSS2 (radiación):** η_rad ≥ 0,6 en las 11 frecuencias y ganancia realizada broadside ≥ 2 dBi en el canal. Se calcula así:
  - η_rad: columna `RadiationEfficiency []` de `antenna_params.csv` (Prad/Pacc, sin unidades).
  - Ganancia realizada broadside, **en dB**: desde `ff_P1.csv` (1 W incidente), con G = 4π(|rEθ|² + |rEφ|²)/(2·η0) en θ = 0, convertida a dBi, y contrastada con `dB(RealizedGainTotal)` de `realized_gain_cuts.csv` en θ = 0. Se comprobó con US3_PS6 que las dos vías coinciden (3,80 / 4,05 / 4,24 / 4,37 / 4,43 / 4,43 / 4,38 / 4,26 / 4,10 / 3,86 / 3,48 dBi). **No** se usa `PeakRealizedGain []` de `antenna_params.csv`, que es lineal y es el máximo, no broadside.
  - Referencia: en US3_PS6, HFSS dio η_rad 0,690–0,738 frente a 0,592–0,683 de openEMS 038 (+0,05…+0,10), y ganancia realizada broadside 3,48–4,43 dBi frente a 3,10–4,23 dBi (+0,2…+0,4 dB). openEMS 050/051 da 0,65–0,71 y 4,0–4,7 dBi, con margen suficiente sobre 0,6 y 2 dBi. Se espera que H_HFSS2 se cumpla con holgura; un valle de η dentro del canal (como el 0,32 de US3_PS4_2_1 en 8,137 GHz) la refutaría.
- El retardo de grupo radiado, la fase y la dispersión se calcularán con `hfss/analysis/element_hfss_patterns.py` sobre los mismos ficheros; no se pre-registra un valor.

### Regla de decisión para la siguiente iteración

1. **Mínimo en 7,86–7,90 GHz y peor S11 por encima de −10 dB solo por el desplazamiento** (η plana, sin segundo modo, forma de la curva como en openEMS): la siguiente iteración es `patch_L`, **como variante nueva**, con la pendiente medida en US3_PS6_1: **≈ 5,7 MHz por 0,01 mm** (US3_PS6 patch_L 6,29 mm y mínimo 8,005 GHz; US3_PS6_1 patch_L 6,32 mm y mínimo 7,988 GHz: −17 MHz por +0,03 mm). Reducir patch_L sube el mínimo; el tamaño del cambio se calcula con esa pendiente y el desvío observado, y la variante nueva se pre-registra por separado.
2. **Si el peor S11 empeora por otra causa** (cambio de forma, segundo modo dentro del canal, valle de η, retardo de grupo con signo negativo): análisis antes de iterar; no se aplica la regla de patch_L.
3. **Si el peor S11 es ≤ −10 dB y η_rad ≥ 0,6:** candidato, con la reserva del puerto (siguiente punto).

### Precauciones

- **Resolución de la lectura:** ΔS 0,01 en la convergencia adaptativa equivale a ≈ ±0,3 dB alrededor de −10 dB (20·log10(1,0316) = 0,27 dB). Una diferencia de menos de 0,3 dB con −10 dB no distingue cumplir de no cumplir; la convergencia de cada pasada se registra y se compara con 0,01.
- **El puerto lumped puede sesgar la lectura de S11.** Ningún resultado de este pre-registro pasa a `HFSS_VALIDATED` en adaptación sin el **contraste con wave port**. Mientras tanto, la procedencia es `EM_SIMULATED` (HFSS con puerto lumped).
- El borde superior del canal es la zona de mayor riesgo: la banda a −10 dB acaba solo 7–30 MHz por encima de 8,2368 GHz en la base desplazada.

## R2. Array 1x5 (paso nominal 18,2 mm)

**Todo lo de esta sección es extrapolación a partir de otros diseños, no resultado de US3_PS6_4.**

### Geometría

El parche de US3_PS6_4 mide 14,00 mm en x (dirección del array) frente a 11,42 mm de US3_PS4_2_1 y de P01_MS2, con el parásito de 13,58 mm. Al paso de 18,2 mm el hueco entre parches es:

| Diseño | Ancho de parche en x | Hueco a 18,2 mm |
|---|---|---|
| US3_PS4_2_1 / P01_MS2 | 11,42 mm | 6,78 mm |
| US3_PS6_4 | 14,00 mm | **4,20 mm** |

Para repetir el hueco de 6,78 mm haría falta un paso de 20,78 mm, fuera de la rejilla prevista de `arr_d` (16,5–20,5 mm, con 18,2 mm añadido). Un hueco de 4,20 mm equivale en los otros diseños a un paso de 15,62 mm.

### Datos de partida (recalculados de `array_pitch_sweep_hfss.json`)

Acoplamiento entre vecinos (peor caso del canal, en dB, frente al paso) y S11 activo a broadside (peor caso, theta0 = 0°):

| Array | Paso 16,5 mm | Paso 18,2 mm | Pendiente local del acoplo |
|---|---|---|---|
| US3_PS4_2_1 | −15,32 dB (activo −8,70) | **−18,27 dB** (activo −10,04) | −1,75 dB/mm (16,5–18,5); −2,04 (18,5–19,5); ajuste global −1,86 |
| P01_MS2 | −14,30 dB (activo −8,35) | −16,90 dB (activo −9,27) | −1,26 dB/mm (13,5–15,5); −1,55 (15,5–20,5); ajuste global −1,48 |

En P01_MS2, interpolando (sin extrapolar) al paso de 15,62 mm, que da el mismo hueco de 4,20 mm, el acoplo es de −13,0 dB y el S11 activo a broadside es de −7,9 dB.

### Extrapolación para US3_PS6_4 al paso de 18,2 mm

- **Acoplo vecino ≈ −13…−15 dB**, frente a −18,3 dB de US3_PS4_2_1 al mismo paso. Método: de −18,27 dB a 18,2 mm se resta 2,58 mm de hueco con −1,3 a −1,8 dB/mm, que da −14,9 a −13,6 dB; el dato interpolado de P01_MS2 al mismo hueco (−13,0 dB) cae en el extremo pesimista. Es una extrapolación: ninguno de los arrays simulados llega a un hueco de 4,2 mm con un elemento de este tipo, y el tramo estimado queda fuera del rango simulado de US3_PS4_2_1 (hueco mínimo 5,08 mm).
- **S11 activo a broadside probablemente peor que −10 dB**, en torno a −8 dB (rango plausible −7,5…−9,5 dB). Método: US3_PS4_2_1 da −8,70 dB a 16,5 mm y −10,04 dB a 18,2 mm (≈ −0,5 a −0,8 dB/mm); llevarlo a 15,62 mm da −8,0 a −8,3 dB; P01_MS2 interpolado da −7,9 dB al mismo hueco. El S11 del elemento aislado (≈ −10,3 dB tras el desplazamiento) no compensa este aumento del acoplo.
- **Incertidumbres que no se cuantifican:** el elemento es distinto (mayor ancho, otra Z de entrada y otro patrón), el acoplo no es solo función del hueco, el array de US3_PS4_2_1 **no estaba convergido** (15 pasadas con ΔS 0,012–0,021 frente a 0,01; 0,019 a 18,2 mm) y el de P01_MS2 no tiene datos de convergencia.
- **Qué lo confirmaría o lo refutaría:** el `array_pitch_sweep_hfss.json` y el `array_analysis_*.json` de `ARR1x5_US3_PS6_4_dparam` al paso de 18,2 mm. Se refuta la extrapolación si el acoplo vecino es mejor que −15 dB o el S11 activo a broadside es ≤ −10 dB en todos los puertos.
- La conclusión de esta sección no condiciona el elemento: la decisión sobre el elemento sigue las reglas de R1, y el array con paso de 18,2 mm se juzga después con sus propios resultados.

# Variantes de diseño (variants/)

Estado de todo lo de este directorio: **GEOMETRY_ONLY**. Son definiciones geométricas, no resultados EM. No contienen S11, ganancia, eficiencia, fase ni retardo de grupo.

## Esquema de `P01_R1.json`
Una variante = un JSON que lee el script de `em-solver`. Campos: `id`, `base_design` (clave de `designs.candidates()`), `evidence`, `substrate` (nombre, eps_r, tan_delta, h_mm, caja `size_mm`), `metal` (conductividad, grosor en m), `patch_polygon_mm` (4 vértices, antihorario, centrado en el origen), `slots_polygon_mm` (vacío), `feed` (sonda vertical concentrada, x/y en mm, Z0 = 50 ohm), `changed_vs_base` (única variable cambiada), `rationale`, `computation`.

## P01_R1: única variable cambiada, L (eje y)
| | Base P01 | P01_R1 |
|---|---|---|
| W (x) | 11.4213 mm (11.421267) | igual |
| L (y) | 8.2800 mm | **7.65 mm** |
| Sonda (x, y) | (0, -1.8216) mm | **(0, -1.6830) mm** |
| Material, h, caja, cobre | FR4 provisional 4.4 / 0.017 / 1.6 mm / 26x26 mm / 35 um | igual |

La regla de alimentación se conserva (inset relativo y_feed = -0.22 L, x = 0), así que la posición absoluta de la sonda cambia de -1.8216 a -1.6830 mm. No es una segunda variable de diseño, sino consecuencia de la regla.

### Cálculo (modelo de línea de transmisión, solo estimación geométrica)
1. `designs.rectangular_patch_dimensions()` da W = 11.4213 mm, eps_eff = 3.7382 y L = 8.2800 mm. Con las fórmulas de Hammerstad usadas allí: dL = 0.7132 mm por extremo, por lo que L_eff = L + 2 dL = 9.7065 mm.
2. Resonancia paralela medida (pico de Re(Zin)): 7.47 GHz (P01_OPENEMS_001/002) frente a f0 = 7.9872 GHz. Factor = 7.47/7.9872 = 0.93525.
3. Se escala L_eff (dL y eps_eff constantes, porque W, h y eps_r no cambian): L_eff' = 9.7065 x 0.93525 = 9.0780 mm. Entonces L' = L_eff' - 2 dL = **7.6515 mm**, redondeado a 0.01 mm: **7.65 mm**.
4. Escalado ingenuo L x 7.47/7.9872 = 7.7439 mm. Diferencia ingenua - justificada = +0.092 mm: el escalado ingenuo acorta poco porque ignora que 2 dL (1.43 mm) no escala con la frecuencia.
5. Con el mismo modelo, L = 7.65 mm daría resonancia en 7.9885 GHz; cada 0.01 mm de L desplaza ~8.8 MHz. Es consistencia interna del modelo, no predicción EM.

### Tolerancias y fabricación
7.65 mm está en una rejilla de 0.01 mm. La tolerancia real de grabado/PCB depende del fabricante y no se ha consultado; hay que pedirla y evaluarla con la sensibilidad anterior. La simulación debe usar exactamente los vértices del JSON. Parche 11.42 x 7.65 mm en caja 26x26 mm: margen al borde de 7.29 mm en x y 9.18 mm en y; sonda dentro del metal.

### Qué se espera (cualitativo, sin promesa de S11)
- El pico de Re(Zin) debería acercarse a f0 si la hipótesis de dL/eps_eff constantes y la identificación pico = resonancia se sostienen; es lo que hay que verificar con FDTD.
- La reactancia inductiva de la sonda (Im(Zin) positiva, ~+55-60 ohm en el pico base) sigue presente: cambiar L no la corrige. Puede desplazar el pico respecto de la resonancia real.
- Probablemente haga falta reajustar el inset después; sería otra variable en otra ronda. No se promete S11 ni cobertura de banda.

## Procedencia de los números
| Dato | Fichero |
|---|---|
| W, L, eps_eff, dL, regla -0.22 L, material, caja, cobre | `designs.py` (`rectangular_patch_dimensions`, `candidates()`, constantes) |
| Pico Re(Zin) 7.47 GHz (~54.5-54.9 ohm), Im ~ +55-60 ohm, min S11 -8.9/-8.0 dB a 7.625 GHz | `em/wideband_reanalysis/P01_OPENEMS_00{1,2}_6to10GHz.{csv,json}` (válido 6.98-9.0 GHz) |
| Resto del cálculo | `computation` en `P01_R1.json` |

## Aclaración pendiente sobre P01_R1: de dónde sale «7,9885 GHz»
La cifra de 7,9885 GHz del punto 5 del cálculo de P01_R1 **no es una predicción pura de Hammerstad**. L_eff se escaló desde la resonancia medida en FDTD (7,47 GHz), así que la cifra queda anclada a ese dato por construcción: es una comprobación de consistencia del escalado, no una validación independiente. Hammerstad sin ancla, aplicado a P01 base (L = 8,28 mm), da una resonancia de ~8,54 GHz (cifra aportada por el orquestador; no se ha reejecutado aquí), muy lejos de los 7,47 GHz medidos. El resultado EM de P01_R1_OPENEMS_003 (fr del ajuste 7,961 GHz, pico de Re(Zin) en 7,955 GHz) confirma el escalado empírico, no el modelo analítico.

## P01_R2: punto de diseño de adaptación (segundo y último refinamiento de P01)
Estado del fichero de geometría: **GEOMETRY_ONLY**. Resultado EM: [`em/P01_R2_OPENEMS_004`](../em/P01_R2_OPENEMS_004/) (`EM_SIMULATED`, ver `reports/claude_run_004.md`). **Predicción frente a resultado:** el modelo de guía predijo un peor caso de −7,13 dB en el borde superior con R_pico 85,7 Ω; la FDTD dio −6,53 dB en el borde inferior, con R ajustado de 101,9 Ω (+19 %), Q 13,0, fr 7,721 GHz y Ls 1,232 nH. El modelo sirve como guía cualitativa, no como predicción cuantitativa. Fichero: `P01_R2.json`, mismo esquema que `P01_R1.json`. Mismo material, W, placa 26x26 mm y sonda vertical concentrada de 50 ohm con x = 0.

| | Base P01 | P01_R1 | **P01_R2** |
|---|---|---|---|
| W (x) | 11,4213 mm | igual | igual |
| L (y) | 8,28 mm | 7,65 mm | **7,95 mm** |
| s/L (sonda) | 0,22 | 0,22 | **0,34** |
| Sonda y | -1,8216 mm | -1,6830 mm | **-2,7030 mm** |
| Distancia sonda-borde del parche | 2,32 mm | 2,14 mm | **1,272 mm** |

### Dos parámetros ligados, un solo objetivo
Cambian L y la posición de la sonda a la vez, ambos derivados del mismo objetivo: minimizar el peor |S11| en 7,7376-8,2368 GHz con una Ls ≈ 1,2 nH que no se puede quitar (modelo de guía ajustado a P01_R1_OPENEMS_003). Compensar esa reactancia serie exige operar por encima de la resonancia (fr por debajo del canal) con R_pico mayor que 50 ohm. **Con una sola simulación no se podrá atribuir el efecto a cada parámetro por separado.**

### (a) Sonda: R(s) = R_edge sin²(π s/L)
- R_edge = 45,37 / sin²(π·0,22) = **111,7 ohm** (calibrado con el único dato de P01_R1). Con el ajuste de P01 base sale 125,7 ohm (+12 %), lo que da una idea de la incertidumbre.
- s/L = 0,34 → R_pico = **85,7 ohm** (96,6 ohm con la calibración de P01 base).
- Límite del modelo: es una cavidad de un solo modo calibrada con un punto. No incluye modos superiores, campo de borde ni cambios de Ls con la posición, y pierde validez cerca del borde. R no puede superar ≈ R_edge; la curva es plana cerca del borde, así que cada mm adicional hacia el borde aporta cada vez menos R.

### (b) L: escalado de L_eff
- L_eff = L + 2 dL, con dL = 0,7132 mm. Se mantiene fr·L_eff constante desde P01_R1.
- Ancla: **fr del ajuste, 7,961 GHz**, y no el pico muestreado de 7,955 GHz. Es el parámetro del modelo con el que se evalúa; la diferencia de 6 MHz es menor que la rejilla de 5 MHz.
- Comprobación: fr·L_eff vale 72,26 (P01_R1) y 72,48 GHz·mm (P01 base), una diferencia del 0,3 %, equivalente a ±23 MHz en fr.
- L = 7,95 mm → **fr ≈ 7,706 GHz**. Para 7,67 GHz haría falta L = 7,99 mm.
- Por qué 7,706 y no 7,67 GHz: con R_pico ≈ 86 ohm, el óptimo del modelo está en ~7,71 GHz. Los 7,67 GHz corresponden a R_pico ≈ 100 ohm, que exigiría s/L = 0,395 y dejaría la sonda a ~0,84 mm del borde.

### Evaluación con el modelo de guía (no es una predicción EM)
Parámetros: R0 = 5,64 ohm, Ls = 1,2007 nH, Q = 13,5, R = 85,7 ohm, fr = 7,706 GHz. Cálculo con `em/fit_patch_circuit.py` (`model`, `worst_in_band_db`), 300 puntos en banda.
- Peor caso nominal: **-7,13 dB**, en el borde superior (8,2368 GHz). Margen ≈ 1,1 dB sobre -6 dB. Con el mismo modelo, el ajuste de P01_R1 da -3,05 dB frente a -3,12 dB en la FDTD.
- Sensibilidad (una variable cada vez, peor caso en dB):

| Variación | Peor caso |
|---|---|
| Q ×0,85 / ×1,15 | -7,26 / **-5,71** |
| Ls ×0,9 / ×1,1 | -7,90 / -6,27 |
| fr -50 / +50 MHz | -6,15 / -6,19 |
| R ×0,8 / ×0,9 / ×1,1 / ×1,2 | **-5,21** / -6,11 / -7,16 / -6,89 |
| R con R_edge de P01 base (96,6 ohm) | -7,10 |

- Combinando las esquinas (Q ±15 %, Ls ±10 %, fr ±50 MHz, y R ±15 %) el peor caso baja a **-3,5 dB** (-4,3 dB sin variar R). El margen sobre -6 dB es fino y depende sobre todo de acertar R_pico y Q.
- −10 dB en todo el canal no es alcanzable con este modelo y Q = 13,5.

### Fabricabilidad
- Parche 11,42 x 7,95 mm; margen a la caja de 26 x 26 mm de 7,29 mm en x y 9,03 mm en y.
- La sonda queda a **1,272 mm del borde del parche** (y = -3,975 mm) y a 6,68 mm del borde opuesto. Es el compromiso: R_pico ≈ 100 ohm (peor caso ≈ -8 dB en el modelo) pondría la sonda a ~0,84 mm del borde, y por encima se aproxima al borde y se pierde la validez del modelo, así que se descartó.
- El pad o la vía de un conector necesita su anillo de cobre y su holgura respecto del borde del parche. No se han consultado reglas de fabricante ni de conector, y no se dan cifras: hay que comprobar que el pad completo cabe en 2 x 1,272 mm menos la holgura. Si no cabe, hay que bajar s/L (menos R, menos margen en S11) o cambiar la topología de alimentación.
- Tolerancias: sensibilidad de fr ≈ 8,8 MHz por 0,01 mm de L (modelo de P01_R1) y de R ≈ 3 ohm por 0,01 de s/L en este punto (dR/d(s/L) ≈ 296 ohm). Las tolerancias reales de grabado y taladro no se han consultado.

### Riesgos
1. Calibración de R_edge con un solo punto (±12 % visible entre P01 y P01_R1); el peor caso del modelo con R ×0,8 es -5,2 dB.
2. Q real puede ser mayor; Q +15 % → -5,7 dB.
3. Ls puede cambiar al mover la sonda y no está en el modelo.
4. La FDTD usa un puerto concentrado ideal; su Ls no corresponde a un conector real.
5. fr predicha con ±23 MHz de incertidumbre de escalado; mover la sonda puede desplazarla más.
6. FR4 provisional (eps_r y tan_delta no medidos).

## P02_MS1 y P03_MS1: elementos con línea microstrip de 50 Ω e inset (ronda Claude 6)
Estado de los dos ficheros: **GEOMETRY_ONLY**. No hay S11, ganancia, fase ni retardo de grupo. Son **primeras iteraciones**: la adaptación es el punto más incierto.

**Decisión del propietario:** alimentar P02 y P03 con una línea microstrip que acaba en un conector SMA en el borde de la placa. El SMA se modela solo como un puerto de 50 Ω en el plano y = −13 mm (borde de placa); el cuerpo del conector no se modela (no hay referencia de pieza).

**Esquema.** Igual que `P01_R2.json`, con estos cambios:
- `patch_polygon_mm`: parche **ya con las muescas del inset recortadas** (no convexo, antihorario).
- `slots_polygon_mm`: `[ [ ... ] ]` con la U (P02) o el hexágono interior (P03).
- `feed.type = "microstrip_inset_edge"`, con `line_width_mm`, `line_x_mm` = 0, `line_start_y_mm` = −13, `line_end_y_mm`, `notch_gap_mm`, `inset_depth_mm` y `connector`.
- La línea es un **rectángulo separado** [x ± w/2, y de −13 a `line_end_y_mm`], que añade `em-solver`. Toca el parche a lo largo de su extremo, en el fondo del inset (`line_end_y_mm` coincide con la coordenada y del fondo de la muesca en el polígono).

### Parámetros comunes
| | Valor | Origen |
|---|---|---|
| Material, h, cobre, placa | FR4 provisional 4,4 / 0,017, 1,6 mm, 35 µm, 26×26 mm, masa completa | igual que P01 |
| Ancho de línea w | **3,02 mm** | Hammerstad–Jensen, εr 4,4, h 1,6 mm, t 35 µm |
| εeff cuasi-estático | 3,331 | mismo cálculo |
| Gap de muesca g | **0,5 mm** | ver abajo |
| Profundidad de inset y0 | **2,0 mm** (desde el borde radiante y = −L/2) | cos² con R_edge de sondas, con ajuste de cobertura |
| Muesca | ancho w + 2g = 4,02 mm, de y = borde a y = borde + y0 | |
| Plano del puerto | y = −13 mm, línea a lo largo de +y, x = 0 | |

### Ancho de la línea de 50 Ω
Hammerstad–Jensen con corrección de grosor. Con u = w/h: f(u) = 6 + (2π−6)·exp(−(30,666/u)^0,7528); Z01 = (η0/2π)·ln(f/u + √(1+(2/u)²)); εeff = (εr+1)/2 + (εr−1)/2·(1+10/u)^(−a·b), con a y b de la fórmula original (en el `computation` de los JSON); Z0 = Z01(u_r)/√εeff(u_r). Corrección de grosor: Δu1 = (t/πh)·ln(1 + 4e/((t/h)·coth²√(6,517u))), Δu_r = ½(1 + 1/cosh√(εr−1))·Δu1.
- Resolviendo Z0 = 50 Ω: **w/h = 1,886, w = 3,017 mm → 3,02 mm**; εeff = 3,331. Sin grosor (t = 0) sale 3,062 mm, igual que la síntesis de Hammerstad 1975 (w/h = 1,913). El cobre de 35 µm estrecha la línea 0,045 mm.
- Es un valor cuasi-estático. La dispersión de Getsinger sube εeff a ~3,64–3,67 en el canal y cambia Z0 unos pocos por ciento; no está corregido. εr es provisional.

### Gap de muesca y fabricabilidad
g = 0,5 mm es el mínimo que fija el encargo. Se usa también como ancho de la ranura de la U y como holgura mínima, para que el layout tenga una sola dimensión mínima. **No se ha consultado ningún fabricante ni se inventa ninguna regla**: hay que confirmar con la casa de PCB elegida que 0,5 mm (y, en P03, una lengüeta de cobre de 0,59 mm) es fabricable. Para el FDTD, g = 0,5 mm son ~1,4 celdas con la malla `base` (0,35 mm): `em-solver` necesita líneas de malla locales en las paredes de la muesca (g/3 o mejor).

### Profundidad de inset
Ley de cavidad R(y0) = R_edge·cos²(π y0/L), con y0 medido desde el borde radiante.
- R_edge de sondas: 111,7 Ω (P01_R1, s/L 0,22 → 45,4 Ω), 125,7 Ω (P01 base) y 132,7 Ω (ajuste de P01_R2_OPENEMS_004, 101,9 Ω en s/L 0,34). Rango usado: 110–135 Ω; punto medio 123 Ω.
- Para 50 Ω con L = 7,65 mm: y0 = 2,02 / 2,14 / 2,23 mm (R_edge 110 / 123 / 135 Ω).
- **Elegido y0 = 2,0 mm** (y0/L = 0,261): extremo bajo del rango cos², desplazado ~0,14 mm hacia la alternativa cos⁴ (abajo) para acotar el peor caso. R esperada en y0 = 2,0 mm: **51–63 Ω** con cos² y **24–29 Ω** con cos⁴.
- **Incertidumbre:** R_edge sale de **sondas, no de borde**. Con inset, el borde radiante, la muesca y la inductancia de unión cambian la admitancia. La literatura (Basilio et al., 2001; citada de memoria, **no comprobada aquí**) indica que para muescas estrechas R(y0) se parece más a cos⁴, lo que exigiría y0 = 1,48–1,65 mm. La simulación sirve como punto de calibración, y la siguiente iteración debería ajustar y0 con el R medido.

### P02_MS1: parche con U-slot
| | designs.py (P02) | **P02_MS1** |
|---|---|---|
| W (x) | 11,4213 mm | igual (11,4213 mm) |
| L (y) | 8,28 mm | **7,65 mm** (ancla de P01_R1: fr de ajuste 7,961 GHz sin ranura) |
| U-slot | x ±0,275 W, y de −0,08 L a +0,36 L, t 0,35 mm | mismas reglas con L = 7,65 mm: x ±3,141 mm, y de −0,612 a +2,754 mm, **t 0,5 mm** |
| Alimentación | sonda en y = −0,22 L | **línea 3,02 mm, inset 2,0 mm, gap 0,5 mm**, `line_end_y` = −1,825 mm |

- **La U se abre hacia +y** (borde radiante lejano), con la base del lado de la línea. Los brazos quedan paralelos a la corriente del modo TM10 (eje y). Con la U abierta hacia −y, la muesca y la línea entrarían en su boca y compartirían metal estrecho con la ranura.
- Resonancias esperadas, **sin promesa de valores**: (1) modo del parche a lo largo de y, anclado en L = 7,65 mm; la ranura y las muescas alargan el camino de corriente y es de esperar que lo bajen, en una cantidad no estimada. (2) Modo de la U: línea central de ~12,0 mm; la regla de media onda da del orden de 6,8–7,6 GHz según el εeff supuesto (3,33 o 2,7), así que puede quedar en el borde inferior del canal o por debajo. Es una estimación tosca. Si los dos modos se acoplan puede haber una doble resonancia; también puede haber un valle entre modos o un modo fuera de banda.

### P03_MS1: parche hexagonal con ranura hexagonal
| | designs.py (P03) | **P03_MS1** |
|---|---|---|
| Radio del hexágono (circunradio) | 0,53 W = 6,0535 mm | **5,2 mm** (apotema 4,5033 mm; entre lados planos, 9,007 mm) |
| Orientación | vértices en 0°, 60°… | igual: lados planos hacia ±y, vértices hacia ±x. El lado plano inferior (5,2 mm) recibe la línea |
| Ranura hexagonal | radio 1,1 mm, centrada | igual |
| Alimentación | sonda en y = −0,42 r | **línea 3,02 mm, inset 2,0 mm, gap 0,5 mm**, `line_end_y` = −2,503332 mm |

**Dimensionado del radio.** Es una aproximación con dos estimaciones, no una predicción.
- Círculo de igual área: (3√3/2)·r² = π·a², es decir r = 1,0996·a. Modo TM11 con radio efectivo, fr = 1,8412·c/(2π·a_e·√εr) y a_e = a·√(1 + (2h/(π a εr))·(ln(πa/2h) + 1,7726)), fórmula de franja de Garg/Bahl citada de memoria.
- **A (modelo puro):** fr = f0 → a = 4,871 mm, a_e = 5,243 mm, **r = 5,357 mm**.
- **B (con el sesgo de P01):** el parche P01 resonó un 6,5 % por debajo de su predicción de línea (7,47 frente a 7,9872 GHz). Se escala a_e por 0,93525 (el mismo procedimiento de P01_R1) → a = 4,540 mm, **r = 4,993 mm**. Supone que la fórmula circular tiene el mismo sesgo que la rectangular, lo que **no está establecido**.
- Con **r = 5,2 mm**: modelo A da 8,216 GHz y modelo B da 7,684 GHz, que acotan el canal (7,7376–8,2368 GHz). Son aritmética de modelo, sin la ranura central ni la muesca, que bajarán la frecuencia. **Es más probable que el modo quede por debajo de f0 que por encima.**
- r = 5,2 mm es también casi el mínimo que deja cobre junto a la muesca: se pide ≥ 0,5 mm de tira medida perpendicular al lado oblicuo, lo que da r ≥ 5,17 mm. Con un vértice hacia −y, la muesca no cabría hasta unos 1,5 mm de profundidad.
- Inset: se usa el mismo (y0 = 2,0 mm) por instrucción. Con modelo Bessel TM11 y con cos² sobre la longitud entre lados planos, y0 para 50 Ω sale de 2,12 a 2,63 mm, así que **R en y0 = 2,0 mm es probablemente >50 Ω**: 54–66 Ω (Bessel) o 65–79 Ω (cos²). R_edge del hexágono se supone igual al de los parches rectangulares (no establecido).
- Resonancia esperada: un modo principal TM11 a lo largo de y, sin segundo modo útil previsto en el canal. La ranura hexagonal está en el centro, donde el campo E del modo es nulo y la corriente máxima, y carga inductivamente (efecto no estimado).

### Comprobaciones geométricas (script en Python puro, con intersección de segmentos, punto en polígono y distancias segmento–segmento; no es un fichero del repo)
| Comprobación | P02_MS1 | P03_MS1 |
|---|---|---|
| Parche y ranura: polígonos simples, antihorarios | sí | sí |
| Vértices de la ranura dentro del metal | sí | sí |
| Ranura–borde del parche (incluye muescas) | 1,071 mm | 1,551 mm (a la muesca; al borde exterior 3,55 mm) |
| Ranura–muesca | 1,213 mm | 1,551 mm |
| Línea–pared de la muesca (= g) | 0,5 mm | 0,5 mm |
| Pared de muesca–bordes exteriores no adyacentes | 3,70 mm | 0,59 mm (lengüeta junto al vértice) |
| Margen del parche al borde de la placa (x / y) | 7,29 / 9,175 mm | 7,80 / 8,497 mm |
| La línea toca y = −13 | sí | sí |
| La línea toca el parche en `line_end_y` | −1,825 mm | −2,503332 mm |
| Línea fuera del parche | 9,175 mm | 8,497 mm |

### Riesgos
1. **Adaptación:** R_edge viene de sondas; hay un factor ~2 entre las leyes cos² y cos⁴ en y0, y el resultado puede estar mal adaptado en cualquier sentido. Es una calibración.
2. **Frecuencia:** inset, ranura y línea cargan el parche y la bajarán en una cantidad no estimada. En P03 la incertidumbre del radio es de ~7 %.
3. **La muesca ocupa el 35 % del ancho del parche** en P02 (4,02 de 11,42 mm), y la línea de 3,02 mm es ancha frente al parche; la discontinuidad de unión y la radiación de la propia línea no son despreciables.
4. **Puerto:** el plano de referencia es el borde de placa y no hay cuerpo de SMA ni transición del pin. Un puerto de línea (MSL) es más adecuado que un puerto concentrado en el extremo abierto; lo decide `em-solver`. La fase de S11 incluye ~9 mm de línea.
5. **Fabricación:** 0,5 mm (gap, ancho de ranura) y la lengüeta de 0,59 mm de P03 no están contrastados con ningún fabricante.
6. **Malla:** gap y ranura de 0,5 mm y el agujero hexagonal de P03 (lado 1,1 mm, bordes oblicuos en escalera) necesitan celdas ≤ ~0,25–0,3 mm.
7. FR4 provisional; sin campo lejano, así que ni ganancia ni eficiencia ni retardo radiado.

## P03_MS2: hexagonal ranurado con alimentación de borde y transformador λ/4 (ronda Claude 7)
Estado: **GEOMETRY_ONLY**. Fichero: [`P03_MS2.json`](P03_MS2.json). Revisión fabricable y mallable de P03_MS1, que se conserva **sin simular** como registro. No hay S11, ganancia, fase ni retardo de grupo.

**Motivo.** P02_MS1 (`EM_SIMULATED`, `reports/claude_run_006.md`), con inset de 2,0 mm y muesca de 4,02 mm, dio |S11| ≈ −0,7 dB en el canal y ~2 Ω en la base del inset a f0 (resonancia probablemente bajo 7 GHz, no establecida). En P03_MS1 la muesca de 4,02 mm ocupa un lado plano de 5,2 mm y deja lengüetas de 0,59 mm que una malla de 0,25–0,46 mm no resuelve. P03_MS2 elimina la muesca.

### Geometría
| | P03_MS1 | **P03_MS2** |
|---|---|---|
| Circunradio del hexágono | 5,2 mm | **4,8 mm** (apotema 4,1569 mm; lado plano 4,8 mm) |
| Centro del parche | (0, 0) | **(0, +3,3) mm** |
| Ranura hexagonal | r = 1,1 mm | **r = 1,1 mm** (lado 1,1; 1,905 mm entre lados planos; 3,20 mm de cobre alrededor) |
| Alimentación | línea + inset 2,0 mm, gap 0,5 mm | `microstrip_edge_qw`: **sin muesca** |
| Línea de 50 Ω | 3,02 mm, y de −13 a −2,50 | 3,02 mm, y de **−13 a −6,0769** (6,923 mm) |
| Transformador λ/4 | no | **0,72 mm × 5,22 mm** (Zt = 97,1 Ω), y de −6,0769 a −0,8569 |
| Placa, material, cobre | 26×26 mm, FR4 4,4 / 0,017 / 1,6 mm, 35 µm | igual |

`feed_polygons_mm` trae la línea y el transformador como rectángulos antihorarios explícitos. Comparten el borde y = −6,076922 (línea–transformador) y y = −0,856922 (transformador–parche) con coordenadas idénticas a las del parche. El transformador cae en el centro del lado plano, con 2,04 mm de cobre a cada lado.

**Por qué el parche está en y = +3,3 mm.** Con el parche en el origen la sección de 50 Ω mediría 3,6 mm. `add_edge_port` de `em/patch_openems.py` exige que el plano de medida del puerto MSL esté a ≥ h de la fuente y del parche, y avisa por debajo de 2h = 3,2 mm. Con 6,92 mm el plano de medida queda a 3,71 mm del plano de lanzamiento y a 3,21 mm de la fuente y del transformador. El margen superior a la placa es 5,54 mm (3,5 h). Si se prefiere el parche centrado, `em-solver` tendría que relajar esa condición.

### Radio: dos estimaciones y elección
Mismo modelo que P03_MS1 (círculo de igual área, TM11, franja de Garg/Bahl citada de memoria).
| r (mm) | A: modelo puro | B: con sesgo de P01 (×0,93525) |
|---|---|---|
| 4,8 | 8,865 GHz | 8,291 GHz |
| 5,0 | 8,528 | 7,976 |
| 5,2 (P03_MS1) | 8,216 | 7,684 |
| 5,357 (A = f0) | 7,987 | 7,469 |

- La ranura central carga el modo. Como indicador (no predicción), la fracción de energía magnética del modo TM11 ideal bajo la huella del agujero es 10,5 % (fracción de área 5,3 %). Un desplazamiento relativo de hasta ~−5 % es plausible. No es un resultado EM.
- **Elegido r = 4,8 mm.** B menos hasta un 5 % de carga da ~7,9–8,3 GHz; A menos lo mismo da ~8,4–8,9 GHz. Es decir, queda en f0 o por encima, como se pidió (la excitación de la próxima simulación cubrirá ~5,5–9,5 GHz). P03_MS1, con r = 5,2 mm, ya estaba bajo f0 en B antes de contar la ranura. El sesgo de la fórmula circular no está establecido: incertidumbre de fr ±5 % o más.
- **Ranura:** se mantiene r = 1,1 mm (trazabilidad con `designs.py`). Todos sus huecos son ≥ 1,9 mm (≥ 6 celdas a 0,3 mm). Agrandarla bajaría más la frecuencia.

### R_borde: hipótesis a calibrar, no un dato
- **Rango asumido: 110–320 Ω; nominal 188 Ω** (media geométrica).
- **Cota baja, 110 Ω:** R_borde derivado de las sondas de P01 (111,7 / 125,7 / 132,7 Ω; `em/circuit_fits/*.json`), sin escalar. Es una extrapolación de una sonda interior, no un valor de borde.
- **Cota alta, 320 Ω:** 135 Ω × (11,42 mm de ancho de P01 / 4,8 mm del lado plano) = 321 Ω, con conductancia de borde proporcional al ancho radiante. Supone que solo radia el lado plano; los lados oblicuos del hexágono también radian en un modo TM11, lo que apunta a valores menores.
- **Descartado:** la conductancia G1 de la cavidad (integral de Balanis, calculada aquí) da 516 Ω para P01, es decir 3,8–4,7 veces más que el valor derivado de las sondas, así que sus valores absolutos no sirven. Escalar P01 con su cociente de G1 daría ~730 Ω, que el transformador no puede adaptar (Zt = 191 Ω). La literatura da valores de borde mayores que 110–135 Ω, como señaló el orquestador; no se cita ninguna cifra porque no se ha comprobado ninguna.

### Transformador
- **Ancho.** Zt = √(50·188,5) = 97,1 Ω. Con Hammerstad–Jensen y corrección de grosor (las mismas fórmulas que la línea de 50 Ω), w = **0,72 mm** da 97,09 Ω (w/h = 0,45, εeff estática 3,044).
- **Longitud.** εeff con dispersión de Getsinger, εeff(f) = εr − (εr − εeff0)/(1 + G(f/fp)²), G = 0,6 + 0,009·Z0, fp = Z0/(2µ0h) = 24,1 GHz. Da εeff = 3,232 a f0, λg/4 = **5,22 mm** (estática: 5,38 mm). La diferencia (0,16 mm, 2,7° de fase de línea) es de segundo orden para un transformador λ/4. No incluye el efecto del escalón 50→97 Ω ni de la unión con el parche.
- **Cabe:** el transformador (5,22 mm) más la línea (6,92 mm) ocupan los 12,14 mm entre el borde de placa y el borde del parche. No choca con nada: la ranura queda a 3,20 mm del transformador.

### Efecto de R_borde en el transformador
| R_borde (Ω) | Zt ideal (Ω) | w ideal (mm) | Zin tras Zt = 97,1 Ω (aritmética) | desadaptación aritmética |
|---|---|---|---|---|
| 110 | 74,2 | 1,41 | 85,7 Ω | −11,6 dB |
| 150 | 86,6 | 0,98 | 62,8 Ω | −18,9 dB |
| 188,5 | 97,1 | 0,72 | 50 Ω | ~0 (por construcción) |
| 250 | 111,8 | ~0,47 | 37,7 Ω | −17,1 dB |
| 320 | 126,5 | 0,30 | 29,5 Ω | −11,8 dB |
| 500 (fuera de la hipótesis) | 158,1 | 0,11 | 18,9 Ω | −6,9 dB |

Esto es aritmética de la hipótesis (Zin = Zt²/R con línea ideal a f0), **no el S11 del diseño**: ignora la reactancia del parche, la banda, la unión, la ranura y las pérdidas. Para w ≥ 0,7 mm hace falta Zt ≤ ~98 Ω (R_borde ≤ ~192 Ω); para w ≥ 0,5 mm, Zt ≤ ~110 Ω (R_borde ≤ ~242 Ω). **Si R_borde supera ~300 Ω, un transformador λ/4 fabricable ya no la adapta** y habría que cambiar de topología.

### Comprobaciones geométricas (Python puro, sobre las coordenadas del JSON)
| Comprobación | Resultado |
|---|---|
| Parche, ranura, línea y transformador: polígonos simples, antihorarios | sí |
| Vértices de la ranura dentro del metal | sí |
| Ranura–borde del parche | 3,204 mm (≥ 0,7) |
| Ranura–transformador | 3,204 mm |
| Todo dentro de la placa | sí; margen del parche: 8,2 mm (x), 5,54 mm (arriba), 12,14 mm (abajo hasta el borde) |
| La línea toca y = −13 | sí |
| Línea–transformador comparten borde (ancho 0,72 dentro de 3,02) | sí, y = −6,076922 |
| El transformador toca el lado plano del parche, dentro de él | sí, y = −0,856922; cobre a cada lado 2,04 mm |
| Detalle de cobre mínimo / hueco mínimo | 0,72 mm (transformador) / 1,905 mm (ranura) |
| Geometría del puerto MSL con las constantes actuales (feed_shift 0,5; meas 3,71) | d_fuente = d_transformador = 3,21 mm (≥ 3,2) |

### Qué necesita `em-solver`
1. Un tipo `microstrip_edge_qw`: dibujar `feed_polygons_mm` tal cual, sin interpretar. `line_end_y_mm` coincide con `transformer_start_y_mm`; el puerto MSL debe usar el inicio del transformador (y no el borde del parche) como límite de la sección de 50 Ω. El parche ya no está centrado: ranura y NF2FF se centran en (0, 3,3) o en el origen según decida `em-solver`.
2. Malla: el transformador (0,72 mm) necesita ≥ 3 celdas de ancho (≤ 0,24 mm) o líneas en sus bordes y una central. La ranura (1,905 mm entre lados planos) necesita ≥ 6 celdas.
3. Excitación de ~5,5–9,5 GHz y compuerta de puerto (`PORT_INVALID`) según `reports/claude_run_006.md`.

### Riesgos
1. **R_borde (dominante):** rango asumido 110–320 Ω, factor ~3. Es un punto de calibración, no una adaptación. Resultado mediocre posible en cualquier sentido.
2. **Frecuencia:** ±5 % o más en fr. La línea de 3,02 mm queda como parte del circuito (la fase de S11 incluye 6,9 mm de línea y el transformador).
3. **Transformador estrecho (0,72 mm):** la tolerancia de grabado de ±0,05 mm mueve Zt unos ±5 Ω (estimación a partir de la tabla w–Z, no calculada aparte). La línea de 97 Ω radia y acopla algo; tampoco se incluyen el escalón 50→97 Ω ni la unión.
4. **Parche descentrado (y = +3,3 mm):** la placa es asimétrica en y (5,54 mm arriba, 12,14 mm abajo del parche), lo que afecta al patrón y a la corriente en el plano de masa; con parche centrado el puerto MSL no cabe.
5. **Puerto:** referencia en el borde de placa, sin cuerpo de SMA; el punto de lanzamiento de un SMA de borde real no se modela.
6. **Fabricación:** ningún fabricante consultado; 0,72 mm es el detalle mínimo de cobre y no hay huecos de cobre estrechos.
7. FR4 provisional; sin campo lejano, así que ni ganancia ni eficiencia ni retardo radiado.

## Serie U-slot sobre h = 2,07 mm: US0 y US1 (ronda Claude 12)
Estado de los dos ficheros: **GEOMETRY_ONLY**. No hay S11, ganancia, eficiencia, fase ni retardo. Familia `USLOT_PROBE_H207`; los ficheros `US0.json` y `US1.json` los genera [`uslot_family.py`](uslot_family.py) (función pura, sin openEMS) y los parámetros están explícitos en `uslot_params`.

**Dirección del propietario:** priorizar U-slots inspirados en el artículo, **variando una dimensión cada vez** y conservando alimentación y material al comparar; objetivo S11 ≤ −6 dB en toda la banda (preferido −10 dB), con convergencia comprobada antes de aceptar mejoras; eficiencia y retardo radiado cuando haya campos.

**Procedencia (importante).** El artículo EuCAP 2027 solo da: parche excitado por sonda, resonancia a lo largo de y, sustrato S1000H de 2,07 mm, εr ≈ 4,4–4,7 y tanδ ≈ 0,017. **No da dimensiones de parche, de ranuras ni posición de sonda.** Ninguna dimensión de esta serie procede del artículo, y las que salgan de una optimización tampoco se le atribuirán. Su elemento es un parche apilado con cavidad, parásito y peine de ranuras; un U-slot simple es **una aproximación de investigación, no una reproducción**.

### Decisiones comunes de la serie (orquestador; van también en `series_common` de cada JSON)
| | Valor |
|---|---|
| Alimentación | sonda vertical concentrada de 50 Ω (`probe_lumped_vertical`), x = 0, s/L = 0,34 |
| Material | FR4 homogéneo, εr 4,4, tanδ 0,017, **h = 2,07 mm** (espesor total del artículo; homogéneo es una aproximación de su pila de seis capas) |
| Cobre | 35 µm, 5,8e7 S/m |
| Placa | 26 × 26 mm centrada, masa completa (la del laboratorio, **no** la del artículo) |
| Regla de comparación | una sola dimensión de la U cambia por variante; parche, sonda y material fijos |

### US0: parche rectangular sin ranura (referencia, no se optimiza)
| | US0 | P01_R2 (h 1,6) |
|---|---|---|
| W (x) | 11,421266 mm | 11,421267 mm |
| L (y) | **7,67 mm** | 7,95 mm |
| Sonda (x, y) | (0, **−2,608**) mm, s/L 0,34 | (0, −2,703) mm |
| Distancia sonda–borde radiante | 1,227 mm | 1,272 mm |
| ε_eff Hammerstad | 3,654 | 3,738 |
| ΔL Hammerstad | 0,909 mm | 0,713 mm |

**Criterio.** La única evidencia EM de un parche con sonda que adaptó es P01_R2: fr de ajuste circuital 7,723 GHz (malla fina, 005), mínimo de S11 en ~8,05 GHz y peor caso en banda −6,29 dB. Se busca que US0 resuene en la **misma posición** (7,723 GHz) a h = 2,07 mm.
1. Hammerstad con h = 2,07 mm da ε_eff = 3,654 (antes 3,738) y ΔL = 0,909 mm (antes 0,713). Los dos efectos van en sentido opuesto sobre fr, de modo que L cambia poco.
2. El modelo puro de Hammerstad **no** reproduce el EM: a h = 1,6 mm da fr 8,27 GHz para L = 7,95 mm, frente a 7,723 GHz del ajuste EM. El cociente fr_EM/fr_Hammerstad vale 0,932 (P01_R1), 0,934 (P01_R2) y 0,935 (P01) para tres L distintas, es decir, es casi constante (±0,2 %). Se usa **k_cal = 0,93405** (el de P01_R2) como factor empírico, aplicado también a h = 2,07 mm.
3. Con k_cal: L + 2ΔL = k_cal · c / (2 √ε_eff · 7,723 GHz) = 9,484 mm, y L = 9,484 − 2 · 0,909 = **7,666 mm → 7,67 mm** (fr calibrada 7,720 GHz, a 3 MHz del objetivo; es la rejilla de 0,01 mm).
4. **W se conserva** (11,4213 mm): fija el ancho de la cavidad, la R_edge y la huella en x, y cambiarla añadiría una segunda variable. **s/L = 0,34 se conserva** porque la R de entrada del modo escala como R_edge·sin²(π s/L) y R_edge ∝ Q·h/(ε W L): con h un 29 % mayor y Q algo menor, R_edge queda del mismo orden (hipótesis, no verificada).

**Incertidumbre.** k_cal varía ±0,2 % entre tres puntos a h = 1,6 mm (~±15 MHz). La **extrapolación a h = 2,07 mm no está verificada** (más inductancia de sonda, otro campo de borde, FR4 homogéneo, sin calibración EM a ese espesor): orden de magnitud ±2–3 % en fr (~±200 MHz). Este valor es una estimación geométrica.

### US1: US0 más un U-slot (primera variante)
| Parámetro | Valor |
|---|---|
| Parche y sonda | igual que US0 |
| Orientación | base ⟂ y (a lo largo de x), brazos ∥ y, **abierta hacia +y** (borde opuesto a la sonda) |
| Ancho exterior Wu | 4,4 mm (x de −2,2 a 2,2) |
| Altura de brazos Lu | 3,2 mm |
| Anchura de ranura t | 0,8 mm |
| Base (borde exterior), y0 | −0,7 mm; U ocupa y de −0,7 a 2,5 mm |
| Longitud media de la U | Wu + 2 Lu − 2 t = 9,2 mm |

Vértices de la U (antihorario): (−2,2; −0,7), (2,2; −0,7), (2,2; 2,5), (1,4; 2,5), (1,4; 0,1), (−1,4; 0,1), (−1,4; 2,5), (−2,2; 2,5).

**Criterio de la longitud.** Se toma la longitud media de la U ≈ media longitud de onda guiada, l = c/(2 √ε_eff f) con ε_eff = 3,654 (el del parche: es una **hipótesis**, la ranura puede ver otra permitividad efectiva). Con f = 8,5 GHz sale l ≈ 9,2 mm, y la fórmula con l = 9,2 mm da **8,52 GHz**. La intención es colocar una segunda resonancia por encima de la del parche (~7,72 GHz en US0), de modo que ambas rodeen el canal 7,7376–8,2368 GHz y ensanchen la banda. Es una estimación de ordenación: **no tengo una regla verificada** que relacione l con la resonancia real de la U, que dependerá del acoplo con el parche y solo la dará la simulación.

**Criterio de la orientación (hipótesis).** Base cerca de la sonda y U abierta hacia +y deja la sonda fuera de la U, con cobre continuo entre la sonda y el borde radiante cercano, y una distancia sonda–ranura holgada. **No hay una regla verificada que decida entre abrir hacia la sonda o en sentido opuesto**; `open` es un parámetro de la familia para probar la otra orientación después. De la literatura de parches con U-slot solo recuerdo, sin cifras verificadas, que la U sirve para ensanchar la banda en sustratos gruesos y compensar la inductancia de la sonda; no se asume más.

**Criterio de la anchura y de los márgenes.** t = 0,8 mm (≥ 0,5 mm exigido, 0,7–1,0 mm preferible por malla). Márgenes calculados sobre la geometría:

| Comprobación | Valor | Exigido |
|---|---|---|
| Anchura de ranura | 0,8 mm | ≥ 0,5 |
| Cobre entre ranura y borde del parche (mínimo) | 1,335 mm (arriba) | ≥ 0,7 |
| Cobre lateral a cada lado | 3,511 mm | ≥ 0,7 |
| Isla de cobre entre brazos | 2,8 mm | ≥ 0,7 |
| Sonda–ranura (mínimo) | 1,908 mm | ≥ 1,0 |
| Sonda–borde del parche | 1,227 mm | ≥ 1,0 (aviso) |
| Polígonos simples, antihorarios, U dentro del metal, sonda fuera de la U | sí | sí |

Estos márgenes son criterios de diseño declarados; no se ha consultado ninguna regla de fabricante.

### `uslot_family.py`
Función pura (`build_variant`, `build_preset`, `derive`) y CLI. Valida polígonos simples, la U dentro del metal con margen, la sonda fuera de la ranura con margen y el parche dentro de la placa.
```
python variants/uslot_family.py --preset US0 --out variants/US0.json
python variants/uslot_family.py --preset US1 --out variants/US1.json
python variants/uslot_family.py --base variants/US1.json --set Lu=3.4 --id US2 --out variants/US2.json
python variants/uslot_family.py --verify variants/US1.json
```
`--set` acepta **una sola** clave por llamada (`L`, `W`, `s_over_L`, `Wu`, `Lu`, `t`, `y0`, `open`) y rellena `changed_vs_previous`. `y0` es la coordenada del borde exterior de la base; con `open=-y` los brazos se extienden hacia −y desde `y0`. `--verify` regenera el JSON desde `uslot_params` y lo compara byte a byte (US0 y US1 regeneran idénticos).

### Riesgos
1. **Ls de la sonda con h = 2,07 mm.** Si Ls ∝ h (hipótesis), pasa de ~1,3 a ~1,7 nH (X ≈ 65 → 85 Ω a f0). El modelo de guía (`GUIDE_MODEL`, no resultado EM) con esa Ls, Q 10,6–13 y R 80–125 Ω da un peor caso en banda de −4 a −5 dB en fr = 7,72 GHz. **US0 puede no cumplir −6 dB.** Con ese mismo modelo, bajar fr a ~7,6 GHz mejoraría el peor caso (~−6 dB), pero no se hace: US0 es una referencia sin optimizar y es una sola variable que se puede barrer.
2. **k_cal extrapolado** de 1,6 a 2,07 mm (±2–3 % en fr, no verificado).
3. **La resonancia de la U es una hipótesis** (λg/2 con ε_eff del parche); la U también perturba el modo del parche y mueve la fr de US1 respecto a US0.
4. **Orientación de la U** sin regla verificada; sonda a 1,227 mm del borde (acaso poco para un conector real, sin reglas de fabricante).
5. **Malla (para `em-solver`).** t = 0,8 mm necesita ≥ 4 celdas en la ranura (≤ 0,2 mm) o líneas en sus bordes; la isla de 2,8 mm y los brazos deben quedar resueltos. La malla fina de 005 (xy 0,35 mm) da solo ~2 celdas en la ranura. h = 2,07 mm: usar ≥ 10 celdas en el sustrato (0,207 mm) o líneas en las caras.
6. **FR4 homogéneo** frente a la pila de seis capas del artículo, con cavidad y rugosidad: no comparable en Q ni en eficiencia.
7. **Evidencia:** todo es `GEOMETRY_ONLY`; antes de aceptar cualquier mejora hace falta convergencia de malla, y −10 dB es objetivo, no resultado.

### Orden propuesto de barrido (una variable cada vez, tras simular US1)
Se parte de US1 y se acepta un cambio solo si mejora el peor |S11| en banda con convergencia de malla comprobada (dos mallas, diferencia de peor caso menor que el margen que se pretende ganar).

| # | Variable | Paso inicial | Rango válido (por márgenes) |
|---|---|---|---|
| 1 | Lu (longitud de brazos; mueve la resonancia de la U) | ±0,4 mm | 1,0–3,8 mm |
| 2 | Wu (ancho exterior de la U) | ±0,6 mm | 2,6–9,0 mm |
| 3 | t (anchura de ranura) | 0,6 → 1,0 mm (pasos de 0,2) | 0,5–1,2 mm |
| 4 | y0 (posición de la base) | ±0,5 mm | −1,4 mm a −0,1 mm con Lu 3,2 (y0 + Lu ≤ 3,13) |
| 5 | s_over_L (sonda; R de entrada) | ±0,03 | 0,30–0,36 (sonda a ≥ 1 mm del borde: 0,36 da 1,07 mm) |
| 6 | open (+y / −y) | binaria, con y0 reajustado | — |
| 7 | L (re-sintonía del parche; mueve la sonda por s/L fijo) | ±0,15 mm | ~7,3–8,0 mm |

Si US0 falla por la Ls de la sonda, la primera variable a barrer es L de US0 (pasos de 0,15 mm, hacia fr menor), antes de la U.

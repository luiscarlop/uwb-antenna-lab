# Revisión HFSS de P01_MS1 y US3_MS3 (propietario, 2026-11-13)

- **Datos de HFSS:** los exportó el propietario (commit `1093b2a`); ahora están en [`hfss/results_2026-11-13/`](../hfss/results_2026-11-13/). Hay una simulación por diseño.
- **No se facilitaron los datos de convergencia adaptativa** (número de pasadas y ΔS).
- **Modelo:** el que construye `hfss/claude_aedt_native_ch9.py`. Usa el mismo plano de referencia que openEMS: un puerto concentrado de 50 Ω al comienzo de la línea, en el borde de la placa.
- **Script de comparación:** [`hfss/compare_hfss_openems.py`](../hfss/compare_hfss_openems.py). Sus resultados están en [`hfss_vs_openems_2026-11-13.json`](../hfss/hfss_vs_openems_2026-11-13.json).

## S11
El barrido de HFSS va cada 1 MHz, así que las muestras más próximas a los extremos del canal son 7,738 y 8,236 GHz.

| | P01_MS1 HFSS | P01_MS1 openEMS (025/026) | US3_MS3 HFSS | US3_MS3 openEMS (023/024) |
|---|---|---|---|---|
| Peor S11 en el canal | **−9,36 dB** (7,738 GHz) | −8,34 / −8,17 dB | −6,80 dB (8,236 GHz) | −8,18 / −8,04 dB |
| Mínimo | −36,5 dB en **7,991 GHz** | 8,053 / 8,054 GHz | −15,7 dB en **7,906 GHz** | 7,979 / 7,986 GHz |
| Banda a −6 dB | 7,596 a más de 8,5 GHz | 7,62–8,5 GHz | 7,593–8,292 GHz | 7,64–8,39 GHz |
| Banda a −10 dB | **7,758–8,268 GHz (510 MHz)** | 7,80–8,34 GHz (~540 MHz) | 7,740–8,090 GHz (350 MHz) | 7,80–8,18 GHz (~380 MHz) |
| \|ΔΓ\| máx entre HFSS y openEMS (fina) en el canal | 0,10 | — | 0,13 | — |

Lo que se ve:
- **Los dos diseños cumplen −6 dB en todo el canal también en HFSS.** P01_MS1 tiene un margen de 3,4 dB y US3_MS3 de 0,8 dB.
- **P01_MS1 se queda muy cerca de −10 dB.** Solo lo incumplen unos 20 MHz en el borde inferior: la peor muestra es −9,36 dB.
- US3_MS3 tiene una banda de −10 dB más estrecha (350 MHz), inferior a los 499,2 MHz del canal.
- **Las resonancias salen entre un 0,8 y un 1,0 % más bajas en HFSS que en openEMS.** El desplazamiento es sistemático: −63 MHz en P01_MS1 y −73/−80 MHz en US3_MS3. Sirve como calibración de lo que se diseñe a partir de ahora con openEMS.

## Diagrama de radiación a f0 (HFSS, solo 7,9872 GHz)
La columna `GainTotal` del CSV no lleva unidades; se trata como ganancia lineal. Es ganancia, no ganancia realizada.

| | Ganancia en broadside | Máximo | Corte yz (plano E), donde +θ apunta hacia +y |
|---|---|---|---|
| P01_MS1 | 5,39 dBi | 5,64 dBi en θ = 10°, φ = 270° | pico en −10°, ancho a −3 dB de −65° a +30° |
| US3_MS3 | 4,71 dBi | 5,10 dBi en θ = 15°, φ = 275° | pico en −15°, ancho a −3 dB de −60° a +30° |

- En los dos diseños el haz está inclinado entre 10° y 15° hacia −y, el lado de la alimentación, igual que en openEMS (Dmax en θ = 15°, φ = 270°).
- Para medir el beam squint (cómo cambia esa dirección con la frecuencia) faltan los diagramas a 7,7376 y 8,2368 GHz. El barrido `Edges_and_f0` ya guarda esos campos.
- Por comparar: en openEMS la ganancia en broadside a f0 es 4,82 dBi (P01_MS1) y 4,17 dBi (US3_MS3), con un modelo de pérdidas σ constante. HFSS da +0,6 dB, con un modelo de tanδ constante salvo que se usara `sigma`.

## Propuestas (no simuladas)
- **US3_MS3, sugerencia del propietario (patch_L más corto):** para llevar el mínimo de 7,906 a 7,987 GHz (+1,0 %), patch_L pasaría de 6,502 a unos **6,417 mm** (−0,085 mm). Es un escalado con L + 2ΔL y ΔL = 0,909 mm, y no tiene en cuenta cómo la U carga el parche.
  - La mejora esperada es solo un peor caso más equilibrado.
  - Con 350 MHz a −10 dB, US3_MS3 **no** puede cumplir −10 dB en todo el canal sin ensanchar la banda.
- **P01_MS1, centrar la banda de −10 dB (centro actual en 8,013 GHz):** patch_L pasaría de 7,322 a unos **7,352 mm** (+0,030 mm). Quedarían unos 5 MHz de margen a cada lado.
  - La sensibilidad es de unos 8,8 MHz por cada 0,01 mm de L, así que la tolerancia de grabado se come ese margen.
  - Cumplir −10 dB en todo el canal sería frágil.

## Pendiente
1. Los datos de convergencia de HFSS (número de pasadas y ΔS) de los dos diseños.
2. RealizedGainTotal en 3D a 7,7376 y 8,2368 GHz, para medir el beam squint.
3. Decidir qué variables se cambian y en qué orden.

Estado: los dos siguen en `EM_SIMULATED`. Hay datos de HFSS, pero sin convergencia documentada todavía no se marcan `HFSS_VALIDATED`.

## Actualización (17:05): convergencia y diagramas en los extremos del canal
El propietario subió `Project1_*.conv` y `Gain * 3D.csv` (commit `6648401`). Se han movido a [`hfss/results_2026-11-13/`](../hfss/results_2026-11-13/); los 3D de tres frecuencias se llaman `Gain <D> 3D 3freq.csv` y el 3D anterior, solo a f0, `Gain <D> 3D f0.csv`.

### Convergencia adaptativa de HFSS (Setup_ch9, una sola frecuencia: 7,9872 GHz)
| | Pasadas | ΔS final (objetivo 0,02) | Elementos | ¿Convergido? |
|---|---|---|---|---|
| P01_MS1 | 9 de 15 | 0,0159 | 12 104 | sí |
| US3_MS3 | 8 de 15 | 0,0031 | 10 137 | sí |

- Las variables registradas en cada fichero `.conv` son las del script.
- **Ambos convergen con el criterio de HFSS.**
- Matices: la adaptación se hizo en una sola frecuencia, el barrido es interpolado, P01_MS1 cumple con poco margen (0,0159 frente a 0,02) y US3_MS3 no baja de forma monótona (0,025 → 0,037 → 0,003).

**Estado:** los dos pasan a `HFSS_VALIDATED`, **solo para el criterio de −6 dB en todo el canal**. Ese cumplimiento lo predicen openEMS (con dos mallas) y HFSS (convergido). No se valida −10 dB (ninguno lo cumple), ni el material (el FR4 es provisional), ni el conector (no se modela el SMA). La ganancia y el patrón son simulaciones, no medidas.

### Beam squint
Script: [`hfss/hfss_beam_squint.py`](../hfss/hfss_beam_squint.py). Resultados: [`hfss_beam_squint_2026-11-13.json`](../hfss/hfss_beam_squint_2026-11-13.json).

**Correspondencia confirmada por el propietario:** `GainTotal` es 7,9872 GHz, `GainTotal_1` es 7,7376 GHz y `GainTotal_2` es 8,2368 GHz.

Pico del plano E (yz; +θ apunta hacia +y, el lado opuesto a la alimentación). El ángulo es un ajuste parabólico sobre la rejilla de 5°, con una precisión de ±1° aproximadamente.

| | 7,7376 GHz | 7,9872 GHz | 8,2368 GHz | Squint en el canal |
|---|---|---|---|---|
| P01_MS1, plano E | −12,0° (5,65 dBi) | −10,6° (5,64 dBi) | −9,3° (5,49 dBi) | **+2,7°** |
| US3_MS3, plano E | −15,8° (5,24 dBi) | −13,1° (5,10 dBi) | −10,0° (4,82 dBi) | **+5,7°** |
| P01_MS1, plano H (xz) | +0,1° | +0,6° | +1,3° | +1,1° |
| US3_MS3, plano H (xz) | +0,3° | +0,5° | +1,0° | +0,6° |

- **El squint está en el plano E**: al subir la frecuencia, el haz se acerca a broadside. En el plano H, que es el del azimut del array del artículo (array a lo largo de x), el desplazamiento es de 1° o menos.
- La U-slot duplica el squint y la inclinación: el pico pasa de unos −12° a unos −16° en el borde inferior.
- La ganancia en broadside es de 5,29–5,39 dBi (P01_MS1) y 4,57–4,71 dBi (US3_MS3). Es ganancia, no ganancia realizada.
- Posible causa, sin demostrar: la radiación de la línea y el transformador, que están en −y, junto con la asimetría que introduce la U. Habría que confirmarlo con las corrientes de superficie de HFSS.

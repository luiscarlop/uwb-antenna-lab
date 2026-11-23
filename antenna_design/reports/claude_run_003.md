# Ronda Claude 003: llevar la resonancia de P01 a f0 (P01_R1)

- **ID del experimento:** P01_R1_OPENEMS_003, primer refinamiento de P01. Fecha 2026-11-03, de 12:18 a 12:45 UTC. Sesión autónoma, ronda 3/40.
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:**
  - `rf-designer`: diseño de la geometría.
  - `em-solver`: script genérico, en paralelo con `rf-designer`.
  - `validator`: auditoría.
- **FDTD:** 1, lanzada por el orquestador con el script verificado.
- **Evidencia:** `EM_SIMULATED`, con solo S11 y Zin en un puerto concentrado ideal. La independencia de malla es NOT_ESTABLISHED. No hay campo lejano.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**, sin hallazgos críticos.

## 1. Reanálisis de banda ancha sin nueva FDTD
[`em/reanalyze_port_dft.py`](../em/reanalyze_port_dft.py) recalcula la DFT de las señales de puerto ya guardadas (`port_ut_1` y `port_it_1`).
- Reproduce `s11_complex.csv` de 001 y 002 con un error de 5e-15.
- Solo evalúa frecuencias donde la excitación queda a menos de 20 dB de su pico, lo que da un rango válido de 6,98–9,0 GHz.
- Datos: [`em/wideband_reanalysis/`](../em/wideband_reanalysis/).

**Resultado:** en las dos mallas, el máximo de Re(Zin) está en **7,47 GHz**, con R ≈ 55 Ω y X ≈ +55…60 Ω. La resonancia paralela de P01 queda por debajo del canal, y la sonda añade una reactancia inductiva importante.

## 2. Propuesta P01_R1: una sola variable, L
[`variants/P01_R1.json`](../variants/P01_R1.json), escrito por `rf-designer`.
- **Cambio:** L pasa de 8,28 a **7,65 mm**. Se calcula separando la longitud efectiva (L + 2ΔL de Hammerstad, con ΔL = 0,713 mm) y escalándola por 7,47/7,9872. El escalado ingenuo daría 7,74 mm.
- **Sin cambios:** W = 11,4213 mm, el FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), la placa de 26×26 mm y la regla de alimentación (sonda vertical de 50 Ω en y = −0,22·L, que ahora queda en −1,683 mm).
- **Script nuevo:** [`em/patch_openems.py`](../em/patch_openems.py) construye el modelo a partir del JSON de variante.
  - Con [`variants_ref/P01_BASE.json`](../variants_ref/P01_BASE.json) reproduce **byte a byte** el XML de 001 (SHA f8291328…). Lo comprobaron `em-solver` y `validator`.
  - Entre el XML de 001 y el de 003 solo cambian el parche, la sonda y la malla resultante.

## 3. Recursos
| | Estimación | Observado |
|---|---|---|
| Celdas | 1 795 680 (1 841 790 nodales) | — |
| RAM | 295 MB (base medida), 590 MB con margen ×2 | RSS pico de 337 MiB |
| Tiempo | 266 s | 289 s de pared, 494 s de CPU, 2 CPU |
| Pasos y decaimiento de energía | — | 7695 pasos, −50,67 dB |

Comando: `timeout 900s taskset -c 0,1 python em/patch_openems.py solve --variant variants/P01_R1.json --out em/P01_R1_OPENEMS_003`, con openEMS 0.37.0.post1.dev40+g5fecbb58d y CSXCAD 0.7.0.post1.dev8+g626b99f2f.

## 4. Métricas
Ficheros:
- [`result.json`](../em/P01_R1_OPENEMS_003/result.json)
- [`s11_complex.csv`](../em/P01_R1_OPENEMS_003/s11_complex.csv)
- [`s11_wideband.csv`](../em/P01_R1_OPENEMS_003/s11_wideband.csv)
- [`s11_analysis.json`](../em/P01_R1_OPENEMS_003/s11_analysis.json) (analizador de Codex)

| | 001 (P01) | 003 (P01_R1) |
|---|---|---|
| Máximo de Re(Zin) | 54,5 Ω en 7,47 GHz | 50,9 Ω en **7,955 GHz** |
| X en ese máximo | +55 Ω | +60 Ω |
| Peor S11 del canal | −1,94 dB (8,2368 GHz) | −3,12 dB (7,7376 GHz) |
| Mejor S11 del canal | −7,63 dB | −7,31 dB (8,112 GHz) |
| ≤ −6 dB en todo el canal | No | **No** (229 de 501 muestras por encima) |
| ≤ −10 dB en todo el canal | No | No |

- **Lo que funcionó:** el cambio de L llevó la resonancia a 32 MHz de f0, como se había calculado.
- **Lo que no se resolvió:** la adaptación sigue mal. Lo que queda es sobre todo una reactancia en serie de unos +60 Ω.

## 5. Modelo circuital de guía (no es un resultado EM)
[`em/fit_patch_circuit.py`](../em/fit_patch_circuit.py) ajusta Zin = R0 + jωLs + R/(1 + jQ(f/fr − fr/f)). Resultados en [`em/circuit_fits/`](../em/circuit_fits/).

| | Q | Ls | R | fr | Error RMS del ajuste |
|---|---|---|---|---|---|
| 003 | 13,5 | 1,20 nH (+60 Ω en f0) | 45,4 Ω | 7,961 GHz | 1,0 Ω |
| 001 | 13,5 | 1,20 nH | 51,1 Ω | 7,467 GHz | — |

Lo que sugiere el modelo, que habrá que confirmar con FDTD:
- **Con Q = 13,5, el mejor peor caso en el canal es de unos −9,6 a −9,8 dB**, haya o no inductancia de sonda. Así que **−10 dB en todo el canal no parece alcanzable con este parche en FR4 de 1,6 mm**. Para eso haría falta bajar Q (U-slot P02, otro sustrato o más grosor).
- Mover solo la sonda no basta: el peor caso se queda en unos −3 dB. Para compensar Ls hay que trabajar por encima de la resonancia, con R_pico ≈ 90–110 Ω y fr ≈ 7,64–7,70 GHz. Eso daría unos −7,5 a −8,4 dB en el peor punto del canal, por debajo del mínimo de −6 dB.

## 6. Reservas de `validator` y su tratamiento
- **Media.** `s11_wideband.csv` de 003 incluye una fila de 9,0 GHz con la excitación en −20,01 dB, fuera del criterio, aunque las métricas de `result.json` sí la excluyen. **Corregido en el script** para las siguientes ejecuciones. El CSV bruto de 003 no se reescribe; queda documentado aquí y en el propio script.
- **Media.** Interpretación: el máximo de Re(Zin) indica la resonancia, pero no la demuestra. S11 está muestreado cada 1 MHz, sin garantía entre muestras. El FR4 y sus pérdidas son provisionales.
- **Baja.** Las líneas de malla siguen la regla de openEMS de 001 y no se alinearon con los bordes del parche, al contrario de lo que pedía `next_task`. Así se mantiene la comparabilidad con 001.
- **Baja.** El puerto es una línea concentrada ideal de 1,6 mm, así que su inductancia está incluida en Zin. Ni ese puerto ni la Ls ajustada son un conector real.
- **Baja.** El README de la variante debe aclarar que la cifra de «7,9885 GHz» está anclada a la resonancia medida y no es una predicción pura de Hammerstad.

## 7. Siguiente hipótesis (ronda 004)
P01_R2 sería el segundo y último refinamiento de P01 que permite CLAUDE.md. Consiste en un punto de diseño para la adaptación, guiado por el modelo:
- subir el inset de la sonda para aumentar R_pico;
- alargar L para bajar fr a la zona de unos 7,65–7,70 GHz;
- mantener el material y el tipo de alimentación.

El objetivo es cumplir −6 dB en todo el canal, sin esperar −10 dB. Después pasar a P02 (U-slot) para bajar Q.

**Decisión pendiente del propietario (no bloquea):** el puerto concentrado ideal da una Ls de unos 1,2 nH que no corresponde a ningún conector concreto. Habría que fijar qué alimentación real usar (por ejemplo, el diámetro del pin de un SMA de panel) para modelar el pin y no una línea ideal.

## Estado
- Ronda 3/40. Ningún candidato es viable para HFSS.
- Tests: 20 OK.
- **CONTINUE.**

## Corrección (2026-11-03, tras leer el artículo EuCAP 2027)
Lo que aquí se afirma sobre que −10 dB «no es alcanzable con Q ≈ 13» vale **solo dentro del modelo de guía**: resonancia única más la Ls de la sonda, ajustando solo R_pico y fr. El límite de Bode–Fano para el canal 9 (B = 6,25 %, Q ≈ 13) es de unos −33,6 dB con una red ideal, así que −10 dB no está prohibido por el ancho de banda. Bajar Q es una vía, no la única. Detalles en [`claude_eucap2027_context.md`](claude_eucap2027_context.md). Los resultados EM no cambian.

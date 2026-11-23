# Resultados de HFSS

Una carpeta por elemento, `results_<diseño>/`, **sin fechas** en los nombres. Dentro, lo del elemento aislado
(S11, ganancia, convergencia, JSON de análisis) y una subcarpeta por array, con el nombre del diseño de HFSS
(`ARR1x5_<elemento>_dparam/`, `ARR1x4_<elemento>_dparam/`).

| Carpeta | Contenido |
|---|---|
| `results_P01_MS1/` | Elemento P01_MS1: CSV de HFSS, `hfss_vs_openems.json`, `hfss_beam_squint.json`, `virtual_array_pitch_sweep.json` |
| `results_US3_MS3/` | Elemento US3_MS3: CSV de HFSS (incluye el barrido de `patch_L`), `hfss_vs_openems.json`, `hfss_beam_squint.json`, `hfss_parametric_patch_L.json` |
| `results_P01_MS2/` | Elemento `P01_MS2/` (HFSS, 20-11); `ARR1x4_P01_MS2_dparam/` y `ARR1x5_P01_MS2_dparam/`: 16 pasos de `arr_d` con `.sNp` y `convergence.conv`, campos en 13,5/17/18,2/20,5 mm, `array_pitch_sweep_hfss.json`, `array_analysis_d*mm.json`, `virtual_3d/`, `virtual_mono/`. Los datos del 15-11 y el run manual de 17 mm están en `ARR1x5_P01_MS2_dparam/legacy_2026-11-15/` |
| `results_US3_PS4/` | Vacía: `ARR1x5_US3_PS4_dparam/` pendiente |
| `results_US3_PS6/` | Elemento resuelto en HFSS (17-11): `US3_PS6/` (`.s1p`, `ff_P1.csv`, `antenna_params.csv`, `realized_gain_cuts.csv`, `convergence.conv`, `element_patterns_gd.json`); `ARR1x5_US3_PS6_dparam/` (16 pasos, 20-11) |
| `results_US3_PS6_4/` | `preregistro_hfss.md`, elemento `US3_PS6_4/` y `ARR1x5_US3_PS6_4_dparam/` (11 pasos), HFSS 20-11 |
| `results_US3_PS4_2_1/` | Elemento resuelto en HFSS (17-11): `US3_PS4_2_1/`; `ARR1x5_US3_PS4_2_1_dparam/`: 15 pasos convergidos (ΔS 0,01; sin 20 mm) con `.s5p` y `convergence.conv`, campos en 13,5/17/18,2/20,5 mm, análisis y logs; el barrido sin convergencia del 20-11 y los zips, en `legacy_2026-11-20/` |

Los exportadores de `../export/` escriben en la carpeta del proyecto de AEDT (`ch9_array_export/`, `ch9_element_export/`):
copia lo exportado a la carpeta que corresponda de aquí. Los scripts de `../analysis/` leen y escriben aquí.

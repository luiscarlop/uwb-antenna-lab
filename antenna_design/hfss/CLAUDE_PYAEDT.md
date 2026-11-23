# Carpeta `hfss/`: estructura, scripts y guía de PyAEDT

## Índice de la estructura (reorganizada el 2026-11-17)
```
hfss/
├── CLAUDE_PYAEDT.md              esta guía
├── build/                        scripts de CREACIÓN en HFSS (los ejecuta el propietario en AEDT)
│   ├── claude_pyaedt_ch9.py      versión PyAEDT; --check compara la geometría con variants/*.json
│   ├── make_aedt_native_script.py, make_aedt_array_script.py     generadores (necesitan pyaedt 1.9.0)
│   ├── P01_MS1/  P01_MS2/  US3_MS3/  US3_PS4/  US3_PS6/  US3_PS4_2_1/  US3_PS6_4/    una carpeta por elemento:
│   │       claude_aedt_native_<elemento>_ch9.py       elemento aislado (todos los diseños)
│   │       claude_aedt_array1x…_ch9.py                sus arrays (P01_MS2: 1×4 de pasos fijos, 1×4 y 1×5 paramétricos;
│   │                                                  US3_PS4, US3_PS6, US3_PS4_2_1, US3_PS6_4: 1×5 paramétrico)
├── export/                       scripts de EXPORTACIÓN (Tools → Run Script, con el diseño resuelto)
│   ├── claude_aedt_export_element_ch9.py   elemento: lista de elementos comentada/descomentada en DESIGN
│   ├── claude_aedt_export_array_ch9.py     array: .s<N>p, campos y convergencia; lista de arrays en DESIGN
│   └── claude_aedt_export_fields_ch9.py    array: solo campos, por tandas; lista de arrays en DESIGN
├── analysis/                     análisis en Python de lo exportado (se importan entre sí: déjalos juntos)
├── results/                      resultados de HFSS, sin fechas: results_<diseño>/ con sus arrays dentro (ver results/README.md)
└── legacy/                       lo heredado de Codex: handoff_v1/, export_handoff.py, verify_handoff.py, HFSS_STEPS.md
```
Flujo: **1)** ejecuta `build/<elemento>/…` en AEDT; **2)** resuelve y exporta con `export/…` (en el script, descomenta la línea `DESIGN` del diseño; `N_PORTS` se deduce del nombre); **3)** copia lo exportado a `results/results_<elemento>/`; **4)** analiza con `analysis/…`. Los generadores se ejecutan desde la raíz del repositorio: `python antenna_design/hfss/build/make_aedt_native_script.py` y `python antenna_design/hfss/build/make_aedt_array_script.py`; escriben en `build/<elemento>/`.

Decisiones de la reorganización: el fichero multidiseño `claude_aedt_native_ch9.py` se eliminó (hay un script nativo por elemento, también para P01_MS1, P01_MS2 y US3_MS3; P01_MS2 se añadió a `DESIGNS` de `claude_pyaedt_ch9.py`); los JSON que mezclaban P01_MS1 y US3_MS3 (`hfss_vs_openems`, `hfss_beam_squint`) se partieron en uno por diseño, y los scripts de análisis correspondientes escriben ahora un fichero por diseño; en los JSON movidos solo se tocaron las rutas.

### Ruta antigua → ruta nueva (relativas a `antenna_design/hfss/`)
| Ruta antigua | Ruta nueva |
|---|---|
| `claude_pyaedt_ch9.py` | `build/claude_pyaedt_ch9.py` |
| `make_aedt_native_script.py`, `make_aedt_array_script.py` | `build/make_aedt_native_script.py`, `build/make_aedt_array_script.py` |
| `claude_aedt_native_ch9.py` (multidiseño, heredado) | eliminado: un script por elemento, `build/<elemento>/claude_aedt_native_<elemento>_ch9.py` (también `build/P01_MS1/`, `build/P01_MS2/`, `build/US3_MS3/`, nuevos) |
| `claude_aedt_native_US3_PS4_ch9.py`, `…_US3_PS6_ch9.py`, `…_US3_PS4_2_1_ch9.py` | `build/US3_PS4/…`, `build/US3_PS6/…`, `build/US3_PS4_2_1/…` (mismo nombre; `build/US3_PS6_4/…` es nuevo, 2026-11-19) |
| `claude_aedt_array1x4_ch9.py` | `build/P01_MS2/claude_aedt_array1x4_ch9.py` |
| `claude_aedt_array1x4_P01_MS2_param_ch9.py` | `build/P01_MS2/claude_aedt_array1x4_P01_MS2_param_ch9.py` |
| `claude_aedt_array1x5_param_ch9.py` | `build/P01_MS2/claude_aedt_array1x5_P01_MS2_param_ch9.py` (renombrado) |
| `claude_aedt_array1x5_US3_PS4_param_ch9.py`, `…US3_PS6…`, `…US3_PS4_2_1…` | `build/US3_PS4/…`, `build/US3_PS6/…`, `build/US3_PS4_2_1/…` (mismo nombre) |
| `claude_aedt_export_element_ch9.py`, `…_array_ch9.py`, `…_fields_ch9.py` | `export/` (mismo nombre) |
| `array_hfss_analysis.py`, `array_mimo_metrics.py`, `array_pitch_sweep_hfss.py`, `virtual_array_pattern.py`, `virtual_array_pitch_sweep.py`, `compare_hfss_openems.py`, `hfss_beam_squint.py`, `hfss_parametric_patch_L.py` | `analysis/` (mismo nombre) |
| `results_2026-11-13/*P01_MS1*` | `results/results_P01_MS1/` |
| `results_2026-11-13/*US3_MS3*` (incluye `S Parameter US3_MS3 parametric patch_L.csv`) | `results/results_US3_MS3/` |
| `hfss_vs_openems_2026-11-13.json` | `results/results_P01_MS1/hfss_vs_openems.json` y `results/results_US3_MS3/hfss_vs_openems.json` (partido por diseño) |
| `hfss_beam_squint_2026-11-13.json` | `results/results_P01_MS1/hfss_beam_squint.json` y `results/results_US3_MS3/hfss_beam_squint.json` (partido por diseño) |
| `hfss_parametric_patch_L_2026-11-13.json` | `results/results_US3_MS3/hfss_parametric_patch_L.json` |
| `virtual_array_pitch_sweep_2026-11-14.json` (elemento P01_MS1) | `results/results_P01_MS1/virtual_array_pitch_sweep.json` |
| `results_2026-11-15/ARR1x5_P01_MS2_d17mm/` | `results/results_P01_MS2/ARR1x5_P01_MS2_dparam/manual_d17mm/` |
| `results_2026-11-15/ch9_array_export/ARR1x5_P01_MS2_dparam_d*mm/`, `array_pitch_sweep_hfss.json`, `export_log.txt` | `results/results_P01_MS2/ARR1x5_P01_MS2_dparam/` |
| `results_2026-11-15/ch9_array_export/ARR1x5_US3_PS4_2_1_dparam_[12].zip` | `results/results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/` |
| `results_2026-11-17/ARR1x5_US3_PS4_2_1_dparam/` | `results/results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/` |
| (nuevo, vacío) | `results/results_US3_PS4/`, `results/results_US3_PS6/`, `results/results_P01_MS2/ARR1x4_P01_MS2_dparam/` |
| `handoff_v1/`, `export_handoff.py`, `verify_handoff.py`, `HFSS_STEPS.md` | `legacy/` (mismo nombre; ningún test, `AGENTS.md` ni `.codex/` los referencia) |

Los informes históricos de `../reports/` citan las rutas antiguas y no se han reescrito: esta tabla las resuelve.

---

## Script HFSS paramétrico (PyAEDT): P01_MS1, P01_MS2, US3_MS3, US3_PS4, US3_PS6, US3_PS4_2_1 y US3_PS6_4

Script: [`build/claude_pyaedt_ch9.py`](build/claude_pyaedt_ch9.py).

Construye en HFSS los candidatos con alimentación microstrip (P01_MS1, US3_MS3 y, desde 2026-11-16, US3_PS4, US3_PS6, US3_PS4_2_1 y, desde 2026-11-19, US3_PS6_4; ver sus secciones al final). **Todas las dimensiones son variables de diseño** de HFSS, así que se pueden editar o barrer con Optimetrics.

**Estado:** `GEOMETRY_ONLY` para HFSS en el script. **Claude no lo ha ejecutado en AEDT**, porque este entorno no tiene Ansys; el propietario sí resolvió en HFSS P01_MS1, US3_MS3, el 1×5 de P01_MS2 y, el 17-11, los elementos US3_PS6 y US3_PS4_2_1 (este también como 1×5); US3_PS4 y US3_PS6_4 no se han resuelto en HFSS. Lo comprobado hasta ahora:
- las firmas de todas las llamadas, contra `pyaedt` 1.9.0 (módulo `ansys.aedt.core`);
- que la geometría paramétrica reproduce exactamente `variants/P01_MS1.json` y `variants/US3_MS3.json` (`--check`, y el test `tests/test_hfss_pyaedt_script.py`; US3_PS4, US3_PS6, US3_PS4_2_1 y US3_PS6_4 se comprueban también con `--check` y con `tests/test_hfss_us3_ps4.py`, `tests/test_hfss_us3_ps6.py`, `tests/test_hfss_us3_ps4_2_1.py` y `tests/test_hfss_us3_ps6_4.py`).

Antes de lanzar el solve, revisa en la interfaz:
- los objetos;
- el hueco de la U;
- el puerto y su línea de integración;
- la frontera de radiación;
- el setup.

## Uso
Hace falta Ansys Electronics Desktop con HFSS y Python con PyAEDT:

```bash
pip install pyaedt
```

Comprobar los parámetros (no necesita AEDT):

```bash
python antenna_design/hfss/build/claude_pyaedt_ch9.py --check
```

Construir los dos diseños en un proyecto:

```bash
python antenna_design/hfss/build/claude_pyaedt_ch9.py --design P01_MS1 --design US3_MS3 --project ch9_candidates_claude.aedt
```

Opciones:
- `--version 2025.1`: versión de AEDT; por defecto, la más reciente instalada.
- `--non-graphical`: sin interfaz gráfica.
- `--loss-model sigma`: el modelo de pérdidas de openEMS, para comparar con sus resultados.
- `--solve --cores 2`: lanza el análisis. Está desactivado por defecto.

## Variables (mm)
| Variable | P01_MS1 | US3_MS3 | US3_PS4 | US3_PS6 | US3_PS4_2_1 | US3_PS6_4 | Qué es |
|---|---|---|---|---|---|---|---|
| `board_x`, `board_y` | 26 | 26 | 26 | 26 | 26 | 26 | Placa y masa |
| `sub_h` | 2,07 | 2,07 | 2,07 | 2,07 | 2,07 | 2,07 | Altura del FR4 (homogéneo) |
| `cu_t` | 0,035 | 0,035 | 0,035 | 0,035 | 0,035 | 0,035 | Espesor del cobre de las láminas* |
| `patch_W` | 11,421266 | 11,421266 | 11,421266 | 11,421266 | 11,421266 | **14,0** | Ancho del parche (x) |
| `patch_L` | 7,322 | 6,502 | 6,302 | 6,29 | 6,222 | 6,29 | Largo resonante (y) |
| `line_w` | 3,92 | 3,92 | 3,92 | 3,92 | 3,92 | 3,92 (tramo de 50 Ω de solo **2,605 mm**, y −13 → −10,395) | Línea de 50 Ω desde el borde de la placa |
| `tr_w`, `tr_l` | 0,80 / 6,60 | 0,80 / 6,60 | 0,80 / 6,60 | 0,80 / 6,60 | 0,80 / 6,60 | **1,00 / 7,25** | Transformador λ/4 |
| `u_Wu`, `u_Lu`, `u_t`, `u_y0` | — | 4,4 / 2,65 / 0,8 / −0,7 | igual que US3_MS3 | igual que US3_MS3 | igual que US3_MS3 | igual que US3_MS3 | Ranura en U: ancho exterior, alto de los brazos, ancho de ranura y borde inferior de la base |
| `par_L`, `par_W`, `par_yc`, `par_z` | — | — | 7,46 / 11,0 / 0,75 / 1,035 | 7,05 / 11,0 / 0,615 / 1,035 | 7,46 / **10,0** / 0,75 / 1,035 | 7,05 / **13,58** / 0,615 / 1,035 | Parásito enterrado: largo (y), ancho (x), centro en y y altura z sobre la masa |
| `pad_xy`, `pad_zp`, `pad_zn` | 22 / 33 / 25 | igual | igual | igual | igual | igual | Distancia a la frontera de radiación |
| `arr_d` (solo arrays 1×5 paramétricos) | — | — | 18,2 al construir | 18,2 al construir | 18,2 al construir | 18,2 al construir (mínimo físico 14,0; práctico 14,5) | Paso entre elementos; `board_x` = 4·`arr_d` + 2·`board_m` |

Hay dos valores que se fijan al construir. Si los cambias, vuelve a ejecutar el script:
- el **espesor del cobre** (*) de la condición *finite conductivity*;
- la **línea de integración del puerto** (de z = 0 a `sub_h`).

## Modelo
| Elemento | Cómo se modela |
|---|---|
| Sustrato | FR4 provisional: εr 4,4 y tanδ 0,017 constante (`--loss-model tand`). Con `sigma` se usa σ = 2π·f0·ε0·εr·0,017 ≈ 0,0332 S/m y tanδ = 0, como en openEMS. |
| Cobre | Láminas con *finite conductivity* de 5,8e7 S/m y 35 µm: la masa, y el parche unido a la línea y al transformador. La U se resta del parche como tres rectángulos. |
| Puerto | *Lumped port* de 50 Ω sobre una lámina vertical en el arranque de la línea (y = −`board_y`/2). No incluye SMA ni de-embedding, igual que en openEMS. |
| Frontera | `create_region` con *Absolute Offset* y condición de radiación. |
| Setup | Driven Modal a 7,9872 GHz, ΔS ≤ 0,02, una pasada convergida y como máximo 15 pasadas (P01_MS1, US3_MS3 y P01_MS2; así se resolvieron). **US3_PS4, US3_PS6, US3_PS4_2_1, US3_PS6_4 y sus arrays** (corrección del `design-reviewer`, 2026-11-16): 2 pasadas convergidas, ΔS ≤ 0,01 y `SolveType` `MultiFrequency` con 7,7376 / 7,9872 / 8,2368 GHz a ΔS 0,01. Claves verificadas en `ansys.aedt.core.modules.setup_templates` y `solve_setup` de pyaedt 1.9.0 (`MinimumConvergedPasses`, `MaxDeltaS`, `SolveType`, `MultipleAdaptiveFreqsSetup`); los valores por diseño están en `SETUP_OVERRIDES` de `build/claude_pyaedt_ch9.py`. **US3_PS6_4 y su array: `MaximumPasses` 25** (corrección E1 del `design-reviewer`, 2026-11-19; los demás, 15): si no llega a ΔS 0,01 en dos pasadas convergidas, exporta la convergencia y no lo etiquetes como convergido; vigila la RAM (~400k tetraedros hacia la pasada 22) y el disco. |
| Barridos | Uno interpolado de 7,5 a 8,5 GHz (1001 puntos) y uno discreto `Edges_and_f0` con campos: 3 puntos (7,7376 / 7,9872 / 8,2368 GHz) en todos los diseños, salvo los **elementos US3_PS4, US3_PS6, US3_PS4_2_1 y US3_PS6_4: 11 puntos** cada 49,92 MHz (las 11 frecuencias NF2FF de openEMS; mismo nombre de barrido). En los arrays se dejan 3, salvo `ARR1x5_US3_PS4_2_1`: **5 puntos** (7,7376 / 7,8624 / 7,9872 / 8,1120 / 8,2368 GHz, paso 124,8 MHz) para que los campos embebidos muestreen el valle de η. |
| Campo lejano | Esfera infinita de θ 0–180° y φ 0–360°, cada 5°. |

## Qué esperar (openEMS, no HFSS)
Son resultados `EM_SIMULATED` de openEMS, sin validar en HFSS:

| | P01_MS1 (rondas 025/026) | US3_MS3 (rondas 023/024) |
|---|---|---|
| Peor S11 en el canal (malla base / fina) | −8,34 / −8,17 dB | −8,18 / −8,04 dB |
| Regla de dos mallas | pasa (`READY_FOR_HFSS_REVIEW`) | **no pasa** (\|ΔΓ\| 0,045 > 0,03) |

Ninguno de los dos cumple −10 dB.

## Script nativo para Tools → Run Script (sin instalar nada)
**Qué script ejecutar para cada elemento.** Hay un fichero por elemento, en `build/<elemento>/`, con su valor por defecto fijo (no hace falta editar nada):

| Elemento | Script | Diseño HFSS |
|---|---|---|
| P01_MS1 | [`build/P01_MS1/claude_aedt_native_P01_MS1_ch9.py`](build/P01_MS1/claude_aedt_native_P01_MS1_ch9.py) | `P01_MS1` |
| P01_MS2 | [`build/P01_MS2/claude_aedt_native_P01_MS2_ch9.py`](build/P01_MS2/claude_aedt_native_P01_MS2_ch9.py) | `P01_MS2` |
| US3_MS3 | [`build/US3_MS3/claude_aedt_native_US3_MS3_ch9.py`](build/US3_MS3/claude_aedt_native_US3_MS3_ch9.py) | `US3_MS3` |
| US3_PS4 | [`build/US3_PS4/claude_aedt_native_US3_PS4_ch9.py`](build/US3_PS4/claude_aedt_native_US3_PS4_ch9.py) | `US3_PS4` |
| US3_PS6 | [`build/US3_PS6/claude_aedt_native_US3_PS6_ch9.py`](build/US3_PS6/claude_aedt_native_US3_PS6_ch9.py) | `US3_PS6` |
| US3_PS4_2_1 | [`build/US3_PS4_2_1/claude_aedt_native_US3_PS4_2_1_ch9.py`](build/US3_PS4_2_1/claude_aedt_native_US3_PS4_2_1_ch9.py) | `US3_PS4_2_1` |
| US3_PS6_4 | [`build/US3_PS6_4/claude_aedt_native_US3_PS6_4_ch9.py`](build/US3_PS6_4/claude_aedt_native_US3_PS6_4_ch9.py) | `US3_PS6_4` |

El fichero multidiseño heredado `claude_aedt_native_ch9.py` (valor por defecto `["US3_PS6"]`) **se eliminó** en la reorganización de 2026-11-17: ahora hay un fichero por elemento, también para P01_MS1, P01_MS2 y US3_MS3. Los siete son el mismo código y las mismas tablas (incluido P01_MS2, que ahora está en `DESIGNS` de `build/claude_pyaedt_ch9.py`: P01_MS1 con `tr_l` 7,1 mm, comprobado con `--check` contra `variants/P01_MS2.json`): solo cambia el valor por defecto de `DESIGNS_TO_BUILD` y la nota de cabecera. Cada uno sigue pudiendo construir cualquier otro elemento si cambias `DESIGNS_TO_BUILD`.

1. Copia el fichero del elemento al ordenador de HFSS.
2. En Ansys Electronics Desktop, ve a **Tools → Run Script…** y elige el fichero.
3. Se crea el diseño del elemento en el proyecto activo (o en uno nuevo) y se guarda el proyecto.
4. **Reejecución.** Si el diseño ya existe en el proyecto (`oProject.GetTopDesignList()`), el script lo avisa en el *Message Manager* (aviso) y **lo omite**, sin duplicarlo ni renombrarlo; para reconstruirlo, borra el diseño o usa otro proyecto. Lo mismo vale para los arrays. `GetTopDesignList` se verificó en el código de PyAEDT 1.9.0 (`design_types.py` y `application/design.py`, que la usan y leen el nombre tras el último «;»), no en AEDT.
5. Al terminar cada diseño escribe en el *Message Manager* «construido <diseño>: patch_L …, par_W …» (confirmación de que se ha construido hasta el final; comprueba que los valores son los esperados).

Al principio del fichero hay dos opciones:
- `DESIGNS_TO_BUILD`: qué diseños se construyen (por defecto, el del nombre del fichero).
- `LOSS_MODEL`: `tand` o `sigma`.

El modelo, las variables y lo que se fija al construir son los mismos que en el script de PyAEDT.

**No lo edites a mano.** Se genera con [`build/make_aedt_native_script.py`](build/make_aedt_native_script.py), que necesita `pyaedt` solo en el equipo donde se genera. Los argumentos de contorno, puerto, setup, barridos, esfera y material salen de las plantillas y del conversor `_dict2arg` de `pyaedt` 1.9.0, con los mismos diccionarios que usan sus métodos. La geometría sigue los formatos de `CreateBox`, `CreateRectangle`, `CreatePolyline`, `Unite` y `Subtract` de PyAEDT.

**Comprobado:**
- se ejecuta completo con un HFSS simulado que registra las llamadas (sin errores de nombres ni de flujo);
- sus variables coinciden con las variantes (test).

**No comprobado:**
- no se ha ejecutado en AEDT;
- la caja de aire es un `CreateBox` de vacío que contiene la placa, y no un `CreateRegion`;
- el tipo de solución se intenta como «HFSS Modal Network» y, si falla, como «DrivenModal».

## Array 1×4 multipuerto (MIMO): `build/P01_MS2/claude_aedt_array1x4_ch9.py`
Script nativo para **Tools → Run Script**, generado por [`build/make_aedt_array_script.py`](build/make_aedt_array_script.py). Estado: `GEOMETRY_ONLY`. El array 1×4 no se ha simulado. El ARR1x5 de P01_MS2 sí se simuló en HFSS (`results/results_P01_MS2/ARR1x5_P01_MS2_dparam/`); los arrays no simulados son `ARR1x5_US3_PS4`, `ARR1x5_US3_PS6`, `ARR1x5_US3_PS4_2_1` y `ARR1x5_US3_PS6_4`.

**Qué construye.** Un array lineal de 4 elementos a lo largo de x, con **un puerto concentrado de 50 Ω por elemento** (P1…P4, de −x a +x, todos en el borde y = −board_y/2). Sustrato y masa compartidos. HFSS resuelve así la matriz S 4×4 completa (adaptación de cada puerto y acoplo Sij) y el diagrama embebido de cada elemento.

| Diseño HFSS | Elemento |
|---|---|
| `ARR1x4_P01_MS2_d13p5mm` (por defecto) | P01_MS2: P01_MS1 con `tr_l` 7,1 mm |
| `ARR1x4_P01_MS1_d13p5mm` | P01_MS1 (validado en HFSS como elemento) |
| `ARR1x4_US3_MS3_d13p5mm` | US3_MS3 (U-slot) |

**Constantes editables** al principio del script:
- `DESIGNS_TO_BUILD`: qué arrays se construyen.
- `LOSS_MODEL`: `tand` o `sigma`.
- `PITCHES_MM`: pasos entre elementos; se crea un diseño por paso con el paso en el nombre. Por defecto `[13.5, 15.5, 17.0, 18.2]` (13,5 mm es el del artículo; 18,2 mm es λ/2 en 8,2368 GHz). Son 4 soluciones de 4 puertos: deja solo los que quieras resolver.

**Variables (Design Properties).** Las del elemento (`patch_L`, `patch_W`, `tr_l`, `tr_w`, `line_w`, `sub_h`, `cu_t`, `board_y` y las de la U), comunes a los 4 elementos, más `board_m` (margen del elemento extremo al borde, 13 mm) y `pad_*`. `board_x` = 3·paso + 2·`board_m` (66,5 mm por defecto).

**Fijado al construir.** El **paso** (las posiciones y las líneas de integración de los puertos son números, así que el paso no se puede barrer con Optimetrics: pon los pasos en `PITCHES_MM`), las líneas de integración (z de 0 a `sub_h`) y `cu_t`.

**Cómo usarlo.**
1. Ejecuta el script y revisa los 4 parches, los 4 `PortSheet_i` y los puertos P1…P4.
2. Analyze. El setup y los barridos son los mismos que en el elemento.
3. **Acoplo y adaptación:** representa dB(S(Pi,Pj)). Exporta la matriz completa en Touchstone: clic derecho en el barrido `Sweep_7p5_8p5` → *Export* → *Touchstone* (`.s4p`, 50 Ω).
4. **Diagrama embebido de un elemento:** *HFSS → Fields → Edit Sources*, con 1 W en ese puerto y 0 en el resto (los demás quedan cargados con 50 Ω).
5. **Diagrama del array apuntado a θ₀ en xz:** en *Edit Sources* pon 1 W en los 4 puertos y fase progresiva −k·x_i·sinθ₀. Por ejemplo, a 7,9872 GHz con paso 13,5 mm, para θ₀ = 15° la fase entre puertos vecinos es −33,5° (P1 +50,3°, P2 +16,8°, P3 −16,8°, P4 −50,3°).

**Métricas MIMO.** [`analysis/array_mimo_metrics.py`](analysis/array_mimo_metrics.py) lee el `.s4p` y calcula:
- |Sij| en el canal;
- ECC a partir de S (supone antenas sin pérdidas, así que con η ≈ 0,8 solo es indicativo);
- coeficiente de reflexión activo de cada puerto y TARC al apuntar a θ₀.

```
python antenna_design/hfss/analysis/array_mimo_metrics.py <fichero.s4p> --pitch-mm 13.5 --steer 0 15 30 --out <salida.json>
```

**Comprobado:** se ejecuta completo con un HFSS simulado que registra las llamadas (4 parches, 4 puertos, líneas de integración en x = ±6,75 y ±20,25 mm), y hay tests del lector Touchstone y de las métricas. **No comprobado:** no se ha ejecutado en AEDT.

## Array virtual MIMO (1 TX + 2 RX): `analysis/virtual_array_pattern.py`
**No hace falta simular cada combinación de conmutadores.** HFSS es lineal: con la solución multipuerto del array (`ARR1x4_…`) se obtiene cualquier estado de los conmutadores en post-proceso.
- **Puertos apagados a 50 Ω** (el convenio del artículo para los diagramas embebidos): cada canal TX t → RX r es el producto de los campos embebidos E_t·E_r y no depende de la combinación.
- **Apagado con otra impedancia** (Γ_off ≠ 0, por ejemplo un conmutador abierto): los campos de cada estado se obtienen combinando los embebidos con la matriz S: a = (I − ΓS)⁻¹·e_p.

**Decisión del propietario (2026-11-14).** Un puerto apagado del conmutador queda terminado en 50 Ω, y la secuencia es `RF_CONFIGS` del código del TFG. Por tanto Γ_off = 0 (el valor por defecto del script): basta con los 4 campos embebidos de HFSS (*Edit Sources*: 1 W en un puerto y los demás cargados con 50 Ω), sin la matriz S. El `.s4p` sigue haciendo falta para el acoplo y la adaptación activa (`analysis/array_mimo_metrics.py`).

**Suma de los canales.** El elemento virtual del canal t → r está en x_t + x_r. El haz del array virtual es la **suma coherente** (con fase) de todos los canales de la secuencia, ponderados con exp(−j·k·(x_t + x_r)·sinθ₀). Sumar los diagramas en potencia de cada combinación da un diagrama medio, no un haz.

**Secuencia por defecto.** Cada elemento transmite por turnos y reciben todos los pares de los otros tres: 4 × 3 = 12 adquisiciones y 24 canales. Con 4 elementos y paso d salen 5 elementos virtuales (−2d … 2d) con multiplicidad 4, 4, 8, 4, 4. Una secuencia propia se pasa con `--sequence "1:2,3 1:2,4 …"`.

**Qué exportar de HFSS (por frecuencia: 7,7376, 7,9872 y 8,2368 GHz).**
1. *Fields → Edit Sources*: 1 W en P1 y 0 W en el resto.
2. Informe *Far Fields* sobre `FF_sphere`, *Data Table*, con `re(rETheta)`, `im(rETheta)`, `re(rEPhi)`, `im(rEPhi)` para todo θ y φ. *Export* → `P1.csv`.
3. Repetir con P2, P3 y P4.
4. Exportar la matriz S (`.s4p`). Solo hace falta si los puertos apagados no están a 50 Ω.

```
python antenna_design/hfss/analysis/virtual_array_pattern.py --ff P1.csv P2.csv P3.csv P4.csv --freq-ghz 7.9872 --pitch-mm 13.5 --steer 0 15 30 --out virtual_f0.json [--s4p array.s4p --gamma-off 1+0j]
```
Por defecto usa la componente copolar Ludwig-3 referida a y, como el artículo (`--pol vector` usa el producto escalar completo).

**Comprobado:** tests de la secuencia, de las posiciones virtuales, de las cargas, de la suma coherente y del lector de CSV. **No comprobado:** no se ha probado con una exportación real de HFSS (los nombres de columna se buscan por subcadena).

## Barrido de paso del array virtual: `analysis/virtual_array_pitch_sweep.py`
Modelo guía (no EM): diagrama del elemento de HFSS (P01_MS1, solo magnitud), elementos idénticos, **sin acoplo**, secuencia `RF_CONFIGS` y puertos apagados a 50 Ω. Barre el paso de 12 a 25 mm y calcula, en el plano del array y para 3 frecuencias y θ₀ = 0–60°, el haz de ida y vuelta a −3 dB, el error de apuntamiento, el lóbulo secundario más alto y si hay lóbulo de rejilla. Resultado: [`results/results_P01_MS1/virtual_array_pitch_sweep.json`](results/results_P01_MS1/virtual_array_pitch_sweep.json).

El acoplo entre elementos, que es lo que más depende del paso, solo sale de HFSS: resuelve los diseños `ARR1x4_P01_MS2_d…mm` de `PITCHES_MM` y compara |S21|, |S31| y la adaptación activa con `analysis/array_mimo_metrics.py`.

## Array 1×5 con paso paramétrico: `build/P01_MS2/claude_aedt_array1x5_P01_MS2_param_ch9.py`
Generado por el mismo [`build/make_aedt_array_script.py`](build/make_aedt_array_script.py). Estado: `GEOMETRY_ONLY` para el script (Claude no lo ha ejecutado en AEDT); el ARR1x5 de P01_MS2 lo resolvió el propietario en HFSS (`results/results_P01_MS2/ARR1x5_P01_MS2_dparam/`).
- **Geometría.** 5 elementos en x, con centros en (i − 2)·`arr_d` (i = 0…4) y puertos P1…P5 de −x a +x. `board_x` = 4·`arr_d` + 2·`board_m`.
- **Diseños.** Uno por elemento: `ARR1x5_P01_MS2_dparam` (por defecto), `ARR1x5_P01_MS1_dparam`, `ARR1x5_US3_MS3_dparam`, `ARR1x5_US3_PS4_dparam`, `ARR1x5_US3_PS6_dparam`, `ARR1x5_US3_PS4_2_1_dparam` y `ARR1x5_US3_PS6_4_dparam`. El fichero `build/US3_PS4/claude_aedt_array1x5_US3_PS4_param_ch9.py` construye por defecto `US3_PS4`, `build/US3_PS6/claude_aedt_array1x5_US3_PS6_param_ch9.py`, `US3_PS6` y `build/US3_PS4_2_1/claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py`, `US3_PS4_2_1`; `build/US3_PS6_4/claude_aedt_array1x5_US3_PS6_4_param_ch9.py`, `US3_PS6_4` (**ojo: parche de 14 mm, paso mínimo físico 14,0 mm; ver la sección de US3_PS6_4**).
- **Paso paramétrico.** `arr_d` es una variable de diseño (17 mm al construir), así que se puede barrer con *Optimetrics → Parametric*, por ejemplo de 13,5 a 18,2 mm.
  - Las láminas de los puertos y sus líneas de integración se escriben como expresiones de `arr_d`.
  - **No sé si AEDT acepta expresiones en la línea de integración.** Si las rechaza, el script usa números para `arr_d` = 17 mm y avisa en *Message Manager*. En ese caso **no barras `arr_d`**: usa el script 1×4 con varios `PITCHES_MM` o cambia el valor inicial.
  - **Comprobación tras construir:** cambia `arr_d` y mira que la línea de integración de P1 se mueve con su lámina (*Excitations → P1 → Properties*). Haz *Validation Check* antes de lanzar el barrido.
- **Array virtual.** El módulo del TFG tiene 4 antenas y su secuencia `RF_CONFIGS` es de 4. Con 5 elementos, `analysis/virtual_array_pattern.py` usa por defecto todas las combinaciones de 1 TX + 2 RX: 5 × 6 = 30 adquisiciones, 60 canales y 7 elementos virtuales. Si el hardware de 5 antenas usa otra secuencia, pásala con `--sequence`.

## Array 1×4 con paso paramétrico: `build/P01_MS2/claude_aedt_array1x4_P01_MS2_param_ch9.py` (2026-11-17)
Petición del propietario: comparar el 1×4 y el 1×5 de P01_MS2 en las mismas condiciones (sobre todo la resolución angular del array virtual) para justificar el quinto elemento.
- Diseño `ARR1x4_P01_MS2_dparam`: 4 elementos P01_MS2 en x, centros (i − 1,5)·`arr_d`, puertos P1…P4 de −x a +x con la línea de integración en función de `arr_d`, `board_x` = 3·`arr_d` + 26 mm.
- Mismo elemento, setup y barridos que `ARR1x5_P01_MS2_dparam` (comprobado en `tests/test_hfss_array1x4_param.py`); `arr_d` nominal 17 mm.
- Optimetrics: **la misma rejilla que el 1×5 de P01_MS2** (13,5–20,5 mm cada 0,5 y 18,2), con «Save Fields And Mesh».
- Exportación: en `export/claude_aedt_export_array_ch9.py` y `export/claude_aedt_export_fields_ch9.py` descomenta `DESIGN = "ARR1x4_P01_MS2_dparam"` (`N_PORTS` se deduce del nombre: 4), y en el exportador del array descomenta `ARR_D_MM` con la rejilla larga (13,5–20,5 cada 0,5 y 18,2). El exportador de campos se para tras 10 informes por sesión (aquí, 2,5 pasos de 4 puertos).
- El 1×4 de pasos fijos (`build/P01_MS2/claude_aedt_array1x4_ch9.py`) se mantiene por compatibilidad.
- Estado: `GEOMETRY_ONLY` en HFSS; **no se ha ejecutado en AEDT**, solo con un AEDT simulado.

## Exportar los resultados del array: `export/claude_aedt_export_array_ch9.py`
Script nativo (**Tools → Run Script**) que se ejecuta con el proyecto abierto y el array ya resuelto. **Guarda antes el proyecto (Ctrl+S)**; el script también lo guarda al empezar.

**Diseño y puertos.** Arriba del script hay un bloque con todos los arrays, uno por línea y comentados salvo uno (`ARR1x5_US3_PS4_2_1_dparam` por defecto): descomenta el que vayas a exportar y comenta el otro. `N_PORTS = None` deduce el número de puertos del nombre (`ARR1x4_…` → 4, `ARR1x5_…` → 5); pon un número para fijarlo a mano. Junto a `ARR_D_MM` están comentadas la rejilla larga (13,5–20,5 cada 0,5 y 18,2), la de P01_MS2 y el 1×4, y la de `ARR1x5_US3_PS6_4` (16,5–20,5 cada 0,5 y 18,2, 10 pasos: con el parche de 14 mm, 13,5 mm solapa los parches). `claude_aedt_export_fields_ch9.py` trae comentada la tanda `[18.2, 16.5, 20.5]` para ese array. Lo exportado se copia luego a `results/results_<elemento>/<diseño>/`.

Para cada paso de `ARR_D_MM` (por defecto 16,5–19,5 mm cada 0,5 mm y 18,2 mm, la rejilla corta de US3_PS4, US3_PS6 y US3_PS4_2_1; los campos, de `FIELDS_ARR_D_MM = [18.2]`) guarda en `<carpeta del proyecto>/ch9_array_export/<diseño>_d<paso>mm/`:
- `ARR1x5_d<paso>mm.s5p`: matriz S completa de `Setup_ch9 : Sweep_7p5_8p5`, en Touchstone a 50 Ω.
- `ff_P<i>.csv`: campo lejano embebido de cada puerto (1 W en ese puerto y 0 W en el resto) en `FF_sphere`, con las frecuencias de `Edges_and_f0` (3; **5 en `ARR1x5_US3_PS4_2_1`**) en la columna `Freq`. **Limitación del análisis:** `analysis/array_hfss_analysis.py` lee el formato largo (columna `Freq`) y solo analiza las tres frecuencias de `SUFFIX_FREQ` (7,7376 / 7,9872 / 8,2368 GHz); con 5 puntos acepta el CSV (selecciona por `Freq`) pero **ignora 7,8624 y 8,1120 GHz**: están en los CSV (para η y diagramas en el valle), no en el JSON del análisis. El formato ancho (familias de columnas `_1`, `_2`) solo vale para 3 frecuencias: con 5 puntos no se debe usar. Test: `tests/test_hfss_us3_ps4_2_1.py`.

`export_log.txt` se escribe línea a línea, así que si AEDT se cierra dice hasta dónde llegó. Si se cierra, exporta por tandas:
- deja en `ARR_D_MM` solo los pasos que faltan;
- o pon primero `FIELDS_ARR_D_MM = []`, que exporta solo los `.s5p` y es muy rápido.

Cómo se elige cada variación:
- Las claves de variación se toman **tal cual** de `GetAvailableVariations`, incluidas `board_x` y las demás variables dependientes. La tercera versión cambiaba solo `arr_d` en la nominal: `board_x` quedaba en 94 mm y `ExportNetworkData` fallaba.
- El script exporta el `.s5p` de cada paso de `ARR_D_MM`, que es ligero. Los campos solo los exporta de los pasos de `FIELDS_ARR_D_MM`, que deben ser 1–2 por ejecución.
- Para exportar los campos de un paso, el script pone antes ese `arr_d` como valor del diseño y al final restaura el original.

Historial: la primera versión usaba `ListVariations` (no existe en HFSS 2024.2) y la segunda `GetAvailableVariations`. Esta exportó solo 17 mm y AEDT se cerró; la causa no se conoce.

El lector de `analysis/virtual_array_pattern.py` convierte las unidades de cada columna (V, mV…), porque AEDT puede dar una unidad distinta a cada una.

## Exportar solo los campos, por tandas: `export/claude_aedt_export_fields_ch9.py`
Igual que el exportador completo (mismo bloque de `DESIGN` comentado/descomentado y `N_PORTS = None`), pero **sin `.s5p`**: solo exporta los campos embebidos de los pasos de `FIELDS_ARR_D_MM`, por defecto la tanda `[18.2, 16.5, 19.5]` (rejilla de US3_PS4, US3_PS6 y US3_PS4_2_1).
- Cada paso va a `ch9_array_export/<diseño>_d<paso>mm/ff_P1…P5.csv`, en formato largo con columna `Freq`.
- **Tope por sesión (2026-11-16):** AEDT se ha cerrado varias veces tras unos 14–15 informes de campo lejano en la misma sesión (logs del propietario, P01_MS2 y US3_PS4_2_1), sin error de Python. Por eso el script se para limpio tras `MAX_REPORTS_PER_RUN = 10` informes (dos pasos de 5 puertos), restaura `arr_d` y escribe `PARADA` en el log. Cierra AEDT, vuelve a abrir el proyecto y relanza con la misma lista: sigue donde se quedó.
- Un `ff_P<i>.csv` de menos de `MIN_CSV_BYTES = 1000` bytes se considera incompleto (por ejemplo, si AEDT se cerró mientras escribía) y se vuelve a exportar.
- Al terminar restaura `arr_d` al valor que tenía el diseño al empezar (`GetNominalVariation`, como el exportador completo), también si algo falla dentro del script. Ya no hay un «17 mm» fijo. Si `GetNominalVariation` no estuviera disponible, no restaura nada y el log lo avisa. Deja *Edit Sources* con P1 a 1 W.
- Con `SKIP_EXISTING = True` salta los ficheros que ya existen: si AEDT se cierra a mitad, se puede relanzar con la misma lista y sigue donde se quedó.
- Log línea a línea en `ch9_array_export/export_fields_log.txt`.
- Si AEDT se cierra de golpe, el proyecto guardado al empezar conserva el `arr_d` original. Al reabrirlo, elige «Open saved project file and results».

## Exportar el elemento unitario: `export/claude_aedt_export_element_ch9.py`
**No se ha ejecutado en AEDT real.** Solo se ha probado con un AEDT simulado (`tests/test_hfss_export_element.py`, que comprueba llamadas, nombres de ficheros, variación usada y que un fallo no aborta los demás pasos). Si algo falla en AEDT, el log dice en qué paso; manda `export_log.txt`.

Script nativo (**Tools → Run Script**) para el elemento ya resuelto, sin dependencias externas y con el mismo estilo que los exportadores del array (log línea a línea, `try/except` por paso, guarda el proyecto al empezar). Arriba hay un bloque con los siete elementos (`P01_MS1`, `P01_MS2`, `US3_MS3`, `US3_PS4`, `US3_PS6`, `US3_PS4_2_1`, `US3_PS6_4`), uno por línea y comentados salvo `US3_PS4_2_1`: descomenta el tuyo y comenta el otro. `OUT_DIR` vacío = `<carpeta del proyecto>/ch9_element_export`. Variables: `SETUP = "Setup_ch9"`, `SWEEP = "Sweep_7p5_8p5"`, `FF_SWEEP = "Edges_and_f0"`, `SPHERE = "FF_sphere"`, `PORT = "P1"`, `EXPORT_GAIN_CUTS`, `EXPORT_CONVERGENCE` (ambas `True`).

Ficheros en `OUT_DIR/<DESIGN>/`:
- `<DESIGN>.s1p`: S11 del barrido interpolado (Touchstone, 50 Ω), con la variación nominal tal cual la lista `GetAvailableVariations` (la que coincide con `GetNominalVariation`; si no coincide ninguna y hay varias, no exporta nada y lo dice).
- `ff_P1.csv`: 1 W en P1; `re/im(rETheta)`, `re/im(rEPhi)` sobre `FF_sphere`, todo θ y φ y todas las frecuencias de `Edges_and_f0` (formato largo con columna `Freq`, como el array).
- `antenna_params.csv`: informe *Antenna Parameters* (Data Table, `Freq` en X) con `RadiationEfficiency`, `RadiatedPower`, `AcceptedPower`, `IncidentPower`, `PeakRealizedGain`, `PeakGain`, `PeakDirectivity`. **Si AEDT rechaza el informe conjunto** (por ejemplo, por un nombre de cantidad que no existe), el script prueba cantidad a cantidad y deja `antenna_params_<cantidad>.csv` de las que sí existen; el log dice cuáles fallaron.
- `realized_gain_cuts.csv` (opcional): `dB(GainTotal)` y `dB(RealizedGainTotal)` sobre la esfera, con el mismo recorrido que `ff_P1.csv` y el mismo fallback por cantidad. `ff_P1.csv` ya permite calcularlo; si la cantidad no se acepta, se omite sin más.
- `convergence.conv`: perfil de convergencia adaptativa (`oDesign.ExportConvergence`); `profile.prof`: tabla de perfil (`oDesign.ExportProfile`).
- `export_log.txt`: lo que se hizo y la variación usada.

Al terminar deja *Edit Sources* con 1 W en P1.

**Llamadas verificadas en PyAEDT 1.9.0:** `GetNominalVariation`, `GetAvailableVariations`, `ExportNetworkData` (mismos argumentos que `export_touchstone`), `EditSources`, `CreateReport`/`ExportToFile`/`DeleteReports`, `ExportConvergence(setup, variaciones, fichero)` con el setup **sin** `: barrido` y las variaciones como `nombre=valor,nombre=valor`, `ExportProfile` (con el fallback a cuatro argumentos de PyAEDT), la categoría `Antenna Parameters` con `["Context:=", esfera]` y las cantidades `IncidentPower`, `RadiatedPower`, `AcceptedPower` (y `GainTotal` en los ejemplos).
**No verificadas en PyAEDT:** los nombres `RadiationEfficiency`, `PeakRealizedGain`, `PeakGain`, `PeakDirectivity` y `dB(RealizedGainTotal)` (salen del Report Editor de AEDT), el formato exacto de variación que acepta `ExportConvergence` en este diseño (el script prueba la cadena completa y luego la vacía, y el log dice cuál funcionó) y la extensión `.conv`/`.prof` que escriba AEDT.

**Convergencia en el exportador del array.** `export/claude_aedt_export_array_ch9.py` tiene ahora `EXPORT_CONVERGENCE = True`: tras el `.s5p` de cada paso de `ARR_D_MM`, exporta `<carpeta del paso>/convergence.conv` con la misma llamada (`ExportConvergence`; prueba la variación completa y luego solo `arr_d`). Un fallo se anota como `ERR convergencia` y no cambia nada de lo demás. Ponla a `False` para omitirlo.

## US3_PS4: U-slot con parche parásito enterrado (2026-11-16)
`claude_pyaedt_ch9.DESIGNS["US3_PS4"]` reproduce [`variants/US3_PS4.json`](../variants/US3_PS4.json), la geometría simulada en openEMS en la ronda 036 (lo comprueba `--check`).
- **Parche y U-slot:** parche de 11,421 × 6,302 mm con la U de US3_MS3.
- **Alimentación:** línea de 50 Ω de 3,92 mm y transformador de 0,80 × 6,60 mm.
- **Parásito:** lámina de cobre flotante de `par_L` × `par_W` = 7,46 × 11,0 mm, centrada en (0, `par_yc` = 0,75) a la altura `par_z` = 1,035 mm, **dentro** de la caja del sustrato.
  - Es un rectángulo con Finite Conductivity interna (`IsInternal`), sin vías.
  - El sustrato sigue siendo una sola caja de FR4 homogéneo.

Setup y barrido propios de US3_PS4 (corrección del `design-reviewer`, 2026-11-16; los demás diseños no cambian):
- 2 pasadas convergidas (`MinimumConvergedPasses` 2), ΔS ≤ 0,01 y adaptativo `MultiFrequency` en 7,7376 / 7,9872 / 8,2368 GHz a ΔS 0,01. Las claves están verificadas en pyaedt 1.9.0 (`setup_templates.HFSSDrivenDefault` y `enable_adaptive_setup_multifrequency`); no hay claves inventadas.
- Elemento: `Edges_and_f0` con `RangeCount` 11 (paso 49,92 MHz, las 11 frecuencias NF2FF de openEMS), con el mismo nombre de barrido. El array deja 3 puntos.
- Se aplican por diseño: `SETUP_OVERRIDES` y `EDGES_COUNT` en `build/claude_pyaedt_ch9.py`; los scripts generados llevan `SETUP_ARGS` y `SWEEP_ARGS` indexados por diseño.

Scripts nuevos o actualizados:
- Elemento: `build/US3_PS4/claude_aedt_native_US3_PS4_ch9.py` (valor fijo `["US3_PS4"]`). Ver «Qué script ejecutar para cada elemento».
- `build/US3_PS4/claude_aedt_array1x5_US3_PS4_param_ch9.py`: array 1×5 `ARR1x5_US3_PS4_dparam` con un parásito por elemento (`Parasitic_1…5`) y `arr_d` de **18,2 mm** al construir. Es el paso recomendado por el barrido de P01_MS2; barrido sugerido de 16,5 a 19,5 mm cada 0,5 mm.
- Para exportar, se usan los mismos exportadores con `DESIGN = "ARR1x5_US3_PS4_dparam"` (en los exportadores, comenta la línea `DESIGN` activa y descomenta la de este diseño):
  - `export/claude_aedt_export_array_ch9.py` para los `.s5p`: `ARR_D_MM` = 16,5…19,5 cada 0,5 y 18,2; `FIELDS_ARR_D_MM = [18.2]`;
  - `export/claude_aedt_export_fields_ch9.py` para los campos por tandas: `FIELDS_ARR_D_MM = [18.2, 16.5, 19.5]`. Restaura `arr_d` al nominal leído al empezar (antes lo fijaba a 17 mm).
- **18,2 mm no está en la rejilla 16,5–19,5 cada 0,5 mm.** El array se construye con `arr_d` = 18,2 mm. Añade 18,2 a la tabla de *Optimetrics → Parametric* (como se hizo con P01_MS2) o resuelve el nominal aparte; si no, los exportadores avisan «arr_d = 18.2 mm no está resuelto» y lo saltan.

**Límites de la parametrización** (lo que no sigue a las variables):
- `par_z` debe cumplir 0 < `par_z` < `sub_h`; **no sigue a `sub_h`**: si cambias `sub_h`, reajusta `par_z` (1,035 mm = `sub_h`/2).
- `par_yc` **no sigue a `patch_L`**. La holgura del parásito al borde −y del parche es `patch_L`/2 + `par_yc` − `par_L`/2 = 0,171 mm con los valores actuales: si cambias `patch_L`, `par_yc` o `par_L`, recomprueba que siga siendo positiva (el borde −y del parásito queda dentro del parche).
- En el array, `arr_d` > `patch_W` + 0,7 mm (11,421 + 0,7 ≈ 12,1 mm), para que los parches no se toquen.
- Se fijan al construir (no siguen a las variables): la **línea de integración** del puerto (en y = −`board_y`/2 y z de 0 a `sub_h`) y `cu_t` (espesor de la condición Finite Conductivity). Cambiarlos exige regenerar el script o rehacerlos a mano.

**Comprobaciones tras construir** (en AEDT):
1. *Validation Check* sin avisos sobre `Parasitic` (ni sobre `Parasitic_i` en el array).
2. *Boundary Display* (Modeler → Boundary Display) muestra `Cu_Parasitic` (`Cu_Parasitic_1…5` en el array).
3. *Plot Mesh* sobre `Parasitic` muestra triángulos tras la primera pasada: si la lámina no tiene malla, AEDT la ignora.
4. El S11 debe tener **dos mínimos**. Una sola resonancia indicaría que la lámina se ignora.
5. Alternativa si AEDT protesta por la lámina dentro de la caja del sustrato: partir el sustrato en `Substrate_lo` (z de 0 a `par_z`) y `Substrate_hi` (z de `par_z` a `sub_h`), del mismo material, con la lámina en la interfaz.

**Criterio del contraste HFSS, fijado antes de ver resultados (2026-11-16, `design-reviewer`).** Se compara HFSS con openEMS con este criterio, que no se cambia después:
- Dos mínimos de S11 separados 300–400 MHz.
- El valle de η queda ligado al mínimo superior.
- Desfase esperado HFSS − openEMS de −60 a −75 MHz (P01_MS1: −62 MHz; US3_MS3: −73 MHz).
- Por ello es **probable que HFSS dé peor que −10 dB en 8,2368 GHz**, aunque openEMS dé −10,7 dB en toda la banda.
- **No se reajustan cotas con una sola pasada de HFSS.**

**Estado: GEOMETRY_ONLY. No se ha ejecutado en AEDT.** Comprobado solo con un AEDT simulado. En HFSS, revisa que la lámina interna del parásito quede dentro del sustrato y tenga su condición de cobre.

Aviso de diseño (`design-reviewer`, 2026-11-16): en openEMS el modo superior de US3_PS4 radia poco (η 0,24 y ganancia realizada −0,5 dBi hacia 8,14–8,19 GHz). Su S11 de −10,7 dB en todo el canal es en parte adaptación por pérdidas. HFSS servirá para contrastarlo.

## US3_PS6: U-slot con parásito enterrado, parche recentrado (ronda 41, 2026-11-16)
`claude_pyaedt_ch9.DESIGNS["US3_PS6"]` reproduce [`variants/US3_PS6.json`](../variants/US3_PS6.json), la geometría simulada en openEMS en las rondas 038 (malla base) y 039 (malla fina). Lo comprueba `python build/claude_pyaedt_ch9.py --check`. Estado: `GEOMETRY_ONLY` en HFSS; no se ha ejecutado en AEDT.

**Fe de erratas:** `variants/US3_PS6.json` hereda de PS5 varios metadatos de texto y derivados con valor erróneo (p. ej. connector.modeled, holgura 0,18 mm en lugar de 0,235 mm, `geometry_checks`). Los polígonos, `feed.*_y_mm`, `uslot_params` y `parasitic_params` (Lp, Wp, centro, z) son correctos. Valores correctos en [`variants/US3_PS6.errata.json`](../variants/US3_PS6.errata.json); el JSON original no se edita porque su sha256 está registrado en las ejecuciones 038 y 039.

**Geometría** (diferencias con US3_PS4; el resto, igual: FR4 homogéneo εr 4,4, tanδ 0,017, h 2,07 mm, placa de 26 × 26 mm, U-slot, cobre de 35 µm, puerto de 50 Ω):
| Variable | US3_PS4 | US3_PS6 |
|---|---|---|
| `patch_L` | 6,302 | **6,29** (borde radiante en y = −3,145) |
| `tr_w` × `tr_l` | 0,80 × 6,60 | 0,80 × 6,60, desde y = −9,745 hasta −3,145 |
| línea de 50 Ω (`line_w` 3,92) | y −13 → −9,751 | y −13 → −9,745 (3,255 mm) |
| `par_L` × `par_W` | 7,46 × 11,0 | **7,05 × 11,0** (y −2,91…4,14) |
| `par_yc` | 0,75 | **0,615** |
| `par_z` | 1,035 | 1,035 |
| `u_Wu`, `u_Lu`, `u_t`, `u_y0` | 4,4 / 2,65 / 0,8 / −0,7 | igual |
- El parásito sigue siendo una lámina flotante dentro de la caja del sustrato (Finite Conductivity interna, sin vías). Su borde −y (−2,91) **no debe moverse**: queda 0,235 mm por encima del borde del parche en y y no cubre el transformador.
- Los límites de parametrización de la sección de US3_PS4 valen también aquí. Holgura del parásito al borde −y del parche: `patch_L`/2 + `par_yc` − `par_L`/2 = 0,235 mm (recompruébala si cambias `patch_L`, `par_yc` o `par_L`).
- **Fe de erratas:** el `mesh_hint_note` de `variants/US3_PS4_2_1.json` dice que se añaden tres líneas entre el borde del parche y el del parásito; la malla efectiva de openEMS 045 solo conserva en y ∈ [−3,2, −2,9] las líneas −3,111 y −2,97 (−3,07 y −3,03 se fundieron). La geometría (polígonos, feed, `uslot_params`, `parasitic_params`) es correcta. Detalle, incluida la malla fina de 047, en [`variants/US3_PS4_2_1.errata.json`](../variants/US3_PS4_2_1.errata.json); el JSON original no se edita porque su sha256 está registrado en las ejecuciones 045 y 047.

**Setup y barrido** (los mismos que US3_PS4, `SETUP_OVERRIDES["US3_PS6"]` y `EDGES_COUNT["US3_PS6"]`): 2 pasadas convergidas (`MinimumConvergedPasses` 2), ΔS ≤ 0,01, `SolveType` `MultiFrequency` en 7,7376 / 7,9872 / 8,2368 GHz a ΔS 0,01; `Sweep_7p5_8p5` interpolado (1001 puntos) y `Edges_and_f0` de 11 puntos en el elemento (3 en el array).

**Scripts y nombres de diseño**
- Elemento: **`build/US3_PS6/claude_aedt_native_US3_PS6_ch9.py`** (valor fijo `["US3_PS6"]`). Diseño HFSS: `US3_PS6`. Se regenera con `build/make_aedt_native_script.py` (pyaedt 1.9.0 solo en la máquina que lo genera).
- Array: `build/US3_PS6/claude_aedt_array1x5_US3_PS6_param_ch9.py`, diseño `ARR1x5_US3_PS6_dparam`, un puerto de 50 Ω y un parásito (`Parasitic_1…5`) por elemento, `arr_d` **nominal 18,2 mm**, `board_x` = 4·`arr_d` + 2·`board_m`. Mismo esquema de puertos y parásitos que el de US3_PS4; se genera con `build/make_aedt_array_script.py`.
- **Optimetrics → Parametric** sobre `arr_d`: 16,5–19,5 mm cada 0,5 mm **más 18,2 mm** (8 pasos; el nominal 18,2 mm no está en la rejilla de 0,5 mm). Es la misma rejilla que US3_PS4. **Antes de lanzar el barrido marca Optimetrics → Parametric → Options → «Save Fields And Mesh»**: sin eso, el exportador de campos solo puede sacar los campos embebidos de la variación nominal (18,2 mm), no los de 16,5 y 19,5 mm.
- Exportación: `export/claude_aedt_export_array_ch9.py` (`.s5p` y campos de `FIELDS_ARR_D_MM`) y `export/claude_aedt_export_fields_ch9.py` (campos por tandas). Descomenta `DESIGN = "ARR1x5_US3_PS6_dparam"` (y comenta la activa); la lógica no cambia (`ARR_D_MM` = 16,5…19,5 cada 0,5 y 18,2; tanda `[18.2, 16.5, 19.5]`; restauran `arr_d` al nominal leído al empezar).

**Comprobaciones tras construir** (en AEDT; las de US3_PS4, adaptadas):
1. *Validation Check* sin avisos sobre `Parasitic` (`Parasitic_i` en el array).
2. *Boundary Display* muestra `Cu_Ground`, `Cu_Patch` y `Cu_Parasitic` (`Cu_Patch_i` y `Cu_Parasitic_i` en el array).
3. *Plot Mesh* sobre `Parasitic` muestra triángulos tras la primera pasada.
4. Las variables de diseño valen `patch_L` = 6,29 mm, `par_L` = 7,05 mm, `par_yc` = 0,615 mm, `par_z` = 1,035 mm y `tr_l` = 6,6 mm; el transformador acaba en y = −3,145 mm y el borde −y del parásito queda en y = −2,91 mm.
5. Hay un único puerto de 50 Ω en y = −13 mm (cinco en el array, con la línea de integración desplazada al cambiar `arr_d`; compruébalo cambiando `arr_d`).
6. A diferencia de US3_PS4, **no se esperan dos mínimos separados**: en openEMS (039) US3_PS6 tiene un único mínimo profundo en el canal (−24,7 dB a 8,005 GHz) y, según el diseño (ronda 037), el modo dominado por el parásito se ha sacado del canal (no verificado en HFSS). Si en HFSS aparece un segundo mínimo dentro de 7,7376–8,2368 GHz, anótalo como diferencia con openEMS.
7. Alternativa si AEDT protesta por la lámina dentro de la caja del sustrato: partir el sustrato en `Substrate_lo` y `Substrate_hi` en z = `par_z`, como en US3_PS4.
8. *Convergencia del array.* En el perfil de convergencia de cada variación de `arr_d` comprueba que converge antes de `MaximumPasses` 15 (`MultiFrequency` en 3 frecuencias, ΔS 0,01). Si no converge, sube `MaximumPasses` antes de leer los acoplos.
9. *Message Manager.* No debe salir el aviso de línea de integración con números, y la línea de integración de P1 debe moverse al cambiar `arr_d`.
10. *`Cu_Parasitic`.* Comprueba que está en Boundary Display y que la lámina queda mallada tras la primera pasada. Un segundo mínimo dentro del canal en HFSS se anota como diferencia con openEMS, no se corrige.

**Criterios pre-registrados para el contraste HFSS (hipótesis, fijadas antes de ver resultados; no son resultados).** Referencia openEMS, ronda 039 (malla fina; 038 y 039 difieren 0,02 dB en el peor S11 y 0 MHz en el mínimo): peor S11 del canal **−8,14 dB en 7,7376 GHz**, mínimo −24,7 dB a **8,005 GHz**, banda ≤ −10 dB de 7,80 a 8,275 GHz, η 0,625–0,69.
- *Desfase esperado.* HFSS − openEMS observado en P01_MS1 (−62 MHz) y US3_MS3 (−73 MHz): 60–75 MHz hacia abajo. Hipótesis: el mínimo de HFSS cae en **7,93–7,95 GHz** (8,005 GHz − 60…75 MHz).
- *Peor S11 en HFSS.* Si la curva de openEMS 039 se limitara a trasladarse 60–75 MHz hacia abajo (aproximación de orden cero: la forma de la curva puede cambiar), el borde inferior de HFSS (7,7376 GHz) equivaldría a 7,80–7,81 GHz de openEMS (≈ −10,0 a −10,6 dB) y el superior (8,2368 GHz) a 8,30–8,31 GHz de openEMS (≈ −9,3 a −8,9 dB). Es decir: **el borde inferior mejoraría respecto de −8,14 dB y el peor caso pasaría al borde superior, en torno a −9 dB**. H1: el peor S11 del canal en HFSS está entre −8 y −10 dB. Esto no es una predicción del resultado, solo una guía para leerlo.
- *Borde inferior.* Puede mejorar (desfase hacia abajo de 60–75 MHz, como arriba) o empeorar (desfase menor de lo observado en otros diseños, o una forma de la curva distinta). Si el desfase fuese de 0 MHz, el borde inferior seguiría en torno a −8 dB. Cualquier valor se anota sin reajustar cotas.
- *Eficiencia y ganancia (hipótesis H2, equivalente a la H2 de 038/039; no es un resultado).* En los 11 puntos de `Edges_and_f0` del elemento: **η ≥ 0,55** y **ganancia realizada broadside ≥ 2 dBi**, con Dmax a menos de 20° de broadside. Referencia openEMS 039 (malla fina): η 0,625–0,690 y ganancia realizada 3,40–4,32 dBi; el Dmax de openEMS se muestreó en θ 15–20° (rejilla de 5°, 4 cortes en φ), así que el máximo real puede estar fuera de la rejilla. **Marca de fallo:** η < 0,5 en algún punto del canal, o caída de η hacia 8,2368 GHz mayor de 0,1 respecto del centro (7,9872 GHz). **Cómo calcular η en HFSS:** η = *Radiated Power* / *Accepted Power* del informe de antena (*Antenna Parameters*, `RadiationEfficiency`, a cada frecuencia de `Edges_and_f0` con campos). Es la misma definición que la η 0,625–0,690 de openEMS 039 (`radiation_efficiency_Prad_over_Pacc` de `nf2ff_summary.json`), así que se comparan directamente. No uses la eficiencia total (`Radiated Power` / *Incident Power*, que incluye la desadaptación; en openEMS es `total_efficiency_Prad_over_Pinc`, 0,56 en 7,7376 GHz en 039). La ganancia realizada de HFSS ya incluye la desadaptación.
- *Marcas de fallo.* Peor S11 en el canal peor que −6 dB (no cumple el mínimo de adaptación); mínimo fuera de 7,90–7,98 GHz; segundo mínimo dentro del canal. Estos casos se comunican al propietario y no se corrigen con una sola pasada de HFSS.
- *Mismos límites que US3_PS4:* no se reajusta ninguna cota con una sola pasada de HFSS; el S11 de HFSS sin fichero real no existe; η y ganancia realizada se contrastan solo con los campos exportados.
- *Rango de `arr_d` recomendado para Optimetrics:* 16,5–19,5 mm cada 0,5 mm y 18,2 mm.

## US3_PS4_2_1: US3_PS4_2 con el parche motor más corto (2026-11-16)
`claude_pyaedt_ch9.DESIGNS["US3_PS4_2_1"]` reproduce [`variants/US3_PS4_2_1.json`](../variants/US3_PS4_2_1.json), la geometría simulada en openEMS en la ronda 045 (malla base) y 047 (malla fina, ver abajo). Lo comprueba `python build/claude_pyaedt_ch9.py --check`. Estado: `GEOMETRY_ONLY` en HFSS; **no se ha ejecutado en AEDT**, solo con un AEDT simulado (`tests/test_hfss_us3_ps4_2_1.py`).

**Geometría** (único cambio de diseño respecto de US3_PS4_2: `patch_L` 6,302 → 6,222 mm; el resto, igual: FR4 homogéneo εr 4,4, tanδ 0,017, h 2,07 mm, placa de 26 × 26 mm, cobre de 35 µm, puerto de 50 Ω):
| Variable | US3_PS4 | US3_PS6 | US3_PS4_2_1 |
|---|---|---|---|
| `patch_L` | 6,302 | 6,29 | **6,222** (borde radiante en y = −3,111) |
| `tr_w` × `tr_l` | 0,80 × 6,60 | 0,80 × 6,60 | 0,80 × 6,60, desde y = −9,711 hasta −3,111 |
| línea de 50 Ω (`line_w` 3,92) | y −13 → −9,751 | y −13 → −9,745 | y −13 → −9,711 (3,289 mm) |
| `par_L` × `par_W` | 7,46 × 11,0 | 7,05 × 11,0 | **7,46 × 10,0** (y −2,98…4,48) |
| `par_yc` | 0,75 | 0,615 | 0,75 |
| `par_z` | 1,035 | 1,035 | 1,035 |
| `u_Wu`, `u_Lu`, `u_t`, `u_y0` | 4,4 / 2,65 / 0,8 / −0,7 | igual | igual |
- **Ojo: el ancho del parásito (`par_W`) es 10,0 mm, no 11,0 mm** como en US3_PS4 y US3_PS6.
- El parásito sigue siendo una lámina flotante dentro de la caja del sustrato (Finite Conductivity interna, sin vías). Su borde −y (−2,98) **no debe moverse**: queda 0,131 mm por encima del borde del parche en y (capas distintas, separadas 1,035 mm en z) y no cubre el transformador; el voladizo +y es de 1,369 mm.
- Los límites de parametrización de la sección de US3_PS4 valen también aquí. Holgura del parásito al borde −y del parche: `patch_L`/2 + `par_yc` − `par_L`/2 = 0,131 mm (recompruébala si cambias `patch_L`, `par_yc` o `par_L`; es del orden de la tolerancia de registro entre capas).

**Setup y barrido** (los mismos que US3_PS4 y US3_PS6, `SETUP_OVERRIDES["US3_PS4_2_1"]` y `EDGES_COUNT["US3_PS4_2_1"]`): 2 pasadas convergidas (`MinimumConvergedPasses` 2), ΔS ≤ 0,01, `SolveType` `MultiFrequency` en 7,7376 / 7,9872 / 8,2368 GHz a ΔS 0,01; `Sweep_7p5_8p5` interpolado (1001 puntos) y `Edges_and_f0` de 11 puntos en el elemento y **5 en el array** (7,7376 / 7,8624 / 7,9872 / 8,1120 / 8,2368 GHz; corrección del `design-reviewer`, 2026-11-16: así los campos embebidos muestrean el valle de η, que openEMS 045 sitúa en 8,137 GHz; los demás arrays siguen con 3 puntos). El análisis de arrays solo usa tres de las cinco frecuencias (ver la limitación en «Exportación»).

**Scripts y nombres de diseño**
- Elemento: **`build/US3_PS4_2_1/claude_aedt_native_US3_PS4_2_1_ch9.py`** (valor fijo `["US3_PS4_2_1"]`). Diseño HFSS: `US3_PS4_2_1`. Se regenera con `build/make_aedt_native_script.py` (pyaedt 1.9.0 solo en la máquina que lo genera).
- Array: `build/US3_PS4_2_1/claude_aedt_array1x5_US3_PS4_2_1_param_ch9.py`, diseño `ARR1x5_US3_PS4_2_1_dparam`, un puerto de 50 Ω y un parásito (`Parasitic_1…5`) por elemento, `arr_d` **nominal 18,2 mm**, `board_x` = 4·`arr_d` + 2·`board_m`. Mismo esquema de puertos y parásitos que los de US3_PS4 y US3_PS6; se genera con `build/make_aedt_array_script.py`.
- **Optimetrics → Parametric** sobre `arr_d`: 16,5–19,5 mm cada 0,5 mm **más 18,2 mm** (8 pasos; el nominal 18,2 mm no está en la rejilla de 0,5 mm). Es la misma rejilla que US3_PS4 y US3_PS6. **Antes de lanzar el barrido marca Optimetrics → Parametric → Options → «Save Fields And Mesh»**: sin eso, el exportador de campos solo puede sacar los campos embebidos de la variación nominal (18,2 mm), no los de 16,5 y 19,5 mm.
- Exportación: `export/claude_aedt_export_array_ch9.py` (`.s5p` y campos de `FIELDS_ARR_D_MM`) y `export/claude_aedt_export_fields_ch9.py` (campos por tandas). Descomenta `DESIGN = "ARR1x5_US3_PS4_2_1_dparam"` (es la activa por defecto); la lógica no cambia (`ARR_D_MM` = 16,5…19,5 cada 0,5 y 18,2; tanda `[18.2, 16.5, 19.5]`; restauran `arr_d` al nominal leído al empezar).

**Comprobaciones tras construir** (en AEDT; las mismas 10 de US3_PS6, adaptadas):
1. *Validation Check* sin avisos sobre `Parasitic` (`Parasitic_i` en el array).
2. *Boundary Display* muestra `Cu_Ground`, `Cu_Patch` y `Cu_Parasitic` (`Cu_Patch_i` y `Cu_Parasitic_i` en el array).
3. *Plot Mesh* sobre `Parasitic` muestra triángulos tras la primera pasada.
4. Las variables de diseño valen `patch_L` = 6,222 mm, `par_L` = 7,46 mm, `par_W` = 10,0 mm, `par_yc` = 0,75 mm, `par_z` = 1,035 mm y `tr_l` = 6,6 mm; el transformador acaba en y = −3,111 mm y el borde −y del parásito queda en y = −2,98 mm.
5. Hay un único puerto de 50 Ω en y = −13 mm (cinco en el array, con la línea de integración desplazada al cambiar `arr_d`; compruébalo cambiando `arr_d`).
6. Como US3_PS4 y a diferencia de US3_PS6, **se esperan dos mínimos separados**: en openEMS (045) hay mínimos a 7,880 y 8,137 GHz. Si en HFSS aparece un único mínimo, la lámina probablemente se ignora (revisa las comprobaciones 1 a 3).
7. Alternativa si AEDT protesta por la lámina dentro de la caja del sustrato: partir el sustrato en `Substrate_lo` y `Substrate_hi` en z = `par_z`, como en US3_PS4.
8. *Convergencia del array.* En el perfil de convergencia de cada variación de `arr_d` comprueba que converge antes de `MaximumPasses` 15 (`MultiFrequency` en 3 frecuencias, ΔS 0,01). Si no converge, sube `MaximumPasses` antes de leer los acoplos.
9. *Message Manager.* No debe salir el aviso de línea de integración con números, y la línea de integración de P1 debe moverse al cambiar `arr_d`.
10. *`Cu_Parasitic`.* Comprueba que está en Boundary Display y que la lámina queda mallada tras la primera pasada. Un mínimo adicional o desplazado dentro del canal en HFSS se anota como diferencia con openEMS, no se corrige.

**Criterios pre-registrados para el contraste HFSS (hipótesis, fijadas antes de ver resultados; no son resultados).** Referencia openEMS, ronda 045 (malla base; `em/US3_PS4_2_1_OPENEMS_045`): mínimos de S11 a **7,880 y 8,137 GHz**; peor S11 del canal **−10,35 dB en 8,2368 GHz**, es decir, todo el canal ≤ −10 dB **por solo 0,35 dB** (no robusto: cualquier desplazamiento o diferencia de malla lo cruza); η (= *Radiated Power* / *Accepted Power*, `radiation_efficiency_Prad_over_Pacc`) mínima **0,273 a 8,137 GHz**, ganancia realizada broadside de **−0,07 a 4,22 dBi** en los 11 puntos de NF2FF. **Estatus (corrección del `design-reviewer`, 2026-11-16):** por su propia regla de decisión **US3_PS4_2_1 no es candidato** (η mín 0,273 < 0,30); HFSS se lanza **por decisión del propietario del 2026-11-16**, para contrastar el modelo y no para promover el diseño. **Malla fina, ronda 047 (informada al lado; las cotas de arriba NO se cambian):** mínimos 7,890 y 8,190 GHz, peor −11,38 dB en 7,7376 GHz, todo el canal ≤ −10 dB, η_rad mín 0,268 en 8,187 GHz, ganancia realizada −0,12…4,27 dBi; |ΔΓ| máx frente a 045 = 0,20 (resonancia superior +53 MHz). Con 047 y desfase 0, el mínimo superior (8,190) quedaría fuera de la ventana 8,03–8,16 GHz; se informa, no se reajusta.
- *Desfase esperado.* El desfase HFSS − openEMS se mide **contra la malla base 045** (de ella salen las ventanas de abajo); las cifras de la malla fina 047 se informan **al lado**, sin sustituirlas, cuando estén. HFSS − openEMS observado en P01_MS1 (−62 MHz) y US3_MS3 (−73 MHz): 60–75 MHz hacia abajo, **medido solo en diseños sin parásito**; no está medido en diseños con parásito, así que es una guía y no una predicción. Hipótesis: los dos mínimos de HFSS caen en **7,805–7,820 GHz** (7,880 − 60…75 MHz) y **8,062–8,077 GHz** (8,137 − 60…75 MHz), todavía dos mínimos separados.
- *H1 (S11).* Si la curva de openEMS 045 se limitara a trasladarse 60–75 MHz hacia abajo (aproximación de orden cero: la forma puede cambiar), el borde inferior de HFSS (7,7376 GHz) equivaldría a 7,80–7,81 GHz de openEMS (≈ −16 a −17 dB) y el superior (8,2368 GHz) a 8,30–8,31 GHz de openEMS (≈ −7,5 a −8 dB, con rejilla de 5 MHz). H1: **el peor S11 del canal en HFSS está en el borde superior, entre −7 y −10 dB** (cumple el mínimo de −6 dB pero probablemente no el objetivo de −10 dB en todo el canal), con el borde inferior mejor que −12 dB. Esto no es una predicción del resultado, solo una guía para leerlo. **Traslación de la curva 045** (peor S11 de la banda 7,7376–8,2368 GHz desplazada; calculada de `em/US3_PS4_2_1_OPENEMS_045/s11_complex.csv`, rejilla de 1 MHz, orden cero): 0 MHz −10,35 dB; −30 MHz −8,97 dB; −60 MHz −7,96 dB; −75 MHz −7,52 dB; −100 MHz −6,89 dB (siempre en el borde superior). **Un peor S11 ≤ −10 dB en HFSS refuta H1 por el lado favorable y no es una marca de fallo** (se anota como diferencia con la hipótesis, no como fallo del diseño).
- *H2 (eficiencia y ganancia).* En los 11 puntos de `Edges_and_f0` del elemento: **η ≥ 0,55** y **ganancia realizada broadside ≥ 2 dBi**, con **Dmax muestreado a θ ≤ 20° de broadside** (openEMS 045 ya da 20° en 5 de los 11 puntos y 15° en los otros 6, con rejilla de 5°). **Aquí se espera que H2 FALLE**: openEMS 045 da η 0,273 y ganancia realizada −0,07 dBi en 8,137 GHz (η de 0,27 a 0,35 y ganancia realizada de −0,07 a 0,94 dBi entre 8,087 y 8,187 GHz), por el valle de η ligado al modo superior, que sigue dentro del canal. Con un desfase de 60–75 MHz hacia abajo el valle caería en torno a 8,06–8,08 GHz, también dentro del canal; el fallo de H2 no depende del desfase. **Cómo calcular η en HFSS:** η = *Radiated Power* / *Accepted Power* del informe de antena (*Antenna Parameters*, `RadiationEfficiency`, a cada frecuencia de `Edges_and_f0` con campos): es la misma definición que `radiation_efficiency_Prad_over_Pacc` de `nf2ff_summary.json`. No uses la eficiencia total (*Radiated Power* / *Incident Power*, que incluye la desadaptación). La ganancia realizada de HFSS ya incluye la desadaptación.
- *Marcas de fallo (adaptadas a dos mínimos).*
  - Peor S11 en el canal peor que −6 dB (no cumple el mínimo de adaptación).
  - Un único mínimo o ninguno dentro de 7,6–8,3 GHz (la lámina se ignora o los dos modos se han fundido).
  - Primer mínimo fuera de 7,78–7,90 GHz o segundo fuera de 8,03–8,16 GHz (≈ 100 MHz de margen alrededor de la hipótesis de desfase).
  - Separación entre mínimos fuera de 200–330 MHz (openEMS 045: 257 MHz).
  - Valle de η (mínimo de η en los 11 puntos) por debajo de 0,2, o desplazado más de 100 MHz respecto del segundo mínimo de S11.
  Estos casos se comunican al propietario y no se corrigen con una sola pasada de HFSS.
- *Mismos límites que US3_PS4 y US3_PS6:* no se reajusta ninguna cota con una sola pasada de HFSS; el S11 de HFSS sin fichero real no existe; η y ganancia realizada se contrastan solo con los campos exportados. Un mínimo puntual no es cobertura del canal, y la derivada de la fase de S11 no es el retardo de grupo radiado.
- *Rango de `arr_d` recomendado para Optimetrics:* 16,5–19,5 mm cada 0,5 mm y 18,2 mm.

## US3_PS6_4: US3_PS6 con el parche más ancho (openEMS ronda 051, 2026-11-19)
`claude_pyaedt_ch9.DESIGNS["US3_PS6_4"]` reproduce [`variants/US3_PS6_4.json`](../variants/US3_PS6_4.json), la geometría simulada en openEMS en la ronda 051 (informe `reports/claude_run_051.md`). Lo comprueba `python build/claude_pyaedt_ch9.py --check` y `tests/test_hfss_us3_ps6_4.py`. **Estado: `GEOMETRY_ONLY` en HFSS**; no se ha ejecutado en AEDT, solo con un AEDT simulado. Referencia openEMS (no es un resultado de HFSS): ronda 050 (malla base), peor S11 −10,92 dB y mínimo a 7,936 GHz; ronda 051 (malla fina), −11,24 dB y 7,947 GHz; η_rad 0,65–0,71. Pre-registro de las hipótesis para HFSS: [`results/results_US3_PS6_4/preregistro_hfss.md`](results/results_US3_PS6_4/preregistro_hfss.md) (lo escribe `rf-designer`).

**Geometría** (cambios respecto de US3_PS6; el resto, igual: FR4 homogéneo εr 4,4, tanδ 0,017, h 2,07 mm, placa de 26 × 26 mm, cobre de 35 µm, U-slot, `patch_L` 6,29, parásito a z 1,035 mm, puerto de 50 Ω):
| Variable | US3_PS6 | US3_PS6_4 |
|---|---|---|
| `patch_W` | 11,421266 | **14,0** (x ±7,0; a 6,0 mm del borde de la placa en x) |
| `par_W` | 11,0 | **13,58** (x ±6,79: la misma holgura de 0,21 mm a cada lado) |
| `tr_w` × `tr_l` | 0,80 × 6,60 | **1,00 × 7,25** (Zt 94,9 Ω), y −10,395 → −3,145 |
| línea de 50 Ω (`line_w` 3,92) | y −13 → −9,745 (3,255 mm) | y −13 → **−10,395 (2,605 mm)** |
| `par_L`, `par_yc`, `par_z` | 7,05 / 0,615 / 1,035 | igual (y −2,91…4,14) |
| `u_Wu`, `u_Lu`, `u_t`, `u_y0` | 4,4 / 2,65 / 0,8 / −0,7 | igual |
- La parametrización de `claude_pyaedt_ch9.py` ya admitía `W`, `tr_w`, `tr_l` y `pW` por diseño (`DESIGNS` sobrescribe `COMMON`): no se tocó el código de construcción y los diseños existentes no cambian (se comprobó que las tablas `VARIABLES`, `FINITE_COND_ARGS`, `LUMPED_PORT_ARGS`, `SETUP_ARGS` y `SWEEP_ARGS` de los demás diseños son idénticas antes y después de regenerar).
- El parásito sigue siendo una lámina flotante (Finite Conductivity interna, sin vías); su borde −y (−2,91) queda 0,235 mm por encima del borde del parche en y.
- **Reservas del informe 051 que HFSS debe contrastar:** (1) el tramo de 50 Ω es de solo 2,605 mm (0,66 × su ancho): el puerto *lumped* queda más cerca del escalón 3,92 → 1,00 mm que en cualquier diseño anterior (3,21–3,255 mm), y su efecto sobre la impedancia en el plano del puerto no está validado; (2) la unión transformador-parche (1,00 mm contra un borde de 14 mm) tampoco; (3) el margen en x de la placa es de 6,0 mm (7,29 mm en US3_PS6), sin cuantificar el efecto de masa finita sobre el diagrama.

**Setup y barrido** (`SETUP_OVERRIDES["US3_PS6_4"]` y `EDGES_COUNT["US3_PS6_4"]`): 2 pasadas convergidas, ΔS ≤ 0,01, `SolveType` `MultiFrequency` en 7,7376 / 7,9872 / 8,2368 GHz a ΔS 0,01 y, **a diferencia de US3_PS6, `MaximumPasses` 25** (corrección E1 del `design-reviewer`; el resto del setup es el de US3_PS6, y los demás diseños siguen con 15). **Si no llega a ΔS 0,01 en dos pasadas convergidas, exporta la convergencia (`convergence.conv`) y no lo etiquetes como convergido.** Vigila la RAM (~400k tetraedros hacia la pasada 22) y el disco. `Sweep_7p5_8p5` interpolado (1001 puntos, 7,5–8,5 GHz) y `Edges_and_f0` de **11 puntos** en el elemento y **3 en el array** (corrección E4: en openEMS 051 η es plana, sin valle en el canal; solo `ARR1x5_US3_PS4_2_1` lleva 5). **5 puntos en el array solo servirían para ver un posible valle de η embebida (el acoplo entre elementos puede crearlo aunque el elemento aislado no lo tenga) y cuestan disco**; si se quisieran, basta añadir `, 5` a su entrada de `OUTPUTS` en `build/make_aedt_array_script.py` y regenerar.

**Scripts y nombres de diseño**
- Elemento: **`build/US3_PS6_4/claude_aedt_native_US3_PS6_4_ch9.py`** (valor fijo `["US3_PS6_4"]`). Diseño HFSS: `US3_PS6_4`. Puerto: *lumped* de 50 Ω en el borde de la placa (y = −13), como todos los demás.
- Array: `build/US3_PS6_4/claude_aedt_array1x5_US3_PS6_4_param_ch9.py`, diseño `ARR1x5_US3_PS6_4_dparam`, un puerto de 50 Ω y un parásito por elemento, `arr_d` **nominal 18,2 mm**, `board_x` = 4·`arr_d` + 2·`board_m`. Se generan con `build/make_aedt_native_script.py` y `build/make_aedt_array_script.py`.
- **Paso mínimo del array.** Con `patch_W` = 14,0 mm el hueco de cobre entre parches vecinos es `arr_d` − 14,0: a **13,5 mm los parches se solapan 0,5 mm** (el mínimo de la rejilla larga de P01_MS2 no vale aquí), a 14,0 mm se tocan y los parásitos (13,58) quedan a 0,42 mm. El **mínimo físico es 14,0 mm (cobre en contacto, no válido)** y el práctico **14,5 mm** (hueco de 0,5 mm, parásitos a 0,92 mm). El borde de la placa no limita (parche a 6,0 mm del borde en x para cualquier paso). `make_aedt_array_script.py` rechaza un paso nominal con hueco < 0,5 mm (`check_pitches`) y la cabecera del script lo anota.
- **Optimetrics → Parametric** sobre `arr_d` (corrección E3 del `design-reviewer`): **16,5–20,5 mm cada 0,5 mm más 18,2 mm** (9 valores de la rejilla + 18,2 = **10 pasos**). Los pasos más cortos (14,5–16,0 mm, hueco de cobre de 0,5–2,0 mm) quedan fuera por coste: cada variación es una resolución FEM de 5 puertos con hasta 25 pasadas. **Recomendación: lanza primero solo 18,2 mm (el nominal) para medir pasadas, tiempo, RAM y disco**, y amplía a la rejilla solo si caben. Opcional: un único punto a **15,0 mm** (hueco de 1,0 mm, parásitos a 1,42 mm) si se quiere un caso de acoplo fuerte; no está en la rejilla por defecto, así que habría que añadirlo a la tabla de Optimetrics y a las listas `ARR_D_MM`/`FIELDS_ARR_D_MM`. `make_aedt_array_script.py` mantiene `check_pitches` y `MIN_GAP_MM` = 0,5 (hueco mínimo de cobre entre parches). **Antes de lanzar el barrido marca Optimetrics → Parametric → Options → «Save Fields And Mesh»** (el exportador de campos solo saca los de la variación nominal si no).
- **Riesgo de disco.** US3_PS6 marcaba 834 MB libres en el equipo del propietario: *Save Fields And Mesh* con 10 variaciones y 5 puertos puede llenarlo. Comprueba el espacio libre antes de lanzar, y borra o mueve resultados ya exportados si hace falta.
- Exportación: `export/claude_aedt_export_array_ch9.py` y `export/claude_aedt_export_fields_ch9.py` (descomenta `DESIGN = "ARR1x5_US3_PS6_4_dparam"` y la línea de `ARR_D_MM`/`FIELDS_ARR_D_MM` de 16,5–20,5, esta última `[18.2, 16.5, 20.5]`), y `export/claude_aedt_export_element_ch9.py` (`DESIGN = "US3_PS6_4"`). Los resultados irán a `results/results_US3_PS6_4/` (`US3_PS6_4/` y `ARR1x5_US3_PS6_4_dparam/`, vacías por ahora).

**Contraste del escalón del puerto con un *wave port* (OBLIGATORIO antes de etiquetar el S11 como `HFSS_VALIDATED`; no aplicado todavía; corrección E2/E6 del `design-reviewer`).** El script deja el puerto *lumped* para poder comparar con los demás diseños y con openEMS. Pero la reserva 1 (tramo de 50 Ω de solo 2,605 mm entre el puerto y el escalón 3,92 → 1,00 mm) solo se descarta comparando con un puerto de modo propio. Se hace en **copias de control** del diseño, **solo para S11 y Zin**: no se usan para ganancia, eficiencia ni diagramas (la placa alargada y el puerto interno cambian el campo radiado). Todo se hace **a mano en la GUI de AEDT** (el propietario usa *Tools → Run Script* y no PyAEDT): no dependas de `hfss.wave_port` de PyAEDT, cuya geometría de lámina no se ha comprobado aquí.
1. **No pongas a 0 la caja de aire en −y** (la versión anterior de esta guía lo proponía): recortaría la radiación hacia −y y deformaría el S11 del propio parche. La región de aire conserva el margen `pad_xy` en −y.
2. **Wave port interno respaldado por una tapa PEC.** Pon la lámina del *wave port* dentro de la región de aire (no en su frontera de radiación) y cierra su cara trasera con una **tapa PEC de 1–2 mm** de grosor, de la misma sección que la lámina, en el lado −y.
3. **Tamaño de la lámina: ancho ≈ 12 mm y alto 8–10 mm sobre la masa**, centrada en x = 0. No uses 5·`line_w` = 19,6 mm (la recomendación anterior): deja propagar modos de caja. *Estimación orientativa, no verificada en AEDT:* una guía rectangular de aire de ancho *a* tiene el primer corte en c/(2a): 7,65 GHz para 19,6 mm (por debajo de la banda: se propaga) y 12,5 GHz para 12 mm; el FR4 bajo la tira baja esos cortes, así que las cifras son solo de orden de magnitud y por eso hace falta la comprobación del punto siguiente.
4. **Comprobación previa «Ports Only»** con **3 modos** a **8,5 GHz** (el extremo alto de las curvas): el modo 2 debe ser evanescente (constante de propagación atenuante, sin parte de fase apreciable) y la Z0 del modo 1 debe salir **50 ± 2 Ω**. Si el modo 2 se propaga o la Z0 se sale de 50 ± 2 Ω, reduce el ancho o el alto de la lámina y repite antes de resolver nada.
5. **Segunda copia con la línea alargada 10 mm hacia −y:** sustrato, masa y línea de 50 Ω alargados 10 mm hacia −y (la placa llega a y = −23; el extremo +y no cambia), alarga también la caja de aire 10 mm, y pon el puerto en **y = −23**. Hazlo editando las posiciones y tamaños de `Substrate`, `Ground`, `Line50`/`Patch` y `AirBox` desde sus propiedades (no cambies `board_y`: es simétrico en ±y y desplazaría también el borde +y).
6. **Referencia de fase (*deembed*) en esa segunda copia:** `deembed` de **10 mm** lleva el plano a **y = −13**, el mismo del *lumped* (comparable con el diseño original); `deembed` de **12,605 mm** (10 + 2,605) lo lleva **al escalón, y = −10,395**. Compara S11 y la impedancia de entrada de ambos contra el *lumped* original: una diferencia grande indicaría que el escalón cercano al puerto *lumped* sesga la medida.
7. El *wave port* da el modo cuasi-TEM de la línea; el *lumped* impone una tensión entre masa y tira sin modo propio y puede excitar modos de orden superior cerca del escalón. Un solo modo en el barrido principal.

*Las cifras de corte y de atenuación de este procedimiento son estimaciones de orden de magnitud, no resultados de HFSS: la comprobación del punto 4 las sustituye por el cálculo real del solver.*

**Control de convergencia del elemento (corrección E5; sin operaciones de malla en el nominal).** Para que la comparación con los demás diseños siga siendo válida, no añadas operaciones de malla al nominal del elemento. Para acotar el error de convergencia: (1) repite el elemento con **ΔS 0,005** o con **3 pasadas más** y compara el **mínimo de S11 y el peor S11 del canal**; (2) compara el barrido interpolado (`Sweep_7p5_8p5`) frente a los 11 puntos discretos de `Edges_and_f0`: **|ΔΓ| ≤ 0,005** en cada frecuencia; (3) ten en cuenta que **ΔS 0,01 equivale a unos ±0,3 dB alrededor de −10 dB** (|Γ| = 0,316; una variación de 0,01 en |Γ| son 0,27 dB), es decir, el margen de −10 dB del objetivo preferido está dentro del error de convergencia. *Opcional, solo en el array:* siembra de malla (*Length Based*) de **≤ 1,5 mm** en `Patch_i` y `Parasitic_i`.

**Riesgos a tener en cuenta.** (1) *Disco:* US3_PS6 marcaba 834 MB libres; *Save Fields And Mesh* con 10 variaciones y 5 puertos puede llenarlo (ver el barrido de `arr_d`). (2) *RAM:* hacia la pasada 22 se esperan ~400k tetraedros. (3) `PeakRealizedGain` de `antenna_params.csv` es **lineal** y **de pico** (máximo en cualquier dirección), **no la ganancia realizada en broadside**: para la ganancia realizada broadside de la H2 usa `dB(RealizedGainTotal)` de `realized_gain_cuts.csv` en θ = 0°, o convierte `PeakRealizedGain` con 10·log10 sabiendo que es el pico y no el valor en θ = 0°.

**Comprobaciones tras construir** (en AEDT; las de US3_PS6, adaptadas): *Validation Check* sin avisos sobre `Parasitic`; las variables valen `patch_W` = 14 mm, `patch_L` = 6,29 mm, `par_W` = 13,58 mm, `par_L` = 7,05 mm, `par_yc` = 0,615 mm, `tr_w` = 1 mm y `tr_l` = 7,25 mm; el transformador acaba en y = −3,145 mm y empieza en −10,395 mm; el borde −y del parásito queda en y = −2,91 mm; un único puerto de 50 Ω en y = −13 mm (cinco en el array, con la línea de integración desplazada al cambiar `arr_d`); en el array, ningún solape entre parches en todo el rango de `arr_d`. Un segundo mínimo dentro del canal en HFSS se anota como diferencia con openEMS, no se corrige.

**Hipótesis (fijadas antes de ver resultados; no son resultados).** Las hipótesis H0/H1/H2 y la regla de decisión de esta variante están pre-registradas en `variants/US3_PS6_4.json` (`pre_registered_hypothesis`) para openEMS; para HFSS vale la lectura de orden cero de US3_PS6: mínimo de S11 unos 50–75 MHz por debajo del de openEMS (en torno a 7,86–7,89 GHz con la malla base, según el desfase HFSS − openEMS observado en P01_MS1, −62 MHz, y US3_MS3, −73 MHz; el JSON de la variante estima unos 50 MHz), peor S11 en el borde superior del canal y η ≥ 0,55 con ganancia realizada broadside ≥ 2 dBi en los 11 puntos. η = *Radiated Power* / *Accepted Power* (`RadiationEfficiency`), la misma definición que `radiation_efficiency_Prad_over_Pacc` de openEMS. No se reajusta ninguna cota con una sola pasada de HFSS; un mínimo puntual no es cobertura del canal y la derivada de la fase de S11 no es el retardo de grupo radiado. Rango de `arr_d` recomendado para Optimetrics: 16,5–20,5 mm cada 0,5 mm y 18,2 mm (10 pasos; empezar solo por 18,2 mm).

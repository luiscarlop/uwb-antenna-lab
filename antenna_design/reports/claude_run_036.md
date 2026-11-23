# Ronda Claude 036: US3_PS4, parásito enterrado con las dos resonancias desplazadas hacia arriba

- **ID del experimento:** US3_PS4_OPENEMS_036.
- **Fecha:** 2026-11-16, ronda 36/40.
- **Orquestador:** `claude-opus-5-5`.
- **FDTD:** 1, con malla base y `--max-timesteps 60000`.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.
- **Veredicto de `validator`:** **OK con observaciones**.

## Origen y cambio
- **Primera petición del propietario:** acercar las dos resonancias de US3_PS1 (032: 7,675 y 8,03 GHz). Después la cambió: subir la principal y mantener la segunda.
- El `rf-designer` mostró que con el parásito enterrado la separación tiene un suelo de ≈ 335 MHz por el acoplo. Subir solo la principal daba unos +12 MHz, por debajo de la incertidumbre de malla. Esa versión no se simuló y queda guardada en [`variants/US3_PS4_rf_designer_alternative.json`](../variants/US3_PS4_rf_designer_alternative.json).
- **Decisión final del propietario: desplazar las dos ≈ 140 MHz hacia arriba.**

[`variants/US3_PS4.json`](../variants/US3_PS4.json) parte de US3_PS1 con:
- `patch_L` 6,502 → **6,302 mm**;
- parásito Lp 7,60 → **7,46 mm**;
- centro del parásito en y 0,80 → 0,75 mm (y −2,98…+4,48). Es un **tercer parámetro, forzado por la malla**: con los centros 0,78–0,82 la gradación en y superaba 1,5 frente al nuevo borde del parche, −3,151.
- Derivados de la alimentación: borde del parche −3,151, transformador desde −9,751, tramo de 50 Ω de 3,249 mm.
- Sin cambios: U, transformador 0,8 × 6,6 mm, z del parásito 1,035 mm, Wp 11 mm, material, placa y puerto.

**Trazabilidad del JSON.** La geometría que se simuló es la de los polígonos (`patch_polygon_mm`, `parasitic_patches[0].polygon_mm`, `feed`) y la de `changed_vs_previous`. Otros campos del mismo fichero vienen de la versión del `rf-designer` y **describen la geometría no simulada**: `parasitic_params`, `parasitic_patches[0].note`, `rationale`, `computation.predicted_shift_PS4_mhz`, `geometry_checks`, `purpose`, `mesh_hint_note` y `risks`. El fichero no se reescribe, para que su SHA siga coincidiendo con el del run (`d01cb125…`). La decisión real está en `owner_decision_2026_11_16`.

## Ejecución
- Converge a −51,02 dB en 34 892 pasos, en 657 s y 0,46 GB con 2 CPU.
- 2,31 M celdas, malla base.
- Los volcados NF2FF brutos se borraron tras guardar sus hashes; solo queda `nf2ff.h5`.

## Resultados (malla base)
Los valores del canal son de la rejilla de 1 MHz (`s11_complex.csv`); el resto, de la rejilla de 5 MHz (`s11_wideband.csv`).

| | US3_PS1 (032) | **US3_PS4 (036)** | P01_MS2 (027) |
|---|---|---|---|
| Mínimos de S11 | 7,675 / 8,03 GHz | **−30,2 dB en 7,826 GHz y −32,2 dB en 8,158 GHz** | −22,3 dB en 7,99 GHz |
| Banda de −10 dB | 7,49–8,115 GHz | **7,631–8,245 GHz (614 MHz)** | 7,724–8,306 GHz |
| Peor S11 en el canal | −5,96 dB | **−10,66 dB** (8,2368 GHz) | −10,42 dB |
| η en el canal | 0,64 → 0,23 → 0,51 | 0,677 → 0,615 (7,937) → **0,244 (8,137)** → 0,373 | 0,73–0,76 |
| Ganancia realizada broadside | 4,1 → −0,6 dBi | 4,3 → **−0,48 dBi (8,187)** | 4,3–4,8 dBi |

## Hipótesis
- **H0 se cumple.** Los dos mínimos suben +150 y +130 MHz y mantienen la separación de ≈ 335 MHz. Eso es coherente con un desplazamiento común de los dos modos acoplados.
- **H1 se cumple en malla base**, incluido el −10 dB preferido. El margen en el borde superior es mínimo: se pierde el −10 dB en 8,245 GHz, 8 MHz por encima del canal, con 0,66 dB de margen. Es menor que la incertidumbre de malla (≈ 13 MHz) y no hay malla fina.
- **H2 falla, como se predijo:**
  - η < 0,55 en 5 de los 11 puntos (8,037–8,237 GHz);
  - ganancia realizada < 2 dBi en 4 de los 11 (8,087–8,237 GHz).

## Lectura
- **«Adaptación asistida por pérdidas en la mitad superior del canal, mecanismo por confirmar.»**
  - El valle de η coincide con el mínimo superior de S11 y se desplaza con él. El modo inferior conserva η ≈ 0,66.
  - No se ha separado la pérdida dieléctrica de la metálica (no hay control con tanδ = 0).
  - El valle está muestreado con 11 puntos (50 MHz); su mínimo y su anchura reales son desconocidos.
- **El −10,66 dB no es una mejora de la antena** sin su contrapartida: η 0,24–0,37 y ganancia ≤ 0,5 dBi en el extremo superior del canal. Para una señal real, US3_PS4 es peor que P01_MS2.
- **Siguiente paso, por instrucción del propietario:** S11 comparable a US3_PS1 y mejor centrado, así que `design-reviewer` (Fable) asesora un cambio de diseño para que el modo superior radie.

## Estado
Ronda 36/40. Queda 1 refinamiento de este candidato (rondas 37–40 disponibles).

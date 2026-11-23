# Ronda Claude 033: US3_PS2, apilado invertido (U-slot enterrado y parásito en la cara superior)

- **ID del experimento:** US3_PS2_OPENEMS_033.
- **Fecha:** 2026-11-15, ronda 33/40.
- **Origen:** decisión del propietario tras las rondas 031–032 («invertir el apilado»).
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:**
  - `em-solver` añadió la capa excitada enterrada (`driven_z_mm`, commit `42453de`, 25 tests nuevos). Sin la clave, las variantes existentes no cambian.
  - `rf-designer` diseñó la variante.
- **FDTD:** 1, con malla base y `--max-timesteps 60000`.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.
- **Veredicto de `validator`:** **OK con observaciones**, sin hallazgos críticos.

## Propuesta
[`variants/US3_PS2.json`](../variants/US3_PS2.json):
- **Capa interior a z_d = 1,29375 mm:** parche excitado de 11,421 × 6,42 mm con la U de US3_MS3, línea de 50 Ω enterrada de 2,10 mm y transformador de 0,50 × 5,70 mm.
  - Las impedancias salen de un solver electrostático 2D del `rf-designer`: Z0 ≈ 50 Ω y Zt ≈ 89 Ω. Son una estimación (GUIDE_MODEL) que el run no confirma.
  - Con la línea enterrada, Zt queda limitado a ≈ 89 Ω para el ancho mínimo de 0,5 mm.
- **Cara superior:** parásito de 11,421 × 7,15 mm.
- FR4 homogéneo εr 4,4, tanδ 0,017, 2,07 mm.
- Puerto concentrado de 0 a z_d en el borde. Es una idealización: no hay vía ni lanzamiento del conector.
- **No es un cambio de una sola variable frente a PS1:** cambian L, la línea, el transformador, z_d y la separación entre metales.

## Ejecución
- Converge a **−50,07 dB en 22 248 pasos**, en 484 s y 0,49 GB con 2 CPU.
- 2,42 M celdas; en z hay 5 + 3 celdas de 0,259 mm.
- Los bordes del transformador (x = ±0,25 mm) y de la línea (±1,05 mm) no caen sobre líneas de malla en x (desfase de 0,06–0,08 mm). El ancho efectivo del transformador tiene una incertidumbre de ≈ ±12 %, lo que pesa sobre Zt y sobre el nivel de Re(Zin).

## Resultados (malla base)
| | US3_PS1 (032) | **US3_PS2 (033)** |
|---|---|---|
| Mínimo principal de S11 | 7,675 y 8,03 GHz | **−13,3 dB en 7,085 GHz** (fuera del canal) |
| Segunda característica | | débil: −4,3 dB en 8,06 GHz (Re ≈ 14 Ω) |
| Re(Zin) en el puerto, dentro del canal | | ≈ 9–14 Ω |
| Peor S11 en el canal | −5,96 dB | **−2,73 dB** (ningún punto llega a −6 dB) |
| η en el canal (11 puntos) | 0,64 → 0,23 → 0,51 | **0,54 → 0,69 (f0) → 0,72**, monótona |
| Ganancia realizada broadside | −0,6 dBi en f0 | 0,2–3,0 dBi |
| Dmax | | 6,9 dBi en θ 15–20°, φ 270° (rejilla de 5°) |

## Hipótesis
- **H1 falla.** Aparece una segunda característica débil, pero el peor caso es −2,73 dB. La respuesta fuerte cae unos 0,9 GHz por debajo de f0.
- **H2 falla** en dos puntos: η 0,539 en 7,7376 GHz y 0,584 en 7,7875 GHz, por debajo de 0,6. Dmax en θ = 20°, en el límite.
- **H3_null no es aplicable:** estaba definida para un S11 bueno. El valle de η **no aparece en los 11 puntos del canal**, pero un modo poco radiante podría haberse movido fuera de ellos (el NF2FF no cubre 7,0–7,2 GHz). Que el parásito enterrado causara el valle de PS1 sigue siendo una **hipótesis**.

## Decisión
- Refinamiento 1 (ronda 034, US3_PS3, diseñado por `rf-designer`): retocar la geometría para subir la resonancia al canal.
- Queda un refinamiento más para este candidato.

## Reservas (validator)
1. Lectura de H3_null (arriba).
2. Malla en los bordes de la línea y del transformador (arriba). La desintonía de 0,9 GHz y el nivel de Re(Zin) son provisionales hasta una malla fina.
3. η es Prad/Paceptada. La eficiencia total en el borde superior es ≈ 0,42 por la desadaptación.
4. Retardo de grupo radiado solo como diagnóstico.
5. FR4 provisional, puerto idealizado, sin conector.

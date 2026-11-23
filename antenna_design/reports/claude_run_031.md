# Ronda Claude 031: US3_PS1, U-slot con parche parásito enterrado

- **ID del experimento:** US3_PS1_OPENEMS_031.
- **Fecha:** 2026-11-15, ronda 31/40, en la sesión del propietario. Petición: «simular el mejor U-slot añadiéndole una capa parásita intermedia».
- **Orquestador:** `claude-opus-5-5`.
- **Trabajo de los subagentes:**
  - `rf-designer` diseñó la variante.
  - `em-solver` añadió a `em/patch_openems.py` el soporte de parches parásitos enterrados (commit `bca8ea2`, 20 tests nuevos). Las variantes sin parásito dan un XML idéntico byte a byte.
- **FDTD:** 1, con malla base.
- **Evidencia:** `EM_SIMULATED`, con el run **truncado**: llegó al tope NrTS de 30 000 pasos con la energía en −43 dB.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Contexto bibliográfico (sin verificar en las fuentes completas)
- Un parche parásito añade una segunda resonancia acoplada, y la banda se ensancha si las dos están próximas.
- El tamaño del parásito y su separación del parche excitado fijan el acoplo, pero también desplazan las frecuencias.
- Las guías habituales (Waterhouse 1999; K.-F. Lee, *Microstrip Patch Antennas*) son para parches alimentados por sonda sobre aire o espuma, no para FR4 con línea microstrip.
- El elemento del artículo EuCAP usa un parásito enterrado bajo el parche excitado.

## Propuesta
[`variants/US3_PS1.json`](../variants/US3_PS1.json) es US3_MS3 con **un solo cambio: se añade un parche parásito enterrado** `par1`.
- Lámina de cobre de 11,0 × 7,6 mm (x ±5,5 mm, y de −3,0 a +4,6 mm) a z = 1,035 mm (h/2), sin vías.
- Sustrato homogéneo: FR4 provisional εr 4,4, tanδ 0,017, 2,07 mm en total.
- Parche, U, línea con transformador, placa y puerto iguales a US3_MS3.
- Estimación guía (GUIDE_MODEL), no resultado:
  - resonancia del parásito ≈ 7,99 GHz ± 4 %;
  - acoplo necesario k ≈ 0,04–0,05;
  - banda ≈ 1,5 veces la de US3_MS3.
- Hipótesis pre-registradas:
  - H1: segunda característica y peor caso ≤ −8,5 dB.
  - H2: η ≥ 0,55 y Dmax a menos de 20° de broadside.

## Ejecución
- **Comando:** el mismo que la ronda 023 (malla base, puerto concentrado, NF2FF de 11 puntos, fc 2,5 GHz), con `timeout 1500s` y `taskset -c 0,1`.
- **Malla:** unos 2,25 M celdas. En z hay 4 + 4 celdas de 0,259 mm (masa–parásito y parásito–parche). Gradación ≤ 1,42.
- **Recursos:** 644 s de pared y 0,46 GB, con 2 CPU.
- **Fin:** el run llegó a **NrTS = 30 000 sin alcanzar −50 dB** (energía final −43 dB). La ronda 023 había convergido en 11 232 pasos.
- Los volcados NF2FF brutos se borraron tras guardar sus hashes. `solver.log` se guarda como `solver_log.txt`.

## Resultados (malla base)
| | US3_MS3 (023) | **US3_PS1 (031)** |
|---|---|---|
| Mínimos de S11 | 1: −16,4 dB en 7,98 GHz | **2: ≈ −32 dB en 7,675 GHz y ≈ −26 dB en 8,03 GHz** (±1 dB, la profundidad no está convergida) |
| Lazo en la carta de Smith | no | **sí**: cruces X = 0 en 7,68, 7,88 y 8,03 GHz |
| Banda de −10 dB | 7,80–8,17 GHz | 7,49–8,115 GHz |
| Tramo ≤ −10 dB dentro del canal | 375 MHz | **378 MHz** (sin ganancia dentro del canal) |
| Peor S11 en el canal | −8,18 dB | **≈ −6,0 dB** en 8,2368 GHz (en el umbral) |
| Eficiencia de radiación | 0,65–0,67 | **0,64 → 0,23 (f0) → 0,51** |
| Ganancia realizada broadside en f0 | 4,0 dBi | **−0,6 dBi** |

- **Truncamiento** (análisis del validator): recortar el registro al 80–95 % cambia S11 en ≤ 0,014 y la potencia aceptada en ≤ 1,6 %. Los bordes de banda quedan fijados a ±3 MHz. La profundidad de los mínimos no está convergida.
- **Valle de eficiencia:** la potencia aceptada se mantiene casi constante y la radiada cae. El truncamiento no lo explica.
- **Hipótesis no probada:** el segundo modo radia poco (modo «oscuro», con corrientes en contrafase en parche y parásito) y disipa en el FR4 (tanδ 0,017). Sería una adaptación por pérdidas. No hay volcados de campo, así que no está identificado qué modo es el del parásito.

## Hipótesis
- **H1 falla** por el peor caso (≈ −6,0 dB frente a −8,5 dB), aunque la segunda resonancia sí aparece (k ≈ 0,045). La respuesta se desplaza unos 0,1 GHz hacia abajo respecto a la guía.
- **H2 falla** por la eficiencia (0,23 en f0).

## Decisión
- **No es candidato.** No va a Fable ni a HFSS.
- **Siguiente paso (validator):** repetir la misma geometría con NrTS = 60 000 (ronda 032, diagnóstico, sin cambio geométrico) para cerrar la duda sobre η y el NF2FF.
- **Control opcional después:** la misma geometría con tanδ = 0.
- No gastar refinamientos en patch_L ni en Lp hasta saber si el valle de η es disipación inherente al parásito enterrado.

## Reservas (validator)
1. Run truncado a −43 dB (ver arriba).
2. La causa del valle de η no está probada.
3. «Banda de 625 MHz» engaña: dentro del canal no hay ganancia de banda.
4. La malla base de 031 no es idéntica a la de 023: el parásito añade líneas x/y. Diferencias de ~13 MHz o ~0,15 dB no se deben atribuir al parásito.
5. FR4 homogéneo provisional; sin conector; metal como lámina ideal.

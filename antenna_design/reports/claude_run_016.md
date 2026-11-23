# Ronda Claude 016: US3, se acortan los brazos de la U (Lu)

- **ID del experimento:** US3_FINE_OPENEMS_016.
- **Fecha:** 2026-11-04, de 21:13 a 21:30 UTC aproximadamente. Ronda 16/40.
- **Orquestador:** `claude-opus-5-5`, con auditoría de `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED` con una sola malla (la fina, que es la de evaluación de la serie). **La convergencia no está establecida.**
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Propuesta
[`variants/US3.json`](../variants/US3.json) es US2 con **una sola variable cambiada: Lu, de 3,2 a 2,65 mm**.
- Lo que cambia como consecuencia: la parte superior de la U baja de y = 2,5 a 1,95 mm, la distancia de la ranura al borde sube de 0,925 a 1,475 mm y la longitud media de la U baja de 9,2 a 8,1 mm.
- Lo que no cambia: L 6,85 mm, W, t, y0, la sonda, el material y la placa.

## Hipótesis registrada antes (ronda 015) y resultado
- **Predicción principal:** volvería a aparecer al menos un cruce de X = 0 en 7–9 GHz. **No se cumple:** no hay ningún cruce en todo el rango de 5,46 a 10,52 GHz. **La hipótesis queda refutada.**
- **Predicción secundaria:** la banda de −6 dB se ensancharía. **Se cumple:** pasa de 515 a unos 587 MHz (bordes muestreados de 7,682 a 8,269 GHz).
- La explicación alternativa de que X se acerca a 0 **no** la respaldan los datos: el mínimo local de X sube de 6,1 a 16,8 Ω.
- Lo que sí se observa: el máximo de R pasa de 7,37 a 7,58 GHz, y en f0 Zin pasa de 27 + j37 Ω a 59 + j22 Ω. Sin campos ni corrientes no se puede saber qué modo lo causa.
- La «resonancia de la U en 7,1–7,2 GHz» que usé en el pre-registro no estaba identificada con evidencia EM.

## Recursos
- 5,11 M celdas.
- 292 s de pared con 2 CPU y 0,91 GB de RSS.
- 6848 pasos; energía hasta −51,9 dB.
- El presupuesto estimaba 1264 s, unas 4,3 veces más que el tiempo real.

## Resultados (malla fina)
| | US2 (015) | **US3 (016)** |
|---|---|---|
| S11 en el canal | −2,68 … −17,16 dB | **−6,65 (8,2368 GHz) … −13,64 dB (7,972 GHz)** |
| ≤ −6 dB en las 501 muestras | no | **sí, con 0,65 dB de margen** |
| ≤ −10 dB | no | no (banda de −10 dB de 7,833 a 8,112 GHz) |
| Banda de −6 dB (muestreada) | 7,465–7,980 GHz | 7,682–8,269 GHz (unos 587 MHz) |
| Eficiencia de radiación | 0,74–0,75 | **0,79–0,81** |
| Ganancia realizada en broadside | 0,9–5,2 dBi | **4,35–5,42 dBi** |
| Directividad en broadside | — | 6,35–6,71 dBi |
| Retardo copolar (diagnóstico) | 0,274 ns, rizado de 192 ps | 0,290 ns, **rizado de 46 ps** (38 ps sin los extremos) |

Hasta ahora, **US3 es el mejor resultado en malla fina de toda la campaña**. Aun así, **no se acepta** sin la verificación de convergencia que exige el propietario.

## Regla de convergencia (fijada ahora, antes de simular)
Comparación de la malla fina con la `xfine` (fine × 0,7), con US3 sin ningún otro cambio y sobre la rejilla de 1 MHz del canal:
1. **Se acepta** el cumplimiento de −6 dB solo si el peor S11 con `xfine` es ≤ −6,0 dB y el cambio frente a la malla fina es ≤ 0,5 dB.
2. La diferencia en Γ complejo debe ser ≤ 0,03 en todo el canal, y los bordes de −6 dB no deben moverse más de 10 MHz.
3. Debe cumplirse lo mismo en energía (≤ −50 dB), `port_validity` OK y |S11| ≤ 1,02.
4. Si el cambio está entre 0,5 y 1 dB, el resultado es «sensible a la malla» y no se afirma el cumplimiento. Si supera 1 dB, la malla no converge.
5. Con dos mallas se habla de «sensibilidad acotada», no de «convergencia».

El perfil `xfine` ya está añadido al script (xy 0,245 mm, aire z 0,42 mm, 14 celdas en el sustrato, borde 0,1225 mm). Los XML congelados no cambian.

## Bloqueo de presupuesto: decide el propietario
`prepare` con `xfine` da **13,86 M celdas** y unos 4,2 GiB de RAM (con margen ×2).
- La regla calcula con 53 Mcell·paso/s, lo que da **3747 s sin NF2FF** y 4671 s con NF2FF.
- Ambos superan los 2700 s autorizados, así que el script **no lanza la simulación**.
- Con la velocidad realmente medida (134–170 M) tardaría unos 15–20 minutos.
- No se cambia ni la tasa ni el límite sin autorización del propietario.

## Estado
- Ronda 16/40. Campaña ACTIVE.
- La verificación de US3 está **pendiente de decisión del propietario**.

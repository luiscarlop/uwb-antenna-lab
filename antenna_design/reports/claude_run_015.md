# Ronda Claude 015: US2, solo cambia la longitud L

- **ID del experimento:** US2_FINE_OPENEMS_015.
- **Fecha:** 2026-11-04, de 20:58 a 21:12 UTC aproximadamente. Ronda 15/40.
- **Orquestador:** `claude-opus-5-5`, con auditoría de `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`. El retardo radiado es solo DIAGNÓSTICO.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Propuesta
[`variants/US2.json`](../variants/US2.json): US1 con **una sola variable cambiada, L de 7,67 a 6,85 mm**.
- La sonda pasa de y = −2,608 a −2,329 mm porque se mantiene s/L. Es consecuencia del cambio de L, no otra variable.
- La ranura es idéntica.
- Al acortar L, el margen entre la ranura y el borde del parche baja a 0,925 mm (era 1,3 mm en US1).

## Recursos
- 4,99 M celdas.
- 306 s de pared con 2 CPU y 0,91 GB de RSS.
- 7722 pasos, con la energía hasta −50,1 dB.

## Resultados (malla fina)
| | US1 (014) | US2 (015) |
|---|---|---|
| S11 en el canal | −1,38 … −3,81 dB | −2,68 (8,2368 GHz) … −17,16 dB (7,7376 GHz) |
| Mínimo | −25,7 dB en 7,30 GHz | −17,4 dB en 7,725 GHz |
| Banda a −6 dB | 7,010–7,595 GHz (585 MHz) | 7,465–7,980 GHz (515 MHz) |
| Banda a −10 dB | 7,135–7,470 GHz (335 MHz) | 7,585–7,860 GHz (275 MHz) |
| Cruces de X = 0 | 7,10 y 7,24 GHz | **ninguno**: el bucle desaparece |
| Eficiencia de radiación | 0,76–0,77 | 0,74–0,75 |
| Ganancia realizada en broadside | 2,8 → −1,8 dBi | 5,2 → 0,9 dBi |
| Retardo copolar (diagnóstico) | 0,129 ns, rizado de 100 ps | 0,274 ns, rizado de 192 ps |

- El canal **no** cumple −6 dB: la banda de −6 dB solo cubre unos 242 MHz de los 499,2 MHz.
- Acortar L sube la respuesta unos 425 MHz, pero separa el modo del parche y el de la U, así que se pierde el ensanchamiento de banda.

## Hipótesis falsable para la ronda 016 (registrada antes de simular)
- **Variable única:** Lu de 3,2 a **2,65 mm**.
- **Razonamiento:** la longitud media de la U pasa de 9,2 a unos 8,1 mm, lo que subiría su resonancia de unos 7,1–7,2 a unos 8,1 GHz (escala ~1/l; es una estimación).
- **Predicción:** **reaparece al menos un cruce de X = 0 en 7–9 GHz** (el bucle de doble resonancia) y la banda de −6 dB se ensancha respecto a US2.
- **Se descarta la hipótesis** si no aparece ningún cruce de X = 0 en 7–9 GHz.
- **Sin cambios:** L = 6,85 mm, W, t, y0, la sonda, el material y la placa.
- Por la regla de convergencia del propietario, ninguna mejora se acepta sin la malla xfine.

## Estado
- Ronda 15/40. Campaña ACTIVE.
- **CONTINUE.**

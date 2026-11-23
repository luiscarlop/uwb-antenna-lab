# Ronda Claude 014: US1, primera U-slot

- **ID del experimento:** US1_FINE_OPENEMS_014.
- **Fecha:** 2026-11-04, de 20:37 a 20:55 UTC aproximadamente.
- **Ronda:** 14/40.
- **Orquestador:** `claude-opus-5-5`, con auditoría de `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`. Solo hay una malla para US1 (la fina, que es la de evaluación de la serie), así que la convergencia no está establecida.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Propuesta
[`variants/US1.json`](../variants/US1.json): US0 más una ranura en U abierta hacia +y, con Wu 4,4 mm, Lu 3,2 mm, t 0,8 mm e y0 −0,7 mm.
- Se comparan una sola variable: la presencia de la ranura.
- Se mantienen la sonda de 50 Ω, el FR4 de 2,07 mm y la placa.
- Las dimensiones de la ranura son hipótesis de diseño. **No proceden del artículo.**

## Recursos
- 4,99 M celdas.
- 263 s de pared con 2 CPU y RSS de 0,91 GB.
- 7446 pasos, con la energía decayendo hasta −50,5 dB.
- La ranura se resuelve con unas 5 celdas a lo ancho y una relación entre celdas vecinas de 1,40.

## Resultados frente a US0 (malla fina en los dos)
| | US0 (013) | US1 (014) |
|---|---|---|
| S11 en el canal | −5,70 … −8,60 dB | **−1,38 … −3,81 dB** |
| Mínimo de S11 | −8,60 dB en 7,95 GHz | **−25,7 dB en 7,30 GHz** |
| Banda a −6 dB | 7,700–8,210 GHz (510 MHz, 6,4 %) | 7,010–7,595 GHz (**585 MHz, 8,0 %**) |
| Banda a −10 dB | ninguna | 7,135–7,470 GHz (335 MHz) |
| Cruces de X = 0 | ninguno | 7,10 y 7,24 GHz (doble resonancia, bucle en la carta de Smith) |
| Eficiencia de radiación | 0,84–0,86 | 0,76–0,77 |
| Ganancia realizada en broadside | 4,5–5,3 dBi | 2,8 → −1,8 dBi (desadaptada en el canal) |
| Retardo copolar (diagnóstico) | 0,249 ns, rizado de 37 ps | 0,129 ns, rizado de 100 ps |

## Interpretación
- La U-slot produce el efecto esperado: **un bucle de doble resonancia que ensancha la banda de −6 dB un 15 %** y adapta muy bien en el centro.
- Pero también **baja la frecuencia**, de unos 7,95 a 7,30 GHz.
- La caída de eficiencia es plausible (más energía almacenada y pérdidas del FR4), pero no está demostrada.
- Los 335 MHz a −10 dB no cubrirían los 499,2 MHz del canal ni aunque la respuesta estuviera centrada.

## Decisión para la ronda 015
- `validator` desaconsejó reescalar de forma uniforme: cambia 6 o 7 variables y, como h no escala, tampoco escala la frecuencia.
- **US2 = US1 con solo L cambiada, de 7,67 a 6,85 mm.**
  - Se calcula escalando L_eff = L + 2ΔL (ΔL = 0,909 mm) por 7,30/7,9872.
  - La sonda pasa de y = −2,608 a y = −2,329 mm por mantener s/L. Es una consecuencia del cambio de L, no una segunda variable.
  - La ranura, y0, W, el material y la placa no cambian.
  - Es una estimación: la resonancia propia de la U no se escala con L.
- `validator` mencionó L de 11,42 a unos 10,3–10,5 mm, pero 11,42 es W, no la dimensión resonante. Se corrige aquí.

## Estado
Ronda 14/40. Campaña ACTIVE. **CONTINUE.**

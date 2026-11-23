# Ronda Claude 028: P01_MS2 con malla fina, pasa la regla de −10 dB

- **ID del experimento:** P01_MS2_FINE_OPENEMS_028.
- **Fecha:** 2026-11-13. Ronda 28/40, en la sesión del propietario.
- **Orquestador:** `claude-opus-5-5`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**. Es correcto declarar `BOUNDED_SENSITIVITY_PASS` para −10 dB en openEMS y pasar a `READY_FOR_HFSS_REVIEW`.
- **Incidencia:** el primer `prepare` olvidó `--owner-long-convergence` (autorización del propietario, hasta 4000 s). La regla de presupuesto paró el solve antes de empezar: no se creó `run_started.json`. Se preparó de nuevo con las mismas opciones que la ronda 026.

## Regla (fijada en [`claude_run_027.md`](claude_run_027.md) antes de simular)
| Condición | Resultado |
|---|---|
| Peor S11 ≤ −10 dB en las dos mallas | **sí**: −10,42 dB (base) y −10,36 dB (fina), ambos en 7,7376 GHz; ninguna muestra por encima de −10 dB |
| \|ΔΓ\| ≤ 0,03 en el canal | **sí**: 0,0291 (en 7,7376 GHz) |
| Bordes de −10 dB contiguos con f0 ≤ 10 MHz | **sí**: 7,724–8,306 → 7,726–8,305 GHz (+2 / −1 MHz) |
| Energía ≤ −50 dB, puerto OK, \|S11\| ≤ 1,02 | **sí**: −50,05 dB en 13 724 pasos; \|S11\| máx 0,53 |

**Veredicto: `BOUNDED_SENSITIVITY_PASS` para −10 dB en todo el canal 9 (openEMS).** Es la primera vez en la campaña.

Fichero: [`mesh_comparison.json`](../em/P01_MS2_FINE_OPENEMS_028/mesh_comparison.json).

Recursos: 5,20 M celdas, 744 s de reloj, 1351 s de CPU, 2 CPU y 0,94 GB de RSS.

## Campo lejano (malla fina)
| Magnitud | Valor |
|---|---|
| Eficiencia de radiación | 0,726–0,762 |
| Ganancia realizada en broadside | 4,33–4,81 dBi |
| Balance de potencia | correcto |

Prácticamente igual que con la malla base (027).

## Reservas obligatorias (validator)
1. **Margen de energía casi nulo:** −50,05 frente a −50,00 dB, y la curva no baja de forma monótona. En \|ΔΓ\| se mezclan el efecto de la malla y el truncamiento de la DFT.
2. **\|ΔΓ\| queda a 0,0009 del límite.** Se da en el borde inferior, que es además donde S11 es peor.
3. **Dos mallas no demuestran convergencia.** Solo acotan la sensibilidad a la malla.
4. **HFSS da resonancias un 0,9 % más bajas aproximadamente.** Si se aplica ese desplazamiento, S11 en 8,2368 GHz quedaría en unos **−9,9 dB**, así que **−10 dB podría no cumplirse en HFSS**. Es lo primero que hay que comprobar.
5. **FR4 provisional:** εr 4,4, tanδ 0,017, 2,07 mm.
6. **Sin conector:** puerto concentrado de 50 Ω en el borde de la placa, sin SMA.
7. **Metal ideal:** lámina 2D sin rugosidad.
8. **Comprobado solo en las muestras:** 501 puntos, uno por MHz.
9. **Faltan magnitudes:** la ganancia y la eficiencia vienen de una sola malla; el retardo de grupo y la dispersión de fase radiada no se han evaluado.

**Redacción:** «−10 dB en el canal 9 con openEMS, con sensibilidad de malla acotada (\|ΔΓ\| ≤ 0,03). No es convergencia ni validación HFSS. Estado EM_SIMULATED».

## Cómo comprobarlo en HFSS
P01_MS2 es P01_MS1 con `tr_l` = 7,1 mm. En el diseño P01_MS1 de HFSS:
1. Cambia la variable `tr_l` de 6,6 a 7,1 mm.
2. La línea de 50 Ω se ajusta sola, porque su longitud es `board_y/2 − patch_L/2 − tr_l`. El puerto no cambia.
3. Vuelve a analizar.

Lo que hay que comprobar: el peor S11 en el canal, sobre todo en 8,2368 GHz.

## Estado
- Ronda 28/40. Campaña **READY_FOR_HFSS_REVIEW**, con P01_MS2 como candidato.
- Las rondas de Claude se detienen hasta la revisión HFSS.

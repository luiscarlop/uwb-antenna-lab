# Ronda Claude 032: US3_PS1 repetida hasta convergencia temporal (diagnóstico)

- **ID del experimento:** US3_PS1_OPENEMS_032.
- **Fecha:** 2026-11-15, ronda 32/40.
- **Orquestador:** `claude-opus-5-5`.
- **FDTD:** 1, con malla base.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Qué se hizo
La misma geometría que la ronda 031 ([`variants/US3_PS1.json`](../variants/US3_PS1.json)) con la nueva opción `--max-timesteps 60000` de `em/patch_openems.py` (commit `9726784`).
- La opción solo puede subir el límite de pasos.
- El XML difiere de 031 solo en `NumberOfTimesteps`.
- Sin la opción, el XML de cualquier variante es el de antes.

## Resultado
- **Convergencia temporal:** «end-criteria of −50 dB reached after 33 228 timesteps (−50,84 dB)», en 704 s y 0,46 GB con 2 CPU. Durante cientos de pasos la energía oscila entre −43 y −50 dB, y el criterio se cumplió en un pico de esa oscilación.
- **La forma reproduce 031:**
  - Mínimos de S11: −31,7 dB en 7,675 GHz y −25,4 dB en 8,03 GHz.
  - Banda de −10 dB: 7,49–8,115 GHz.
  - η en el canal: 0,638 → **0,225 (f0)** → 0,515, diferencia ≤ 0,005 frente a 031.
  - Ganancia realizada broadside en f0: −0,61 dBi.
- **Lo que cambia frente a 031 es el cumplimiento de −6 dB, que se invierte por 0,06 dB.** El peor caso en el canal (rejilla de 1 MHz) es **−5,96 dB** en 8,2368 GHz: US3_PS1 **no cumple −6 dB**, por 0,04 dB.
  - El «cumple» de 031 (−6,02 dB) venía del truncamiento y no se sostiene.
  - La rejilla de banda ancha de 5 MHz da −5,998 dB en 8,235 GHz. Se cita siempre la del canal (1 MHz).
  - El margen es de centésimas de dB, por debajo de la incertidumbre de malla.

## Conclusión
- El valle de eficiencia **no** es un artefacto del truncamiento temporal.
- No se ha descartado la malla (solo hay malla base), el modelo de pérdidas ni el puerto concentrado. La causa sigue **sin probar**.
- Es un resultado de un solo modelo (openEMS), no `HFSS_VALIDATED`.
- US3_PS1 queda descartado como candidato.
- **Decisión del propietario:** probar el apilado clásico invertido (US3_PS2): parche excitado con U-slot en una capa interior y parásito encima.

## Estado
- Ronda 32/40.
- La campaña sigue en READY_FOR_HFSS_REVIEW con P01_MS2 como candidato del elemento.
- La ronda 031 queda anotada como no convergida en el tiempo.

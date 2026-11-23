# Ronda Claude 048: US3_PS6_2 (patch_L 6,38 mm)

- **ID:** US3_PS6_2_OPENEMS_048.
- **Fecha:** 2026-11-16, ronda 48/60.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «A ps6_1 se le puede aumentar algo más patch_L, a 6,38 mm tal vez. Si con esa medida conseguimos ≤ −10 dB en toda la banda, mándaselo a Fable».
- **Variante:** `variants/US3_PS6_2.json`, escrita por `rf-designer` a partir de US3_PS6_1.
  - Único cambio de diseño: `patch_L` pasa de 6,32 a 6,38 mm.
  - Los derivados se recalcularon desde los polígonos: borde en y = −3,19 mm, transformador desde −9,79 mm y holgura de 0,28 mm.
  - El hint de malla en y pasa de −3,078 a −3,104 mm; la ventana que cumple el gradado en malla fina es de solo 0,003 mm. La malla efectiva está descrita en el JSON y el registro de la búsqueda quedó en el scratchpad.
- **FDTD:**
  - 1 simulación en malla base, con `--max-timesteps 60000`, 2 hilos y afinidad 0,1.
  - Se lanzó en cola detrás de la ronda 047, de modo que nunca corrieron dos a la vez.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.

## Ejecución
- 32 812 pasos sobre 2 268 650 celdas nodales, con 627 s de solver, 637 s de pared y un pico de RSS de 458 144 KiB.
- Energía final −50,45 dB. Los tres últimos muestreos dan −48,0, −49,0 y −50,45 dB. Solo la última muestra baja de −50 dB; las 19 anteriores promedian −45,1 dB (máximo −40,5): el run paró en un mínimo de una energía que oscila unos 5 dB, como en el resto de la campaña.
- `port_validity` OK. Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256.

## Resultados (malla base; S11 en rejilla de 1 MHz)

| | US3_PS6 (038, 6,29) | US3_PS6_1 (046, 6,32) | **US3_PS6_2 (048, 6,38)** |
|---|---|---|---|
| Mínimo de S11 | −20,43 dB en 8,005 GHz | −20,04 dB en 7,988 GHz | **−19,66 dB en 7,953 GHz** |
| Bordes 7,7376 / 8,2368 GHz | −8,16 / −10,40 dB | −8,57 / −9,65 dB | **−9,59 / −8,23 dB** |
| Peor S11 en el canal | −8,16 dB | −8,57 dB | **−8,23 dB (8,2368 GHz)** |
| Canal ≤ −10 dB | 88,0 % | 88,8 % | 87,2 % |
| Banda de −10 dB | 7,797–8,248 GHz | 7,783–8,227 GHz | 7,750–8,186 GHz |
| η_rad (P_rad/P_acept) | 0,592–0,683 | 0,571–0,683 | **0,526–0,683** (mínimo en 8,2368 GHz) |
| Ganancia realizada broadside | 3,10–4,23 dBi | 2,81–4,23 dBi | **2,08–4,22 dBi** |

## Hipótesis pre-registradas
- **H0 se cumple.** El mínimo cae en 7,953 GHz, dentro del rango 7,940–7,968 GHz y a 1 MHz de la guía (7,954 GHz).
- **H1 falla, como se había previsto.** El peor caso es −8,23 dB, en el borde superior.
  - La extrapolación lineal de 038→046 daba unos −9,4 dB abajo y −8,15 dB arriba; lo observado es −9,59 y −8,23 dB.
- **H2 falla por poco.** En 8,2368 GHz η_rad = 0,526, por debajo de 0,55. La ganancia realizada se queda en 2,08 dBi, por encima de los 2 dBi exigidos.

## Lectura
- **Con solo `patch_L` no se llega a ≤ −10 dB en todo el canal.** La serie 6,29 → 6,32 → 6,38 mm desplaza el mínimo de forma casi lineal, unos 5,7 MHz por cada 0,01 mm. Lo que gana un borde del canal lo pierde el otro.
  - En los tres puntos simulados el peor caso queda entre −8,2 y −8,6 dB. Interpolando los bordes de 046 y 048, el equilibrio estaría hacia `patch_L` ≈ 6,346 mm con ≈ −9,0 dB: es una estimación GUIDE_MODEL no simulada, con una incertidumbre de al menos ±0,7 dB (la diferencia base–fina vista en 038/039), con el hint de malla cambiando en cada ronda.
  - **La banda contigua de −10 dB es siempre más estrecha que el canal (499,2 MHz):** 451 MHz (038), 482 (039, fina), 444 (046) y 436 MHz (048); US3_MS3 tenía 349–359 MHz. Con `patch_L` solo se desplaza la banda; para cubrir el canal a −10 dB hace falta ensancharla, con otro grado de libertad.
- **Al bajar la resonancia, la eficiencia en el borde superior cae** (η_rad 0,59 → 0,57 → 0,53).
- **Según la regla del propietario, US3_PS6_2 no se manda a Fable.** Los peores casos de la serie (−8,16, −8,57 y −8,23 dB) son indistinguibles dentro de la sensibilidad de malla (≈ 0,7 dB en 038/039); no hay un ganador significativo entre US3_PS6, US3_PS6_1 y US3_PS6_2 en S11, aunque η_rad en el borde superior baja con `patch_L` (0,59 → 0,57 → 0,53).
- La guía basada en la pendiente medida acertó con 1 MHz en el mínimo y con unos 0,2 dB en los bordes. Aun así, el cambio de hint de malla impide atribuir toda la variación a `patch_L`.

- El registro de la búsqueda del hint de malla se ha copiado a `em/US3_PS6_2_OPENEMS_048/hint_search_log.csv` (estaba solo en el scratchpad).
- Reservas heredadas: puerto lumped en el borde de la placa sin conector y FR4 provisional homogéneo (εr 4,4, tanδ 0,017, h 2,07 mm).

## Auditoría
`validator` (2026-11-16): **OK con observaciones**. Run único, hashes, energía, variante (solo `patch_L` y derivados, sin restos de la fe de erratas) y todas las cifras confirmados. Sus reservas (equilibrio de −9 dB como estimación, respaldo de la banda contigua, ranking no significativo, energía de parada, trazabilidad del hint) están incorporadas arriba.

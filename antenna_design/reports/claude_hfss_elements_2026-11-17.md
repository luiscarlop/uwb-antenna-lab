# HFSS: elementos US3_PS4_2_1 y US3_PS6 (exportados por el propietario, 2026-11-17)

- **Fuente:** exportación del propietario con `hfss/export/claude_aedt_export_element_ch9.py` (HFSS 2025.1.0), descargada de su Google Drive (`ch9_results/ch9_element_export/`) y guardada en `hfss/results/results_US3_PS4_2_1/US3_PS4_2_1/` y `hfss/results/results_US3_PS6/US3_PS6/`.
- **Convergencia adaptativa: CONVERGIDOS.**
  - US3_PS4_2_1: 15 pasadas, ΔS 0,0085 frente al objetivo 0,01.
  - US3_PS6: 14 pasadas, ΔS 0,0077.
  - Fichero `convergence.conv` en cada carpeta.
- **Estado:** `HFSS_VALIDATED` para el elemento aislado (S11, campo lejano, parámetros de antena), con el modelo del repositorio: FR4 homogéneo provisional (εr 4,4, tanδ 0,017, h 2,07 mm), puerto lumped de 50 Ω en el borde de la placa y sin conector.
- La η de la tabla es la de HFSS (*Radiated Power* / *Accepted Power*), la misma definición que `radiation_efficiency_Prad_over_Pacc` de openEMS. La ganancia de HFSS es la **máxima** realizada (no broadside).

## S11 (rejilla de 1 MHz; el barrido de HFSS llega a 8,236 GHz, no a 8,2368)

| | Mínimos | Peor S11 en el canal | Bordes inferior / superior | Canal ≤ −10 dB | Banda de −10 dB |
|---|---|---|---|---|---|
| **HFSS US3_PS4_2_1** | 7,875 (−41,4) y 8,140 GHz (−49,4) | **−10,00 dB** (8,236) | −12,99 / −10,00 | 100 % (justo en el límite) | 7,681–8,236 GHz |
| openEMS 045 (base) | 7,880 y 8,137 GHz | −10,35 dB | −12,11 / −10,35 | 100 % | 7,693–8,243 GHz |
| openEMS 047 (fina) | 7,890 y 8,190 GHz | −11,38 dB | −11,38 / −14,97 | 100 % | 7,709–8,284 GHz |
| **HFSS US3_PS6** | 7,955 GHz (−18,4) | **−8,72 dB** (8,236) | −9,07 / −8,72 | 83,6 % | 7,765–8,181 GHz |
| openEMS 038 (base) | 8,005 GHz | −8,16 dB | −8,16 / −10,40 | 88,0 % | 7,797–8,248 GHz |
| openEMS 039 (fina) | 8,003 GHz | −8,14 dB | −8,14 / −11,10 | 88,2 % | 7,796–8,278 GHz |

## Radiación (11 frecuencias de `Edges_and_f0`)

| | η_rad | Ganancia realizada máx. | Directividad máx. |
|---|---|---|---|
| **HFSS US3_PS4_2_1** | **0,32–0,74**; valle 0,32 en 8,137 GHz, 0,44 en 8,2368 | 1,15–5,32 dBi | 5,7–6,7 dBi |
| openEMS 045 / 047 | 0,27–0,67 / 0,27–0,68 (broadside) | | |
| **HFSS US3_PS6** | **0,69–0,74**, sin valle | 3,72–4,90 dBi | 6,0–6,4 dBi |
| openEMS 038 / 039 | 0,59–0,68 / 0,63–0,69 | | |

## Lectura frente a los criterios pre-registrados (`hfss/CLAUDE_PYAEDT.md`)
- **US3_PS4_2_1.**
  - **Mínimos dentro de las ventanas** (7,78–7,90 y 8,03–8,16 GHz), con una separación de 265 MHz (ventana 200–330).
  - **HFSS coincide con openEMS en malla base con un margen de 5 MHz**, y no con la malla fina (mínimo superior en 8,190). **No hay desplazamiento HFSS–openEMS de −60 a −75 MHz**: ese desfase se midió en diseños sin parásito y aquí no se cumple.
  - **El peor S11 es −10,00 dB:** el canal queda justo en −10 dB. Está en el límite favorable de H1 (−7 a −10 dB).
  - **H2 falla, como se esperaba:** η_rad baja a 0,32 en 8,137 GHz, en 4 de 11 puntos es < 0,55 y la ganancia realizada máxima baja a 1,15 dBi. El valle de η de openEMS queda confirmado en HFSS, algo menos profundo.
- **US3_PS6.**
  - **Un solo mínimo, en 7,955 GHz**, 50 MHz por debajo de openEMS. Es coherente con un desfase hacia abajo, aunque menor que 60–75 MHz.
  - **H1 se cumple:** peor caso −8,72 dB, dentro de −8 a −10 dB. El peor borde pasa a ser el superior, como se predijo.
  - **H2 se cumple:** η_rad 0,69–0,74 sin valle, mejor que en openEMS.
- **Comparación entre los dos.** US3_PS4_2_1 cubre el canal a −10 dB, pero con adaptación por pérdidas en la mitad alta (η 0,32). US3_PS6 radia de forma uniforme (η ≥ 0,69), pero no llega a −10 dB (−8,7 dB). La elección depende de qué pese más en el TFG: adaptación en todo el canal o eficiencia y ganancia uniformes. Para IR-UWB, una η y una ganancia planas suelen pesar más en la respuesta temporal; aun así, el retardo de grupo radiado no se ha calculado todavía con HFSS.

## Retardo de grupo radiado y diagramas (`hfss/analysis/element_hfss_patterns.py`)
- **Método.** τ_g = −d(arg E_co)/dω de la componente copolar Ludwig-3 y del `ff_P1.csv` (1 W incidente), en 11 frecuencias con paso de 49,92 MHz. Diferencias centradas en el interior y laterales en los bordes. Los saltos de fase entre muestras son < 0,15 rad, así que el desenrollado no es ambiguo. El retardo incluye línea, transformador y antena: lo que importa es el **rizado**. Resultados en `element_patterns_gd.json` de cada carpeta.
- **US3_PS4_2_1.**
  - Rizado en broadside: **664 ps pico a pico**; a ±30° en xz y yz, 587–715 ps.
  - τ_g ≈ 394–442 ps hasta 8,04 GHz, cae a 199 ps en 8,087 y es **negativo** en 8,137–8,237 GHz (−174, −222, −79 ps).
  - Es la firma de la resonancia poco radiante dentro del canal, donde η = 0,32. openEMS 045 da la misma forma (−85 / −305 / −44 ps).
  - Con 50 MHz de paso esa estructura está submuestreada: los picos son indicativos.
- **US3_PS6.** Rizado en broadside **20 ps pico a pico** (339–358 ps); a ±30°, 14–33 ps. Respuesta casi plana, coherente con η plana (0,69–0,74).
- **Ganancia realizada máxima desde el campo:** coincide con `PeakRealizedGain` de AEDT con un margen de ±0,01 dB en las 11 frecuencias de los dos elementos, lo que comprueba las unidades.
  - Máximo en θ 10–20°, φ 270–275°: inclinado hacia −y, como en openEMS.
  - En broadside: US3_PS4_2_1 da 4,54 / 4,33 / 1,10 / 1,34 dBi en 7,74 / 7,99 / 8,14 / 8,24 GHz; US3_PS6, 3,80 / 4,43 / 4,10 / 3,48 dBi.
- **Lectura.** Para IR-UWB, US3_PS6 es claramente mejor en respuesta temporal: 20 ps de rizado frente a 664 ps. El S11 algo mejor de US3_PS4_2_1 (−10,0 dB frente a −8,7 dB) se paga con una dispersión fuerte y con una caída de ganancia de unos 3 dB en la mitad alta del canal.
- Gráficas en el artifact «U-slot con parche parásito · openEMS»: retardo de grupo, cortes 2D y diagrama 3D por frecuencia.

## Pendiente
- Comparación con el array (`ARR1x5_US3_PS4_2_1_dparam`, sin convergencia completa).
- Auditoría `validator`.

# Rondas Claude 045–046: ajuste fino de patch_L en US3_PS4_2 y US3_PS6

- **IDs:**
  - US3_PS4_2_1_OPENEMS_045: Wp 10 mm, patch_L 6,302 → 6,222 mm.
  - US3_PS6_1_OPENEMS_046: patch_L 6,29 → 6,32 mm.
  - Este informe cubre las dos rondas.
- **Fecha:** 2026-11-16, rondas 45–46/50.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «Prueba Wp 10 mm con patch_L un poco menor y PS6 con un patch_L un poco mayor, para bajar la resonancia unos pocos MHz; llámalos con sus respectivas versiones y muéstrame los resultados en el artifact».
- **Variantes:** `rf-designer` escribió `variants/US3_PS4_2_1.json` y `variants/US3_PS6_1.json`.
  - Hay un solo cambio de diseño en cada una, y los derivados de la alimentación se recalcularon desde los polígonos.
  - Ninguna toma metadatos de la fe de erratas de US3_PS6.
- **Cambios de malla.** Para que las mallas base y fina pasen el gradado de 1,5 hubo que cambiar los hints de malla en y:
  - US3_PS4_2_1: [−0,215, −3,07, −3,03, −2,97], frente a [−0,215, −2,99] en 042.
  - US3_PS6_1: [−0,215, −3,078], frente a [−0,215, −3,06] en 038.
  - Por eso la comparación con el diseño de partida mezcla el cambio de `patch_L` con un cambio de malla.
  - **Malla efectiva de 045 (validator):** de los hints pedidos, −3,07 y −3,03 se fundieron con otras líneas; en y ∈ [−3,2, −2,9] solo quedan −3,111 (borde del parche) y −2,97. Frente a 042: 167 frente a 172 celdas en y, 2 241 960 frente a 2 308 685 celdas nodales, paso temporal 2,2577e-13 frente a 2,1823e-13 s, y la línea junto al borde del parásito (nominal −2,98) pasa de −2,99 a −2,97, lo que puede mover el Lp efectivo 0,01–0,02 mm. El `mesh_hint_note` de `variants/US3_PS4_2_1.json` («three lines added») no describe la malla efectiva; no se edita el JSON porque su hash está registrado en la ejecución.
  - **046:** el hint pasa de −3,06 a −3,078 con el mismo número de celdas (2 655 655); la confusión de malla es menor que en 045.
- **FDTD:** 2, una por ronda y en secuencia. Malla base, `--max-timesteps 60000`, 2 hilos, afinidad 0,1. En cada carpeta, `prepare` y `solve` se ejecutaron uno detrás de otro.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.

## Ejecución

| Ronda | Energía final | Pasos | Tiempo de solver | Pico RSS |
|---|---|---|---|---|
| 045 | −51,49 dB | 34 424 | 619 s | 453 072 KiB |
| 046 | −50,61 dB | 31 720 | 730 s | 522 224 KiB |

- En los últimos muestreos la energía fluctúa: 045 tiene una meseta en torno a −44 dB y luego −49,1 y −51,5 dB; 046 rebota entre −42,6 y −48 dB antes de −50,6 dB. El criterio de −50 dB se cumple por una caída puntual, como en 038; en cambio 036 y 042 decaen de forma monótona. No hay evidencia de que S11 esté convergido en el tiempo, sobre todo para la resonancia superior de 045, poco radiante y de Q alto.
- `port_validity` OK en las dos. Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256.

## Resultados (malla base; S11 en rejilla de 1 MHz)

| | US3_PS4 (036) | US3_PS4_2 (042) | **US3_PS4_2_1 (045)** | US3_PS6 (038) | **US3_PS6_1 (046)** |
|---|---|---|---|---|---|
| Mínimos de S11 | 7,826 / 8,158 GHz | 7,868 / 8,098 GHz | **7,880 / 8,137 GHz** | 8,005 GHz | **7,988 GHz** |
| Picos de Re(Zin) | 7,76 / 8,17 GHz | 7,801 / 8,120 GHz | 7,814 / 8,151 GHz | 7,933 GHz | 7,921 GHz |
| Peor S11 en el canal | −10,66 dB | −8,56 dB | **−10,35 dB (8,2368)** | −8,16 dB | **−8,57 dB (7,7376)** |
| Bordes 7,7376 / 8,2368 | −16,6 / −10,7 | −13,4 / −8,6 | −12,1 / −10,35 | −8,16 / −10,40 | −8,57 / −9,65 |
| Canal ≤ −10 dB | 100 % | 93,2 % | **100 %** | 88,0 % | 88,8 % |
| Banda de −10 dB | 7,631–8,245 | 7,671–8,203 | 7,693–8,243 | 7,797–8,248 | 7,783–8,227 |
| η_rad = P_rad/P_acept, mín. (frecuencia) | 0,244 (8,137) | 0,301 (8,087) | **0,273 (8,137)** | 0,592 (8,237) | **0,571 (8,237)** |
| Puntos con η < 0,55 | 5 | 6 | 5 | 0 | 0 |
| Ganancia realizada | −0,48…4,33 dBi | 0,43…4,25 dBi | **−0,07…4,22 dBi** | 3,10…4,23 dBi | **2,81…4,23 dBi** |

## Hipótesis pre-registradas

**US3_PS4_2_1**
- **H0 se cumple:** dos mínimos, 7,880 GHz (rango 7,88–7,92, justo en el límite) y 8,137 GHz (rango 8,10–8,14).
  - Los desplazamientos observados son +12 MHz el inferior y +39 MHz el superior, frente a +36 y +21 previstos. Ese reparto no se puede atribuir a la geometría, porque la malla también cambió y la discrepancia (±10–25 MHz) es del orden de los efectos de malla; la guía no queda recalibrada por esta ronda.
- **H1 se cumple en malla base, sin robustez demostrada:** peor caso −10,35 dB en 8,2368 GHz; todo el canal queda a ≤ −10 dB en la rejilla de 1 MHz. El margen (0,35 dB, unos 6 MHz: la banda de −10 dB acaba en 8,243 GHz) es menor que el cambio del borde superior entre mallas en 038/039 (0,70 dB), y la familia PS4 no tiene malla fina.
- **H2 falla:** η mínima 0,273 en 8,137 GHz, con 5 de 11 puntos por debajo de 0,55, y ganancia realizada −0,07 dBi en 8,137 GHz.
- **Regla de decisión:** pedía «H1 cierta y η mínima por encima de 0,30» para declararlo candidato. η mínima es 0,273, así que **según su propia regla no es candidato**: se informa del compromiso y decide el propietario.

**US3_PS6_1**
- **H0 se cumple:** un solo mínimo en 7,988 GHz (rango 7,980–7,995), desplazado −17 MHz como predecía la guía (−15 a −21).
- **H1 falla:** −8,57 dB en 7,7376 GHz. El borde inferior mejora 0,41 dB; el superior pierde 0,75 dB (−10,40 → −9,65), como se había avisado.
- **H2 se cumple:** η ≥ 0,571 y ganancia realizada ≥ 2,81 dBi en los 11 puntos.
- **Regla de decisión:** ninguna cláusula cubre literalmente «H1 falsa y H2 cierta» con el borde superior por encima de −8 dB; se aplica por analogía: se informa del compromiso (el peor borde sigue siendo el inferior) y no se continúa con `patch_L` sin el propietario.

## Lectura
- **US3_PS4_2_1 consigue en malla base, sin robustez demostrada, lo que el propietario pedía al principio para US3_PS4:** el mínimo inferior queda 54 MHz más arriba que en PS4 (7,880 frente a 7,826 GHz) y todo el canal queda a ≤ −10 dB por 0,35 dB.
  - El valle de eficiencia vuelve a 8,137 GHz, el mismo sitio que en PS4, y apenas menos profundo (0,27 frente a 0,24).
  - En la práctica es PS4 con el par de resonancias algo más junto y más centrado, con la misma adaptación por pérdidas en la mitad alta del canal.
- **US3_PS6_1 desplaza el mínimo los MHz pedidos.** El precio es el ya conocido: lo que gana el borde inferior lo pierde el superior. El peor caso del canal mejora solo 0,41 dB y no llega a −10 dB. US3_PS6 y US3_PS6_1 son prácticamente equivalentes.
- **Ninguno de los dos supera a P01_MS2** (peor −10,42 dB, η 0,73–0,76, 4,3–4,8 dBi en malla base) en eficiencia ni ganancia.
- Los dos cambios de `patch_L` (0,08 y 0,03 mm) son del orden de una tolerancia de grabado supuesta de ±0,02 mm (no verificada con un fabricante). Con la pendiente medida en 046 (≈ 5,7 MHz por 0,01 mm) serían unos ±11 MHz.
- **Diagnóstico de fase (no concluyente):** el ripple del retardo de grupo derivado de la fase del campo en el eje (`nf2ff_summary.json`, DIAGNOSTIC) es 1431 ps pico a pico en 045 y 134 ps en 046; el valor alto de 045 es coherente con la resonancia superior poco radiante dentro del canal. No es un retardo de grupo radiado medido.

## Gráfica
En el artifact «U-slot con parche parásito · openEMS» hay un apartado nuevo, «Ajuste fino de patch_L: US3_PS4_2_1 y US3_PS6_1». Muestra cada diseño de partida en línea discontinua y su versión refinada en línea continua, con US3_PS4 (036) como referencia.

## Auditoría
`validator` (2026-11-16): **OK con observaciones** en las dos rondas. Variantes, run único por carpeta, hashes, energía y todas las cifras confirmados. Sus reservas (malla efectiva de 045, margen de H1 no robusto, reparto de desplazamientos confundido con la malla, energía de parada, tolerancia supuesta, banda de 036, regla de decisión de 046, diagnóstico de fase) están incorporadas arriba. Las búsquedas de hints solo-prepare de rf-designer no se guardaron; la malla fina de 045/046 no se ha preparado en sus carpetas.

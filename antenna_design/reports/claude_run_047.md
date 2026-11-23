# Ronda Claude 047: US3_PS4_2_1 en malla fina

- **ID:** US3_PS4_2_1_FINE_OPENEMS_047.
- **Fecha:** 2026-11-16, ronda 47/60. El propietario subió el límite de 50 a 60.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «Lanza la malla fina de US3_PS4_2_1, que yo lo veo bastante bueno».
- **Geometría:** `variants/US3_PS4_2_1.json`, la misma que en 045. Su sha256 (5bd0ef44…) coincide en 045 y en 047. La malla efectiva está descrita en `variants/US3_PS4_2_1.errata.json`: en el tramo y ∈ [−3,2, −2,9], la malla fina tiene las líneas −3,169, −3,111, −3,042 y −2,949, y ninguna cae en el borde del parásito (−2,98).
- **FDTD:** 1, en malla fina, con `--max-timesteps 60000 --owner-long-convergence`, 2 hilos (afinidad 0,1) y tope de pared de 3960 s. `prepare` y `solve` se lanzaron en la misma carpeta.
- **Evidencia:** `EM_SIMULATED`, con dos mallas (045 base, 047 fina). La convergencia no está demostrada.

## Ejecución
- 49 096 pasos sobre 5 744 250 celdas nodales: 3046 s de solver y 3069 s de pared, con un pico de RSS de 1 013 524 KiB (≈ 0,97 GiB).
- Energía final −50,68 dB. Los últimos muestreos dan −45,7, −48,8 y −50,7 dB, así que el criterio se cumple en el último. `port_validity` OK.
- Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256.

## Base frente a fina (S11 en rejilla de 1 MHz)

| | Base (045) | **Fina (047)** |
|---|---|---|
| Mínimos de S11 | 7,880 (−25,0 dB) y 8,137 GHz (−22,8 dB) | **7,890 (−23,3 dB) y 8,190 GHz (−31,3 dB)** |
| Picos de Re(Zin) | 7,814 y 8,151 GHz | 7,833 y 8,197 GHz |
| Peor S11 en el canal | −10,35 dB (8,2368) | **−11,38 dB (7,7376)** |
| Bordes 7,7376 / 8,2368 | −12,11 / −10,35 dB | −11,38 / −14,97 dB |
| Canal ≤ −10 dB | 100 % | **100 %** |
| Banda de −10 dB | 7,693–8,243 GHz | 7,709–8,284 GHz |
| η_rad (P_rad/P_acept) | 0,273–0,670; mínimo en 8,137 GHz | 0,268–0,675; mínimo 0,268 en 8,187 GHz |
| Ganancia realizada broadside | −0,07…4,22 dBi | −0,12…4,27 dBi |
| Máx. \|ΔΓ\| en el canal | | **0,20** |

## Lectura
- **En las dos mallas todo el canal queda a ≤ −10 dB.** En la fina el peor caso mejora a −11,38 dB y pasa al borde inferior del canal.
- **Pero las dos mallas no coinciden: la resonancia superior es muy sensible a la malla.**
  - El mínimo superior se desplaza +53 MHz (de 8,137 a 8,190 GHz) y el inferior +10 MHz.
  - La diferencia máxima de Γ en el canal es 0,204 en 8,155 GHz, casi cuatro veces la de US3_PS6 entre 038 y 039 (0,056) y unas 6,8 veces el umbral de |ΔΓ| ≤ 0,03 que la campaña usó en las rondas 026/028 para dar por acotada la sensibilidad de malla. Los bordes de la banda de −10 dB se mueven +16 MHz (inferior) y +41 MHz (superior).
  - Ese 0,20 es sobre todo un desplazamiento de la resonancia superior, no un cambio de forma: trasladando la curva fina −42 MHz, |ΔΓ| máx baja a ≈ 0,06.
  - Las dos mallas difieren a la vez en resolución de bordes metálicos (0,25 → 0,175 mm), paso máximo en xy (0,5 → 0,35) y en z (0,8 → 0,6) y líneas de sustrato (9 → 11): es un contraste de sensibilidad, no una prueba de convergencia.
  - **La causa no está identificada.** Ninguna línea cae en el borde −y del parásito (−2,98), pero la primera línea dentro de la lámina solo cambia 0,021 mm entre mallas, y el borde +y (4,48) se mueve en sentido contrario, de modo que la longitud efectiva en y casi no cambia (7,367 frente a 7,371 mm). También cambian los bordes efectivos en x del parche y del parásito, y la resolución de la ranura y de z. Una prueba que mueva un solo hint aislaría la causa; solo con decisión del propietario.
- **La cobertura ≤ −10 dB en todo el canal es un resultado de las dos mallas, pero el detalle de la curva no ha convergido.** Las posiciones de los mínimos, el borde que manda y el margen dependen de la malla. Antes de fijar cotas haría falta una tercera malla, o bien HFSS.
- **El valle de eficiencia sigue dentro del canal en las dos mallas:** η_rad mínima 0,27 y ganancia realizada −0,1 dBi. En la fina el mínimo pasa de 8,137 a 8,187 GHz, un paso de la rejilla NF2FF (49,92 MHz), lo que es consistente con el desplazamiento de la resonancia superior con resolución de ±25 MHz. En el borde superior del canal (fina) η_rad = 0,347 y 0,55 dBi. Es la «adaptación por pérdidas» ya conocida: un buen S11 aquí no implica buena radiación ni buena respuesta temporal.
- **Criterios pre-registrados para HFSS** (`hfss/CLAUDE_PYAEDT.md`): las ventanas de mínimos salen de 045. Con 047 la ventana superior (8,03–8,16 GHz para un desfase de 0 a −100 MHz) puede quedarse corta. Se informa al propietario y no se reajustan las ventanas después de ver 047; la comparación de HFSS se hará contra las dos mallas.

- **Tope de pared:** el `timeout` usado (3960 s) era menor que el límite externo que pedía `prepared.json` (4263 s). La ejecución real (3069 s) no se vio afectada, pero el próximo run fino debe usar el tope que indique `prepare`.

## Auditoría
`validator` (2026-11-16): **OK con observaciones**. Run único, hashes, energía y todas las cifras confirmados; los criterios HFSS no se reajustaron tras ver 047. Sus reservas (|ΔΓ| como desplazamiento frente a forma, regla de 0,03, causa no identificada, resolución del valle de η, tope de pared) están incorporadas arriba.

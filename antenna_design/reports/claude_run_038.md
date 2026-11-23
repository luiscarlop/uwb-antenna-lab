# Ronda Claude 038: US3_PS6, US3_PS5 recentrado

- **ID del experimento:** US3_PS6_OPENEMS_038.
- **Fecha:** 2026-11-16, ronda 38/40.
- **Orquestador:** `claude-opus-5-5`.
- **Autoría:** regla de decisión del super revisor (`design-reviewer`, Fable 5.2) aplicada a 037: si la asimetría entre bordes supera 2 dB, retocar solo `patch_L`. `rf-designer` escribió el JSON.
- **FDTD:** 1, con malla base, `--max-timesteps 60000` y 2 hilos (afinidad 0,1).
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla (la malla fina es la ronda 039).

## Cambio
[`variants/US3_PS6.json`](../variants/US3_PS6.json), con US3_PS5 como base:
- `patch_L` 6,18 → **6,29 mm**; derivados de la alimentación (borde del parche −3,09 → −3,145; inicio del transformador −9,69 → −9,745).
- Parásito, U-slot, transformador, z_par y material sin cambios.
- **Hint de malla y −3,06 mm** (solo malla), para que las mallas base y fina pasen el límite de gradado 1,5 entre el nuevo borde del parche y el borde del parásito.

**Aviso del validator: la comparación 037 → 038 no es «solo patch_L».**
- El hint cambia la discretización: la malla y pasa de 184 a 199 líneas y casi todas se mueven; las celdas suben de 2 455 480 a 2 655 655 (+8 %).
- Inferido de la malla (sin verificar con el código de snap de openEMS): el borde del parásito (−2,91) cae en y = −2,923 en 037 y en −2,952 en 038, así que el Lp efectivo cambia ≈ +0,03 mm solo por malla. Con la pendiente de la guía serían ≲ 10–30 MHz de orden de magnitud.
- Los bordes del parche son líneas exactas en las dos mallas; su longitud efectiva cambia 0,110 mm, como la nominal.
- Por tanto 038 es «patch_L +0,11 mm más cambio de malla», y la diferencia entre el desplazamiento observado (−60 MHz) y el de la guía (−78 MHz) no se puede atribuir solo a `patch_L`. Lo decide la malla fina (039).

## Resultados (malla base)
- **Ejecución:** converge a −50,21 dB en 31 861 pasos, en 833 s, pico RSS 509,8 MiB (521 984 KiB). openEMS v0.37.0-40-g5fecbb5, CSXCAD v0.7.0-8. `port_validity` OK.
- Material y contornos como en 037: FR4 h 2,07 mm, εr y tanδ 0,017 del JSON, puerto lumped de 50 Ω en y = −13 mm sin de-embedding.

| | US3_PS5 (037) | **US3_PS6 (038)** | P01_MS2 (027, referencia) |
|---|---|---|---|
| Mínimo de S11 (rejilla 1 MHz) | −22,7 dB en 8,063 GHz | **−20,43 dB en 8,005 GHz** | −22,3 dB |
| Peor S11 en el canal | −6,87 dB (7,7376) | **−8,16 dB (7,7376)** | −10,42 dB |
| S11 en 8,2368 GHz | −13,1 dB | **−10,40 dB** | |
| Banda de −10 dB | 7,85–8,32 GHz | **7,797–8,248 GHz** | |
| Canal ≤ −10 dB | | **88,0 % (441/501 muestras)** | 100 % |
| η en el canal | 0,639–0,688 | **0,592–0,683, sin valle** (mínimo en 8,2368) | 0,728–0,761 |
| Ganancia realizada broadside | 2,99–4,25 dBi | **3,10–4,23 dBi** | 4,30–4,78 dBi |
| Ganancia broadside (sin desadaptación) | | 3,52–4,27 dBi | |
| Dmax muestreado (rejilla de 5°) | 6,3–6,6 dBi, θ 15–20° | 6,06–6,56 dBi, θ 15–20°, φ 270° | |

## Hipótesis pre-registradas
- **H0 se cumple:** mínimo brillante en 8,005 GHz (rango 7,95–8,03).
- **H1 se cumple en malla base con margen 0,16 dB, no robusto:** peor caso −8,16 dB frente a ≤ −8 dB. El margen equivale a ≈ 5 MHz de desplazamiento del borde inferior, por debajo de la incertidumbre de malla declarada (~13 MHz).
- **H2 se cumple:** η ≥ 0,592 y ganancia realizada ≥ 3,10 dBi en los 11 puntos; Dmax a 15–20° de broadside. El margen de η en 8,2368 GHz es solo 0,04.
- **La guía del JSON no se reprodujo.** Desplazar la curva de 037 −78 MHz da −8,86 dB abajo y −10,43 dB arriba (−8,34 y −11,2 con −60 MHz). Lo observado (−8,16 y −10,40) queda ≈ 0,7 dB peor en el borde inferior y coincide en el superior.

## Lectura
- El recentrado mejora el borde inferior (−6,87 → −8,16 dB) y mantiene la eficiencia sin valle.
- **Pero empeora el borde superior** frente a 037: S11 −13,1 → −10,40 dB, η 0,639 → 0,592 y ganancia realizada 3,74 → 3,10 dBi en 8,2368 GHz, con η decreciendo de forma monótona hacia ese borde. Al bajar el modo brillante, el modo oscuro vuelve a acercarse al canal. Es un aviso para 039 y para cualquier paso siguiente.
- **US3_PS6 no supera a P01_MS2** en ninguna métrica de peor caso: S11 (P01_MS2 mejor por 2,3 dB), η (mejor por ≈ 0,05–0,17), ganancia mínima (mejor por ≈ 1,2 dB) y mínimo de S11. PS6 solo cubre −10 dB en el 88 % del canal, y lleva un parásito enterrado con una altura z_par que el TFG no controla en fabricación. P01_MS2 es de una sola capa y ya tiene una comprobación en malla fina (028: −10,36 dB). **No hay ventaja demostrada de PS6.**
- Regla de decisión: H1 y H2 se cumplen, así que la ronda 039 es la malla fina de US3_PS6.

## Auditoría
`validator` (2026-11-16, 037 y 038 en conjunto): **OK con observaciones, no bloqueante**. Cifras y convergencia recalculadas y confirmadas; `variant.json` del run igual byte a byte al de `variants/`. Sus reservas (malla en 037 → 038, H1 no robusto, guía no reproducible, empeoramiento del borde superior, posición frente a P01_MS2, unidades, Dmax muestreado) están incorporadas arriba. El borde superior de la banda de −10 dB es 8,248 GHz en el CSV (el borrador decía 8,245).

## Ficheros
- `em/US3_PS6_OPENEMS_038/`: `run_numeric.json`, CSV de S11 y campo lejano, `native_mesh.csv`, `patch_openems.xml`, `solver_log.txt`, `nf2ff_raw_dumps.sha256`.

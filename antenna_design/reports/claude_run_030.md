# Ronda Claude 030: P01_IN1, parche simple con inset directo

- **ID del experimento:** P01_IN1_OPENEMS_030.
- **Fecha:** 2026-11-14, ronda 30/40, en la sesión del propietario (petición: «pruebas en openEMS con el patch con inset»).
- **Orquestador:** `claude-opus-5-5` (comprobado con `get_session`). Diseño de la variante: `rf-designer`.
- **FDTD:** 1, malla base.
- **Evidencia:** `EM_SIMULATED`. Convergencia de malla: NOT_ESTABLISHED (una sola malla).
- **Veredicto de `validator`:** **APROBAR CON RESERVAS** (cifras reproducidas; tests 68 OK).

## Propuesta
[`variants/P01_IN1.json`](../variants/P01_IN1.json): el parche de P01_MS2 (11,421 × 7,322 mm) con **alimentación por inset directo**: línea de 50 Ω (w 3,92 mm) desde el borde de la placa (y = −13 mm) hasta la punta del inset (y = −1,561 mm), sin transformador λ/4.
- Inset de 2,1 mm y hueco de muesca de 1,0 mm por lado (muesca en x = ±2,96 mm, 5,92 mm en total, el 52 % de W).
- Profundidad elegida con la ley cos² y una R de borde de ≈130 Ω (124–137 Ω), estimada quitando analíticamente la línea y el transformador del Zin de las rondas 025–028 (GUIDE_MODEL).
- Sustrato (FR4 provisional εr 4,4, tanδ 0,017, 2,07 mm), cobre (35 µm, 5,8e7 S/m), placa 26 × 26 mm y puerto concentrado de 50 Ω en el borde: iguales a P01_MS2.
- Hipótesis pre-registradas en la variante:
  - H1: peor S11 en el canal ≤ −6 dB.
  - H2: Re(Z) en la punta del inset, en su pico, entre 33 y 75 Ω.
  - Regla: H1 falsa con H2 cierta → parar la vía de inset directo.

## Ejecución
- **Comando** ([`launcher.json`](../em/P01_IN1_OPENEMS_030/launcher.json)): `python em/patch_openems.py solve --variant variants/P01_IN1.json --out em/P01_IN1_OPENEMS_030 --mesh base --edge-port lumped --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9`, con `timeout 1200s` y `taskset -c 0,1`. Mismo comando que la ronda 027 (P01_MS2) salvo la variante.
- **Malla:** 1 889 244 celdas (153 × 147 × 84); unas 5 celdas en cada hueco de la muesca; gradación ≤ 1,40. Es el mismo perfil base que 027, pero **no la misma malla** (cada geometría genera la suya: paso mínimo en y 0,222 frente a 0,083 mm, paso de tiempo 4,50e-13 frente a 2,93e-13 s).
- **Recursos:** estimación 423 s de motor y ≤ 0,7 GB; real 97 s de pared, 168 s de CPU, RSS 0,40 GB, 2 CPU.
- **Fin:** EndCriteria 1e-5 en el paso 5720; **energía −51,41 dB** según `solver.log` (criterio de −50 dB cumplido). `port_validity` OK (|S11| máx. 0,85).
- Volcados NF2FF brutos borrados tras guardar sus hashes en [`nf2ff_raw_dumps.sha256`](../em/P01_IN1_OPENEMS_030/nf2ff_raw_dumps.sha256). `solver.log` está en `.gitignore`.

## Resultados (malla base)
| | P01_MS2 (027) | **P01_IN1 (030)** |
|---|---|---|
| Peor S11 en el canal | −10,49 dB | **−2,06 dB** (7,7376 GHz) |
| Mejor S11 en el canal | | −4,22 dB (8,2368 GHz) |
| Pico de Re(Zin) en el plano del puerto | 58,4 Ω en 8,005 GHz | 149,4 Ω en 8,34 GHz |
| Mínimo de S11 | −22,3 dB en 7,99 GHz | −14,0 dB en 8,77 GHz |
| Banda de −10 dB | 7,724–8,306 GHz | 8,59–8,98 GHz (fuera del canal); otro tramo 9,93–10,505 GHz (borde de validez) |
| Eficiencia de radiación en el canal | | 0,60–0,70 |
| Ganancia realizada broadside | | −2,7 a +0,7 dBi |
| Dmax muestreado | | 6,6–6,8 dBi en θ 35°, φ 270° (rejilla de 11 puntos) |

Los mínimos fuera del canal no son cobertura de la banda: el canal queda en el flanco bajo de la resonancia.

## Hipótesis
- **H1: falsa** (−2,06 dB).
- **H2: cumplida solo formalmente.** Quitando 11,439 mm de línea de 50 Ω ([`inset_tip_deembed.py`](../em/inset_tip_deembed.py), GUIDE_MODEL), el pico de Re(Z) en la punta es 39,2 Ω en 8,665 GHz. Pero:
  - en el canal Re(Z_punta) es solo 8–19 Ω, y en f0 vale 11,8 + j34,2 Ω;
  - el resultado depende del modelo de la línea dentro de la muesca, que se trata como microstrip normal: desincrustar 10,0 mm en lugar de 11,439 mm daría 78 Ω (fuera de la ventana) y 9,34 mm, 136 Ω.
  - **La ley cos² no queda validada.**
- **Desplazamiento de frecuencia:** en el mismo plano del puerto, el pico de Re(Zin) pasa de 8,005 a 8,34 GHz (+4,2 %). El sentido es **contrario al previsto** (se esperaba que la muesca alargase el camino de la corriente y bajase la resonancia). **La causa no se conoce**; la muesca ancha es solo una hipótesis no probada (también podría intervenir el acoplo entre línea y parche dentro de la muesca).

## Decisión
- Por la regla pre-registrada (H1 falsa, H2 formalmente cierta) **se para la vía de inset directo**.
- Esto no prueba que un inset no pueda funcionar si se reajusta L o se cambia el ancho de la muesca: no se ha probado. En f0 fallan a la vez la resistencia y la reactancia.
- P01_MS2 (transformador λ/4) sigue siendo el candidato del parche simple. Cualquier nueva variante con inset la decide el propietario.

## Reservas (validator)
1. H2 depende del modelo de línea para la muesca; sin él no se puede afirmar que la ley cos² se cumpla.
2. La causa del desplazamiento hacia arriba es desconocida.
3. Comparación con 027 en el mismo perfil de malla, no en la misma malla; ninguna de las dos tiene convergencia de malla.
4. Ganancia y Dmax absolutos salen de potencias muy pequeñas de la excitación gaussiana: solo valen las razones. Dmax en una rejilla de 11 puntos.
5. FR4 provisional, sin conector (puerto concentrado en el borde), metal como lámina ideal.

## Corrección de método (energía)
La primera lectura del orquestador fue −49,23 dB, calculada como último valor de `openEMS_run_stats.txt` entre el **máximo de las muestras impresas**. openEMS normaliza con su máximo interno, que es mayor: el valor correcto es el del `solver.log` (−51,41 dB). La ronda 029 usó el mismo método (−50,08 dB, informe 029) y su `solver.log` no se conserva en este contenedor: aquel valor es probablemente una **cota superior** de la energía real, no el valor de openEMS. No cambia ninguna conclusión de 029.

## Estado
- Ronda 30/40. Campaña en **READY_FOR_HFSS_REVIEW** con P01_MS2 como candidato del elemento; arrays 1×4 y 1×5 preparados (GEOMETRY_ONLY) y pendientes del propietario.

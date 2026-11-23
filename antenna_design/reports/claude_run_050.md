# Rondas Claude 049–050: ensanchar la banda de US3_PS6

- **IDs:**
  - US3_PS6_3_OPENEMS_049: parásito Lp 7,05 → 7,25 mm.
  - US3_PS6_4_OPENEMS_050: parche ancho W 11,421 → 14,0 mm, Wp 11,0 → 13,58 mm (mismo inset de 0,21 mm), transformador 1,0 × 7,25 mm (Zt 94,9 Ω), línea de 50 Ω de 2,605 mm, patch_L 6,29 mm.
  - Este informe cubre las dos rondas.
- **Fecha:** 2026-11-19, rondas 49–50/60.
- **Orquestador:** `claude-opus-5-5`.
- **Petición del propietario:** «Utiliza las siguientes rondas para iterar ese diseño con variaciones para conseguir peor S11 por debajo de −10 dB y bajar un poco la resonancia hacia 7,9 GHz».
- **Variantes:** `variants/US3_PS6_3.json` y `variants/US3_PS6_4.json`, con hipótesis H0/H1/H2 pre-registradas.
  - 050 no sale de la regla 3 de 049 (que mandaba Wu 5,0 mm). Es el cambio de parche ancho que decidió el orquestador dentro del encargo del propietario. Es un cambio múltiple (W, Wp, transformador, línea) declarado como excepción, así que la mejora no se puede atribuir a un solo parámetro.
- **FDTD:** 2, una por ronda y en secuencia. Malla base, `--max-timesteps 60000`, 2 hilos (afinidad 0,1). `prepare` y `solve` en la misma carpeta.
- **Software:** openEMS 0.37.0.post1.dev40, CSXCAD 0.7.0.post1.dev8, `em/patch_openems.py` sha256 `2fc739d5…`.
- **Material y puerto:** FR4 homogéneo provisional (εr 4,4, tanδ 0,017, h 2,07 mm), cobre de 35 µm, placa de 26 × 26 mm, puerto lumped de 50 Ω en y = −13 mm sin conector SMA.
- **Evidencia:** `EM_SIMULATED`, una sola malla en cada ronda; `mesh_convergence: NOT_ESTABLISHED`.

## Ejecución

| Ronda | Energía final | Pared | CPU | Pico RSS | Celdas nodales |
|---|---|---|---|---|---|
| 049 | −51,48 dB | 877 s | 1539 s | 461 888 KiB | 2,24 M |
| 050 | −51,26 dB | 915 s | 1612 s | 533 328 KiB | 2,66 M |

`port_validity` OK en las dos. Los volcados `nf2ff_*.h5` se borraron después de guardar su sha256.

## Resultados (malla base; S11 en rejilla de 1 MHz)

| | US3_PS6 (038) | US3_PS6_3 (049) | **US3_PS6_4 (050)** |
|---|---|---|---|
| Mínimos de S11 en el canal | 8,005 GHz | 7,928 (−32,6 dB) y 8,192 GHz (−17,6 dB) | **7,936 GHz (−21,66 dB), único** |
| Peor S11 en el canal | −8,16 dB | −10,94 dB (7,7376) | **−10,92 dB (8,2368)** |
| Bordes 7,7376 / 8,2368 | −8,16 / −10,40 | −10,94 / — | **−11,77 / −10,92** |
| Canal ≤ −10 dB | 88 % | 100 % | **100 %** |
| Región ≤ −10 dB | 7,797–8,248 (451 MHz) | 7,715–8,270 (555 MHz) | **7,687–8,318 (631 MHz)** |
| η_rad = P_rad/P_acept | 0,592–0,683 | 0,342–0,687 | **0,654–0,709** |
| Ganancia realizada broadside | 3,10–4,23 dBi | 0,65–4,36 dBi | **4,03–4,71 dBi** |
| Rizado τ_g (copolar y, broadside, diagnóstico) | 91 ps | 474 ps | **32 ps** (17,8 ps en el interior) |

- La región ≤ −10 dB de 050 no es un ancho de banda nominal: deja 50 MHz de margen por debajo del canal y 81 MHz por encima.
- El mínimo de −34,8 dB en 9,855 GHz de 050 está fuera del canal.
- El τ_g es la fase del campo lejano copolar en broadside, con 11 puntos cada ≈ 50 MHz (`DIAGNOSTIC`). La componente x es polarización cruzada unos 100 dB por debajo y no se cita.
- η es la de radiación sobre la potencia aceptada. Con la desadaptación, la eficiencia total de 050 queda en 0,60–0,70.

## Hipótesis pre-registradas

**US3_PS6_3 (049)**
- **H0 se cumple solo en parte:** el mínimo está en 7,928 GHz, dentro del rango, pero aparece un segundo mínimo en 8,192 GHz y H0 decía «sin segundo mínimo».
- **H1 se cumple:** −10,94 dB, aunque la guía predecía −9,4 dB.
- **H2 falla:** η cae a 0,415 en 8,187 GHz y a 0,342 en 8,237 GHz, y la ganancia realizada a 0,65 dBi. Es una caída hacia el borde superior, no un valle con mínimo localizado dentro del canal.
- **Regla de decisión:** η < 0,45 activa la regla 3. No se propone para HFSS.

**US3_PS6_4 (050)**
- **H0 se cumple:** mínimo único en 7,936 GHz (rango 7,87–7,99).
- **H1 se cumple en malla base:** −10,92 dB. La guía predecía lo contrario (unos −8,9 dB, probabilidad 15–20 %).
- **H2 se cumple:** η ≥ 0,654, ganancia ≥ 4,03 dBi, sin valle.
- **Regla de decisión 1:** pide la malla fina (≈ 2670 s, más que el tope de 1800 s, así que necesita permiso del propietario) y preguntar si se simula en HFSS.

## Lectura
- **US3_PS6_4 cumple en malla base los dos objetivos del propietario:** peor S11 ≤ −10 dB en todo el canal y mínimo bajado a 7,936 GHz. No pierde eficiencia: es la mejor combinación de los candidatos U-slot hasta ahora (adaptación, η plana, ganancia y τ_g).
- **No es robusta todavía.** El margen es |Γ| 0,284 frente a 0,316 (ΔΓ = 0,032, 0,92 dB). Es menor que la sensibilidad de malla observada en módulo: |ΔΓ| de 0,040–0,056 en los bordes en 038/039 y hasta 0,136 en el borde superior en 045/047.
  - Atenuantes: en esos pares el borde superior siempre mejoró con la malla fina; el inferior tiene 1,77 dB de margen; en frecuencia hay 50 y 81 MHz de margen frente a desplazamientos de borde de 16–41 MHz; 050 es un mínimo único y suave, como 038, no la estructura de dos modos de 045.
  - Si HFSS desplaza la curva unos 50 MHz hacia abajo, como en US3_PS6, el peor caso leído de la propia curva sería de unos −10,4 dB.
- **La malla de 050 tampoco es exactamente la de 038.** Las celdas y son las mismas (198) y el parche coincide, pero en x hay 160 frente a 156 celdas y el transformador pasa de unas 2,5 a unas 3,5 celdas. La comparación 038 → 050 mezcla la geometría con una malla algo mejor en el transformador. La nota de malla de `variants/US3_PS6_4.json` («+27 líneas y») compara con 049, no con 038; no se edita el JSON porque su hash está registrado.
- **La causa del hundimiento de η en 049 no está establecida.** La malla de 049 no es la de 038, aunque la nota de `variants/US3_PS6_3.json` diga que solo cambia una línea de borde: gradado 1,4 frente a 1,5, 171 frente a 198 celdas y, 2,24 M frente a 2,59 M celdas, y solo 73 de 199 posiciones y coinciden. Que el parásito alargado vuelva a acoplarse es plausible (segundo mínimo, τ_g negativo), pero está confundido con la malla más gruesa. No hay que citar «Lp es la palanca fuerte» como conclusión.
- **Escalón cerca del puerto (sin validar).** La línea de 50 Ω de 050 mide 2,605 mm (0,66 veces su ancho, 1,26 h). El escalón 3,92 → 1,0 mm queda más cerca del puerto lumped y su campo evanescente podría llegar al plano del puerto; `port_validity` no lo detecta. El plano de referencia es el mismo que en 038. En HFSS conviene un wave port con de-embedding al mismo plano.
- **Contexto físico.** Holgura lateral de 6,0 mm (0,16 λ0) frente a 7,29 mm en 038: el efecto del plano finito en el diagrama no está cuantificado. El transformador de 94,9 Ω mide unos 125° a f0: es «tipo λ/4», no un λ/4 estricto.

## Siguiente paso
1. Malla fina de US3_PS6_4 (5,57 M celdas nodales, ≈ 2670 s, ≈ 2 GiB): solo con permiso del propietario.
2. Si el propietario va a simularlo en HFSS: scripts del elemento y del array 1×5 con `arr_d` paramétrico, y revisión de `design-reviewer` antes de entregarlos.

## Auditoría
`validator` (2026-11-19): **OK con observaciones** en las dos rondas. Run único por carpeta, hashes, versiones, energía y todas las cifras recalculados y confirmados; 198 tests OK. Sus reservas (malla de 049 distinta de 038, robustez de 050 no demostrada, escalón cerca del puerto, nota de malla de 050, τ_g solo copolar, registro de procedencia, desvío de la regla de 049, contexto físico) están incorporadas arriba.

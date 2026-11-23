# HFSS del elemento US3_PS6_4 (2026-11-20)

- **Fuente:** exportación del propietario (HFSS 2025.1.0, Drive), en `hfss/results/results_US3_PS6_4/US3_PS6_4/`. Script `hfss/build/US3_PS6_4/claude_aedt_native_US3_PS6_4_ch9.py`, revisado por `design-reviewer` antes de simular.
- **Pre-registro:** `hfss/results/results_US3_PS6_4/preregistro_hfss.md` (commit ba0a8da, anterior a los resultados, commit e439276).
- **Geometría:** la variación exportada coincide con `variants/US3_PS6_4.json` (sha256 6c9b0c77…): parche 14 × 6,29 mm, parásito 13,58 × 7,05 mm a z = 1,035 mm, transformador 1,0 × 7,25 mm, línea de 50 Ω de 3,92 mm y 2,605 mm, U-slot 4,4 / 2,65 / 0,8 mm. FR4 εr 4,4, tanδ 0,017, h 2,07 mm, cobre 35 µm. Puerto lumped de 50 Ω en y = −13 mm.
- **Convergencia:** 12 pasadas de 25, ΔS 0,0099 (objetivo 0,01), dos pasadas consecutivas, multifrecuencia en 7,7376 / 7,9872 / 8,2368 GHz, 25 959 tetraedros. 4 núcleos, ≈ 1,4 GB por proceso, 2 min 16 s. La pasada 12 no mejora a la 11: convergencia justa.
- **Barrido:** interpolado 7,5–8,5 GHz (1 MHz), convergido y pasivo; 11 puntos discretos con campos.

## Resultados

| | US3_PS6 (HFSS) | **US3_PS6_4 (HFSS)** | US3_PS6_4 (openEMS base / fina) |
|---|---|---|---|
| Peor S11 en el canal | −8,72 dB | **−9,82 dB** (8,236 GHz) | −10,92 / −11,24 dB |
| Bordes 7,7376 / 8,2368 | | −13,02 / −9,82 dB | −11,77 / −10,92 · −11,46 / −11,24 |
| Canal ≤ −10 dB | 83,6 % | **96,4 %** (100 % ≤ −6 dB) | 100 % |
| Mínimo | 7,955 GHz | **7,886 GHz** (−18,25 dB), único | 7,936 / 7,947 GHz |
| Región ≤ −10 dB | | 7,655–8,219 GHz (563 MHz) | 7,687–8,318 / 7,695–8,380 |
| η_rad | 0,69–0,74 | **0,742–0,775**, sin valle | 0,654–0,709 / 0,661–0,712 |
| Ganancia realizada broadside | 3,5–4,4 dBi | **4,42–5,02 dBi** (pico 4,50–5,29 dBi en θ = 5–15° en yz) | 4,03–4,71 / 4,13–4,71 |
| Rizado τ_g radiado broadside copolar (11 puntos) | ≈ 20 ps | **18,4 ps** (17,5 en el interior) | 32 / 15 ps |

## Contra el pre-registro
- **H_HFSS0 (mínimo 7,86–7,90 GHz):** cumplida, 7,886 GHz. Desfase HFSS−openEMS −50 MHz (base) y −61 MHz (fina), como en US3_PS6.
- **H_HFSS1 (peor S11 entre −9,1 y −10,9 dB; ≈ 50 % de cumplir −10 dB):** dentro del rango, en el borde superior del canal. No cumple −10 dB por 0,18 dB. El borde superior a −10 dB (8,219 GHz) queda por debajo del rango previsto (8,24–8,27 base; 8,31–8,33 fina): la banda de −10 dB es más estrecha (563 MHz) que en openEMS (631 / 685 MHz). Solo coincide con el escenario base con sesgo de 0,35 dB, en su extremo inferior.
- **H_HFSS2 (η ≥ 0,6, ganancia ≥ 2 dBi):** cumplida con holgura; η y ganancia mejoran respecto a openEMS en el sentido previsto.

## Lectura
- **Los 0,18 dB están dentro de la incertidumbre.** |Γ| = 0,323 frente a 0,316 en el umbral; ΔS 0,0099 equivale a unos ±0,27 dB alrededor de −10 dB (−9,55 a −10,09 dB). No se puede afirmar que cumpla ni que no cumpla −10 dB. Sí cumple −6 dB con 3,8 dB de margen.
- **Como radiador es el mejor elemento simulado en HFSS:** la η y la ganancia más altas de la campaña y un retardo de grupo radiado casi plano, sin el valle de eficiencia de la familia PS4.
- **Regla de decisión pre-registrada:** se aplica la regla 1 (iterar en patch_L como variante nueva), con el matiz de que el fallo no es solo un desplazamiento: hay un sesgo optimista de openEMS (≈ 0,6 dB en el borde superior) y una banda más estrecha. Con traslación pura de la curva HFSS, el mejor centrado (+50…+60 MHz) daría como mucho −10,57 dB; subir el mínimo unos +40–50 MHz (patch_L ≈ 6,22 mm, Δ −0,07 mm; la pendiente es incierta entre 5,7 y 7,1 MHz por 0,01 mm) dejaría el peor S11 en −10,3…−10,4 dB y el borde inferior en −11,1…−11,5 dB. Esa mejora es del orden de la tolerancia de grabado y de la incertidumbre de εr del FR4 provisional: −10 dB en toda la banda es un objetivo marginal con este sustrato.
- **Antes de gastar un refinamiento,** hacer el contraste con wave port: si el wave port da ≤ −10 dB, la iteración de patch_L sobra.

## Estado de evidencia
- **S11 (adaptación):** `EM_SIMULATED` (HFSS convergido, puerto lumped). No `HFSS_VALIDATED` hasta el contraste con wave port.
- **Radiación (η, ganancia, τ_g):** `HFSS_VALIDATED`, con la reserva del puerto lumped.
- En tablas de estado del elemento se usa el más bajo, `EM_SIMULATED`.

## Auditoría
`validator` (2026-11-20): **OK con observaciones**. Reproduce todas las cifras (s1p, ff, cortes, parámetros de antena; identidades internas Prad = η·Pacc), la geometría y la convergencia; 223 tests OK. Reservas:
1. Contraste con wave port pendiente (media-alta).
2. Sin control de convergencia más estricto (ΔS 0,005 o 3 pasadas más) (media).
3. Los 11 puntos discretos son los puntos base del barrido: la comparación interpolado/discreto de la guía es vacía aquí; un spline y un leave-one-out independientes dan |ΔΓ| ≤ 3e-4 (media).
4. Etiquetas previas incoherentes: los elementos US3_PS6 y US3_PS4_2_1 se etiquetaron `HFSS_VALIDATED` sin wave port; con la regla más restrictiva su S11 debería llevar la misma reserva (media).
5. Documentación por actualizar (README de resultados y `campaign_state.json`) (media-baja; hecho en este commit).
6. Rizado τ_g con 11 puntos (paso 49,92 MHz); citarlo como «11 puntos» (baja).
7. El pico de ganancia no está en broadside (θ = 5–15° en yz): citar broadside y pico por separado (baja).
8. Mejora alcanzable con patch_L del orden de la tolerancia de fabricación (baja).
9. Avisos «Secondary solver criterion is not converged» en dos puntos base (8,087 y 8,137 GHz), con error de 0,07 y 0,39 %; el barrido final es convergido y pasivo (baja).
10. Una variante de patch_L consume un refinamiento del candidato: pre-registrarla aparte (baja).

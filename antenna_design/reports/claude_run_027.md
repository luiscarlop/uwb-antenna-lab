# Ronda Claude 027: P01_MS2, transformador λ/4 alargado (6,6 → 7,1 mm)

- **ID del experimento:** P01_MS2_OPENEMS_027.
- **Fecha:** 2026-11-13, ronda 27/40, en la sesión del propietario.
- **Orquestador:** `claude-opus-5-5`.
- **FDTD:** 1, con malla base.
- **Evidencia:** `EM_SIMULATED`.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Contexto
El propietario revisó P01_MS1 y US3_MS3 en HFSS ([`claude_hfss_review_2026-11-13.md`](claude_hfss_review_2026-11-13.md)) y pidió seguir iterando en openEMS. La campaña pasa de `READY_FOR_HFSS_REVIEW` (revisión hecha) a **ACTIVE**.

## Modelo guía
[`em/feed_retune_guide.py`](../em/feed_retune_guide.py) es un `GUIDE_MODEL`, no un resultado EM.
- Toma Zin del run 026 y le quita analíticamente la línea de 50 Ω y el transformador, para quedarse con la impedancia del parche (Z_parche).
- Después prueba otros transformadores: más largos o más estrechos ensancharían la banda de −10 dB.
- Plan en tres pasos, cada uno con una sola variable: longitud a 7,1 mm, luego ancho a 0,5 mm y luego longitud a 7,6 mm.

## Propuesta
[`variants/P01_MS2.json`](../variants/P01_MS2.json): P01_MS1 con **solo la longitud del transformador cambiada, de 6,6 a 7,1 mm**.
- La línea de 50 Ω se acorta 0,5 mm porque el borde de la placa es fijo. Es una consecuencia del cambio y no una segunda variable, pero sí altera la fase de S11.
- Se mantienen el parche (7,322 × 11,421 mm), el ancho del transformador (0,8 mm), el material (FR4 εr 4,4, tanδ 0,017, 2,07 mm), la placa y el puerto concentrado en el borde.

## Recursos
- 2,06 M celdas.
- 191 s de reloj y 330 s de CPU, con 2 CPU.
- RSS de 429 MB.
- 9996 pasos; la energía cae a −53,2 dB.

## Resultados (malla base)
| | P01_MS1 (025) | **P01_MS2 (027)** |
|---|---|---|
| Peor S11 en el canal | −8,34 dB | **−10,42 dB** (7,7376 GHz) |
| ≤ −10 dB en las 501 muestras | no | **sí** |
| Banda a −10 dB | 7,798–8,345 GHz (547 MHz) | 7,724–8,306 GHz (582 MHz) |
| Eficiencia de radiación | 0,72–0,76 | 0,73–0,76 |
| Ganancia realizada en broadside | 3,99–4,80 dBi | 4,30–4,78 dBi |

Pasividad, puerto válido y balance de potencia NF2FF correctos. Los volcados brutos están fuera del repositorio, con su SHA registrado.

## Hipótesis
- **H1 (la banda de −10 dB se ensancha): se cumple por poco.** Gana un 6 %, frente al 20 % predicho.
- **H2 (peor caso a menos de 1 dB del modelo): no se cumple.** El modelo predijo unos −9,3 dB y el resultado es −10,42 dB.
- **El modelo guía falla en el valor.** El error medio en el canal es de 2,9 dB, y en el borde superior predijo una tendencia contraria a la real. El Z_parche que se obtiene de 025 y el que se obtiene de 027 difieren en unos 20 Ω de reactancia, porque el modelo no incluye la unión entre línea y transformador, el efecto del extremo abierto ni las pérdidas.
- **Consecuencia:** el modelo vale como guía cualitativa. **No se usa para el paso 2** (cambiar el ancho, que cambia Z0 y la unión). Queda documentado en el script.

## Riesgo frente a HFSS
- HFSS da las resonancias en torno a un 0,9 % **más bajas**.
- Con ese desplazamiento, la banda de −10 dB baja: **gana margen en el borde inferior y pierde en el superior**.
- Aplicando −0,9 % a 027, el peor caso sería unos −9,9 dB en 8,2368 GHz (−9,75 dB con −1,0 %).
- En P01_MS1, HFSS dio además una banda 37 MHz más estrecha que openEMS.
- **No se promete −10 dB en HFSS.**

## Regla para la ronda 028 (fijada antes de simular)
Experimento: P01_MS2 con malla fina, mismo SHA de la variante y mismas opciones.
- **Se afirma −10 dB en todo el canal** solo si se cumplen todas estas condiciones:
  - peor S11 ≤ −10,0 dB en las 501 muestras, **con las dos mallas**;
  - |ΔΓ| ≤ 0,03 en el canal;
  - los bordes de la región contigua de −10 dB que contiene f0 se mueven ≤ 10 MHz;
  - energía ≤ −50 dB, `port_validity` OK y |S11| ≤ 1,02.
  - Si todo se cumple, el resultado es `BOUNDED_SENSITIVITY_PASS` (sensibilidad de malla acotada, no convergencia).
- **Si el peor caso con la malla fina cae entre −9,5 y −10 dB**, el resultado es «sensible a la malla» y no se afirma −10 dB.
- **Se sigue afirmando −6 dB** si se cumple la regla de dos mallas de la ronda 026.
- Lo esperable por la tendencia 025→026 es un peor caso de unos −10,25 dB.

## Estado
Ronda 27/40. Campaña ACTIVE. **CONTINUE.**

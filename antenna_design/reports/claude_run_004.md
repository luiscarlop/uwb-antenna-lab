# Ronda Claude 004: punto de adaptación de P01 (P01_R2)

- **ID del experimento:** P01_R2_OPENEMS_004, segundo y último refinamiento de P01. Fecha 2026-11-03, de 12:36 a 13:05 UTC. Sesión autónoma, ronda 4/40.
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:**
  - `rf-designer`: diseño, con el modelo circuital de guía.
  - `validator`: auditoría y viabilidad.
- **FDTD:** 1, lanzada por el orquestador.
- **Evidencia:** `EM_SIMULATED`, con solo S11 y Zin en un puerto concentrado ideal. La independencia de malla es NOT_ESTABLISHED. No hay campo lejano.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**. Recomienda **B: verificar la malla antes de declarar `READY_FOR_HFSS_REVIEW`**.

## Propuesta y parámetros
[`variants/P01_R2.json`](../variants/P01_R2.json). Es un punto de diseño para la adaptación, derivado del ajuste circuital de P01_R1: Ls = 1,20 nH y Q = 13,5. Para compensar Ls hay que trabajar por encima de la resonancia, con R_pico más alto y fr por debajo de f0.
- **L:** pasa de 7,65 a **7,95 mm**, para bajar fr hasta unos 7,71 GHz.
- **Sonda:** pasa de s/L = 0,22 a **0,34**; queda en y = −2,703 mm, a 1,27 mm del borde. Así R_pico sube a unos 86 Ω según el modelo de cavidad calibrado.
- Las dos se cambian a la vez, de forma declarada, porque responden al mismo objetivo. **No se puede atribuir el efecto a cada una por separado.**
- **Sin cambios:** W, FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), placa de 26×26 mm, sonda vertical de 50 Ω y reglas de malla de 001.
- **Excepción de malla:** el suavizado de openEMS dejó una razón de 1,4286 entre celdas vecinas en y, entre el borde y la sonda.
  - `patch_openems.py` acepta ahora hasta 1,5, pero **solo** si el suavizado no alcanza 1,4, y lo deja registrado en `prepared.json` (`mesh_grading_limit_used`, `mesh_ratio_above_1p4_by_axis`).
  - P01_BASE sigue reproduciendo byte a byte el XML de 001, y P01_R1 el de 003. Lo comprobó `validator`.

## Recursos
| | Estimación | Observado |
|---|---|---|
| Celdas | 1 820 448 (1,867 M nodales) | — |
| RAM (base medida ×2) | 599 MB | RSS de 334 MiB |
| Tiempo | 270 s | 274 s de pared, 266 s de motor, 2 CPU |
| Pasos y decaimiento de energía | — | 6993 pasos, −52,82 dB |

Comando: `timeout 900s taskset -c 0,1 python em/patch_openems.py solve --variant variants/P01_R2.json --out em/P01_R2_OPENEMS_004`.

## Métricas
Ficheros:
- [`result.json`](../em/P01_R2_OPENEMS_004/result.json)
- [`s11_complex.csv`](../em/P01_R2_OPENEMS_004/s11_complex.csv)
- [`s11_wideband.csv`](../em/P01_R2_OPENEMS_004/s11_wideband.csv)
- [`s11_analysis.json`](../em/P01_R2_OPENEMS_004/s11_analysis.json)
- [`circuit_fits/P01_R2_OPENEMS_004_fit.json`](../em/circuit_fits/P01_R2_OPENEMS_004_fit.json)

| Canal 7,7376–8,2368 GHz | 001 (P01) | 003 (P01_R1) | **004 (P01_R2)** |
|---|---|---|---|
| Peor S11 | −1,94 dB | −3,12 dB | **−6,53 dB** (7,7376 GHz) |
| S11 en f0 (7,987 GHz) | −3,6 dB | — | −16,0 dB |
| Mejor S11 | −7,63 dB | −7,31 dB | −19,05 dB (8,059 GHz) |
| ≤ −6 dB en todo el canal | No | No | **Sí, en las 501 muestras** (`PASS_INTERPOLATED` en el analizador de Codex) |
| ≤ −10 dB en todo el canal | No | No | No (128 muestras por encima, de 7,7376 a 7,864 GHz) |

- **Ajuste circuital de 004:** R = 101,9 Ω, Q = 13,0, fr = 7,721 GHz, Ls = 1,232 nH. El error RMS es de 0,76 Ω.
- **El modelo de guía falló en lo cuantitativo.** Predijo −7,13 dB en el borde superior con R = 85,7 Ω, y el peor punto real está en el borde inferior: −6,53 dB, con R un 19 % mayor. Queda como guía cualitativa.

## Viabilidad y decisión
Es el primer resultado EM que cumple el mínimo de −6 dB en todo el canal. **No se declara todavía `READY_FOR_HFSS_REVIEW`**, por estos motivos:
- El margen sobre −6 dB es de solo 0,53 dB, y la sensibilidad de malla medida en P01 (001 frente a 002) fue de +0,19 a +0,78 dB hacia peor adaptación.
- El fallback de malla de 1,43 añade una pequeña diferencia de reglas respecto a 003.
- Declararlo detiene las simulaciones hasta la revisión humana.

**Regla de decisión fijada antes de la ronda 005:** simular P01_R2 con la malla fina de 002 (xy 0,35 mm, z en aire 0,6 mm, 10 celdas en el sustrato, `metal_edge_res` 0,175 mm), sin cambiar la geometría.
- **Si la malla fina cumple ≤ −6 dB en todas las muestras del canal:** declarar `READY_FOR_HFSS_REVIEW`, con la sensibilidad medida en el propio candidato.
- **Si no lo cumple:** registrar la sensibilidad, no declarar nada y pasar a P02 (U-slot), que además baja Q para intentar llegar a −10 dB.

Esa verificación no es un tercer refinamiento de diseño, porque la geometría no cambia.

## Reservas que siguen abiertas
- El puerto es una línea concentrada ideal de 1,6 mm. Su Ls ≈ 1,2 nH no corresponde a ningún conector, y un pin o una vía reales la cambiarán. **Decisión pendiente del propietario (no bloquea):** fijar la alimentación real que hay que modelar.
- La fabricabilidad de la sonda a 1,27 mm del borde no está comprobada con reglas de fabricante ni de conector.
- El FR4 es provisional, no hay campo lejano, y por tanto tampoco ganancia, eficiencia ni retardo radiado.

## Estado
- Ronda 4/40. Hay un candidato **prometedor pero no declarado viable**.
- Tests: 20 OK.
- **CONTINUE.**

## Corrección (2026-11-03, tras leer el artículo EuCAP 2027)
Lo que aquí se afirma sobre que −10 dB «no es alcanzable con Q ≈ 13» vale **solo dentro del modelo de guía**: resonancia única más la Ls de la sonda, ajustando solo R_pico y fr. El límite de Bode–Fano para el canal 9 (B = 6,25 %, Q ≈ 13) es de unos −33,6 dB con una red ideal, así que −10 dB no está prohibido por el ancho de banda. Bajar Q es una vía, no la única. Detalles en [`claude_eucap2027_context.md`](claude_eucap2027_context.md). Los resultados EM no cambian.

# Ronda Claude 037: US3_PS5, propuesta del super revisor (Fable)

- **ID del experimento:** US3_PS5_OPENEMS_037.
- **Fecha:** 2026-11-16, ronda 37/40.
- **Orquestador:** `claude-opus-5-5`.
- **Autoría:**
  - El diseño lo propuso `design-reviewer` (Fable 5.2), a petición del propietario («utiliza a Fable para que ayude en el diseño»).
  - El propietario lo aprobó («go ahead … tomemos como referencia los resultados de PS4»).
  - `rf-designer` escribió el JSON.
- **FDTD:** 1, con malla base y `--max-timesteps 60000`. El contenedor se reinició durante la primera ejecución, y el run se relanzó entero en la misma carpeta.
- **Evidencia:** `EM_SIMULATED`, sin convergencia de malla.

## Diagnóstico del revisor (modelo guía, GUIDE_MODEL)
- **Modelo:** dos resonadores acoplados, uno brillante (unido al puerto) y otro oscuro, ajustados a |S11| y η de 032 y 036. Su modo superior es poco radiante: Q_rad ≈ 200 frente a Q_d ≈ 47 del FR4.
- **Validación del propio modelo:** ajustado solo con 032, predijo 036 con ≈ 1 dB de error, y reproduce US3_MS3 sin haberlo ajustado.
- **Conclusión del revisor:** con tanδ 0,017 no es alcanzable de forma robusta tener dos resonancias radiantes dentro del canal. Propuesta: sacar el modo oscuro del canal (≈ +410 MHz) y centrar el brillante (≈ +85 MHz).

## Cambio
[`variants/US3_PS5.json`](../variants/US3_PS5.json), con US3_PS4 como base:
- `patch_L` 6,302 → **6,18 mm**;
- parásito Lp 7,46 → **7,05 mm** (y −2,91…4,14, z 1,035);
- la alimentación se ajusta al nuevo borde del parche.

## Resultados (malla base)
- **Ejecución:** converge a −51,95 dB en 34 372 pasos, en 777 s y 0,49 GB.

| | US3_PS4 (036) | **US3_PS5 (037)** | Predicción del revisor |
|---|---|---|---|
| Mínimo de S11 | 7,826 / 8,158 GHz | **un solo mínimo: −22,7 dB en 8,065 GHz** | 7,93–8,01 GHz |
| Rasgo superior | | sin mínimo en 8,3–8,6 GHz; cruces X = 0 en 8,035 y 8,61 GHz | 8,45–8,60 GHz |
| Banda de −10 dB | 7,631–8,245 GHz | 7,85–8,32 GHz | |
| Peor S11 en el canal | −10,66 dB | **−6,87 dB** (7,7376 GHz; el borde superior está en −13,1 dB) | ≈ −9,4 (−8,2…−9,7) |
| η en el canal | 0,677 → 0,244 → 0,373 | **0,639–0,688, sin valle** | 0,62–0,70 |
| Ganancia realizada broadside | 4,3 → −0,48 dBi | **2,99–4,25 dBi** | ≥ 3,3 dBi |
| Dmax | | 6,3–6,6 dBi en θ 15–20°, φ 270° | |

## Hipótesis
- **H0 se cumple a medias.** El mínimo brillante queda 55–135 MHz por encima de lo previsto, y no se ve un mínimo del modo superior entre 8,45 y 8,60 GHz (hay un cruce X = 0 en 8,61 GHz).
- **H1 falla:** −6,87 dB frente al objetivo de ≤ −8 dB. Es la asimetría entre bordes por el desplazamiento hacia arriba.
- **H2 se cumple:** η ≥ 0,64 y ganancia ≥ 2,99 dBi en los 11 puntos.

## Lectura
- **Se confirma el diagnóstico central del revisor:** al sacar del canal el modo poco radiante, desaparece el valle de eficiencia.
- La predicción de la frecuencia del modo brillante falló por 55–135 MHz (8,065 GHz frente a 7,93–8,01 GHz).
- El peor caso queda en el borde inferior por el desplazamiento; no es un problema de nivel de adaptación (el mínimo está en −22,7 dB en la rejilla de 1 MHz, en 8,063 GHz).
- **PS5 no mejora a PS4 en S11:** gana en η (sin valle), pero pierde adaptación en el borde inferior (−6,87 dB frente a −10,66 dB; η 0,654 frente a 0,677 en ese punto). Los cruces X = 0 son lecturas de Zin, no mínimos de S11.
- **Siguiente paso** (regla del revisor: si la asimetría entre bordes supera 2 dB, retocar solo `patch_L`): ronda 038, US3_PS6, con `patch_L` +0,11 mm.

## Auditoría
`validator` (2026-11-16, 037 y 038 en conjunto): **OK con observaciones**. Run único y coherente tras el reinicio; cifras recalculadas desde CSV y JSON. Las observaciones (frecuencia del modo brillante, PS5 frente a PS4 en S11) ya están corregidas arriba. Los volcados `nf2ff_*.h5` se borraron tras guardar sus hashes (política del repositorio), por lo que esos hashes no se pueden reverificar a posteriori.

Comparación de modelos y niveles en [`claude_model_tiers_evaluation.md`](claude_model_tiers_evaluation.md).

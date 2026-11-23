# Ronda Claude 008: P03_MS3, escalado del hexágono para centrar la adaptación

- **ID del experimento:** P03_MS3_OPENEMS_008. Fecha: 2026-11-03. Ronda 8/40, routine.
- **Orquestador:** el modelo de la sesión es Sonnet 5.5, no Opus (anotado según el ciclo).
- **Subagentes:** ninguno. `validator` (y el resto de agentes del proyecto) no estaba disponible en este entorno, así que **no hay auditoría independiente**: las comprobaciones de la sección 5 las hizo el propio orquestador.
- **FDTD:** 1. **Solver:** openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f (compilados por el setup script; funcionaban al empezar).

## 1. Propuesta
Hipótesis de la ronda 7: escalar el radio del hexágono de 4,8 a 4,96 mm (+3,3 %, con f ∝ 1/r) para llevar el mínimo de |S11| (8,25 GHz en 007) a f0.
- **Única variable:** radio 4,8 → 4,96 mm ([`variants/P03_MS3.json`](../variants/P03_MS3.json)).
- El centro del parche pasa de y = 3,3 a 3,438564 mm para que el lado plano inferior siga en y = −0,856922 mm. Alimentación (línea 50 Ω, transformador λ/4 de 0,72 × 5,22 mm), ranura (r = 1,1 mm), FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), placa, excitación y reglas de malla: **idénticos a P03_MS2**. Se comprobó por comparación de `variant.json` de 007 y 008.
- Material y alimentación se mantienen, como pide el ciclo.

## 2. Ejecución y recursos
```
python em/patch_openems.py prepare ... && timeout 1300s taskset -c 0,1 python em/patch_openems.py solve --variant variants/P03_MS3.json --out em/P03_MS3_OPENEMS_008 --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9
```
- 2 CPU, **205 s** de pared, 352 s de CPU, RSS de pico 449 MiB, 2,26 M celdas, 10 965 pasos, energía final ≈ −49,7 dB (muestreo de `openEMS_run_stats.txt`).
- `port_validity: OK` (máx |S11| = 0,949, pasivo). Sin muestras de β en valor de reserva dentro del canal.
- Los volcados NF2FF brutos no se versionan; su SHA256 está en `nf2ff_raw_dumps.sha256`.

## 3. Resultados (`EM_SIMULATED`, malla única)
Ficheros: [`result.json`](../em/P03_MS3_OPENEMS_008/result.json), [`s11_measplane.csv`](../em/P03_MS3_OPENEMS_008/s11_measplane.csv), [`nf2ff_summary.json`](../em/P03_MS3_OPENEMS_008/nf2ff_summary.json).

| Frecuencia (GHz) | S11 MS3 (dB) | S11 MS2 (dB, 007) |
|---|---|---|
| 7,7376 | −5,48 | −3,20 |
| 7,8 | −6,61 | |
| 7,9872 (f0) | −10,29 | −6,35 |
| 8,1 | −10,10 | |
| 8,2368 | −7,62 | −10,53 |
| mínimo | −10,58 en 8,035 | −10,55 en 8,25 |

- **−6 dB no se cumple en todo el canal:** 31 de 501 muestras (7,7376–7,767 GHz) quedan por encima, con peor caso −5,48 dB. **−10 dB tampoco**: 142 de 501 muestras lo cumplen (7,966–8,107 GHz).
- El mínimo se desplazó −2,6 % (8,25 → 8,035 GHz), frente al −3,2 % previsto por f ∝ 1/r: coherente.
- Peor caso del canal mejora de −3,20 a −5,48 dB, a −0,52 dB de la referencia mínima.
- **Campo lejano** (`EM_SIMULATED_FAR_FIELD`, balance `ok` en las 11 frecuencias): eficiencia de radiación 0,70–0,74; eficiencia total 0,50 → 0,61 (máx. 0,66 en 8,04 GHz); directividad en broadside 3,9 → 5,4 dBi; **ganancia realizada en broadside +0,97 dBi (7,74 GHz) → +3,25 dBi (8,19 GHz)**, 2,81 dBi en f0. Máximo ≈ 6,9 dBi en θ = 35°, φ = 270° (haz inclinado hacia el lado de la alimentación, como en 007).
- **Retardo de grupo radiado:** diagnóstico (`nf2ff_group_delay_broadside.csv`), **sin citar rizado**, por la reserva de β heredada de 007.

## 4. Comparación con el mejor candidato anterior
| Diseño | Peor S11 en el canal | Cobertura −6 dB | Campo lejano |
|---|---|---|---|
| P01_R2 (sonda, malla fina) | −6,29 dB | sí, en rejilla muestreada | no |
| P03_MS2 (hexágono, MSL) | −3,20 dB | no | sí |
| **P03_MS3 (hexágono, MSL)** | **−5,48 dB** | no (31/501 muestras) | sí, ganancia realizada +1,0…+3,3 dBi |
P01_R2 sigue siendo el candidato para revisión HFSS. P03_MS3 es el primer diseño con alimentación microstrip realista que se acerca a −6 dB, pero **no cumple**.

## 5. Comprobaciones y reservas
- Tests: **38 OK** (tras `pip install ezdxf`, dependencia de `requirements.txt` que faltaba en el entorno de la routine).
- Geometría, alimentación y material idénticos a 007 salvo lo declarado.
- **Reservas heredadas de 007 (sin cambios):** β estimado por tramos y Z_line ≈ 54 Ω frente a 50 Ω (error de ~±0,04 en |Γ|, unos ±1,5 dB en torno a −10 dB y más cerca de −6 dB); malla única (convergencia no establecida); FR4 provisional; SMA no modelado; la eficiencia la calcula el propio solver.
- La diferencia de 0,52 dB hasta −6 dB en el borde inferior es del orden de la incertidumbre del puerto: no se debe leer como «casi cumple» ni como «falla por poco» sin reparar el puerto.
- **Sin validator:** esta ronda carece de auditoría independiente.

## 6. Siguiente hipótesis (no es un resultado)
- La adaptación se ensancha por abajo si el mínimo baja algo más: probar radio ≈ 5,0–5,05 mm (−1 a −2 % más) o, mejor, reparar antes el puerto (β suave único, calibrar Z_line, marcar `PORT_PHASE_UNRELIABLE`) y repetir sobre MS3 para saber si la incertidumbre del puerto cubre los 0,52 dB.
- Después, un refinamiento de malla de MS3 (límite de 2 refinamientos por candidato).
- P02: repetir con fc = 2,5 GHz para localizar la resonancia.

## Estado
CONTINUE. Ronda 8/40. Campaña `ACTIVE`; ningún candidato nuevo para HFSS.

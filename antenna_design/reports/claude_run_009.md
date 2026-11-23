# Ronda Claude 009: P03_MS4, segundo escalado del hexágono

- **ID:** P03_MS4_OPENEMS_009. 2026-11-03. Ronda 9/40, routine.
- **Orquestador:** Sonnet 5.5, no Opus (anotado). **Subagentes:** ninguno; `validator` no está disponible en este entorno, así que **no hay auditoría independiente**.
- **FDTD:** 1. openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f (funcionaban al empezar).

## 1. Propuesta
Hipótesis de la ronda 8: bajar algo más el mínimo de |S11| (8,035 GHz en 008) para recuperar el borde inferior (−5,48 dB a 7,7376 GHz).
- **Única variable:** radio del hexágono 4,96 → 5,03 mm (+1,4 %), [`variants/P03_MS4.json`](../variants/P03_MS4.json). Lado plano inferior (y = −0,856922 mm), alimentación, ranura (r = 1,1 mm, desplazada con el centro), FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), placa, excitación y malla idénticos a MS3.
- No se ha reparado el puerto MSL (queda para otra ronda; ver §6).

## 2. Ejecución y recursos
```
python em/patch_openems.py prepare --variant variants/P03_MS4.json --out em/P03_MS4_OPENEMS_009 --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9
timeout 1300s taskset -c 0,1 python em/patch_openems.py solve (mismos argumentos)
python em/patch_openems.py summarize ...   # tras copiar la salida de la ejecución a solver.log
```
- 2 CPU, **300,6 s** de pared, 519 s de CPU, RSS de pico 439 MiB, 11 648 pasos, energía final −53,65 dB. `port_validity: OK` (máx |S11| = 0,945).
- Volcados NF2FF brutos no versionados (`.h5`).
- Incidencia menor: `summarize` exige un `solver.log`; se creó copiando la salida de `solve`.

## 3. Resultados (`EM_SIMULATED`, malla única)
Ficheros: [`result.json`](../em/P03_MS4_OPENEMS_009/result.json), [`s11_measplane.csv`](../em/P03_MS4_OPENEMS_009/s11_measplane.csv), [`nf2ff_summary.json`](../em/P03_MS4_OPENEMS_009/nf2ff_summary.json).

| f (GHz) | S11 MS4 (dB) | S11 MS3 (dB, 008) |
|---|---|---|
| 7,7376 | −7,08 | −5,48 |
| 7,8 | −8,45 | −6,61 |
| 7,9872 (f0) | −10,36 | −10,29 |
| 8,1 | −8,44 | −10,10 |
| 8,2368 | **−6,01** | −7,62 |
| mínimo | −10,58 en 7,945 | −10,58 en 8,035 |

- **−6 dB en las 501 muestras del canal** (rejilla muestreada), pero el peor caso pasó al borde **superior** y es **−6,013 dB: margen de 0,013 dB**. −10 dB no se cumple (139/501 muestras).
- La mejora del borde inferior (+1,6 dB) se paga en el superior (−1,6 dB): el ancho útil sigue siendo ≈ el del canal.
- Los 111 valores de β de reserva están en 7,5–7,61 GHz, fuera del canal.
- **Campo lejano** (balance `ok` en 11 frecuencias): eficiencia de radiación 0,70–0,73; total 0,55–0,65; ganancia realizada en broadside +1,80 (7,74 GHz) → +3,25 dBi (8,0 GHz), +3,09 dBi en el borde superior; máximo ≈ 7 dBi en θ ≈ 25–35°, φ = 270° (haz inclinado hacia la alimentación). Retardo de grupo radiado: solo diagnóstico, sin rizado citado (β heredada de 007).

## 4. Comparación con el mejor candidato anterior
| Diseño | Peor S11 en el canal | Cobertura −6 dB | Campo lejano |
|---|---|---|---|
| P01_R2 (sonda, malla fina) | −6,29 dB | sí | no |
| P03_MS3 | −5,48 dB | no (31/501) | sí |
| **P03_MS4** | **−6,01 dB** | sí en rejilla, margen 0,013 dB | sí |
P01_R2 sigue siendo el candidato HFSS. MS4 es el primer diseño MSL que cumple −6 dB en la rejilla, pero **no se declara viable**: el margen es inferior en dos órdenes de magnitud a la incertidumbre del puerto (±1,5 dB según 007/008) y a la sensibilidad de malla (0,2–0,4 dB en P01).

## 5. Comprobaciones y reservas
- Tests: **38 OK**.
- Reservas heredadas sin cambios: β por tramos y Z_line ≈ 54 Ω; malla única; FR4 provisional; SMA no modelado; eficiencia calculada por el propio solver; sin validator.

## 6. Siguiente hipótesis (no es un resultado)
- Reparar el puerto (β suave único, calibrar Z_line, marcar `PORT_PHASE_UNRELIABLE`) y repetir sobre MS4 para saber si el 0,013 dB sobrevive; después, refinamiento de malla de MS4 (límite 2).
- Alternativa: radio ≈ 5,0 mm (punto medio) para repartir el margen entre ambos bordes.
- P02: repetir con fc = 2,5 GHz.

## Estado
CONTINUE. Ronda 9/40. Campaña `ACTIVE`; sin candidato nuevo para HFSS.

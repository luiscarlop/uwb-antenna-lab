# Ronda Claude 010: P03_MS5, hexágono r = 5,007 mm

- **ID:** P03_MS5_OPENEMS_010. 2026-11-03. Ronda 10/40, routine.
- **Orquestador:** Sonnet 5.5, no Opus (anotado). **Subagentes:** ninguno; `validator` no está disponible, así que **no hay auditoría independiente**.
- **FDTD:** 1. openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f. Al empezar los bindings no importaban; se repitió `claude_cloud_setup.sh` una vez (29 s) y funcionaron.

## 1. Propuesta
Evidencia: MS3 (r 4,96) peor caso −5,48 dB en el borde inferior; MS4 (r 5,03) −6,01 dB en el superior (run 009). La interpolación lineal de ambos bordes los iguala en r ≈ 5,007 mm (hipótesis: ≈ −6,5 dB en ambos).
- **Única variable:** radio 5,007 mm, [`variants/P03_MS5.json`](../variants/P03_MS5.json) (vértices interpolados linealmente entre MS3 y MS4; transformación afín exacta). Alimentación, ranura, FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), placa, excitación y malla idénticos.
- No se ha reparado el puerto MSL.

## 2. Ejecución y recursos
```
python em/patch_openems.py prepare --variant variants/P03_MS5.json --out em/P03_MS5_OPENEMS_010 --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9
timeout 1300s taskset -c 0,1 python em/patch_openems.py solve (mismos argumentos) > solver.log
python em/patch_openems.py summarize (mismos argumentos)
```
2 CPU, **208 s** de pared (engine 191 s), 356 s de CPU, RSS de pico 439 MiB (449 736 KiB), 11 388 pasos, energía final −51,4 dB. `port_validity: OK`.

## 3. Resultados (`EM_SIMULATED`, malla única)
Ficheros: [`result.json`](../em/P03_MS5_OPENEMS_010/result.json), [`s11_measplane.csv`](../em/P03_MS5_OPENEMS_010/s11_measplane.csv), [`nf2ff_summary.json`](../em/P03_MS5_OPENEMS_010/nf2ff_summary.json).

| f (GHz) | MS5 | MS4 (009) | MS3 (008) |
|---|---|---|---|
| 7,7376 | −6,51 | −7,08 | −5,48 |
| 7,8 | −7,82 | −8,45 | −6,61 |
| 7,9872 | −10,56 | −10,36 | −10,29 |
| 8,1 | −9,04 | −8,44 | −10,10 |
| 8,2368 | −6,50 | −6,01 | −7,62 |

- Peor caso en el canal **−6,50 dB** (8,2368 GHz; borde inferior −6,51 dB): −6 dB en las 501 muestras con **margen de 0,50 dB**, bordes equilibrados como predecía la hipótesis. Mínimo −10,58 dB en 7,975 GHz. −10 dB: solo 140/501 muestras, **no se cumple**.
- Campo lejano (balance `ok` en 11 frecuencias): eficiencia de radiación 0,70–0,74; total 0,55–0,65; ganancia realizada en broadside +1,55 (7,74 GHz) → +3,25 dBi (8,14 GHz), +3,04 dBi en f0; Dmax ≈ 7,0–7,3 dBi en θ ≈ 25–35° (haz inclinado). Retardo de grupo radiado: solo diagnóstico, sin rizado citado.

## 4. Comparación con el mejor candidato anterior
| Diseño | Peor S11 | Cobertura −6 dB | Campo lejano |
|---|---|---|---|
| P01_R2 (sonda, malla fina) | −6,29 dB | sí | no |
| P03_MS4 | −6,01 dB | sí, margen 0,013 dB | sí |
| **P03_MS5** | **−6,50 dB** | sí, margen 0,50 dB | sí |
MS5 es el mejor peor-caso de todos los diseños simulados y el primer MSL con margen no despreciable. **No se declara viable** ni se pasa a `READY_FOR_HFSS_REVIEW`: incertidumbre de puerto ≈ ±1,5 dB (007/008) mayor que el margen, malla única, FR4 provisional, SMA no modelado, eficiencia calculada por el propio solver y sin validator. P01_R2 sigue siendo el candidato HFSS vigente.

## 5. Comprobaciones
Tests: ver final del commit (`python3 -m unittest discover -s tests`). Reservas heredadas sin cambios.

## 6. Siguiente hipótesis (no es un resultado)
- Reparar el puerto (β suave único, calibrar Z_line, `PORT_PHASE_UNRELIABLE`) y repetir MS5 para ver si el margen de 0,5 dB sobrevive; después, refinamiento de malla de MS5 (límite 2).
- Si ambos aguantan, proponer MS5 al propietario para HFSS junto a P01_R2.
- P02: repetir con fc = 2,5 GHz.

## Estado
CONTINUE. Ronda 10/40. Campaña `ACTIVE`; sin candidato nuevo para HFSS.

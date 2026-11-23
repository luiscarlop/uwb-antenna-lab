# Ronda Claude 005: verificación de malla de P01_R2 → READY_FOR_HFSS_REVIEW

- **ID del experimento:** P01_R2_FINE_OPENEMS_005. Es la verificación de malla de P01_R2 con la misma geometría, y no un nuevo refinamiento. Fecha 2026-11-03, de 12:52 a 13:15 UTC. Sesión autónoma, ronda 5/40.
- **Orquestador:** `claude-opus-5-5`. Hizo el cambio del script y lanzó la FDTD; la auditoría fue de `validator`. FDTD: 1.
- **Evidencia:** `EM_SIMULATED`. **No es `HFSS_VALIDATED` ni `MEASURED`.**
- **Veredicto de `validator`:** **APROBAR CON RESERVAS. ¿Procede READY_FOR_HFSS_REVIEW? SÍ.**

## Regla pre-registrada
Quedó fijada en el commit `6e0622c` (ronda 4), antes de este solve, en [`claude_run_004.md`](claude_run_004.md) y en `campaign_state.json`. Decía así: *simular P01_R2 con la malla fina de 002, misma geometría; si todas las muestras del canal ≤ −6 dB → READY_FOR_HFSS_REVIEW; si no, registrar y pasar a P02*. **Se cumple**, y no se ha ajustado el criterio después.

## Cambio del script
[`em/patch_openems.py`](../em/patch_openems.py) admite ahora `--mesh {base,fine}`, con `base` por defecto.
- `fine` aplica las reglas de 002: xy 0,35 mm, z en aire 0,6 mm, 10 celdas en el sustrato y `metal_edge_res` 0,175 mm.
- `validator` comprobó la reproducción byte a byte de cuatro XML:

| Variante | Perfil | Coincide con |
|---|---|---|
| P01_BASE | base | XML de 001 |
| P01_BASE | fine | XML de 002 |
| P01_R2 | base | XML de 004 |
| P01_R2 | fine | XML de 005 |

- Entre el XML de 004 y el de 005 solo cambian las líneas de malla. La malla fina llega a 1,4 sin necesitar el fallback.

## Recursos
| | Estimación | Observado |
|---|---|---|
| Celdas | 4 775 904 | — |
| RAM (base medida ×2) | 1,56 GB | RSS de 752 620 KiB |
| Tiempo | 956 s | 868 s de pared, 848 s de motor, 2 CPU |
| Pasos y decaimiento de energía | — | 9509 pasos, −52,5 dB |

Comando: `timeout 2400s taskset -c 0,1 python em/patch_openems.py solve --mesh fine --variant variants/P01_R2.json --out em/P01_R2_FINE_OPENEMS_005`, con openEMS 0.37.0.post1.dev40+g5fecbb58d y CSXCAD 0.7.0.post1.dev8+g626b99f2f.

## Métricas
Ficheros:
- [`result.json`](../em/P01_R2_FINE_OPENEMS_005/result.json)
- [`s11_complex.csv`](../em/P01_R2_FINE_OPENEMS_005/s11_complex.csv)
- [`s11_wideband.csv`](../em/P01_R2_FINE_OPENEMS_005/s11_wideband.csv)
- [`s11_analysis.json`](../em/P01_R2_FINE_OPENEMS_005/s11_analysis.json)
- [`mesh_comparison.json`](../em/P01_R2_FINE_OPENEMS_005/mesh_comparison.json)

| Canal 7,7376–8,2368 GHz | 004 (malla base) | **005 (malla fina)** |
|---|---|---|
| Peor S11 | −6,53 dB (7,7376 GHz) | **−6,29 dB** (7,7376 GHz) |
| Muestras > −6 dB (de 501) | 0 | **0** (`PASS_INTERPOLATED` en el analizador de Codex) |
| Muestras > −10 dB | 128 | 143 (**−10 dB: FAIL**) |
| Mínimo de \|S11\| | −19,05 dB en 8,059 GHz | −16,69 dB en 8,053 GHz |
| Máximo de Re(Zin) | 107,5 Ω en 7,72 GHz | 107,8 Ω en 7,72 GHz |

- max|ΔS11| complejo entre mallas: **0,052** en el canal.
- La malla fina empeora el canal en +1,05 dB de media (máximo 2,4 dB, cerca del mínimo profundo).
- Coherencia entre S11 y Zin dentro de 3,5e-16, pasividad (|S11| ≤ 0,873) y salidas finitas: todo comprobado por `validator`.
- El ajuste circuital ([`P01_R2_FINE_OPENEMS_005_fit.json`](../em/circuit_fits/P01_R2_FINE_OPENEMS_005_fit.json)) da Q = 13,0 y Ls = 1,31 nH. **Es un GUIDE_MODEL:** sus casos «what-if» de −9,9 a −10,1 dB **no son resultados EM**.

## Reservas obligatorias para la revisión HFSS
1. **El margen es de solo 0,29 dB** sobre −6 dB, en el borde inferior del canal.
2. **Dos mallas miden sensibilidad, no convergencia**, y la tendencia al refinar es **hacia el fallo**: el peor caso pasó de −6,53 a −6,29 dB. Una tercera malla o HFSS podrían cruzar −6 dB.
3. **Puerto concentrado ideal** (línea vertical de 1,6 mm). La Ls ≈ 1,2–1,3 nH no corresponde a ningún conector, y un pin, una vía o un SMA reales cambiarán la adaptación.
4. **FR4 provisional** (εr 4,4, tanδ 0,017, pérdidas modeladas como conductividad constante). Sin datos de fabricante.
5. **Sonda a 1,27 mm del borde radiante**, sin comprobar con reglas de fabricante ni de conector.
6. **Sin campo lejano**, así que no hay ganancia, eficiencia ni retardo de grupo radiado. La derivada de la fase de S11 no es retardo radiado.
7. **−10 dB no se cumple** (143 muestras por encima).
8. La cobertura vale **solo en la rejilla muestreada** (1 MHz, con los extremos exactos), sin garantía entre muestras.
9. El siguiente paso es la **revisión HFSS**, y no supone ninguna validación.

## Decisiones para el propietario
- **Revisar P01_R2 en HFSS** con [`variants/P01_R2.json`](../variants/P01_R2.json): parche de 11,4213 × 7,95 mm y sonda en (0; −2,703) mm, sobre FR4 de 1,6 mm y placa de 26×26 mm. Para la transferencia están las herramientas de Codex.
- **Fijar la alimentación real** (conector y diámetro del pin) y el **sustrato real**. Las dos cosas afectan directamente al margen.
- Decidir si se busca −10 dB. El modelo de guía indica que con Q ≈ 13 no es alcanzable en este parche, y que haría falta bajar Q con P02 (U-slot), otro sustrato o más grosor.

## Estado
- Campaña: **READY_FOR_HFSS_REVIEW**, con el candidato P01_R2 en `EM_SIMULATED`.
- Ronda 5/40. Tests: 20 OK.
- **STOPPED:** la campaña queda a la espera de la revisión humana. El ciclo no prevé más rondas hasta entonces.

## Corrección (2026-11-03, tras leer el artículo EuCAP 2027)
Lo que aquí se afirma sobre que −10 dB «no es alcanzable con Q ≈ 13» vale **solo dentro del modelo de guía**: resonancia única más la Ls de la sonda, ajustando solo R_pico y fr. El límite de Bode–Fano para el canal 9 (B = 6,25 %, Q ≈ 13) es de unos −33,6 dB con una red ideal, así que −10 dB no está prohibido por el ancho de banda. Bajar Q es una vía, no la única. Detalles en [`claude_eucap2027_context.md`](claude_eucap2027_context.md). Los resultados EM no cambian.

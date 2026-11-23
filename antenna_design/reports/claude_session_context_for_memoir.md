# Contexto de la campaña de antena (sesión Claude, 2026-11-13 → 2026-11-18) para la memoria del TFG

Resumen de lo hecho y decidido en la sesión de diseño de antena de la rama `codex/uwb-ch9-antenna-design`, para que los agentes de redacción lo comparen con `latex_memoir/` de la rama `docs/memoria-tfg`. **Las cifras de detalle están en los ficheros citados: esa es la fuente de verdad, no este resumen.**

## Objetivo y restricciones
- Elemento radiante y array para IR-UWB IEEE 802.15.4z **canal 9**: f0 = 7,9872 GHz, banda 7,7376–8,2368 GHz (B = 499,2 MHz), referencia de 50 Ω.
- Sustrato: **FR4 homogéneo provisional** (εr 4,4, tanδ 0,017, h 2,07 mm), placa de 26 × 26 mm por elemento, cobre de 35 µm.
- Puerto lumped de 50 Ω en el borde de la placa, sin conector SMA (decisión del propietario, 2026-11-05).
- Estados de evidencia: `GEOMETRY_ONLY`, `EM_SIMULATED`, `HFSS_VALIDATED`, `MEASURED`. No hay medidas: nada está `MEASURED`.
- Criterios: S11 ≤ −6 dB en todo el canal es el mínimo y −10 dB el objetivo. Además se valoran la eficiencia de radiación, la ganancia realizada y el **rizado del retardo de grupo radiado**; esta última es la clave en IR-UWB.

## Herramientas
- **openEMS** v0.37.0-40-g5fecbb5 y CSXCAD v0.7.0-8, en FDTD sobre un contenedor en la nube.
  - Una simulación por ronda, 2 vCPU, criterio de energía −50 dB.
  - Malla base y fina; la comparación entre las dos es una prueba de sensibilidad, no de convergencia.
  - Script: `antenna_design/em/patch_openems.py`. Variantes en `antenna_design/variants/*.json`, con hipótesis pre-registradas.
- **HFSS 2025.1** en el equipo del propietario.
  - Scripts nativos de AEDT generados con PyAEDT 1.9.0: `antenna_design/hfss/build/<elemento>/`.
  - Exportadores: `antenna_design/hfss/export/`.
  - Análisis: `antenna_design/hfss/analysis/`.
  - Resultados: `antenna_design/hfss/results/results_<elemento>/`.
  - Guía: `antenna_design/hfss/CLAUDE_PYAEDT.md`.
- **Estado de la campaña:** `antenna_design/campaign_state.json` y `antenna_design/automation_policy.json` (48 de 60 rondas). Un informe por ronda en `antenna_design/reports/claude_run_0NN.md`.

## Trayectoria de diseño (resumen)
1. **P01_MS1 / P01_MS2:** parche rectangular con línea de 50 Ω y transformador λ/4.
   - P01_MS2 (ronda 027): peor S11 en el canal −10,4 dB, η 0,73–0,76, ganancia realizada 4,3–4,8 dBi (openEMS).
   - Es el mejor candidato de una sola capa.
   - HFSS: elemento y array 1×5 simulados por el propietario.
2. **Inset (P01_IN1):** resultado negativo.
3. **US3_MS3:** parche con ranura en U. La banda de −10 dB (≈ 350–360 MHz) no cubre el canal.
4. **U-slot con parásito enterrado (z = 1,035 mm)**, en varias versiones:
   - **US3_PS1 y US3_PS4:** dos mínimos y canal a −10 dB, pero la segunda resonancia radia poco. Hay un valle de η de 0,24 hacia 8,14 GHz («adaptación por pérdidas»).
   - **US3_PS5:** propuesta de Fable con un modelo guía de dos resonadores (brillante y oscuro). Saca el modo oscuro del canal y elimina el valle.
   - **US3_PS6:** recentrado con patch_L 6,29 mm. Malla base y fina (rondas 038/039).
   - **Barrido del ancho del parásito Wp** (11 → 7 mm, rondas 040 y 042–044): las resonancias se acercan y se funden, sin cubrir el canal.
   - **US3_PS4_2_1:** Wp 10 mm y patch_L 6,222 mm (ronda 045 base, 047 fina).
   - **US3_PS6_1 y US3_PS6_2:** patch_L 6,32 y 6,38 mm (rondas 046 y 048). Con patch_L solo se desplaza la banda: no se alcanza −10 dB en todo el canal.
5. **Candidatos finales comparados en HFSS (elemento convergido):**

   | | Mínimos de S11 | Peor S11 | η_rad | Rizado τ_g broadside |
   |---|---|---|---|---|
   | US3_PS4_2_1 | 7,875 / 8,140 GHz | −10,00 dB | 0,32–0,74 | ≈ 664 ps |
   | US3_PS6 | 7,955 GHz | −8,72 dB | 0,69–0,74 | ≈ 20 ps |

   - **Conclusión:** para IR-UWB, US3_PS6 es mejor en respuesta temporal y P01_MS2 sigue siendo el más eficiente.
   - HFSS coincide con openEMS en malla base para US3_PS4_2_1. US3_PS6 cae unos 50 MHz más abajo en HFSS.
   - Detalle: `antenna_design/reports/claude_hfss_elements_2026-11-17.md`.

## Arrays y MIMO virtual
- **Arrays lineales 1×4 y 1×5 en x**, con paso `arr_d` paramétrico (Optimetrics 13,5–20,5 mm).
  - Puertos apagados a 50 Ω (decisión del propietario).
  - Secuencia por defecto de 1 TX + 2 RX (`RF_CONFIGS`), con N·C(N−1,2) adquisiciones.
- **Array virtual:** suma coherente de los canales de ida y vuelta E_t·E_r, componente copolar Ludwig-3 y.
  - Elemento virtual en x_t + x_r en el código del análisis (`virtual_array_pattern.py`).
  - **Ojo:** el commit `eec7bf8` de `docs/memoria-tfg` habla de «la convención del punto medio del código». Hay que comprobar qué convención usa la memoria y si coincide con la del análisis de antenas, (x_t + x_r) frente a (x_t + x_r)/2.
- **1×5 de P01_MS2 (HFSS):**
  - Paso recomendado 18–18,2 mm.
  - 13,5 mm descartado (reflexión activa −4,9 dB).
  - A 17 mm: HPBW físico 21,7° y virtual 17,7°.
- **1×5 de US3_PS4_2_1 (HFSS, Optimetrics sin convergencia completa: EM_SIMULATED):**
  - A 18,2 mm y f0: HPBW xz físico 20,8° y virtual 16,5°. Lóbulos laterales del virtual por debajo de −21,8 dB.
  - Rizado de τ_g físico ≈ 580 ps.
  - Datos en `hfss/results/results_US3_PS4_2_1/ARR1x5_US3_PS4_2_1_dparam/`.
- **1×4 de P01_MS2 con `arr_d` paramétrico:**
  - Script preparado (`hfss/build/P01_MS2/claude_aedt_array1x4_P01_MS2_param_ch9.py`).
  - Simulación pendiente: el Optimetrics falló por falta de disco.
  - Objetivo: justificar el quinto elemento por resolución angular.
- **Biestático + monostático (2026-11-18):**
  - El SoC tiene un puerto TX/RX y otro solo RX: 20 parejas ordenadas, 40 canales, apertura virtual ±4d.
  - A 18,2 mm y f0 el HPBW baja de 16,5° a 12,0°.
  - Los lóbulos laterales suben (−21,4 dB en broadside y −8,2 dB apuntando a 30°) por una periodicidad 2d de los pesos.
  - Solo es el canal radiado ideal: no incluye la fuga TX→RX del puerto TX/RX.
  - Datos en `hfss/results/results_*/ARR1x5_*/virtual_mono/`.

## Metodología con agentes (para el capítulo de método)
- **Orquestador:** Claude Opus.
- **Subagentes Sonnet:** `rf-designer` (geometría), `em-solver` (openEMS y scripts HFSS) y `validator` (auditoría independiente después de cada resultado).
- **Super revisor `design-reviewer` (Fable 5.2):** solo antes de simular en HFSS, y sus correcciones se reparten a los agentes Sonnet.
- **Límites:** como máximo 3 subagentes a la vez y 1 FDTD por ronda.
- **Evaluación de tiers de modelos:** `antenna_design/reports/claude_model_tiers_evaluation.md`.
- **Agentes de redacción:** 2 Haiku (redactor y revisor) para la memoria, desde 2026-11-18.

## Artifacts de resultados (para figuras)
- «U-slot con parche parásito · openEMS»: detalle completo.
- «Antena IR-UWB canal 9 · resumen visual»: candidatos, array físico y virtual, comparativa y orquestación.

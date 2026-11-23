# PRIMERA TAREA PARA CODEX CLOUD — antenas IR-UWB canal 9

Trabaja como **orquestador GPT-6 Astra, esfuerzo Medium**. Usa el entorno publicado «IR-UWB canal 9 — laboratorio de antenas», repositorio privado luiscarlop/TFG_Beamforming_FBD, y **solo la rama codex/uwb-ch9-antenna-design**. Antes de editar, verifica la rama y lee AGENTS.md, antenna_design/README.md, antenna_design/campaign_state.json y antenna_design/AUTOMATED_CYCLE.md.

**Único objetivo:** investigación, modelado electromagnético y optimización de *antenas* para IR-UWB IEEE 802.15.4z, canal 9, 7.7376–8.2368 GHz (f0 7.9872 GHz, puerto 50 ohm). Más adelante queremos verificar en Ansys HFSS. NO trabajar en beamforming, MUSIC, Doppler, extracción CIR, radar ni procesamiento de señal.

## Primera campaña: un único elemento
1. Verifica el modelo Astra activo; descubre los subagentes rf_designer (Sol High), em_solver (Sol High) y validator (Luna High) y comprueba que su uso real es compatible con Cloud. Si una herramienta no permite subagentes, trabaja secuencialmente, no afirmes que los has ejecutado. Máximo 3 concurrentes.
2. Ejecuta tests y exporta P01 (rectangular), P02 (U-slot), P03 (hexagonal ranurado), verificando DXF/SVG, geometría, dimensiones, unión de metal y alimentación. Son *candidatos geométricos*, nunca resultados de S11.
3. Delegación: RF revisa geometrías/sustrato/alimentación; EM verifica disponibilidad de un solver EM real (preferente openEMS+CSXCAD) y propone puerto, ground, dieléctrico, malla, fronteras y estimación de memoria; Validator audita supuestos y pruebas.
4. Si el solver está disponible o se puede instalar sin privilegios, costes externos ni compilación desproporcionada, prepara **una sola** simulación EM de P01 con barrido al menos de 7.5 a 8.5 GHz. Antes de ejecutarla, estima RAM, malla y tiempo; no sobrepases límites de recursos del entorno. Guarda los archivos reales del solver, S11 complejo en CSV y metadatos de convergencia. Si no hay solver, deja un diagnóstico reproducible de instalación y marca EM_NOT_RUN; NO inventes datos.
5. Comprueba sobre toda la banda S11 <= -6 dB (criterio mínimo) y objetivo -10 dB; no confundas un mínimo puntual con cobertura de toda la banda. Indica qué falta para estudiar eficiencia, patrones complejos y retardo de grupo radiado, importantes para el pulso UWB.
6. Registra resultados, limitaciones y evidencias en antenna_design/. Cada diseño con ID, geometría, material, puerto, solver/versión, estado GEOMETRY_ONLY o EM_SIMULATED, archivos de soporte y qué métrica mejora. Actualiza campaña sin perder historial. Ejecuta tests. Crea commit en ESTA rama si tienes permisos; si no, indica exactamente cómo conservarlo. No PR, no merge.
7. Entrega una tabla comparativa honesta y el siguiente experimento concreto y reproducible.

## Continuidad automática
El usuario autoriza una **campaña recurrente limitada**, NO una investigación perpetua. Tras terminar la primera tarea y verificar que el entorno está en condiciones de continuar, consulta antenna_design/AUTOMATED_CYCLE.md. Si este cliente Codex admite automatizaciones asociadas a esta tarea y entorno Cloud, crea **una** automatización recurrente de Codex para las 09:00 Europe/Madrid de lunes a viernes, con el texto íntegro de ese archivo, máximo 5 ejecuciones de investigación; confirma explícitamente su ID, próxima ejecución, entorno y modelo. Si no puedes crearla o vincularla al entorno Cloud, no inventes su existencia ni crees una tarea genérica de ChatGPT: indica los pasos para programarla desde Codex.

No empieces otra campaña larga en este mismo turno. Detente tras la primera evaluación y la configuración verificada de la continuidad.

# Reparto propuesto Codex / Claude — 2026-11-03

Propuesta de coordinación, pendiente de conocer la tarea actual de Claude. No constituye confirmación de que Claude la haya leído o aceptado.

## Codex: cierre y persistencia de la ejecución existente

Revisar y publicar únicamente las evidencias ya generadas de instalación openEMS/CSXCAD y P01_OPENEMS_001: scripts em/p01_openems.py, run_official_smoke.py, stage_debian_dependencies.py, runtime_env.sh; em/installation_20261103/, em/P01_OPENEMS_001/, experiments/solver_recovery_20261103/; informes solver_installation.md, solver_recovery.md, p01_preflight_rf.md y este reparto. Conservar los datos brutos y el historial. Ejecutar pruebas y comprobar el remoto antes de push normal.

campaign_state.json y automation_policy.json son compartidos: no editarlos simultáneamente; integrar solo con revisión de diferencias y sin sobrescribir cambios de terceros. Un solo responsable de Git/index/commit/push a la vez, aunque las ediciones sean disjuntas.

## Claude: revisión y propuesta del siguiente experimento

Propuesta: revisar resultados en modo lectura y escribir sus conclusiones en reports/claude_next_experiment.md (o su archivo propio acordado). Priorizar convergencia espacial/temporal antes de optimizar longitud/feed. No modificar datos originales de P01_OPENEMS_001 ni ejecutar nuevas simulaciones como parte de este reparto.

## Estado y límites

Los commits iniciales ef4b9cd/069b30e están en GitHub. La recuperación posterior del solver y P01 están pendientes de publicación al crear este documento. P01 se ejecutó una vez y no cumple adaptación en toda la banda. No se ha establecido convergencia espacial. Automatización PAUSED, cero rondas automáticas.

Sin force push, PR, master, procesamiento radar, API de pago ni nuevas simulaciones por este reparto. Si se detectan modificaciones concurrentes en archivos compartidos o divergencia Git, detener la integración y conservar ambos trabajos.

## Concurrencia detectada al consultar GitHub

Remoto observado: 62b9030b549aa5b7cbe3d391e39050b7fcb4db3d, con commits nuevos 0849de0 y 62b9030 de configuración Claude. HEAD local sigue en 069b30e. El remoto añade claude_routine a automation_policy.json; el archivo local actualiza los campos de Codex a PAUSED y conserva el resultado P01. No reemplazar un JSON por el otro: una integración debe preservar el bloque claude_routine remoto y el historial de ambas sesiones. No se ha efectuado merge, commit ni push de estas evidencias mientras se coordina responsable único.

Observaciones para Claude (sin modificar sus archivos): CLAUDE_CYCLE.md invoca diagnose_solver.py sin --out, pero el script actual lo requiere. En este entorno el solver está en un venv de usuario y requiere source antenna_design/em/runtime_env.sh; ejecutar solo python3 del sistema puede indicar ausencia aunque esté instalado. La disponibilidad en un entorno Claude separado debe comprobarse con su propia instalación; consultar solver_installation.md para reproducirla.

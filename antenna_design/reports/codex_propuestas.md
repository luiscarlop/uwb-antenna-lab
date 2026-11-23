# Propuestas y coordinación con Claude

Reparto confirmado por el propietario: Claude posee geometrías, tests/test_designs.py, outputs/, em/, campaign_state.json, su bloque claude_routine y su configuración. Codex posee hfss/, analysis/, tests/test_analysis.py y reports/codex_*.md. El reparto anterior de task_split.md era provisional y queda sustituido por este acuerdo.

La integración excepcional de las evidencias previas de Codex ya fue autorizada y publicada en064f92b. Se conservaron la ronda1 ACTIVE de Claude, ambos historiales, reports/claude_run_001.md y em/solver_diagnosis_claude_run_001.json. El solver instalado en este entorno Debian no implica que esté instalado en el entorno Ubuntu de Claude; reproducir receta según su plataforma, sin copiar binarios incompatibles.

Propuestas para archivos de Claude (no aplicadas):
- En CLAUDE_CYCLE.md, la invocación de diagnose_solver.py necesita --out; seleccionar archivo nuevo por ronda para no sobrescribir evidencia anterior.
- Usar el intérprete que contiene openEMS/CSXCAD y sus bibliotecas. En este entorno: source antenna_design/em/runtime_env.sh. La importación sola no certifica FDTD: conservar la verificación del ejemplo oficial y sus números.
- Antes de un refinamiento, estudiar estabilidad de malla/tiempo de P01_OPENEMS_001. La ejecución existente cumplió decaimiento, pero no establece independencia de malla. No repetir el baseline por desconocer su publicación.
- Mantener extremos exactos y añadir el centro7.9872GHz al postprocesado si se requiere informar esa frecuencia; el CSV inicial contiene extremos pero no el centro exacto.
- El manifiesto outputs/ permanece de geometrías y debe conservar su procedencia; las herramientas HFSS solo lo leen. Si se cambia, generar otra transferencia con nuevo hash.

Herramientas Codex verificadas solo con datos sintéticos. Claude deberá decidir si/cuándo aplicarlas a resultados reales y documentar procedencia. Los scripts HFSS no han ejecutado Ansys. La revisión cuantitativa de materiales espera PDF EuCAP y fichas accesibles; no cambiar material basándose en valores no verificados.

Para coordinar Git: consultar remoto antes de trabajar y antes de push, usar pull --rebase para commits locales aún no publicados, preservar cambios concurrentes, nunca force push ni reescritura de commits remotos. Un solo escritor del índice/estado de Git si ambas sesiones comparten exactamente el mismo checkout.

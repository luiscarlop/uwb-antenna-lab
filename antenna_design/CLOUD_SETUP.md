# Activar Codex Cloud sin alterar el TFG
1. En https://chatgpt.com/codex crea/abre un entorno Cloud con el repositorio privado luiscarlop/TFG_Beamforming_FBD.
2. Selecciona la rama codex/uwb-ch9-antenna-design (NO master).
3. Si puedes configurar un setup script: python -m pip install -r antenna_design/requirements.txt. No compilar openEMS por defecto. El setup debe ser simple y barato.
4. Tras publicar el entorno, inicia la primera tarea con el contenido de CODEX_FIRST_TASK.md.
5. Antes de cualquier simulación EM, el agente debe verificar RAM, CPU y presencia real de openEMS, registrar su versión y fijar un límite de recursos.
6. No usar llamadas directas al OpenAI API/Agents API: factura por separado. No crear automatizaciones recurrentes hasta inspeccionar cuota real y confirmar que el primer trabajo funciona.
7. No abrir PR automáticamente (el repo tiene workflows de Claude configurados en PR).

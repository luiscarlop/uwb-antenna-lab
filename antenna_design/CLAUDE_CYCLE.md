# CICLO RECURRENTE DE CLAUDE CODE — diseño EM de antenas UWB canal 9

Este fichero es el prompt de la routine de Claude Code. Lo que hay debajo de la línea se pega tal cual en la routine.

Es el equivalente Claude de `AUTOMATED_CYCLE.md` (Codex), con su propio contador en `automation_policy.json` → `claude_routine`. **No toques los campos de Codex** (`status`, `runs_completed`, `max_runs`, `automation_*`).

---

Eres el **orquestador** del laboratorio de antenas IR-UWB del canal 9 (repositorio `luiscarlop/TFG_Beamforming_FBD`, rama `codex/uwb-ch9-antenna-design`, directorio `antenna_design/`). Trabajas solo; nadie te contestará durante esta ejecución. Haz **una sola ronda** y para.

1. **Prepara.**
   - `git fetch origin && git checkout codex/uwb-ch9-antenna-design && git pull --ff-only`. Comprueba que estás en esa rama; si no puedes, para.
   - Lee `CLAUDE.md`, `AGENTS.md`, `antenna_design/README.md`, `antenna_design/campaign_state.json` y `antenna_design/automation_policy.json`.
   - Comprueba que tu modelo es Opus 5.5 (decisión del propietario, 2026-11-05). Si no lo es, no lances ninguna FDTD: anótalo en el informe y para.
   - **Alimentación** (decisión del propietario, 2026-11-05): **no se modela ningún conector SMA ni ninguna sonda coaxial.** Todos los candidatos se alimentan con una **pista microstrip de 50 Ω** que llega al parche, por inset o por el borde.
     - **El puerto:** un `AddLumpedPort` de **R = 50 Ω**, vertical (de la masa a la pista), justo al **inicio de la línea microstrip**, en el borde de la placa y con el ancho de la pista. El plano de referencia de S11 es ese inicio de línea, sin de-embedding.
     - **La pista:** su ancho para 50 Ω se calcula sobre el mismo sustrato y se anota.
     - **Malla:** comprueba la convergencia con dos mallas.
     - **Qué queda pendiente:** los resultados de sonda ideal (P01_R2, US0, US3) no se reutilizan como adaptación convergida. Hay que rehacerlos con esta alimentación.
     - El puerto MSL de openEMS es solo una comprobación secundaria; recuerda sus problemas en `reports/claude_run_006.md`.
     - Esta decisión resuelve el STOP «sonda física / SMA» de las rondas 18 a 20.
2. **Decide si toca trabajar.** Lee el bloque `claude_routine` de `automation_policy.json`:
   - Si `status` es `STOPPED` o `PAUSED`, o si `runs_completed >= max_runs`, **no hagas nada más**. No hagas commit. Responde con el estado y para.
   - Si `campaign_state.json` está en `READY_FOR_HFSS_REVIEW`, para: falta la revisión humana.
   - **Candado.** Mira `claude_routine.candado` en `automation_policy.json`. Si tiene una fecha ISO-8601 de hace menos de 3 horas, hay otra ronda de Claude en marcha: para sin tocar nada. Si es `null` o tiene más de 3 horas, reserva la ronda:
     1. pon `candado` con la hora UTC actual;
     2. haz commit `TFG_AED-13/ClCo: start Claude round <N>`;
     3. haz `git push`.

     Si el push falla por un conflicto, haz `git pull --rebase` y vuelve a mirar el candado. Al cerrar la ronda (paso 6), y también al parar por un STOP, pon `candado: null`.
   - Los commits recientes del propietario o de Codex **no** son motivo para parar: trabajan en otros ficheros (ver `CLAUDE.md`). Haz `git pull --rebase` antes de cada push.
   - Los estados `BLOCKED` (por falta de solver) y `PAUSED` de `campaign_state.json` **no** te paran. Lee su `next_task` e `history`: ahí se dice qué le toca a Claude. El paso 3 vuelve a comprobar el solver.
3. **Solver.**
   - Ejecuta `source antenna_design/em/runtime_env.sh`. El setup script del entorno compila openEMS y CSXCAD en `/workspace/openems-install`, con la receta de `antenna_design/reports/solver_installation.md`, y deja su log en `/workspace/openems-setup.log`.
   - Comprueba el solver: `python -c 'import openEMS, CSXCAD; print(openEMS.__version__, CSXCAD.__version__)'` y `python antenna_design/em/diagnose_solver.py`.
   - **Si funciona**, anota las versiones y pasa a la campaña.
   - **Si falla**, lee el log del setup. Repite la compilación una sola vez con esa receta: el setup script cabe en un `bash antenna_design/claude_cloud_setup.sh` y tarda unos 5 minutos. Si sigue fallando, marca `EM_NOT_RUN`, deja el diagnóstico en `antenna_design/em/` y ve al paso 6.
   - **No inventes S11.**
   - **Punto de partida:** la ejecución real de Codex `em/P01_OPENEMS_001/`. Tiene el estado `EM_SIMULATED`, con la independencia de malla `NOT_ESTABLISHED`, y no cumple −6 dB en toda la banda. El siguiente experimento recomendado está al final de `reports/solver_installation.md`: un refinamiento de malla del mismo P01. Las herramientas de `antenna_design/analysis/` son de Codex: úsalas, pero no las modifiques.
4. **Elige UNA mejora fundamentada**, con pruebas de lo que ya se ejecutó:
   - no repitas candidatos ni sobrescribas resultados anteriores;
   - prioriza validar P01; después, compara el U-slot (P02) y el hexagonal (P03);
   - al comparar una variable, mantén el mismo material y la misma alimentación.

   Delega según `CLAUDE.md`:
   - `rf-designer` (geometría) y `em-solver` (modelo y estimación de recursos) en paralelo, solo si son independientes;
   - después, `em-solver` ejecuta **como máximo 1 FDTD**, si los recursos estimados caben (≤ 2 vCPU en la primera prueba);
   - por último, `validator` audita. Máximo 3 subagentes a la vez.
5. **Valida.** Calcula S11 complejo de 7,5 a 8,5 GHz y evalúa la banda 7,7376–8,2368 GHz completa: −6 dB es el mínimo y −10 dB el objetivo. Guarda los datos brutos y los parámetros. Si el solver lo permite, saca también los patrones complejos y el retardo de grupo radiado; no lo confundas con la derivada de la fase de S11. Si `validator` da `BLOQUEAR`, marca la campaña como `BLOCKED` con el motivo.
6. **Persiste.**
   - Escribe el informe `antenna_design/reports/claude_run_<NNN>.md`, con:
     - el ID del experimento, la propuesta y los parámetros;
     - el solver y su versión, los comandos, los tiempos y la RAM observados;
     - las métricas, con enlaces a los ficheros;
     - los errores y la siguiente hipótesis.
   - Actualiza `campaign_state.json` sin perder historial.
   - En `claude_routine`: incrementa `runs_completed`, añade una entrada a `history` y pon `status: STOPPED` al llegar a `max_runs`. Si hay un candidato viable, pon la campaña en `READY_FOR_HFSS_REVIEW`.
   - Ejecuta los tests: `cd antenna_design && python3 -m unittest discover -s tests -v`.
   - Haz commit con `TFG_AED-13/ClCo: <mensaje>`, usando `git add -f` para los `.md`. Haz `git push origin codex/uwb-ch9-antenna-design`. Si el push falla, no reintentes con `--force`: haz `git pull --rebase` una vez; si sigue fallando, para y repórtalo.

**STOP inmediato**, con el motivo en el informe y en `history`, si:
- se agota la cuota o hay que usar una API de pago;
- falta el solver tras el diagnóstico de tres rondas seguidas (pon entonces `claude_routine.status: PAUSED`);
- fallan los tests;
- la geometría no es fabricable o la malla no converge;
- hay cambios externos concurrentes;
- faltan permisos de push;
- hace falta una decisión humana.

**Prohibido:**
- crear routines o automatizaciones, o reiniciar contadores;
- tocar `.codex/`, `AGENTS.md`, `src/`, `matlab/`, `latex_memoir/` o `data/`;
- abrir PR o hacer merge a `master`;
- trabajar en beamforming, MUSIC, Doppler, CIR o radar.

**Salida:** un informe breve con el número de ronda, la comparación con el mejor candidato anterior, los riesgos y CONTINUE, PAUSED o STOPPED con su motivo.

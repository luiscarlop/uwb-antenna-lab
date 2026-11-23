# Claude Code: laboratorio de antenas IR-UWB, canal 9

Equivalente para Claude Code de `AGENTS.md`, que es la configuración de Codex. Las dos conviven en la rama `codex/uwb-ch9-antenna-design`:
- **Codex** usa `AGENTS.md`, `.codex/config.toml` y `.codex/agents/*.toml`.
- **Claude Code** usa este fichero, `.claude/settings.json` y `.claude/agents/*.md`.

**No modifiques `.codex/` ni `AGENTS.md`.** Las restricciones científicas y técnicas de `AGENTS.md` también te obligan a ti; si este fichero y `AGENTS.md` se contradicen, manda la regla más restrictiva.

## Alcance
- Trabaja **solo en `antenna_design/`** y **solo en la rama `codex/uwb-ch9-antenna-design`**. Antes de editar, comprueba la rama con `git branch --show-current`.
- No modifiques `latex_memoir/` salvo por la excepción de abajo.
- **Excepción (decisión del propietario, 2026-11-18):** los ficheros LaTeX de la memoria se pueden editar **solo en la rama `docs/memoria-tfg`** (worktree `/home/user/memoria-tfg`), por encargo explícito del orquestador a `tfg-writer`. En `codex/uwb-ch9-antenna-design` sigue prohibido tocar `latex_memoir/`.
- No trabajes en MUSIC, Doppler, beamforming, CIR, estimadores ni otros algoritmos de radar. El notebook UWB y el artículo EuCAP son contexto, no tareas de código.
- Sin pull requests. Los workflows de revisión están desactivados en `.github/workflows-disabled/`. Sin merges a `master` sin permiso explícito del propietario (el 2026-11-22 autorizó una fusión para la reorganización del repo).

## Objetivo
Descubrir geometrías de antena fabricables, caracterizar electromagnéticamente el elemento para el canal 9 de IEEE 802.15.4z y preparar diseños transferibles a HFSS.

- Frecuencia central: **7,9872 GHz**.
- Banda: **7,7376–8,2368 GHz** (B = 499,2 MHz).
- Alimentación con referencia de **50 Ω**.

Explora primero P01 (parche rectangular), P02 (U-slot) y P03 (parche hexagonal ranurado). El array hexagonal es una etapa posterior y no una variante del elemento.

## Orquestación
- **Orquestador:** la sesión principal, con **Claude Opus** y esfuerzo **medium** (`.claude/settings.json`). No afirmes que es así sin comprobarlo: mira el modelo en `/status` o en la cabecera de la sesión. En el cloud, el selector de modelo de la sesión o de la routine puede imponerse a `settings.json`.
- **Subagentes** de trabajo con **Sonnet** y esfuerzo **high**, más un super revisor con **Fable 5.2**:

  | Subagente | Fichero | Papel |
  |---|---|---|
  | `rf-designer` | `.claude/agents/rf-designer.md` | Geometrías, sustrato, material y alimentación |
  | `em-solver` | `.claude/agents/em-solver.md` | openEMS/CSXCAD, FDTD, malla, puerto y convergencia |
  | `validator` | `.claude/agents/validator.md` | Auditor independiente, que no modifica ficheros |
  | `design-reviewer` | `.claude/agents/design-reviewer.md` | Super revisor (Fable 5.2) del diseño que se va a simular; no modifica ficheros |
  | `tfg-writer` | `.claude/agents/tfg-writer.md` | Redactor de la memoria (Haiku), solo en `docs/memoria-tfg` |
  | `tfg-reviewer` | `.claude/agents/tfg-reviewer.md` | Revisor de la memoria (Haiku): cifras contra los datos; no modifica ficheros |
  | `artifact-builder` | `.claude/agents/artifact-builder.md` | Datos y gráficas de los artifacts (Sonnet, esfuerzo medio); el orquestador solo publica |
  | `code-auditor` | `.claude/agents/code-auditor.md` | Revisión de código antes del commit (Sonnet, esfuerzo alto); no modifica ficheros |

- **Máximo tres subagentes a la vez** (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=3`).
- Delega en paralelo la investigación RF (`rf-designer`) y la preparación de la simulación EM (`em-solver`) **solo cuando puedan avanzar por separado**. Si una depende de la otra, ve en secuencia.
- Lanza `validator` **después** de tener resultados, nunca antes.
- **Flujo de revisión de diseños (decisión del propietario, 2026-11-14):**
  1. Cada vez que prepares un diseño para simular (variante, script HFSS/PyAEDT, array…), **pregunta al propietario si se va a simular ya en HFSS**.
  2. Solo si responde que sí, lanza `design-reviewer` (Fable 5.2) **sobre ese diseño concreto**. No lo instancies para nada más.
  3. Reparte sus correcciones a `rf-designer` (geometría, material, alimentación) y `em-solver` (puertos, contornos, malla, setup), y vuelve a pedir la revisión solo si hubo correcciones bloqueantes.
- **Al final de cada mensaje al propietario** (decisión del propietario, 2026-11-22, sustituye a la lista de diseños pendientes): añade el **seguimiento de la revisión de la memoria (borrador v1)**, sección por sección, indicando hasta qué sección la ha revisado el propietario. Si hay un diseño preparado y aún no revisado por `design-reviewer`, menciónalo en una línea.
- **Cambios en la memoria** (decisión del propietario, 2026-11-22): enséñalos como diff visual sobre el PDF compilado, con lo quitado o cambiado subrayado en rojo en el «antes» y lo nuevo en verde en el «después» (comparación palabra a palabra con `pdftotext -bbox`).
- `rf-designer` y `em-solver` no editan el mismo fichero a la vez. Asigna a cada uno sus ficheros en el encargo.
- No dupliques trabajo, no anides subagentes sin necesidad, no dejes subagentes esperando sin tarea y no gastes tokens en lo que puedas resolver tú con una lectura o un comando.
- Si la delegación no está disponible, trabaja en secuencia y no digas que has usado subagentes.
- No pases `model` ni `effort` al invocar un subagente: se usan los de su fichero.
- **Reparto (decisión del propietario, 2026-11-19):** el orquestador planifica, razona los problemas difíciles y enruta el feedback de Fable; las visualizaciones las construye `artifact-builder` y los cambios de código los audita `code-auditor` antes del commit. Los commits y push siguen en la sesión de Claude Code: Codex (OpenAI) no se puede invocar desde ella.
- **Resumen visual automático (decisión del propietario, 2026-11-19):** después de cada auditoría `validator` OK (y de cada exportación HFSS analizada), lanza `artifact-builder` para actualizar el artifact de resumen: el run va siempre a «Líneas de desarrollo» y, si es candidato, también a «Candidatos» y «Comparativa». Detalle y criterio de candidato en `.claude/agents/artifact-builder.md`; fuentes en `antenna_design/artifacts/summary/`. El orquestador revisa las capturas y publica.

## Límites de cada campaña
- Como máximo **3 geometrías nuevas**, **1 simulación de elemento aislado** y **2 refinamientos** de un candidato.
- Como máximo **1 simulación FDTD por ejecución**, y una sola a la vez.
- Antes de cualquier FDTD, estima la RAM, la malla y el tiempo. En la primera prueba, **máximo 2 vCPU** y una estimación conservadora de RAM.
- Nada de barridos ilimitados, de APIs de pago ni de simulaciones largas sin consentimiento del propietario.
- El ciclo recurrente y su contador de rondas siguen `antenna_design/automation_policy.json`. No crees routines, automatizaciones ni bucles por tu cuenta.

## Evidencia
- No atribuyas S11, ganancia, eficiencia, fase, retardo de grupo ni ancho de banda a estimaciones de línea de transmisión ni a un DXF.
- Estados permitidos, solo según la procedencia real: `GEOMETRY_ONLY`, `EM_SIMULATED`, `HFSS_VALIDATED`, `MEASURED`.
- **No inventes resultados ni curvas.** Si falta el solver, el estado es `NOT_RUN` (o `EM_NOT_RUN`).
- S11 ≤ −6 dB en **toda** la banda es la referencia mínima de adaptación, y −10 dB el objetivo preferido. Ninguno de los dos es un resultado ni garantiza una buena respuesta temporal. Un mínimo puntual no es cobertura de la banda.
- Prioriza también la dispersión de fase, el ripple del retardo de grupo, la ganancia realizada y la eficiencia. La derivada de la fase de S11 no es el retardo de grupo radiado.
- Registra siempre:
  - f0, la banda, los materiales, eps_r, tan_delta, el grosor y las pérdidas metálicas;
  - la topología de alimentación, el puerto de 50 Ω y los contornos;
  - la definición de la malla y la convergencia;
  - el software y su versión, el consumo de CPU y RAM, y los ficheros de origen.

## Pruebas
```
cd antenna_design && python -m pip install -r requirements.txt && python -m unittest discover -s tests -v && python designs.py --out outputs
```

## Commits
- Solo en `codex/uwb-ch9-antenna-design`, con push a esa misma rama.
- El mensaje de commit solo contiene un título (en imperativo) y, si hace falta, un cuerpo descriptivo. No lleva prefijo de issue ni de desarrollador.
- Los ficheros `*.md` y `.claude/` están en `.gitignore`. Para versionar uno nuevo, usa `git add -f <ruta>`.

## Claude Code en el cloud: limitaciones conocidas
- **Qué se lee.** El cloud lee `.claude/settings.json` y `.claude/agents/` del clon en sesiones de un solo repositorio. No lee `~/.claude/` ni `.claude/settings.local.json`.
- **Modelo.** El selector de la sesión o de la routine puede cambiar el modelo del orquestador. Comprueba al empezar que es Opus. Los subagentes usan Sonnet por su frontmatter, sea cual sea el modelo del orquestador.
- **Esfuerzo.** No definas `CLAUDE_CODE_EFFORT_LEVEL`, ni en el entorno cloud ni en `settings.json`: se impondría sobre el `effort: high` de los subagentes.
- **Agent Teams.** No se usan: la delegación con subagentes basta para tres roles.
- **openEMS y CSXCAD** no vienen instalados. Ningún Ubuntu empaqueta sus bindings de Python. El setup script del entorno (`antenna_design/claude_cloud_setup.sh`) los compila desde las fuentes oficiales, en la misma revisión que usó Codex, dentro de `/workspace/openems-install`. Para activarlos: `source antenna_design/em/runtime_env.sh`. Si faltan, el estado es `EM_NOT_RUN`.
- **Programación.** Las routines de claude.ai solo las crea y cambia el propietario. Desde una sesión no se crean.

## Estado y primera tarea
Lee `antenna_design/README.md`, `antenna_design/campaign_state.json`, `antenna_design/automation_policy.json` y `antenna_design/AUTOMATED_CYCLE.md` antes de empezar. Sustituye «Codex», «Astra», «Sol» y «Luna» por sus equivalentes de este fichero. La primera tarea está descrita en `antenna_design/CODEX_FIRST_TASK.md`.

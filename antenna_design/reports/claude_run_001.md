# Ronda Claude 001: diagnóstico del solver

- **ID:** CLAUDE-RUN-001 (sesión manual, cuenta como ronda 1/40 de `claude_routine`)
- **Fecha:** 2026-11-03, 11:22 UTC
- **Orquestador:** `claude-opus-5-5`, esfuerzo medium, según `get_session` (`session_context.model` y `last_served_model`).
- **Subagentes:** ninguno. Sin solver no hay geometría que simular ni resultados que auditar, y el diagnóstico se resolvía con comandos directos (CLAUDE.md: «no gastes tokens en lo que puedas resolver tú»).
- **Estado EM:** `EM_NOT_RUN`. FDTD ejecutadas: 0. **No hay S11, ganancia, eficiencia ni retardo de grupo.**

## Comprobaciones previas
- Rama `codex/uwb-ch9-antenna-design`, al día con el origen y sin cambios locales.
- Último commit, `62b9030` (11:08 UTC, hace unos 13 min): es la configuración de la routine, hecha por la sesión CLI del propietario, que ahora está inactiva. `list_sessions` no muestra ninguna otra ronda de antenas en curso, así que no hay ejecución concurrente.
- `claude_routine`: `ACTIVE`, 0/40 rondas al empezar. Campaña: `BLOCKED` por falta de solver, lo que no impide la ronda.

## Proposición
No hay mejora de diseño. Con el solver ausente, la ronda se limita al paso 3 del ciclo: un diagnóstico acotado y reproducible del solver.

## Comandos y observaciones
| Comando | Resultado |
|---|---|
| `python3 em/diagnose_solver.py --out …` (`/usr/local/bin/python3`, 3.13.18) | `openEMS` y `CSXCAD`: `ModuleNotFoundError`. No hay ejecutables. |
| `/usr/bin/python3 em/diagnose_solver.py --out …` (3.13.18, GCC) | Igual. |
| `apt-get update` (3,2 s) y `apt-cache policy openems python3-openems python3-csxcad` | `openems`: sin candidato en noble (con universe activado). `python3-openems` y `python3-csxcad`: no existen. |
| API de Launchpad (archivo principal de Ubuntu) | `openems` 0.0.35+git20190103, solo en focal/jammy/lunar/mantic. Binarios: `libopenems0`, `octave-openems`, `libcsxcad0`. **Ninguna versión de Ubuntu empaqueta los bindings de Python.** |
| `pip download openEMS` | No hay distribución en PyPI. |
| API de anaconda.org (conda-forge) | No se encuentran `openems`, `csxcad` ni `python-openems`. |
| `docker version` | Hay cliente, pero no demonio (falta `/var/run/docker.sock`). |
| Documentación oficial ([clone-build-install](https://docs.openems.de/en/latest/install/clone-build-install.html), openEMS 0.37.0) | La vía documentada es compilar desde el código fuente con `./update_openEMS.sh ~/opt/openEMS --python`. |

Recursos: 4 vCPU visibles y unos 15 GiB de RAM según `free -g`. No se ha medido el consumo de ninguna simulación porque no se ha ejecutado ninguna.

El diagnóstico completo está en [`em/solver_diagnosis_claude_run_001.json`](../em/solver_diagnosis_claude_run_001.json). No sobrescribe [`em/solver_diagnosis.json`](../em/solver_diagnosis.json).

## Errores encontrados
- **`claude_cloud_setup.sh` no puede funcionar tal como está.** Instala `python3-openems` y `python3-csxcad`, que no existen en ningún Ubuntu, y en noble tampoco existe `openems`. El fallo es silencioso: el script termina con `exit 0` y un `WARN`.

- **El setup script no llegó a ejecutarse en este contenedor**, o no completó su paso de pip: faltaba `ezdxf` y `test_exports` fallaba con `ModuleNotFoundError`, también sin los cambios de esta ronda. Lo resolvió `python3 -m pip install -r requirements.txt` (ezdxf 1.4.5). Después: `python3 -m unittest discover -s tests -v` → 4 tests OK. El propietario debería comprobar que el script está pegado en el campo «Setup script» del entorno.

## Métricas
Ninguna. Estado `EM_NOT_RUN` para P01, P02 y P03, que siguen en `GEOMETRY_ONLY`.

## Comparación con el mejor candidato anterior
No hay ningún candidato simulado. P01 sigue siendo el primero que habrá que validar cuando haya solver.

## Decisión humana pendiente
Para tener solver hay que compilar openEMS y CSXCAD desde el código fuente. Es una compilación que este ciclo no puede lanzar sin consentimiento, y aquí no se ha medido cuánto dura. Opciones para el propietario:
1. Sustituir en el setup script del entorno la línea de apt por la compilación oficial: dependencias `build-essential cmake git libhdf5-dev libboost-all-dev libtinyxml-dev zlib1g-dev python3-pip python3-venv`, después `git clone --recursive https://github.com/thliebig/openEMS-Project.git` y `./update_openEMS.sh ~/opt/openEMS --python`. Conviene fijar un tag o commit para que sea reproducible. El setup se cachea con el entorno, así que el coste se paga una sola vez. **No se ha probado aquí.** La forma exacta en que `--python` expone los módulos (venv o sistema) hay que comprobarla en la página «Install Python Extensions Automatically» de la documentación.
2. Usar otro entorno que ya tenga openEMS y CSXCAD con bindings de Python.

## Siguiente hipótesis
Con el solver disponible: P01 en FR-4 provisional, `generic_FR4_PROVISIONAL` con εr = 4,4 (los parámetros están en [`em/p01_model_spec.json`](../em/p01_model_spec.json)), 1 FDTD con ≤ 2 hilos, S11 complejo de 7,5 a 8,5 GHz y evaluación de la banda 7,7376–8,2368 GHz completa frente a −6 dB y −10 dB.

## Estado de la routine
Ronda 1/40. Rondas seguidas sin solver: 1 de 3 (con 3 se pone `PAUSED`). **CONTINUE**, a la espera de que el propietario corrija el setup.

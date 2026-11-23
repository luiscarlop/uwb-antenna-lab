# Instalación real openEMS/CSXCAD, 2026-11-03

**Instalación local operativa y verificada con FDTD real.** La evidencia inicial
`em/solver_diagnosis.json` permanece intacta: describía el entorno anterior a
esta instalación posteriormente autorizada. No se utilizó instalación global,
sudo, API facturada, Qt ni VTK.

## Fuentes, entorno y presupuesto previo

Se leyó la documentación oficial del repositorio
`openEMS-Project/doc-src/install/clone-build-install.rst` y `requirements.rst`.
El enlace `docs.openems.de/en/latest/install/clone-build-install.html` devolvió
403 del proxy porque ese host no figura en la política permitida. Se usó el
mismo contenido oficial versionado en GitHub, conservando proxy/CA y TLS.

El entorno era Debian 13.6 x86_64, Python 3.12.14, GCC 14.2,
32 GiB de RAM cgroup, cuota de cuatro CPU y 60 GiB de disco disponible.
Faltaban CMake y cabeceras de desarrollo. Antes de compilar se registró
[build_preflight.json](../em/installation_20261103/build_preflight.json):
presupuesto de compilación <=2 CPU, 1,200 s, estimación conservadora <=8 GiB RAM
y <=2 GiB de disco. La comprobación EM pequeña y la única ejecución P01 tienen
presupuestos separados. No se lanza ninguna simulación desde el instalador.

Fuentes oficiales clonadas recursivamente fuera del checkout de investigación:

| Componente | Commit |
| --- | --- |
| openEMS-Project | fc5a90b906af01c4d35797fc95751386c8e2ede5 |
| openEMS | 5fecbb58d8996a3e6545e7b40584f90b9362e012 |
| CSXCAD | 626b99f2f4d681cb012516b6522b7bc7068ce39c |
| fparser | 4b9c845b449b520c4b8c5f23c74cd04820084f81 |

Todos los submódulos, incluidos los opcionales no compilados, están fijados en
`build_preflight.json`. Código: `/workspace/openems-source`; instalación:
`/workspace/openems-install`; dependencias extraídas: `/workspace/openems-deps`.
Estos directorios son locales al entorno y deben reconstruirse si desaparecen.

## Dependencias y compilación observada

Se extrajeron 20 paquetes binarios oficiales Debian, con hashes comprobados,
mediante `dpkg-deb -x`, sin scripts de instalación ni modificación de `/usr`.
Descarga: 19,122,444 bytes; tamaño instalado declarado: 211,652 KiB.
Incluyen Boost 1.83 y componentes requeridos, HDF5 C/HL 1.14.5 y TinyXML 2.6.2.
Las URLs exactas, versiones y SHA256 están en
[dependency_manifest.json](../em/installation_20261103/dependency_manifest.json).
No se instaló `libboost-all-dev` ni la pila gráfica completa.

Se creó un venv aislado con dependencias Python binarias. Las versiones exactas
están en `python_packages.json`, `python_freeze.txt` y
[bootstrap_requirements.txt](../em/installation_20261103/bootstrap_requirements.txt).
La compilación usó el script oficial
`update_openEMS.sh /workspace/openems-install --disable-GUI --python --njobs=2`
con opciones de venv/red y prefijos locales registradas en `build_local.sh`.
`taskset -c 0,1` restringió todos sus descendientes a dos CPU.

Se conservaron dos fallos y sus correcciones:

1. CMake no localizó HDF5 relocalizado. `toolchain.cmake` fija cabeceras y
   bibliotecas C/HL extraídas; `localConfig.cmake` comunica el toolchain al
   superproyecto y sus subproyectos. No se modificó el código C++ del solver.
2. El Python proporcionado por el entorno esperaba `clang++`, ausente.
   Se seleccionó el compilador disponible con `CC=gcc CXX=g++` y se repitió
   únicamente `scripts/build_python.sh`, sin recompilar el solver nativo.

La compilación nativa corregida más el primer intento de bindings tardó
101.994 s, 174.623 s CPU usuario +16.270 s sistema; máximo RSS de un proceso
hijo 431,460 KiB. La repetición de bindings terminó correctamente en 73.100 s,
70.386 s usuario +2.914 s sistema y máximo RSS de un hijo 435,980 KiB.
Este RSS es el mayor proceso hijo observado por `getrusage`, no el máximo
agregado de todos los procesos concurrentes. El intento inicial corto de
descubrimiento HDF5 no tiene medición de recursos separada. El trabajo completo
quedó ampliamente dentro del presupuesto de veinte minutos.

Versiones verificadas por importación real:

- openEMS Python: `0.37.0.post1.dev1+g5fecbb58d`.
- CSXCAD Python: `0.7.0.post1.dev1+g626b99f2f`.
- Binario nativo: `5fecbb5`; CSXCAD `626b99f`; HDF5 `1.14.5`, Boost `1_83`,
  TinyXML `2.6.2`, zlib `1.3.1`. `ldd` resolvió las bibliotecas requeridas.

Los logs completos, toolchain, scripts de compilación, recursos, lista de
paquetes y documentación oficial están en
[installation_20261103](../em/installation_20261103/).

## Ejemplo EM oficial pequeño

Se ejecutó `Rect_Waveguide.py` del mismo commit oficial, con su geometría,
malla, materiales, excitación, pasos máximos y postprocesado originales.
Solo se adaptaron ruta de salida, exportación XML, límite de dos hilos,
supresión de dumps de campo volumétricos y visualización sin ventana.
La fuente adaptada conserva la cabecera original y su procedencia.

Presupuesto: dos CPU y timeout externo de 60 s. Resultado real:
40,176 posiciones de malla del solver, 1,430 pasos hasta -60.3882 dB de energía,
0.682 s de pared y 96,576 KiB RSS del proceso. En 201 frecuencias 20–26 GHz:
max|S11|=0.006894, min|S21|=0.999328; error relativo máximo de la parte real
de impedancia frente a la solución analítica TE10=0.9713%.

Esto verifica instalación, motor FDTD y extracción numérica de puertos para
esta guía de onda; no valida una antena. XML, puertos temporales, log y CSV
complejo están en
[smoke_waveguide](../em/installation_20261103/smoke_waveguide/).

## Reproducción tras un entorno nuevo

Los directorios binarios no se versionan. En un entorno Debian 13 x86_64 con
GCC y `dpkg-deb`, leer primero la política de red y habilitar el acceso al proxy
del sandbox según el entorno. Desde la raíz del repositorio:

```bash
python antenna_design/em/stage_debian_dependencies.py \
  --manifest antenna_design/em/installation_20261103/dependency_manifest.json \
  --prefix /workspace/openems-deps --cache /workspace/openems-debs
git clone https://github.com/thliebig/openEMS-Project.git /workspace/openems-source
git -C /workspace/openems-source checkout fc5a90b906af01c4d35797fc95751386c8e2ede5
git -C /workspace/openems-source submodule update --init --recursive
python -m venv /workspace/openems-install/venv
/workspace/openems-install/venv/bin/python -m pip install --only-binary=:all: \
  -r antenna_design/em/installation_20261103/bootstrap_requirements.txt
mkdir -p /workspace/openems-build-evidence
cp antenna_design/em/installation_20261103/toolchain.cmake /workspace/openems-build-evidence/
python - <<'PY'
from pathlib import Path
Path('/workspace/openems-source/localConfig.cmake').write_text(
    'set(CMAKE_TOOLCHAIN_FILE "/workspace/openems-build-evidence/toolchain.cmake")\n')
PY
CC=gcc CXX=g++ bash antenna_design/em/installation_20261103/build_local.sh
source antenna_design/em/runtime_env.sh
python -c 'import openEMS,CSXCAD; print(openEMS.__version__,CSXCAD.__version__)'
timeout --signal=TERM --kill-after=5s 60s taskset -c 0,1 \
  python antenna_design/em/run_official_smoke.py \
  --source /workspace/openems-source/openEMS/python/Tutorials/Rect_Waveguide.py \
  --out /tmp/openems_smoke_fresh
```

El manifiesto fija las descargas observadas; Debian/PyPI podrían retirar una
versión en el futuro. Una descarga ausente debe diagnosticarse, sin sustituir
versiones silenciosamente. No editar shell profiles globales. `runtime_env.sh`
configura únicamente la shell actual y conserva el proxy/TLS heredado.

## P01 y límites de interpretación

El proyecto nativo preparado y la ejecución única autorizada se conservan por
separado en [P01_OPENEMS_001](../em/P01_OPENEMS_001/). No se sobrescribieron
la especificación declarativa ni las evidencias iniciales. El XML fue revisado
por RF/Validator antes de lanzar FDTD.

La malla geométrica tiene 144×145×86 intervalos (1,795,680); openEMS informa
145×146×87 posiciones nodales (1,841,790). No son dos mallas diferentes.
La reserva previa de RAM fue 3,677,552,640 bytes (3.43 GiB), dos CPU, 30,000
pasos y timeout externo de 900 s sin relanzamiento. El estimate de paso basado
en el mínimo uniforme Yee del preflight es 4.418e-13 s; **no es un límite
superior del paso del método Rennings usado realmente por openEMS**. El solver
elige 5.00217e-13 s. Por tanto la ventana real debe leerse de la ejecución;
las claves históricas `courant_upper_bound_s`/`maximum_record_upper_bound_s`
de `prepared.json` quedaron incorrectamente nombradas como cotas y solo son
estimaciones de referencia. Se conservan para trazabilidad con esta corrección.
El script ejecutado queda fijado como `P01_OPENEMS_001/executed_p01_openems.py`,
cuyo SHA256 coincide con `prepared.json`. El generador actual corrige los nombres
de estas claves para futuras preparaciones; esta corrección no cambia la física
ni el XML de la ejecución existente.

La única ejecución P01 terminó con exit code 0, sin timeout ni relanzamiento:
7,587 pasos hasta -50.48 dB de energía; tiempo de pared del launcher 142.878 s,
CPU usuario+sistema 246.901 s y RSS máximo 333,300 KiB (325.5 MiB).
El motor tomó 137.741 s; `openEMS_stats.txt` conserva el paso real completo
5.002169567155493e-13 s y tiempo numérico total **3.795146 ns**. La escala
1/T real es aproximadamente 263.5 MHz, no la de la ventana máxima previa.
El decaimiento real permite interpretar el resultado temporal inicial, con
limitaciones de truncamiento; no justifica precisión de 1 MHz en resonancia.

Se guardaron 1,003 frecuencias complejas entre 7.5 y 8.5 GHz, incluidas 501 en
el canal y sus extremos exactos. En el canal, S11 va de -7.6284 dB en
7.7376 GHz a -1.9415 dB en 8.2368 GHz. **Incumple -6 dB y -10 dB en toda la
banda.** El mínimo de la malla de evaluación del barrido es -8.9294 dB en
7.627 GHz; no es una frecuencia de resonancia validada espacialmente.
CSV conserva S11 complejo, impedancia compleja y tensiones/corrientes complejas
de puerto; también se guardan las señales temporales y curva de energía real.

El estado de procedencia es EM_SIMULATED, con convergencia temporal de energía
alcanzada e independencia espacial **NOT_ESTABLISHED**. El puerto es ideal;
el FR4 y el cobre siguen siendo provisionales. No hubo una segunda simulación
de antena ni optimización posterior en esta sesión.

Ni el cumplimiento del criterio temporal de energía ni una sola malla establecen
independencia espacial de malla. El CSV evalúa la DTFT cada 1 MHz con extremos
exactos del canal; ese espaciado no equivale a resolución física de 1 MHz.
No se grabaron campos radiados: eficiencia, ganancia y retardo de grupo radiado
requieren otro diseño de monitores/experimento posterior.

El siguiente experimento recomendado es un único refinamiento de malla del
mismo P01, manteniendo dimensiones, materiales, caja, puerto y excitación:
pasos máximos x/y 0.35 mm y aire z 0.6 mm, diez celdas en el sustrato,
`metal_edge_res=0.175 mm`, suavizado <=1.4. Se debe preparar primero el XML y
reestimar RAM/tiempo con la malla real. Comparar S11 complejo y adaptación sobre
el mismo vector de frecuencias; no atribuir una mejora a la geometría cuando
solo cambia la malla. Dos mallas permitirían medir sensibilidad, no demostrarían
por sí solas convergencia asintótica. Tras esa comprobación, acortar la longitud
resonante podría ser una hipótesis de ajuste, pero este resultado no establece
un óptimo ni valida una dimensión nueva.

# Ronda Claude 002: sensibilidad de malla de P01

- **ID del experimento:** P01_OPENEMS_002, el refinamiento de malla de [P01_OPENEMS_001](../em/P01_OPENEMS_001/).
- **Fecha:** 2026-11-03, de 11:47 a 12:20 UTC aproximadamente. Sesión manual, ronda 2/40 de `claude_routine`.
- **Orquestador:** `claude-opus-5-5`, esfuerzo medium.
- **Subagentes:** `em-solver` preparó el modelo y estimó los recursos. La FDTD la lanzó el orquestador con el comando que propuso `em-solver` (ver «Recursos»). Después, `validator` auditó los resultados.
- **Evidencia:** `EM_SIMULATED`, solo S11 y Zin en un puerto concentrado ideal. La independencia de malla es **NOT_ESTABLISHED**. No hay campo lejano, así que tampoco hay ganancia, eficiencia ni retardo de grupo radiado.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**, sin hallazgos críticos ni altos.

## Arranque
- Ciclo vigente: `CLAUDE_CYCLE.md`, con el candado de `48ec228`. El candado se reservó en el commit `aef3b5b` (11:47:36 Z).
- El solver no existía en este contenedor porque el setup no se había ejecutado. Ejecuté `bash antenna_design/claude_cloud_setup.sh` una vez: tardó 284 s y terminó con rc 0.
  - Python: openEMS `0.37.0.post1.dev40+g5fecbb58d` y CSXCAD `0.7.0.post1.dev8+g626b99f2f`.
  - Commits nativos `5fecbb5` y `626b99f`, los mismos que en 001.
  - La comprobación de dependencias del script upstream avisó de que faltaban paquetes (son los de Python que da el venv y `libboost-all-dev`); el build terminó sin errores.

## Propuesta y parámetros
Es el único refinamiento recomendado al final de [`solver_installation.md`](solver_installation.md). Mantiene la misma geometría P01, el FR4 provisional (εr 4,4, tanδ 0,017 en f0, h 1,6 mm), las láminas de cobre (5,8e7 S/m, 35 µm), la caja de ±35 mm (z de −25 a 35 mm), PML_8, el puerto concentrado de 50 Ω en (0; −1,8216) mm, la Gauss con f0 = 7,9872 GHz y fc = 1 GHz, el criterio EndCriteria 1e-5 y el mismo vector de frecuencias (1003 muestras de 7,5 a 8,5 GHz, 501 en el canal, con los extremos exactos). **Solo cambia la malla:**

| | 001 | 002 |
|---|---|---|
| Paso máximo en x/y | 0,5 mm | 0,35 mm |
| Paso máximo en z (aire) | 0,8 mm | 0,6 mm |
| Celdas en el sustrato | 8 | 10 |
| `metal_edge_res` | 0,25 mm | 0,175 mm |
| Celdas | 1 795 680 | 4 752 832 |
| Razón máxima entre celdas vecinas (x/y, z) | 1,26 / 1,32 | 1,26 / 1,392 |

`validator` comprobó que los dos XML, quitando las líneas de malla, son idénticos. Script: [`em/p01_openems_mesh.py`](../em/p01_openems_mesh.py). Parámetros: [`prepared.json`](../em/P01_OPENEMS_002/prepared.json).

## Recursos y comandos
```
source antenna_design/em/runtime_env.sh
python antenna_design/em/p01_openems_mesh.py prepare --out antenna_design/em/P01_OPENEMS_002
timeout --signal=TERM --kill-after=5s 1442s taskset -c 0,1 python antenna_design/em/p01_openems_mesh.py solve --out antenna_design/em/P01_OPENEMS_002
python antenna_design/em/p01_openems_mesh.py summarize --out antenna_design/em/P01_OPENEMS_002
python antenna_design/em/p01_openems_mesh.py compare --out antenna_design/em/P01_OPENEMS_002
cd antenna_design && python -m analysis s11 em/P01_OPENEMS_002/s11_complex.csv --out em/P01_OPENEMS_002/s11_analysis.json --z0 50 --max-gap-hz 1000000
```

| | Estimación | Observado |
|---|---|---|
| RAM | 9,07 GiB (2048 B/celda); 0,84 GiB escalada con el RSS de 001 | Pico de RSS de 758 256 KiB (unos 740 MiB) |
| Pasos | Unos 10 266 | 10 368 |
| Paso temporal | 3,70e-13 s | 3,7907e-13 s |
| Tiempo del motor | Unos 481 s (con 101 Mcell/s) | 942,6 s (con 53,3 Mcell/s) |
| Tiempo de pared y CPU | — | 963 s de pared y 1678 s de CPU, con 2 CPU (afinidad 0,1) y sin timeout |

- **Excepción registrada (H1 de `validator`).** El encargo que le di a `em-solver` fijaba un tope de 8 GiB, y el script lo recoge como `abort_rule`. La estimación conservadora lo superaba. Lo autoricé de todos modos porque había unos 15,5 GiB disponibles, la estimación basada en lo medido era de 0,84 GiB y se cumplían las reglas reales: 2 CPU, 1 FDTD y un timeout externo. Queda anotado en [`launcher.json`](../em/P01_OPENEMS_002/launcher.json). CLAUDE.md y AGENTS.md no fijan un tope numérico de RAM, así que no se infringe ninguna regla. Pero el contrato previo al lanzamiento quedó contradicho. Para la ronda 003, la RAM debe estimarse con la base medida (unos 0,16 KiB/celda de RSS, con margen).
- **H2.** El rendimiento fue la mitad del de 001: 53 frente a 101 Mcell/s. Para estimar los tiempos hay que calibrar con 002.

## Métricas
Ficheros: [`s11_complex.csv`](../em/P01_OPENEMS_002/s11_complex.csv) (S11 y Zin complejos, tensiones y corrientes de puerto), [`result.json`](../em/P01_OPENEMS_002/result.json), [`mesh_comparison.json`](../em/P01_OPENEMS_002/mesh_comparison.json), [`s11_analysis.json`](../em/P01_OPENEMS_002/s11_analysis.json) (analizador de Codex) y [`s11.png`](../em/P01_OPENEMS_002/s11.png).

| Canal 7,7376–8,2368 GHz | 001 | 002 |
|---|---|---|
| Peor S11 | −1,94 dB (8,2368 GHz) | −1,75 dB (8,2368 GHz) |
| Mejor S11 | −7,63 dB (7,7376 GHz) | −6,85 dB (7,7376 GHz) |
| ≤ −6 dB en todo el canal | **No** (417 de 501 muestras por encima) | **No** (450 de 501) |
| ≤ −10 dB en todo el canal | No | No |
| Mínimo de \|S11\| en 7,5–8,5 GHz | −8,93 dB en 7,627 GHz | −7,98 dB en 7,626 GHz |
| Zin en unos 7,987 GHz | 16,2 + j37,4 Ω | 16,5 + j42,8 Ω |
| Decaimiento de energía | −50,48 dB | −52,12 dB |

- **Sensibilidad a la malla:** max\|ΔS11\| complejo de 0,095 en el canal, en 8,2368 GHz; diferencia máxima de 0,78 dB y media de 0,38 dB, con un desplazamiento sistemático: 002 adapta peor.
- La coherencia entre S11 y Zin y la pasividad están comprobadas por `validator`.
- **Lo que es robusto:** P01 incumple −6 dB en el canal con un margen de unos 4 dB en el borde superior, cinco veces la diferencia entre mallas.
- **Lo que no es robusto:** los valores exactos y las frecuencias donde se cruza −6 dB, que se mueven decenas de MHz con la malla.

## Errores y reservas
- **H3.** La línea de malla más cercana al borde del parche queda 0,083 mm dentro en 001 y 0,058 mm en 002. Por tanto, la geometría efectiva cambia con la malla, y parte de ΔS11 puede deberse a la discretización geométrica. Que la lámina se ajuste a esa línea no está verificado con el solver. En la siguiente malla hay que hacer coincidir las líneas con los bordes nominales.
- **H4.** 002 se compiló en otro contenedor y usa HDF5 1.10.10 y zlib 1.3, frente a HDF5 1.14.5 y zlib 1.3.1 en 001. Son los mismos commits nativos, pero no el mismo binario. El impacto esperable es despreciable, aunque no se ha medido.
- El registro temporal (3,93 ns) es 1,37 veces la duración de la excitación. El criterio de energía se cumple, pero eso no es una prueba de convergencia espectral.

## Siguiente hipótesis
La resonancia de P01 está por debajo del canal: el mínimo de |S11| está en unos 7,63 GHz, la reactancia de Zin es positiva en todo el barrido y Re(Zin) es máxima en el borde de 7,5 GHz. Propuesta para la ronda 003, a cargo de `rf-designer` y `em-solver`, con el mismo material, la misma alimentación y la malla de 001:
- acortar la dimensión resonante y reajustar el inset para llevar Re(Zin) hacia 50 Ω en f0;
- ampliar el barrido por debajo de 7,5 GHz para localizar el pico real;
- separar el efecto de la inductancia de la alimentación vertical.

No se justifica refinar más la malla sobre una geometría que no cumple. Después hay que valorar si el FR4 de 1,6 mm da el ancho de banda de 499,2 MHz, o si hace falta P02 o P03.

## Estado
- Ronda 2/40.
- Ningún candidato es viable para HFSS.
- Tests: 18 OK.
- **CONTINUE.**

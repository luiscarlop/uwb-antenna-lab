# Primera campaña: revisión RF de geometrías, alimentación y fabricación

Fecha: 2026-11-03. Rama comprobada: `codex/uwb-ch9-antenna-design`.
Alcance: elemento aislado del canal 9, centro 7.9872 GHz, banda
7.7376–8.2368 GHz, referencia de puerto 50 Ω. No se evalúa un array.

**Evidencia: GEOMETRY_ONLY. Simulación EM: NOT_RUN.** Este informe contiene
comprobaciones de coordenadas y estimaciones analíticas; no demuestra frecuencia
de resonancia, adaptación, ancho de banda, ganancia, eficiencia ni respuesta
temporal. Los criterios S11 ≤ −6 dB y objetivo ≤ −10 dB sobre toda la banda son
requisitos pendientes de evaluación.

## Fuentes y método

Se leyeron `AGENTS.md`, `.codex/agents/rf_designer.toml`,
`antenna_design/README.md`, `CODEX_FIRST_TASK.md`, `AUTOMATED_CYCLE.md`,
`campaign_state.json`, `automation_policy.json`, `designs.py` y
`tests/test_designs.py`. Las cifras siguientes se calcularon con Python 3.12.14,
importando `designs.candidates()` y `rectangular_patch_dimensions()`, sin exportar
ni modificar candidatos. Las separaciones se obtuvieron mediante la distancia
euclídea mínima de un punto a los segmentos del contorno correspondiente.
Se inspeccionó la conectividad del metal definida por estos polígonos simples.
Esta tarea no ejecutó la suite de pruebas ni ningún solver; las comprobaciones
de exportación de la campaña pertenecen al coordinador/auditor.

## Comparación geométrica

Dimensiones en mm, origen en el centro de la placa. Sustrato provisional común:
FR4 genérico, εr = 4.4, tan δ = 0.017, espesor 1.6; placa 26 × 26.
No hay fabricante, tolerancia ni dispersión dieléctrica confirmados.

| Candidato | Dimensiones de cobre y ranura | Centro de alimentación (x, y) | Distancia del centro a borde exterior / ranura | Dictamen geométrico |
| --- | --- | --- | --- | --- |
| P01 rectangular | W = 11.421267, L = 8.280016 | (0, −1.821603) | 2.318404 / no aplica | Parche continuo, alimentación interior; referencia prioritaria |
| P02 U-slot | Mismo W/L; U exterior 6.281697 de ancho y 3.643207 de alto; anchura local de corte 0.350000 | (0, −1.821603) | 2.318404 / 1.159202 | Metal continuo y centro fuera de la ranura; dimensiones de U heurísticas |
| P03 hexagonal ranurado | Radio exterior a vértice 6.053271; ancho entre vértices 12.106543; alto entre caras 10.484573; radio de ranura hexagonal 1.100000 | (0, −2.542374) | 2.699913 / 1.589746 | Anillo hexagonal continuo, alimentación interior; sin estimación de resonancia |

P01 deja margen de placa de 7.289367 en x y 8.859992 en y. P02 conserva un
ligamento mínimo de cobre de 1.159202 entre la ranura y el borde exterior; sus
dos brazos y su travesaño tienen corte nominal 0.35. La abertura superior de la
U comunica el cobre interior con el resto del parche: no aparece una isla de
cobre desconectada. P03 deja un ancho mínimo de anillo de 4.289659, distancia
entre las caras paralelas de los hexágonos concéntricos. Los tres contornos
están dentro de la placa y no presentan intersecciones entre ranura y borde.

En P01/P02 el eje de longitud es y y el de anchura x. La alimentación a x = 0
mantiene la simetría transversal; su distancia al borde de longitud inferior es
2.318404. La elección de y = −0.22 L es heurística: no establece una impedancia
de entrada de 50 Ω. La polarización y los modos radiantes deben verificarse en
el modelo de campos.

## Material y límites de las estimaciones

El cálculo de línea de transmisión da εef = 3.738232 para el boceto P01;
λ0 = 37.534112 mm y h/λ0 = 0.04263. El espesor equivale a aproximadamente
0.08942 longitudes de onda en el dieléctrico homogéneo de εr = 4.4. El modelo
analítico no incluye alimentación inductiva, plano de masa finito, dispersión,
ondas superficiales ni pérdidas metálicas; este espesor exige especial atención
al lanzamiento de sonda en EM.

La banda requerida tiene ancho fraccional del 6.25 %. No puede inferirse su
cobertura del tamaño de P01 ni de la presencia de ranuras en P02/P03. El FR4
genérico y tan δ constante son hipótesis de simulación, no una especificación
de compra ni una garantía de eficiencia a 8 GHz.

Como comprobación de sensibilidad, manteniendo W/L/h fijos y reevaluando
únicamente la misma aproximación de línea de transmisión con εr = 4.2, 4.4 y
4.6, las frecuencias estimadas son 8.1570, 7.9872 y 7.8275 GHz. Este ejercicio
**no es una tolerancia medida de FR4 ni una simulación**; ilustra que identificar
el laminado y su Dk efectivo a la frecuencia de trabajo es necesario antes de
congelar dimensiones.

## Alimentación y fabricabilidad

`FEED_PROBE_CENTER` sólo representa un marcador circular de radio 0.12 en DXF;
el SVG usa radio 0.14 como símbolo visual. Ninguno define radio de sonda,
taladro, pad, coaxial, apertura de masa ni puerto. Las pruebas actuales de punto
interior tampoco certifican una huella de tamaño finito. Con los márgenes
anteriores existe espacio geométrico para una huella razonable, pero todavía
falta diseñar su conexión tridimensional.

Como especificación provisional de fabricación, proponer cobre de 35 µm,
conductividad nominal 5.8 × 10⁷ S/m para el primer modelo con pérdidas y
superficie lisa; registrar después acabado y rugosidad reales. Para el primer
cupón, proponer sin máscara en el parche y en las ranuras y declarar esta
ausencia en el solver. Mantener la misma pila en la comparación P01/P02/P03.
El DXF debe importarse haciendo una resta booleana de SLOT a PATCH; la capa de
ranura no es un segundo objeto metálico.

La ranura de 0.35 en P02 es el detalle más exigente de los tres candidatos.
Una propuesta inicial de aceptación es error máximo de cada borde grabado de
±0.05 mm: dos desplazamientos adversos dejan 0.25 mm de apertura. Deben
confirmarse las capacidades reales del fabricante, el redondeo de esquinas y
la compensación de grabado. Como objetivos de trabajo, declarar ±0.05 mm de
posición/dimensión de cobre, ±0.10 mm de registro del taladro y ±0.08 mm de
espesor de sustrato; son requisitos propuestos, todavía no tolerancias
garantizadas. P03 no requiere puentes ni vías para conectar su anillo.

## Mejora concreta propuesta: completar el lanzamiento de P01

Priorizar P01 y conservar su W/L, material provisional, placa y centro de
alimentación. La mejora es especificar una alimentación física de sonda y su
retorno antes de optimizar dimensiones o comparar ranuras:

1. Usar dieléctrico 26 × 26, entre z = 0 y 1.6; masa continua de 26 × 26 entre
   z = −0.035 y 0 salvo la apertura de sonda; parche entre z = 1.6 y 1.635.
   Ésta es una propuesta 3D, no una descripción de geometría ya exportada.
2. Proponer pin conductor de diámetro 0.30 mm, taladro acabado de 0.40 mm,
   huella superior circular de diámetro 0.80 mm unida al parche y apertura de
   masa de diámetro 1.20 mm, todos centrados en (0, −1.821603). No conectar el
   metal del pin a la masa a través de un barril de taladro. En fabricación,
   resolver con taladro no metalizado y pin soldado al parche o con el conector
   que se seleccione; incluir el aire/material de relleno real en EM.
3. El radio exterior propuesto de huella 0.40 deja 1.918404 mm al borde de
   P01. Si se reutiliza sin desplazar el centro, deja 0.759202 mm a la ranura
   de P02 y 1.189746 mm a la de P03. Estas separaciones nominales permiten
   comprobar la huella completa y sus tolerancias, además del punto central.
4. Para la primera prueba de solver, el especialista EM puede usar un puerto
   concentrado explícito entre masa y parche como aproximación documentada de
   sonda. Una referencia de 50 Ω sirve para normalizar S11, sin demostrar que
   el lanzamiento físico sea de 50 Ω. Para transferencia HFSS/fabricación,
   sustituir esa aproximación por coaxial y conector de dimensiones/materiales
   conocidos, con conductor exterior unido a masa y plano de referencia
   identificado. Los dos modelos de alimentación deben tener IDs distintos.

No se ha implementado esta propuesta en los archivos de geometría. El pin,
taladro, huella y apertura son parámetros iniciales sujetos a selección real de
conector y validación EM; no constituyen un lanzamiento validado. La siguiente
prueba concreta de la campaña es **una simulación del P01 original con
alimentación y materiales declarados**, siguiendo el presupuesto y el barrido
que prepare el especialista EM. Sólo después de esa evidencia procede elegir
un refinamiento: modificar exclusivamente la posición y del feed, manteniendo
W/L y pila, si la impedancia de entrada lo justifica. No se autoriza aquí un
barrido de candidatos ni una ejecución adicional.

## Evidencia pendiente para decidir

| Campo | Estado en esta revisión |
| --- | --- |
| Geometrías P01/P02/P03 | GEOMETRY_ONLY; coordenadas y márgenes revisados analíticamente |
| Solver/versión; puerto real; fronteras; malla | NOT_RUN; debe completarlos el informe EM |
| Convergencia espacial y temporal | NOT_RUN |
| S11 complejo y cobertura de toda la banda | NOT_RUN |
| Ganancia realizada, eficiencia y patrones co/cross complejos | NOT_RUN |
| Fase radiada, retardo de grupo y ripple por frecuencia/ángulo | NOT_RUN; no derivarlos de la fase de S11 |
| CPU/RAM/tiempo de solver | No se ejecutó solver en esta revisión |
| Proyecto HFSS / medidas | No disponibles |

P01 es la referencia recomendada por su menor número de parámetros y su
trazabilidad analítica. P02 y P03 son candidatos geométricos fabricables en
principio con la tecnología propuesta, pendientes de pila, lanzamiento y
capacidad de fabricación confirmados. No hay evidencia para ordenar su
rendimiento electromagnético.

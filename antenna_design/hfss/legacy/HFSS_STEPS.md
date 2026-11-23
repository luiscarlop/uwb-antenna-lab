# Transferencia manual reproducible P01/P02/P03 a HFSS

Estado: GEOMETRY_ONLY / HFSS_NOT_RUN. No se ha instalado, abierto ni ejecutado HFSS/PyAEDT. Estas instrucciones son la alternativa manual al script PyAEDT solicitada. El exportador solo lee outputs/manifest.json y escribe tablas de parámetros/vértices; nunca llama a un solver ni cambia el manifiesto. La geometría no se redimensiona al cambiar material.

Desde la raíz del repositorio:

```bash
python antenna_design/hfss/legacy/export_handoff.py \
  --manifest antenna_design/outputs/manifest.json \
  --out antenna_design/hfss/legacy/handoff_v1
```

El directorio debe ser nuevo: se rechaza sobrescribir una transferencia. `source.json` fija SHA256 del manifiesto, IDs y evidencia. Tablas: `parameters.csv` (material, placa, feed, propuestas explícitas) y `vertices.csv` (todos los vértices sin redondear). Consultar las tablas generadas al construir cada diseño; si Claude cambia el manifiesto, generar otra carpeta/versionar otro hash.

## Construcción de tres diseños independientes

1. Abrir un proyecto HFSS nuevo. Crear tres diseños **Driven Modal**, uno por ID del manifiesto. Registrar versión/build de AEDT y licencia usada; no ejecutar análisis todavía. Unidades del modelador: **mm**; las frecuencias de las tablas están en Hz. El eje z es normal al PCB, x la anchura del P01, y su longitud.
2. En cada diseño crear las variables de `parameters.csv`: `board_x=26mm`, `board_y=26mm`, `substrate_h=1.6mm`, y feed correspondiente. Los valores de este ejemplo son los del hash entregado; prevalecen las tablas. Propuestas adicionales: `cu_t=0.035mm`, `sigma_cu=5.8e7S_per_m`, `port_w=0.2mm`. Son hipótesis de transferencia, no especificaciones de fabricación.
3. Crear material `generic_FR4_PROVISIONAL`: epsilon relativa 4.4, permeabilidad relativa 1, tan_delta 0.017, según manifiesto. Para comparación con openEMS elegir explícitamente UNO de estos modelos: (A) tan_delta constante en frecuencia, o (B) tan_delta(f)=0.017*f0/f, equivalente a conductividad eléctrica constante aproximadamente0.0332372S/m. El baseline openEMS utilizó B. Si HFSS permite introducir conductividad dieléctrica, usar B con tan_delta=0 para evitar doble contabilización; verificar la interpretación del material en la versión instalada. No afirmar equivalencia con A. Registrar modelo y unidades en el proyecto.
4. Crear caja dieléctrica desde `(-board_x/2,-board_y/2,0)` con tamaño `(board_x,board_y,substrate_h)`. Activar Solve Inside para dieléctrico. No añadir máscara ni adhesivo no especificado.
5. Crear `GROUND` como rectángulo de superficie en z=0, con el contorno completo26×26mm. Crear `PATCH` como polilínea cerrada y cubierta (sheet) en z=substrate_h, usando los vértices PATCH de `vertices.csv` en el orden almacenado. No repetir el primer vértice como arista nula; cerrar la polilínea con la operación de HFSS.
6. P01 no tiene ranuras. P02: construir la polilínea cóncava SLOT_1 en el mismo plano; P03: construir la polilínea hexagonal SLOT_1. Ejecutar **Modeler → Boolean → Subtract**, blank=PATCH, tool=SLOT_1, sin conservar herramienta. Debe quedar un único conductor conectado con el hueco correspondiente. No dejar la ranura como otra hoja metálica. Comparar visualmente con SVG, que es solo guía visual. P02 corte nominal0.35mm; P03 radio interior1.1mm.
7. Asignar a PATCH y GROUND una condición **Finite Conductivity** con sigma=5.8e7S/m y espesor35µm, sin roughness. Confirmar en la versión HFSS cómo se aplica la hoja fina y que el espesor no se ignora. Si se elige cobre volumétrico, crear un modelo distinto, declarar posición/espesor y refinar en consecuencia; no mezclar un sólido PEC con la etiqueta cobre con pérdidas.
8. Alimentación provisional: crear una hoja rectangular vertical en el plano y=feed_y, desde `(feed_x-port_w/2,feed_y,0)` hasta `(feed_x+port_w/2,feed_y,substrate_h)`. Esta hoja es la superficie del puerto, **no cobre**. Asignar un **Lumped Port** de un modo, referencia50Ω, línea de integración de masa `(feed_x,feed_y,0)` a parche `(feed_x,feed_y,substrate_h)`. Revisar normal, polaridad y contacto con ambas hojas. Mantener la masa continua: esta excitación ideal no requiere agujero antipad. El ancho0.2mm es una elección HFSS nueva, no equivalente exacto al puerto lineal openEMS; será necesario estudiar sensibilidad. No añadir simultáneamente sonda física y este puerto. Para un coaxial real hace falta definir pin, dieléctrico, retorno y plano de referencia como otro experimento.
9. Crear caja de aire desde(-35,-35,-25)mm con dimensiones70×70×60mm. Asignar aire y una frontera de radiación abierta a sus seis caras exteriores (o PML documentada). Verificar que la frontera exterior esté al menos lambda0/4 a7.5GHz (~10mm) del metal/PCB; esta caja deja más de ese margen. No asignar radiación a las caras del sustrato. Documentar que frontera HFSS y PML_8 de openEMS son tratamientos diferentes.
10. Validar modelo de HFSS: objetos, materiales, vacío de ranuras, contactos del puerto, frontera exterior, ausencia de volúmenes/hojas duplicadas. Exportar capturas y lista de objetos. Revisar feed con superficie finita, no solo su centro. P02/P03 deben conservar material, placa y referencia de50Ω para comparación.

## Preparación de solución, sin ejecutar automáticamente

11. Crear setup adaptativo con frecuencia central7.9872GHz o adaptación multifrecuencia en7.7376/7.9872/8.2368GHz si la versión lo admite. Propuesta inicial: delta S<=0.02 y máximo10 pases; no confundir máximo de pases con convergencia lograda. Reservar recursos antes de Solve y cumplir el límite acordado de dos núcleos. Refinar bordes, puerto y ranuras; P02 requiere varios elementos a través del corte0.35mm. Las mallas FEM no deben copiar literalmente los pasos FDTD.
12. Preparar barrido7.5–8.5GHz. Para validación usar puntos discretos y añadir explícitamente7.7376,7.9872,8.2368GHz. Una salida cada1MHz puede ser interpolada: registrar tipo de barrido, errores y puntos realmente resueltos. Un mínimo puntual no demuestra cobertura. Una comparación fiable exige verificar adaptación en todo el canal y estabilidad frente a malla/puerto/frontera.
13. Tras autorización de una ejecución por el responsable EM, guardar proyecto AEDT, versión, setup, historial de convergencia, malla, tiempos/RAM y CSV `frequency_hz,s11_real,s11_imag` normalizado a50Ω. Para campos: exportar por ángulo/polarización la transferencia compleja respecto a una excitación/onda incidente común, con convención de fase y distancia anotadas. No inferir retardo radiado de fase de S11.
14. Solo entonces revisar si procede marcar HFSS_VALIDATED; construir un proyecto o lograr convergencia de un único setup no equivale por sí solo a validar todas las métricas.

## Alcance de esta entrega

Generadas y comprobadas las tablas de P01/P02/P03, incluido SHA256 de origen. Las instrucciones HFSS no se han ejecutado en Ansys ni se ha comprobado su interfaz específica en este entorno. El responsable de HFSS deberá validar las opciones de la versión utilizada antes de un solve. No hay resultados electromagnéticos nuevos en esta transferencia.

## Comprobación antes de importar

```bash
python antenna_design/hfss/legacy/verify_handoff.py \
  --manifest antenna_design/outputs/manifest.json \
  --handoff antenna_design/hfss/legacy/handoff_v1
```

Solo lee la transferencia y el manifiesto; regenera tablas en una carpeta temporal y compara hash, coordenadas, parámetros y etiquetas de evidencia. Código de salida0 indica coherencia,1 indica discrepancias. Un fallo puede significar que Claude actualizó el manifiesto: generar una nueva transferencia, sin sobrescribir la anterior. No certifica geometría fabricable ni validación HFSS. Se comprobó con casos sintéticos de tabla alterada y manifiesto cambiado, además de verificar la transferencia original.

# Auditoría independiente de geometría

Auditor ejecutado: validator, selección explícita GPT-6 Luna High. No modificó resultados ni ejecutó EM. Este documento conserva su informe.

Comando reproducido: `cd antenna_design && python -m unittest discover -s tests -v`. Cuatro pruebas correctas. Aviso no bloqueante: ezdxf no puede crear caché en /home/agent/.cache/ezdxf.

Verificaciones: banda 7.7376–8.2368 GHz, centro 7.9872 GHz; unidades DXF INSUNITS=4 (mm); placa 26×26 mm. P01/P02 W=11.4213 mm, L=8.2800 mm, epsilon efectiva estimada 3.7382. P03 radio exterior 6.0533 mm e interior 1.1 mm. Coordenadas dentro de placa, ranuras contenidas en parche y alimentación fuera de ranuras. Dimensión mínima de ranura U: 0.35 mm. DXF legibles con capas BOARD/PATCH/SLOT/FEED_PROBE_CENTER. Sin invalidez dimensional detectada en los candidatos actuales.

Hallazgos:
1. Severidad media: SLOT es una polilínea cerrada sobre PATCH, no una operación booleana. Al importar hay que sustraer explícitamente SLOT del cobre antes de fabricar/modelar. SVG oculta la ranura visualmente, no resuelve la semántica CAD.
2. Severidad media: alimentación solo representada por centro/círculo; radios DXF 0.12 mm y SVG 0.14 mm son marcadores. Falta lanzamiento, conductor, plano de masa y puerto físico de 50 ohmios en 3D.
3. Severidad baja: pruebas actuales no detectan autointersecciones, contención completa de ranuras, holguras mínimas o semántica de sustracción. La inspección independiente de las coordenadas actuales no sustituye esas pruebas para futuras modificaciones.

Estado de los tres candidatos: GEOMETRY_ONLY. No hay validación de fabricabilidad de un stackup/lanzamiento completo, S11 ni radiación.

## Auditoría adicional de la especificación EM

El auditor revisó `em/p01_model_spec.json`, `prepare_p01.py` y `solver_diagnosis.json`: son especificación declarativa y diagnóstico, no un proyecto ejecutado. El generador no llama al solver. Coinciden el hash de designs.py, el producto de celdas 142×141×82=1,641,804 y la estimación de RAM 3.36 GB (3.13 GiB). Dos hilos están dentro de la cuota observada de cuatro CPU; RAM disponible por cgroup 32 GiB. Estas cifras son presupuesto, no consumo observado.

Antes de ejecutar:
- No confundir paso de evaluación de 1 MHz con resolución demostrada. La ventana máxima propuesta es 17.145 ns (escala 1/T≈58.3 MHz); la evaluación de Fourier en puntos densos no prueba que el truncamiento temporal sea despreciable. Exigir decaimiento real, estabilidad temporal y comprobación de la cobertura.
- La bandera de extremos exactos debe materializarse en la lista de frecuencias: 7.7376 y 8.2368 GHz no pertenecen a la cuadrícula de 1 MHz desde 7.5 GHz.
- Verificar el modelo de lámina conductora de 35 µm: la malla de 0.2 mm en z no resuelve ese espesor volumétricamente. La API de hoja/pérdidas debe validarse con el solver instalado.
- Registrar hash del generador, versión del solver/API y commit para la ejecución real. Importar bindings no basta para certificar que el solver funciona.
- Los fallos PyPI y ausencia en el índice Debian consultado no demuestran imposibilidad de instalación desde fuentes u otras distribuciones; únicamente descartan las rutas binarias comprobadas.

No se han ejecutado simulaciones durante esta revisión adicional.

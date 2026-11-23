# Laboratorio de diseño electromagnético — UWB canal 9

**Alcance: SOLO antenas IR-UWB**. No modificar algoritmos del radar. El propósito es proponer, simular, comparar y refinar geometrías físicamente realizables antes de la validación final con Ansys HFSS.

## Requisitos de investigación
- Canal 9 IEEE 802.15.4z: f_c=7.9872 GHz, B=499.2 MHz, banda=[7.7376,8.2368] GHz.
- Puerto de referencia 50 ohmios. S11<=-6 dB durante toda la banda como referencia mínima; <=-10 dB como objetivo preferible, no como resultados.
- Además: ganancia realizada, eficiencia, patrones co/cross polarizados, amplitud y fase radiadas en función de frecuencia y ángulo, retardo de grupo y su ripple.
- Pares/array: Sij y patrones embebidos SOLO cuando el elemento aislado sea viable.
- Sustrato P01 provisional para el primer boceto: FR4 genérico eps_r=4.4, tan_delta=0.017, h=1.6 mm. NO equivale al FR4 de seis capas del artículo ni tiene especificación de fabricante confirmada.

## Propuestas iniciales GEOMETRY_ONLY
1. P01: parche rectangular de referencia por aproximación de línea de transmisión.
2. P02: mismo parche con U-slot interior de dimensiones iniciales heurísticas.
3. P03: parche hexagonal con ranura central hexagonal de dimensiones heurísticas.

Primero validar un elemento; después se podrá probar el array hexagonal. No confundir parche hexagonal con distribución hexagonal de elementos.

## Ejecutar
Python 3.10+.

    cd antenna_design
    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python designs.py --out outputs

Las salidas son DXF (capas BOARD/PATCH/SLOT/FEED_PROBE_CENTER), SVG y manifest JSON. DXF es geometría 2D, no simulación 3D de HFSS. Falta diseñar dieléctrico, plano de masa, alimentación, puerto, radiación, frontera y barrido/convergencia en un solver.

## Agentes Codex
Configuraciones en .codex/config.toml y .codex/agents/*.toml. Ejecutar antenna_design/CODEX_FIRST_TASK.md en Codex Cloud; el agente coordinador decide delegar. Los archivos de rol son reconocidos por clientes Codex compatibles; confirmar disponibilidad efectiva en Cloud.

Para el entorno Cloud: usar rama codex/uwb-ch9-antenna-design. Setup liviano: python -m pip install -r antenna_design/requirements.txt. No compilar openEMS automáticamente en setup ni instalar herramientas con API de pago. Más detalles en CLOUD_SETUP.md.

## Evidencia
- GEOMETRY_ONLY: estimaciones/archivos CAD, SIN S11 ni ganancia EM.
- EM_SIMULATED: requiere solver real, datos numéricos, parámetros y convergencia reproducible.
- HFSS_VALIDATED: requiere proyecto HFSS y simulación ejecutada.
- MEASURED: requiere mediciones reales.

## Contexto técnico
- EuCAP2027_VPA_UWB_doppler.pdf: arreglo apilado con cavidad, ranuras y pads conectados por vías sobre 6 capas, para canales 9/10/12; da especial importancia al retardo de grupo y al rizado espectral.
- uwb_simulation.ipynb: modelo de pulso UWB, con portadora de 7.9872 GHz. La representación directa a 10 GSa/s produce aliasing RF; no interpretar el notebook como una simulación EM.
- Tutorial oficial openEMS: https://docs.openems.de/en/latest/python/openEMS/Tutorials/Simple_Patch_Antenna.html

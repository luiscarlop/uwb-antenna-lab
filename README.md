# Mejora de la resolución angular de un radar UWB mediante arrays virtuales MIMO diseñados con un sistema de orquestación de agentes de IA

Repositorio del Trabajo Fin de Estudios. Contiene el diseño y la caracterización electromagnética del elemento radiante para el canal 9 de IEEE 802.15.4z (7,7376–8,2368 GHz, f0 = 7,9872 GHz, 50 Ω), los arrays lineales simulados en HFSS, el procesado del array virtual MIMO y la memoria.

## Estructura

```
.
├── antenna_design/     Trabajo principal del TFG
│   ├── variants/       Definición geométrica de cada diseño (JSON, fuente única de verdad)
│   ├── em/             Simulaciones FDTD en openEMS (una carpeta por ejecución, con malla, registros y resultados)
│   ├── hfss/           Scripts PyAEDT (build/), exportadores (export/), análisis (analysis/) y resultados (results/) de HFSS
│   ├── analysis/       Análisis comunes de las simulaciones
│   ├── reports/        Informes de cada ronda y de cada exportación de HFSS, con su auditoría
│   ├── artifacts/      Fuentes de la página de resumen visual
│   ├── tests/          Pruebas unitarias
│   └── campaign_state.json, automation_policy.json   Estado de la campaña y límites del ciclo automatizado
├── latex_memoir/       Memoria del TFG (LaTeX) y sus figuras
├── .claude/, CLAUDE.md Configuración del sistema de agentes en Claude Code
└── .codex/, AGENTS.md  Configuración equivalente para Codex
```

Las carpetas `legacy_*` dentro de `antenna_design/hfss/results/` guardan exportaciones superadas, que se conservan por trazabilidad.

## Reproducir

Python 3.10 o superior.

```
cd antenna_design
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

- Las simulaciones de openEMS necesitan openEMS y CSXCAD compilados (`antenna_design/claude_cloud_setup.sh`).
- Las de HFSS necesitan Ansys HFSS: los scripts de `antenna_design/hfss/build/` generan el modelo y los de `export/` exportan los resultados que leen los análisis.

## Memoria

```
cd latex_memoir/src
pdflatex TFG-memoir.tex
```

Hay que compilar dos o tres veces para resolver las referencias.

## Estado de la evidencia

Ningún resultado es una medida. Los estados de cada diseño (`GEOMETRY_ONLY`, `EM_SIMULATED`, `HFSS_VALIDATED`) y su procedencia están en `antenna_design/campaign_state.json` y en los informes de `antenna_design/reports/`.

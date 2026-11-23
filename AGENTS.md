# Codex: laboratorio de antenas IR-UWB, canal 9
Trabaja exclusivamente en antenna_design/ y en codex/uwb-ch9-antenna-design. No modificar src/, matlab/, latex_memoir/, data/, pyproject.toml ni el proyecto operativo del TFG. No trabajar en MUSIC, Doppler, beamforming, CIR, estimadores ni otros algoritmos de radar. El notebook UWB y el artículo EuCAP son contexto, no tareas de código.

Objetivo: descubrir geometrías de antenas fabricables, caracterizar electromagnéticamente el elemento para el canal 9 de IEEE 802.15.4z y preparar diseños transferibles a HFSS.
Frecuencia central 7.9872 GHz; banda 7.7376–8.2368 GHz; referencia de 50 ohmios.
Explorar primero P01 parche rectangular, P02 U-slot y P03 parche hexagonal ranurado. El array hexagonal es una etapa posterior y no una variante del elemento.

## Modelo del orquestador y agentes
El orquestador principal debe utilizar **GPT-6 Astra** con razonamiento **Medium**. La configuracion propuesta esta en `.codex/config.toml`, pero la seleccion explicita de modelo del entorno Cloud puede prevalecer: comprobarla en el selector al iniciar cada tarea. No afirmar que Astra esta activo sin verificarlo. Los roles `rf_designer` y `em_solver` utilizan GPT-6.1 Sol High; `validator` utiliza GPT-6 Luna High. No ejecutar estos roles con Astra por herencia salvo peticion explicita del propietario.

## Agentes y campaña
El coordinador distribuye tareas al especialista RF (geometrías/material/alimentación), EM (solver y malla) y auditor independiente (pruebas y trazabilidad). Máximo tres subagentes abiertos a la vez. Una campaña inicial: <= 3 geometrías nuevas, <= 1 simulación de elemento aislado, <= 2 refinamientos de un candidato. No anidar agentes sin necesidad. El propietario ha autorizado una automatización Codex limitada a 5 rondas, conforme a antenna_design/automation_policy.json; no crear bucles ilimitados ni programación fuera de Codex.
RF y EM no deben editar el mismo archivo simultáneamente. El auditor no modifica resultados: señala problemas y reproduce pruebas.

## Evidencia y restricciones
No atribuir S11, ganancia, eficiencia, fase, retardo de grupo o ancho de banda a estimaciones de línea de transmisión ni DXF. Estados permitidos: GEOMETRY_ONLY, EM_SIMULATED, HFSS_VALIDATED, MEASURED (solo según procedencia real).
El umbral -6 dB de S11 es referencia mínima de adaptación y -10 dB objetivo preferido sobre TODA la banda; ninguno es un resultado ni garantiza buena respuesta temporal. Priorizar también dispersión de fase, ripple de retardo de grupo, ganancia realizada y eficiencia.
Registrar f0, banda, materiales, eps_r, tan_delta, grosor, pérdidas metálicas, topología de alimentación, puerto de 50 ohmios, contornos, definición de malla, convergencia, software y versión, consumo CPU/RAM y archivos de origen. No inventar curvas; si falta solver: NOT_RUN.
No iniciar API de pago ni simulaciones largas sin consentimiento. Máximo 2 vCPU y estimación conservadora de RAM para la primera prueba.
No abrir pull request automáticamente: este repo tiene workflows de revisión que pueden consumir cuota externa. No fusionar en master.

## Pruebas
cd antenna_design && python -m pip install -r requirements.txt && python -m unittest discover -s tests -v && python designs.py --out outputs

## Primera tarea
Leer antenna_design/CODEX_FIRST_TASK.md.

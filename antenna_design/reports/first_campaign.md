# CH9-INITIAL-2026-11-03

Resultado: BLOCKED / EM_NOT_RUN. Tres geometrías exportadas y auditadas; ninguna simulación electromagnética ejecutada. No existen datos complejos S11 ni convergencia que presentar. No se ha modificado el procesado del TFG.

Base: commit 4f5c69f84ed844a7785d258d0370fefd446a6278, rama codex/uwb-ch9-antenna-design. Banda objetivo 7.7376–8.2368 GHz, centro 7.9872 GHz, referencia 50 ohmios. Modelos de material provisionales, sin laminado de fabricante confirmado.

## Modelos y delegación

El coordinador es la sesión Codex actual: la configuración solicita GPT-6 Astra Medium pero no hay verificación del selector ni mecanismo para cambiar el modelo principal en esta sesión. No se certifica Astra activo.

La herramienta de agentes aceptó y ejecutó tres roles con selección explícita:
- rf_designer: gpt-6.1-sol, high; revisión geométrica y propuesta de lanzamiento.
- em_solver: gpt-6.1-sol, high; diagnóstico de solver y especificación EM.
- validator: gpt-6-luna, high; auditoría independiente y reproducción de pruebas, sin modificar resultados.

Estas identidades son las seleccionadas en la herramienta; no hay telemetría adicional del backend. No se lanzaron agentes anidados.

## Resultados geométricos

| Diseño | Geometría nominal | Estado | S11 ≤ −6 / −10 dB en toda la banda |
|---|---|---|---|
| P01 | Rectángulo 11.421267 × 8.280016 mm | GEOMETRY_ONLY | No evaluable |
| P02 | Mismo rectángulo, ranura U de 0.35 mm | GEOMETRY_ONLY | No evaluable |
| P03 | Hexágono radio 6.053271 mm, ranura hexagonal radio 1.1 mm | GEOMETRY_ONLY | No evaluable |

Placa común 26×26 mm; FR4 genérico epsilon_r=4.4, tan_delta=0.017, h=1.6 mm. El dimensionado analítico no demuestra resonancia ni adaptación. Alimentaciones dentro del metal; ranuras contenidas y continuidad revisadas. Falta confirmar fabricación, tolerancias, pila y lanzamiento físico. Los círculos de alimentación son marcadores y las capas SLOT requieren sustracción al importar.

## Evidencias y reproducción

- `python -m unittest discover -s tests -v` desde antenna_design: cuatro pruebas pasan, también reproducidas por el auditor.
- `python designs.py --out outputs`: tres DXF, tres SVG y manifest. Las exportaciones son exclusivamente geometría.
- [Manifest](../outputs/manifest.json), [RF](first_campaign_rf.md), [auditoría](first_campaign_validation.md), [diagnóstico EM](first_campaign_em.md).
- El aviso de caché ezdxf no afecta a los archivos exportados ni al resultado de las pruebas.

No hay ganancia, eficiencia, campos complejos ni retardo de grupo radiado disponibles. No inferir estas métricas de S11 ni del modelo de línea de transmisión. Una primera ejecución tampoco certificará convergencia espacial sin estudio adicional.

## Próximo experimento y continuidad

Resolver la instalación verificable de openEMS/CSXCAD con versión registrada. Revisar la especificación EM del P01 original, su puerto concentrado aproximado y presupuesto antes de ejecutar una sola simulación con espectro 7.5–8.5 GHz. Guardar S11 complejo, configuración, versión, materiales, log temporal, criterio de parada y consumo; incluir los extremos exactos de canal 9 al evaluar cobertura. Solo después considerar un cambio de posición del feed, conservando material y dimensiones.

La campaña inicial queda bloqueada. Contador de rondas automáticas: cero. No se programa ni inicia ninguna simulación adicional. No hay herramienta de automatización Codex disponible en esta sesión; [preparación manual](continuation_setup.md). Próxima ejecución: ninguna. Revisar y resolver el bloqueo antes de activar continuidad.

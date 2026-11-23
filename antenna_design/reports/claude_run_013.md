# Ronda Claude 013: verificación de malla de US0 (rechazada)

- **ID del experimento:** US0_FINE_OPENEMS_013.
- **Fecha:** 2026-11-04, de 20:18 a 20:35 UTC aproximadamente.
- **Ronda:** 13/40.
- **Orquestador:** `claude-opus-5-5`; ha auditado `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`, sin convergencia establecida (solo dos mallas).
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Regla fijada de antemano
La regla está en [`claude_run_012.md`](claude_run_012.md): se acepta si |cambio del peor caso| < margen de la malla base (0,15 dB) y la malla fina sigue ≤ −6 dB. **RESULTADO: RECHAZADA.**

## Datos
- Mismo modelo que 012; solo cambia la malla (perfil `fine`).
- Celdas: 4,65 M. Tiempo: **185 s de pared** con 2 CPU (unos 171 Mcell/s). RSS: 0,85 GB. Pasos: 5880. Energía: −50,3 dB.
- Comparación de mallas: [`mesh_comparison.json`](../em/US0_FINE_OPENEMS_013/mesh_comparison.json).

| | Malla base (012) | Malla fina (013) |
|---|---|---|
| Peor S11 en el canal | −6,15 dB | **−5,70 dB** (24 de 501 muestras por encima de −6 dB, desde 8,214 GHz) |
| Mejor S11 | −9,28 dB | −8,60 dB |
| Máximo de Re(Zin) | 96,4 Ω en 7,615 GHz | 96,4 Ω en 7,62 GHz |
| Eficiencia de radiación | 0,842–0,855 | 0,843–0,856 |
| Ganancia realizada en broadside | 4,65–5,39 dBi | 4,49–5,29 dBi |
| Retardo radiado copolar (diagnóstico) | 0,245 ns, rizado de 31 ps | 0,249 ns, rizado de 37 ps |

- El peor caso cambia +0,44 dB. El desplazamiento medio es de +0,58 dB y siempre **hacia peor adaptación**, como en P01_R2.
- El campo lejano (eficiencia y directividad) se mantiene estable entre mallas.

## Conclusión
- **US0 no cumple −6 dB en todo el canal con la malla fina.**
- Su papel en la serie es solo de referencia geométrica: se queda en US0, sin optimizar.

## Cambio de método (validado)
- **Malla de evaluación de la serie:** el perfil `fine`, igual para todas las variantes, con un coste de unos 3 minutos.
- **Verificación de convergencia de un candidato:** un perfil nuevo `xfine`, a 0,7 de la malla fina (xy ≈ 0,245 mm, borde de 0,12 mm, unos 12 M celdas). La regla y su tolerancia se fijarán por escrito antes de lanzarlo, a partir de la sensibilidad medida.
- **Las diferencias de menos de unos 0,7 dB entre variantes no se dan por resueltas.** También hay que comprobar que la ordenación de variantes no cambie con la malla.

## Siguiente paso
Ronda 014: US1 (US0 más U-slot), con la malla fina y los mismos NF2FF y excitación. Se compara contra US0 con malla fina.

## Estado
- Ronda 13/40.
- Campaña ACTIVE.
- **CONTINUE.**

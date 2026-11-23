# Ronda Claude 011: refinamiento de malla de P03_MS5 — NO LANZADO (regla de presupuesto)

- **Ronda:** 11/40, routine. **Orquestador:** Sonnet 5.5, no Opus (anotado). Sin subagentes (no se ha ejecutado FDTD, no hay nada que auditar).
- **Solver:** los bindings no importaban al empezar; se repitió `claude_cloud_setup.sh` una vez y funcionan: openEMS 0.37.0.post1.dev40+g5fecbb58d, CSXCAD 0.7.0.post1.dev8+g626b99f2f.
- **Estado EM:** `EM_NOT_RUN` en esta ronda. 0 FDTD. No se inventa ningún S11.

## Propuesta
Según la hipótesis del run 010: refinar la malla de MS5 (única variable `--mesh fine`; misma geometría, FR4, alimentación, excitación fc 2,5 GHz y NF2FF de 11 puntos). Es el primer refinamiento de MS5 (límite: 2).

## Resultado del `prepare` (borrado después; no queda `em/` nuevo)
`python em/patch_openems.py prepare --variant variants/P03_MS5.json --out em/P03_MS5_FINE_OPENEMS_011 --mesh fine --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9`
- 5,51 M celdas nodales, ~19 405 pasos; RAM estimada ×2 ≈ 1,94 GB (cabe).
- Tiempo estimado por la regla del código: **2660 s** (peor caso 4113 s) > **1800 s** → `launch_allowed_by_budget: false`. La regla aborta y no se salta.

## Observación para el propietario
La regla usa 53 Mcelda·paso/s (medido en P01_OPENEMS_002). En el run 010 se midió 2,263 M celdas × 11 388 pasos / 191 s ≈ **135 Mcelda·paso/s**. Con esa cifra la malla fina tardaría ≈ 1000 s (sin contar el sobrecoste NF2FF, no medido). No he cambiado la regla ni el límite: son decisión humana (CLAUDE.md: «nada de simulaciones largas sin consentimiento»).

## Decisión humana requerida (una de):
1. Autorizar recalibrar la tasa de la regla a ~135 Mcelda·paso/s (límite 1800 s intacto) y repetir el refinamiento de MS5.
2. Autorizar explícitamente una ejecución de ~45 min.
3. Preferir otra vía (p. ej. P02 con fc 2,5 GHz, de poco valor: P02_MS1 no adapta en el canal).

## Riesgos
Sin cambios respecto al run 010: incertidumbre de puerto ≈ ±1,5 dB > margen 0,50 dB, malla única, FR4 provisional, SMA no modelado, sin validator. Mejor candidato vigente: P01_R2 (HFSS) y P03_MS5 (peor caso −6,50 dB, no declarado viable).

## Estado
STOPPED para esta ronda por «hace falta una decisión humana». Campaña `ACTIVE`; las rondas siguientes repetirán este bloqueo hasta que el propietario decida.

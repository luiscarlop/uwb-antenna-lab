# Ronda Claude 012: serie U-slot, referencia US0

- **ID del experimento:** US0_OPENEMS_012.
- **Fecha:** 2026-11-04, aproximadamente de 19:55 a 20:40 UTC. Sesión del propietario, ronda 12/40.
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:** `rf-designer` y `em-solver` trabajaron en paralelo con ficheros separados; después, `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`. La convergencia de malla es NOT_ESTABLISHED.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Dirección del propietario (2026-11-04)
- Priorizar los diseños U-slot inspirados en el artículo EuCAP. Son **una aproximación de investigación, no una reproducción**: el artículo usa un parche apilado con cavidad, parásito y peine de ranuras.
- Variar una dimensión cada vez, manteniendo la alimentación y el material.
- Buscar S11 ≤ −6 dB en todo el canal, con −10 dB como objetivo.
- Comprobar la convergencia antes de aceptar una mejora.
- Evaluar la eficiencia y el retardo radiado cuando haya campos.
- **Presupuesto:** las ejecuciones de convergencia con malla fina pueden durar hasta 2700 s (opción `--owner-long-convergence`). La tasa de estimación no cambia. Con esto se resuelve el bloqueo de la ronda 11.

## Serie USLOT_PROBE_H207
Ficheros: [`variants/uslot_family.py`](../variants/uslot_family.py), [`US0.json`](../variants/US0.json) y [`US1.json`](../variants/US1.json).

Común a toda la serie:
- **Alimentación:** sonda vertical concentrada de 50 Ω en x = 0.
- **Material:** FR4 homogéneo, con εr 4,4, tanδ 0,017 y **h = 2,07 mm**. El espesor es el del artículo; el resto es una aproximación de su pila de 6 capas.
- **Placa:** 26 × 26 mm.
- **Cobre:** 35 µm.

Del artículo solo se toman h, εr, tanδ y la resonancia a lo largo de y. **Ninguna dimensión del parche ni de la ranura procede del artículo.**

Las variantes de la serie:
- **US0 (referencia, sin ranura):** parche de 11,4213 × 7,67 mm; sonda en (0; −2,608) mm, con s/L = 0,34. L sale de Hammerstad con un factor empírico k_cal = 0,934 calibrado con P01_R2.
- **US1:** US0 más una U abierta hacia +y, con Wu 4,4 mm, Lu 3,2 mm, t 0,8 mm e y0 −0,7 mm. Son hipótesis de diseño.

Cambios en el script (`em/patch_openems.py`):
- la ruta de sonda funciona con h ≠ 1,6 mm;
- se añaden líneas de relleno de malla para la sonda;
- la compuerta `PORT_INVALID` también se aplica al puerto concentrado;
- nuevo criterio de desenrollado de fase para el retardo (pasos < π/2 y |H| ≥ −20 dB);
- nueva opción `--owner-long-convergence`.

Comprobaciones: 54 tests OK. Los 7 XML congelados no cambian.

## Recursos
- 1,77 M celdas, con estimación de 334 s.
- **Real:** 62 s de pared y 51 s de motor, a **143 Mcell·paso/s**. La tasa de 53 Mcell·paso/s de la regla es conservadora por un factor de unos 2,7.
- RSS de 371 MiB, 4042 pasos y energía hasta −51,1 dB.

## Resultados
Ficheros: [`result.json`](../em/US0_OPENEMS_012/result.json) y [`nf2ff_summary.json`](../em/US0_OPENEMS_012/nf2ff_summary.json).

**Adaptación:**
- **S11 en el canal:** peor −6,15 dB (en 8,2368 GHz) y mejor −9,28 dB (en 7,955 GHz).
- **Cumple −6 dB en las 501 muestras, con un margen de solo 0,15 dB.** No cumple −10 dB.
- El máximo de Re(Zin) es de 96,4 Ω en 7,615 GHz.

**Campo lejano** (balance de potencia verificado: `validator` lo recalculó desde los volcados, con Prad igual a 0,9994 veces el flujo de la caja):
- Eficiencia de radiación de **0,84–0,86**.
- Directividad en broadside de 6,5–6,7 dBi.
- **Ganancia realizada en broadside de 4,6–5,4 dBi.** El haz apunta a broadside.

**Retardo de grupo radiado** (broadside, copolar E_φ con φ = 0; solo DIAGNÓSTICO):
- Media de 0,245 ns y **rizado de 31 ps en el canal**. La fase se desenrolla de forma fiable.
- La referencia es a_inc en el puerto. Si se usara U, la media cambiaría unos 75 ps.
- La componente cruzada es ruido y está marcada como UNRELIABLE.

## Reservas
1. **(Media)** El margen de 0,15 dB es inferior a la sensibilidad de malla observada en P01_R2 (0,24 dB). Además, la malla base solo tiene 8 celdas en el sustrato. **US0 no se usa como referencia hasta tener la malla fina.**
2. El modelo de guía predijo un peor caso de −4 a −5 dB y la simulación EM da −6,15 dB: el modelo no es predictivo.
3. La razón entre celdas vecinas en y es 1,43 (registrada, por debajo de 1,5).
4. El FR4 es homogéneo, no la pila del artículo; la sonda es ideal y el SMA no se modela.

## Siguiente paso
Ronda 013: US0 con `--mesh fine`, manteniendo NF2FF y fc 2,5 GHz. La mejora se acepta si el peor caso cambia menos que el margen y se mantiene ≤ −6 dB. Después vendrá US1 con malla base.

## Estado
- Ronda 12/40.
- Campaña **ACTIVE**.
- **CONTINUE.**

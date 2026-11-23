# Ronda Claude 006: P02 (U-slot) con alimentación microstrip

- **ID del experimento:** P02_MS1_OPENEMS_006.
- **Fecha:** 2026-11-03, 17:50–18:45 UTC aproximadamente, en sesión.
- **Origen:** lo pidió el propietario («simular el U-slot y el hexagonal, con alimentación por línea microstrip acabada en un conector SMA»). Es la ronda 6/40.
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:**
  - `rf-designer` y `em-solver`, en paralelo, cada uno con sus ficheros;
  - después `validator`.
- **FDTD:** 1.
- **Evidencia:** `EM_SIMULATED`, con validez parcial (ver [`VALIDITY.json`](../em/P02_MS1_OPENEMS_006/VALIDITY.json)).
- **Veredicto de `validator`:**
  - conclusión física: **APROBAR CON RESERVAS**;
  - puerto MSL tal como está: **BLOQUEAR**.
- **La campaña pasa a `BLOCKED`**, a la espera de corregir el puerto.

## Propuesta y parámetros
Variante [`variants/P02_MS1.json`](../variants/P02_MS1.json), en estado `GEOMETRY_ONLY` antes de simular:
- **Parche:** 11,4213 × 7,65 mm, con U-slot de 0,5 mm (brazos en x = ±3,14 mm, de y = −0,61 a +2,75 mm) abierta hacia +y.
- **Alimentación:** línea de 50 Ω de 3,02 mm (Hammerstad–Jensen, εeff cuasiestática 3,33), inset de 2,0 mm y muesca con gap de 0,5 mm. La línea va desde el borde de la placa (y = −13 mm), donde se coloca el SMA.
- **Conector:** el SMA se modela como un puerto de 50 Ω en el plano de lanzamiento. El cuerpo del conector no se modela, porque no hay referencia de pieza.
- **Material y placa:** FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm), placa de 26×26 mm y cobre de 35 µm.

Cambios en [`em/patch_openems.py`](../em/patch_openems.py) (commit `e0f1fb4`):
- alimentación `microstrip_inset_edge` con puerto MSL de openEMS;
- malla de polígonos robusta;
- `--nf2ff` para el campo lejano.

001, 004 y 005 se siguen reproduciendo byte a byte.

## Recursos
- Malla base: 1,93 M celdas.
- Estimación: 442 s y 679 MiB (base medida ×2).
- Observado: 251 s de pared con 2 CPU, 6090 pasos, energía hasta −53,6 dB.
- Comando:
  ```
  timeout 1200s taskset -c 0,1 python em/patch_openems.py solve --variant variants/P02_MS1.json --out em/P02_MS1_OPENEMS_006 --nf2ff --nf2ff-points 11
  ```
- Los volcados brutos de NF2FF (unos 39 MB) no se versionan. Su SHA256 está en `nf2ff_raw_dumps.sha256`.

## Métricas válidas
Fichero: [`measplane_reanalysis_50ohm.json`](../em/P02_MS1_OPENEMS_006/measplane_reanalysis_50ohm.json), generado con [`em/msl_measplane_reanalysis.py`](../em/msl_measplane_reanalysis.py).
- En el plano de medida del puerto, con referencia fija de 50 Ω, **|S11| ≈ −0,70 dB en todo el canal**. Es pasivo (|S11| ≤ 0,92). `validator` lo confirmó con un estimador de solo tensión.
- El resultado depende poco de la referencia: con Z_ref entre 35 y 80 Ω, |S11| queda entre −0,50 y −1,14 dB.
- **P02_MS1 no funciona en el canal 9**: no cumple −6 dB ni −10 dB.
- Llevando la impedancia hasta la base del inset con una línea ideal (εeff 3,33–3,65), sale Z ≈ 2 − j(7…12) Ω en f0. El máximo de Re(Zin) cae en 6,98 GHz, que es el borde del rango válido. Eso indica una resonancia por debajo de 7 GHz, **pero no la establece**: la excitación gaussiana (fc = 1 GHz) no cubre por debajo de unos 7 GHz.
- **Campo lejano:** solo son válidos, con reservas, la potencia radiada Prad y la forma del patrón. El máximo está en θ = 35–40° y φ = 90°, y la directividad en broadside va de −2,4 a −7,7 dBi. No es el patrón de un modo TM10: la radiación viene de otro mecanismo (la línea, el borde de la placa o la ranura).

## Errores (invalidan parte de las salidas)
- **Puerto MSL.** La extracción de Z_line y β que hace openEMS está mal condicionada cuando hay una onda estacionaria fuerte (|Γ| ≈ 0,92). Da β con εeff de 4,2–4,65, que se vuelve complejo en el borde de la banda, cuando el estimador de solo tensión da 3,62–3,67.
  - `CalcPort(ref_plane_shift)` reutiliza ese β, y el S11 trasladado al borde de la placa llega a |S11| = 1,26.
  - Quedan **inválidos**: `s11_complex.csv`, `s11_wideband.csv`, las métricas `channel_*` de `result.json` (+0,278 dB), Z_line, las eficiencias, la ganancia, la ganancia realizada y el retardo de grupo radiado.
- **Malla.** Las ranuras y gaps de 0,5 mm se resuelven con celdas de 0,43–0,46 mm. La tira queda en 2,85 mm frente a 3,02 mm nominales, y los brazos efectivos de la U miden 0,67–0,70 mm.
- **Sin verificar:** la representación de la ranura como aire con prioridad 20 se usa aquí por primera vez y no se ha comprobado a nivel de rejilla.

## Siguiente hipótesis
Ronda 007, antes de simular P03:
1. **Corregir el puerto.** Usar una referencia fija de 50 Ω y β estimado solo con las tensiones (o el analítico), con traslado propio del plano de referencia.
2. **Añadir una compuerta** que marque `PORT_INVALID` si max|S11| > 1,02 o P_acc < 0, y un test con onda estacionaria sintética.
3. **Excitación más ancha**, que cubra unos 5,5–9,5 GHz, para localizar resonancias por debajo del canal.
4. **Revisar P03_MS1.** La muesca ocupa 4,02 mm de un lado de 5,2 mm y deja lengüetas de 0,59 mm. Con el aprendizaje de P02, conviene un inset menos agresivo y un parche que no resuene bajo.
5. **Rediseñar P02**, que ya es su segundo refinamiento: reducir el tamaño eléctrico. Tanto la U como la muesca bajan la frecuencia.

**Decisión pendiente del propietario (no bloquea):** la referencia del SMA, si se quiere modelar el conector y no solo su plano de lanzamiento.

## Estado
- Ronda 6/40. Tests: 20 OK.
- Campaña en **BLOCKED**, con motivo: puerto MSL inválido en el plano de lanzamiento.
- P01_R2 sigue pendiente de la revisión HFSS del propietario.
- **CONTINUE**: la ronda 7 corrige la causa del bloqueo.

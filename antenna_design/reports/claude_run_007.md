# Ronda Claude 007: puerto corregido y P03 hexagonal con transformador λ/4

- **ID del experimento:** P03_MS2_OPENEMS_007.
- **Fecha:** 2026-11-03, de 18:37 a 19:20 UTC aproximadamente. Ronda 7/40, en la sesión del propietario.
- **Orquestador:** `claude-opus-5-5`.
- **Subagentes:**
  - `em-solver` corrigió el puerto y después añadió la alimentación λ/4;
  - `rf-designer` revisó P03, en paralelo y con ficheros separados;
  - `validator` auditó.
- **FDTD:** 1.
- **Veredicto de `validator`:**
  - puerto corregido: **APROBAR CON RESERVAS**, y se levanta el bloqueo para |S11|, la potencia aceptada y las eficiencias;
  - 007: **APROBAR CON RESERVAS** (`EM_SIMULATED`, malla única).

## 1. Corrección del puerto MSL
Commit `559e428`. Ficheros: [`em/port_postprocess.py`](../em/port_postprocess.py) y [`tests/test_port_postprocess.py`](../tests/test_port_postprocess.py).

- **Qué cambia:**
  - la referencia es fija, de 50 Ω;
  - β se estima con las tres sondas de tensión, mediante cos(βΔ) = (U_A + U_C)/(2·U_B), con un valor analítico de reserva;
  - la corriente se toma como I = media(I_A, I_B)/cos(βΔ/2);
  - el plano de referencia se traslada al de lanzamiento sobre una línea ideal de 50 Ω;
  - nueva compuerta `PORT_INVALID`;
  - nueva opción `--excitation-fc-hz`;
  - nuevo modo `reprocess`.
- **Comprobaciones:** 38 tests OK. Los XML de 001 y de 003 a 007 se regeneran con el SHA idéntico.
- **006 reprocesado** ([`P02_MS1_OPENEMS_006_REPROC_R7`](../em/P02_MS1_OPENEMS_006_REPROC_R7/)): pasivo, con |S11| ≈ −0,70 dB en todo el canal. Confirma que P02_MS1 no está adaptado.
- **Reservas de `validator`:**
  - la compuerta solo detecta errores groseros, no un β o una Z_line sesgados;
  - los tests no cubren una línea con pérdidas ni una Z_line distinta de 50 Ω;
  - la fase, Zin y el retardo en el plano de lanzamiento siguen sin ser fiables.

## 2. P03_MS2
Variante [`variants/P03_MS2.json`](../variants/P03_MS2.json), en estado `GEOMETRY_ONLY` antes de simular:
- **Parche:** hexágono de r = 4,8 mm centrado en (0; +3,3) mm, con ranura hexagonal de r = 1,1 mm.
- **Alimentación:** línea de 50 Ω de 3,02 mm desde el borde de la placa, donde va el SMA, y transformador λ/4 de 0,72 × 5,22 mm (unos 97 Ω). El transformador parte de la hipótesis R_borde = 110–320 Ω.
- **Sin muesca.** El detalle mínimo de cobre es de 0,72 mm.
- **Material y placa:** FR4 provisional (εr 4,4, tanδ 0,017, 1,6 mm) y placa de 26 × 26 mm.

## 3. Recursos
- Celdas: 2,22 M; razón de malla ≤ 1,4.
- Estimación: 827 s y 778 MiB.
- Observado: **434 s** de pared con 2 CPU, RSS de 456 MB, 10 506 pasos y energía hasta −50,3 dB.
- Excitación con fc = 2,5 GHz, rango válido de 5,46 a 10,5 GHz.
- Comando:
  ```
  timeout 1300s taskset -c 0,1 python em/patch_openems.py solve --variant variants/P03_MS2.json --out em/P03_MS2_OPENEMS_007 --nf2ff --nf2ff-points 11 --excitation-fc-hz 2.5e9
  ```
- Los volcados NF2FF brutos no se versionan; su SHA256 está en `nf2ff_raw_dumps.sha256`.

## 4. Resultados
Ficheros: [`result.json`](../em/P03_MS2_OPENEMS_007/result.json), [`s11_measplane.csv`](../em/P03_MS2_OPENEMS_007/s11_measplane.csv) y [`nf2ff_summary.json`](../em/P03_MS2_OPENEMS_007/nf2ff_summary.json).

**Adaptación** (plano de medida, referencia fija de 50 Ω; el puerto es válido y pasivo):

| Frecuencia | S11 |
|---|---|
| 7,7376 GHz | −3,20 dB |
| f0 (7,9872 GHz) | −6,35 dB |
| 8,2368 GHz | −10,53 dB |
| mínimo, en 8,25 GHz | −10,55 dB |

- **No cumple −6 dB ni −10 dB en todo el canal.**
- El mínimo de |S11| está unos 260 MHz por encima de f0. Es el único indicador de frecuencia que no depende del plano de referencia. El máximo de Re(Zin) cambia de sitio según el plano: 8,395 GHz en el de medida y 7,885 GHz en el de lanzamiento.

**Campo lejano** (`EM_SIMULATED_FAR_FIELD`, balance de potencia correcto):

| Magnitud | Valor |
|---|---|
| Eficiencia de radiación (Prad/P_acc) | 0,69–0,74 |
| Eficiencia total | 0,36 (7,74 GHz) → 0,68 (8,24 GHz) |
| Directividad en broadside | 3,1 → 4,6 dBi |
| **Ganancia realizada en broadside** | **−1,4 dBi (7,74 GHz) → +2,9 dBi (8,24 GHz)** |
| Máximo | ≈ 7 dBi en θ = 30–35°, φ = 270° |

- El haz está inclinado hacia −y, el lado de la alimentación. Es plausible por la radiación de la línea y por la placa asimétrica, pero no está demostrado.
- La polarización cruzada en el corte φ = 0 está en torno a −64 dB.

**Retardo de grupo radiado:** es solo **un diagnóstico**. El β por tramos produce un salto espurio de 0,46 ns entre 7,84 y 7,89 GHz. Con un β analítico suave el retardo es monótono, de 0,244 a 0,325 ns. **No hay que citar el rizado.**

## 5. Reservas
1. **β por tramos (gravedad alta según `validator`).** Para la misma línea, el estimador da εeff de 4,3–5,1, frente a 3,65 analítico, y el 29 % de las muestras del canal cae en el valor de reserva. Además, Z_line ≈ 54 Ω frente a la referencia de 50 Ω, lo que da un error de unos ±0,04 en |Γ|. El valor de −10,5 dB en 8,2368 GHz queda, por tanto, entre unos −9 y −12 dB. El fallo de −6 dB es robusto.
   - Reparación pendiente: usar un εeff único y suave, marcar `PORT_PHASE_UNRELIABLE` cuando haya más de un 10 % de muestras en la reserva, y calibrar Z_line.
2. La eficiencia la calcula el propio solver y el balance no se cierra de forma independiente. Integrar con 4 cortes en φ cuadra con Prad dentro de un ±6 %.
3. Malla única, así que no se ha establecido la convergencia. El FR4 es provisional. El cuerpo del SMA no se modela.

## 6. Comparación de los diseños con alimentación microstrip
| Diseño | Peor S11 en el canal | Mejor S11 en el canal | Ganancia realizada en broadside |
|---|---|---|---|
| P02_MS1 (U-slot, inset) | −0,70 dB | −0,73 dB | no válida (antena desadaptada) |
| **P03_MS2 (hexágono, λ/4)** | **−3,20 dB** | **−10,53 dB** | **−1,4 … +2,9 dBi** |
| P01_R2 (sonda, referencia) | −6,29 dB (malla fina) | −16,7 dB | sin campo lejano |

## 7. Siguientes hipótesis (no son resultados)
- **P03_MS3:** escalar el radio de 4,8 a unos 4,96 mm (+3 %, con f ∝ 1/r a partir del mínimo de 8,25 GHz) para centrar el mínimo en f0. Mantener la ranura y revisar el transformador. Antes, conviene desembeber hasta el borde del parche y corregir la estimación de β.
  - El ancho relativo del canal (6,25 %) es exigente con FR4 de 1,6 mm. Puede que no se cubra entero incluso centrado (Q del orden de 13 en P01).
- **P02:** repetir con excitación ancha (fc = 2,5 GHz) para localizar de verdad la resonancia; después, reducir L o la U-slot y usar un inset menos profundo.

**Decisión pendiente del propietario:** la referencia del SMA, si se quiere modelar el conector.

## Estado
- Ronda 7/40. Tests: 38 OK.
- La campaña pasa de `BLOCKED` a `ACTIVE`: la causa del bloqueo está corregida, con reservas.
- P01_R2 sigue pendiente de la revisión HFSS.
- **CONTINUE.**

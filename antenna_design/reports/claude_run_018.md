# Ronda Claude 018: verificación de convergencia de US3 (malla xfine)

- **ID del experimento:** US3_XFINE_OPENEMS_018.
- **Fecha:** 2026-11-05, de 08:28 a 09:15 UTC aproximadamente. Ronda 18/40.
- **Orquestador:** `claude-opus-5-5`, comprobado con `get_session` como exige la nueva regla del ciclo.
- **FDTD:** 1, auditada por `validator`.
- **Evidencia:** `EM_SIMULATED`, sin NF2FF.
- **Veredicto de `validator`:** **APROBAR CON RESERVAS**.

## Decisión del propietario
El 2026-11-05 el propietario autorizó unos 75 minutos para esta verificación. Otra sesión ya había subido ese mismo día el límite de convergencia a 4000 s (commit `415c231`). La estimación de la regla, 3747 s a 53 Mcell·paso/s, cabe en ese límite, así que no hizo falta ampliarlo más.

## Ejecución
- **Modelo:** US3 sin cambios, con el perfil `xfine` (la malla fina × 0,7) y fc = 2,5 GHz. Las dos ejecuciones (fina y xfine) son idénticas salvo la malla.
- **Tamaño:** 13,86 M celdas.
- **Recursos:** **1915 s de pared** (unos 75 Mcell/s en esta malla grande), 9945 pasos, energía hasta −50,85 dB, RSS de 1,97 GB y 2 CPU.

## Resultado frente a la regla fijada de antemano
La regla está en [`claude_run_016.md`](claude_run_016.md). El fichero es [`mesh_comparison.json`](../em/US3_XFINE_OPENEMS_018/mesh_comparison.json).

| | Malla fina (016) | xfine (018) |
|---|---|---|
| Peor S11 en el canal | −6,65 dB | **−5,78 dB** (8,2368 GHz; 13 muestras por encima de −6 dB) |
| Mejor S11 en el canal | −13,64 dB | −11,82 dB |
| Banda de −6 dB | 7,685–8,265 GHz | 7,700–8,220 GHz |

- Cambio del peor caso: +0,88 dB.
- |ΔΓ| máximo: 0,078.
- Desplazamiento del borde superior de la banda: −45 MHz.

**Veredicto: MESH_SENSITIVE (cambio entre 0,5 y 1 dB). US3 NO se acepta.**

## Diagnóstico: la sonda ideal no converge
- Con el modelo de guía [`fit_patch_circuit.py`](../em/fit_patch_circuit.py) (ficheros `em/circuit_fits/*_fit_7to9GHz.json`):
  - la resonancia del parche apenas cambia entre mallas: fr ±4 MHz y R de 141,8 a 143,1 Ω;
  - la inductancia serie de la sonda **crece en cada refinamiento**: US0 1,656 → 1,735 nH, US3 1,826 → 1,971 nH, P01_R2 1,232 → 1,307 nH.
- **Prueba directa de `validator`:** si a Zin se le resta una inductancia serie, la diferencia entre mallas en el canal baja de |ΔΓ| = 0,078 a **0,007** en US3. En US0 baja de 0,041 a 0,005 y en P01_R2 de 0,052 a 0,003. **Todo el cambio de malla es inductancia de la sonda.**
- **Escala con la celda:** ΔL ≈ (μ0·h/2π)·ln(Δ_ant/Δ_nuevo). En US3 el valor esperado es 0,145 nH y el observado 0,146 nH. En US0 y P01_R2 coincide el orden de magnitud.
- **Por qué pasa:** el puerto `LumpedPort` de openEMS (`ports.py`, líneas 249–285) es un elemento de una sola arista, sin radio físico. Su radio efectivo depende del tamaño de celda, así que su inductancia crece como ln(1/Δ) **sin límite**.
- **Conclusión:** con una sonda ideal, pedir que S11 converja es un problema mal planteado. La resonancia del parche sí converge; la adaptación no puede converger con este modelo de sonda.
- **Reservas:** el ajuste usa una rejilla gruesa en Q (paso 0,25) y fr (paso 2 MHz), y la escala se ha comprobado con pares de mallas, no con una regresión.

## Consecuencias para la campaña
1. Ningún resultado de adaptación con la sonda ideal se puede declarar convergido. Esto afecta a P01_R2 (candidato HFSS), US0 y US3. El margen de P01_R2 (0,29 dB) es especialmente frágil.
2. **Próximo paso de método:** una sonda de **radio físico**. Sería un cilindro metálico del diámetro del pin, entre la masa y el parche, con el puerto en un hueco de la masa (un `AddLumpedPort` corto) o un puerto coaxial. La malla debe resolver ese radio (Δ ≲ r/2) y se comprueba con dos mallas.
3. Hace falta **el diámetro del pin o la referencia del conector**, que debe dar el propietario. La campaña de microstrip (P03_MS*) no tiene este problema de sonda, pero sí la incertidumbre de su puerto MSL.

## Estado
- Ronda 18/40. Campaña ACTIVE.
- **STOP en esta ronda**: hace falta que el propietario decida la sonda física (diámetro del pin o modelo de conector).

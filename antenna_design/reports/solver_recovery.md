# Recuperación del solver y primera ejecución P01 — 2026-11-03

## Persistencia y alcance

Los commits ef4b9cd y 069b30e se subieron mediante push normal a codex/uwb-ch9-antenna-design. Un fetch posterior confirmó 069b30ee952db66827f45303064299dab0881116 y la presencia de informes y exportaciones. La nueva instalación comenzó solo después de esa verificación. No hubo force push, cambios en master, PR, API facturada ni activación de automatizaciones.

## Instalación y ejecuciones realmente verificadas

Instalación sin GUI en /workspace/openems-install, dependencias en /workspace/openems-deps y fuentes oficiales fijadas en /workspace/openems-source. Debian13.6 x86_64, Python3.12.14, GCC14.2. Véase [receta, versiones, hashes y logs](solver_installation.md). Los binarios locales deben reconstruirse si desaparece el entorno; la receta y evidencias se conservan en Git, no los binarios.

1. CSXCAD importado: 0.7.0.post1.dev1+g626b99f2f.
2. openEMS importado: 0.37.0.post1.dev1+g5fecbb58d.
3. Binario FDTD ejecutado y bibliotecas resueltas.
4. Ejemplo oficial Rect_Waveguide ejecutado: 1430 pasos, energía −60.3882 dB, 201 frecuencias complejas. Geometría/excitación/malla oficiales conservadas; se adaptaron rutas, salida sin GUI y dos hilos. Error máximo de impedancia real respecto a referencia TE10 0.9713%. Esta guía de prueba no es un diseño de antena fuera del canal9.
5. Una única simulación P01 real, sin relanzamiento. Ninguna otra simulación de antena.

## P01: resultados y límites

P01 original, placa/masa26×26mm, parche11.421267×8.280016mm, FR4 provisional epsilon_r4.4, h1.6mm, tan_delta0.017 a f0; pérdida dieléctrica mediante conductividad constante. Cobre representado por láminas conductoras35µm, sigma58MS/m. Puerto concentrado ideal50Ω entre masa/parche; no conector coaxial físico. PML_8 en seis caras. Malla suavizada; proyecto nativo y parámetros en [P01_OPENEMS_001](../em/P01_OPENEMS_001/).

| Métrica | Resultado real |
|---|---|
| Intervalos de malla / posiciones nodales solver | 1,795,680 / 1,841,790 |
| CPU / pared / pico RSS | dos núcleos; 142.88s; 333,300KiB (~325.5MiB) |
| Terminación | exit0, sin timeout; 7587 pasos, energía −50.48dB |
| Paso temporal real / duración simulada | 5.00217e−13s / aproximadamente3.795ns |
| S11 complejo | 1003 frecuencias7.5–8.5GHz; 501 dentro del canal, extremos exactos incluidos |
| Mejor S11 en canal | −7.628416dB en7.7376GHz |
| Peor S11 en canal | −1.941491dB en8.2368GHz |
| Requisito ≤−6dB en toda banda | NO CUMPLE en los puntos evaluados |
| Objetivo ≤−10dB en toda banda | NO CUMPLE en los puntos evaluados |
| Convergencia espacial | NO ESTABLECIDA: una sola malla |

[CSV complejo](../em/P01_OPENEMS_001/s11_complex.csv), [curva derivada](../em/P01_OPENEMS_001/s11.png), [resumen numérico](../em/P01_OPENEMS_001/result.json). El criterio de energía temporal se cumplió; no prueba independencia temporal/espectral ni espacial. La cuadrícula DTFT de1MHz es evaluación densa, no resolución demostrada: 1/T de la señal registrada es aproximadamente263.5MHz. No hay garantía entre muestras. El centro exacto7.9872GHz no pertenece a la cuadrícula actual, aunque sí ambos extremos. La clave de preflight denominada Courant upper bound fue una estimación Yee, no cota del método temporal real de openEMS; conservar ambos valores para trazabilidad.

No se registraron campos lejanos: no hay resultados de ganancia, eficiencia o retardo de grupo radiado. El estado EM_SIMULATED acredita ejecución, no validación HFSS ni fabricación.

## Auditoría independiente y modelos

RF Designer y EM Solver se ejecutaron con selección explícita GPT-6.1 Sol High; Validator con GPT-6 Luna High. La sesión coordinadora no permite certificar selección Astra Medium; no se afirma que estuviese activo.

Validator revisó el XML y su hash antes de lanzar P01. Tras la ejecución reconstruyó el puerto en un directorio temporal y ejecutó solo CalcPort sobre las trazas port_ut_1/port_it_1 guardadas, sin otro FDTD. Las1003 frecuencias y las13 columnas complejas resultaron idénticas al CSV almacenado. Verificó versiones, fuente del ejemplo oficial, energía de parada, recursos y límites. Las cuatro pruebas del laboratorio pasan, también reproducidas por el coordinador. Aviso benigno: caché ezdxf no escribible en HOME.

## Próximo paso

Estado PAUSED; solver funcional y P01 registrado, pero adaptación insuficiente. Antes de optimizar, proponer un experimento separado de convergencia espacial manteniendo geometría/material/puerto y un criterio temporal más exigente para controlar la estabilidad del S11. Si se confirma el comportamiento, estudiar una reducción moderada de longitud y después posición de alimentación, variando un parámetro cada vez; no inferir una dimensión óptima del mínimo actual. Las siguientes ejecuciones requerirán su propio presupuesto y registro.

Rondas automáticas realizadas:0. No hay automatización activa ni próxima ejecución. El historial inicial bloqueado se conserva y se añade esta recuperación; no se reinicia ningún contador ni se borra evidencia.

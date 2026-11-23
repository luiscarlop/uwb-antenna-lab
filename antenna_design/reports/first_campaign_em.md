# Primera campaña: diagnóstico EM y especificación P01

Fecha UTC: 2026-11-03. Rama verificada: `codex/uwb-ch9-antenna-design`.
**Resultado: EM_NOT_RUN; P01 permanece GEOMETRY_ONLY; cero simulaciones FDTD.**
No hay valores de S11, impedancia, eficiencia, ganancia ni retardo de grupo.

## Disponibilidad observada

El registro reproducible es [solver_diagnosis.json](../em/solver_diagnosis.json).
Python 3.12.14: `import openEMS` e `import CSXCAD` fallan con
`ModuleNotFoundError`; no existen ejecutables openEMS/AppCSXCAD/Octave ni gestores
conda/mamba/micromamba en PATH. No se puede atribuir versión a software ausente.

La comprobación acotada de instalación sin privilegios encontró:

| Fuente consultada | Evidencia observada |
| --- | --- |
| `pip index versions openEMS` y `CSXCAD` | Ninguna distribución encontrada |
| JSON público PyPI de ambos paquetes | HTTP 404 |
| Índice oficial Debian trixie/main/amd64 | HTTP 200, 9,678,380 bytes; ningún paquete cuyo nombre contenga openems/csxcad |
| Tutorial Python oficial openEMS | HTTP 200; referencia recuperada y hash conservado |

El índice comprimido Debian tiene SHA256
`7778d3e3f303b7ddb8ce0fe7c8d57473a076c6bf2e8f241f75421d2396352498`.
El tutorial recuperado tiene SHA256
`48745681b3b4b09a9a182a2e257f318714fa1210fec0d0350f88ba63dd3686ac`.
Su cabecera menciona pruebas con openEMS v0.37/Python 3.14; esto describe el
tutorial, **no software instalado aquí**. Los hashes fijan la evidencia observada;
las URLs de índices/master pueden cambiar en el futuro.

No se intentó una compilación de C++/bindings ni una instalación de sistema.
Estas búsquedas no prueban que toda distribución externa sea imposible; sí que
no hay una vía binaria inmediata identificada en las fuentes comprobadas.
Se detuvo el diagnóstico dentro del presupuesto de la primera campaña.

Antes de acceder a red se leyó la skill Cloud y su referencia de networking,
se consultó environment_status y `/etc/codex/network-policy.json`: política
restringida/enforced, hosts de gestores de paquetes y GitHub permitidos,
vpn_configured=false. Las consultas se realizaron preservando proxy/CA con el
escalado de sandbox necesario para alcanzar el proxy. No hubo API facturada.

## Modelo declarativo preparado, sin validar en solver

[p01_model_spec.json](../em/p01_model_spec.json) contiene unidades, geometría
proveniente de `designs.py` con SHA256, materiales, alimentación y controles.
[p01_mesh.csv](../em/p01_mesh.csv) conserva cada línea propuesta de malla.
Son una especificación y una tabla de coordenadas; no son archivos nativos
openEMS XML ni evidencia de ejecución. [prepare_p01.py](../em/prepare_p01.py)
los reproduce sin importar o arrancar un solver.

- P01 rectangular centrado, PCB/ground finito 26 × 26 mm; sustrato h=1.6 mm.
- FR4 genérico provisional: eps_r=4.4, tan_delta=0.017 en 7.9872 GHz.
  Se propone conductividad dieléctrica constante calculada a f0; por tanto
  tan_delta(f)=tan_delta(f0)·f0/f. No es un material dispersivo medido.
- Cobre liso provisional sigma=5.8e7 S/m y espesor 35 µm, representado por
  lámina conductora con pérdidas. No incluye rugosidad; la API debe verificarse.
- Puerto ideal vertical de 50 ohmios en el centro de alimentación geométrico,
  de ground a parche. Sustituye el probe de excitación; no modela conector,
  transición coaxial, taladro ni barril de vía de radio finito. Sin deembedding.
- Caja [-35,35] × [-35,35] × [-25,35] mm y PML de ocho celdas en seis caras.
- Malla rectilínea explícita: paso x/y <=0.5 mm, aire z <=0.8 mm,
  ocho celdas en sustrato; bordes y puerto alineados. Falta revisar error de
  borde metálico (regla de tercios) y confirmar absorción PML.
- Excitación gaussiana f0=7.9872 GHz, offset de esquina 1 GHz; muestras
  propuestas de 7.5 a 8.5 GHz cada 1 MHz más los extremos exactos del canal.
  El espaciado de evaluación DTFT de 1 MHz no representa resolución física:
  17.145 ns corresponden a una escala 1/T de aproximadamente 58 MHz y la
  exactitud depende del decaimiento y truncamiento reales del registro.
- Monitor propuesto: energía residual <=1e-5, máximo 30,000 pasos; conservar
  curva real de decaimiento y causa de terminación. No hay convergencia probada.

## Recursos antes de cualquier posible ejecución

La malla propuesta tiene 142 × 141 × 82 = **1,641,804 celdas**.
Una reserva conservadora no medida de 2,048 bytes/celda estima
3,362,414,592 bytes (**3.13 GiB**) para FDTD y estructuras auxiliares;
debe revisarse frente al tamaño real asignado por el solver y monitores.
El contenedor permite 32 GiB y cuota de cuatro CPU; la primera simulación
se limitaría a **dos CPU/hilos** mediante afinidad y configuración del solver.
El límite de Courant calculado es 5.715e-13 s y 30,000 pasos cubrirían como
máximo 17.145 ns. El solver puede elegir un paso menor.

Tiempo: sin benchmark fiable, orden de minutos a decenas de minutos en dos CPU;
no se autoriza automáticamente una ejecución larga por esta estimación.
No hay consumo FDTD observado: CPU/RAM de simulación no disponibles.
No se usó cuota de las <=1 simulaciones de elemento de esta campaña.

## Validación y siguiente experimento

Se ejecutaron ambos scripts y compilación sintáctica con `py_compile`.
Se comprobó de forma independiente el conteo de celdas, orden de líneas,
límites y el puerto sobre malla; esta validación no verifica una API FDTD.

El siguiente experimento concreto es completar una instalación ya compatible de
openEMS+CSXCAD, registrar versiones, implementar esta especificación siguiendo
el tutorial y generar XML para revisión antes de una única ejecución acotada.
Conservar log/energía, pico RAM y CPU, S11 complejo, ondas complejas incidente y
reflejada e impedancia compleja. Evaluar el peor S11 en **toda** la banda exacta
7.7376–8.2368 GHz frente a -6 y -10 dB, no un mínimo puntual.
Una única malla inicial no establece independencia de malla; cualquier
refinamiento debe figurar como experimento posterior dentro de su presupuesto.

No hay monitor NF2FF implementado en esta especificación. Para eficiencia,
ganancia realizada y respuesta temporal faltan balance de potencia y campos
far-field complejos en frecuencia/ángulo, con referencia de fase estable y
muestreo para retardo de grupo radiado. La derivada de fase de S11 no sustituye
el retardo de grupo radiado. No corresponde probar arrays antes del elemento.

Comandos reproducibles y límites del diagnóstico: [em/README.md](../em/README.md).

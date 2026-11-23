# Preparación EM P01

**Estado: EM_NOT_RUN.** No existe solver operativo y estos archivos no son un
proyecto XML openEMS ejecutable. No contienen curvas ni métricas EM.

Desde la raíz del repositorio:

```bash
python antenna_design/em/diagnose_solver.py --out /tmp/solver_diagnosis_local.json
python antenna_design/em/prepare_p01.py --out /tmp/p01_model
```

El diagnóstico opcional de red consulta PyPI, el índice oficial Debian 13 amd64
y el tutorial oficial de parche, con timeout de 30 s y límite 32 MiB por descarga:

```bash
python antenna_design/em/diagnose_solver.py --network --out /tmp/solver_diagnosis_network.json
```

En Cloud se debe leer la política de red y preservar proxy/CA antes de esta última
orden; el sandbox puede requerir escalado para alcanzar el proxy. No cambia la
configuración ni instala paquetes. Las URLs y hashes observados están en
`solver_diagnosis.json`; los índices completos no se conservan.

`prepare_p01.py` importa exclusivamente las definiciones geométricas locales,
calcula una malla explícita y exporta `p01_model_spec.json` y `p01_mesh.csv`.
No importa openEMS, no ejecuta FDTD y no realiza acciones al importarse.
El JSON identifica las decisiones físicas, supuestos, límites de recursos y
salidas que debe implementar un futuro proyecto real. La API de lámina conductora,
el puerto y la malla requieren verificación con openEMS/CSXCAD instalados.

Siguiente paso: usar un entorno con ambas bibliotecas compiladas compatibles con
su Python; registrar versiones y probar importación. Implementar y revisar el
modelo real siguiendo el tutorial enlazado en el JSON. Guardar XML antes de FDTD,
limitar a dos hilos/CPU y fijar un límite de tiempo. Una primera malla nunca
demuestra independencia de malla. El resultado solo se podrá declarar
EM_SIMULATED con ejecución real, campos de puerto complejos, logs y convergencia.

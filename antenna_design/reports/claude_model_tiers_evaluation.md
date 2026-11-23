# Evaluación del desempeño por niveles de modelo (tiers) en el laboratorio de antenas IR-UWB canal 9 y en UWBLab

Informe del evaluador independiente (subagente Sonnet 5.5, sesión del 2026-11-16). Todo lo que sigue se apoya en ficheros de los repositorios y en las transcripciones de la sesión; las rutas están en el Anexo B.

**Convención de etiquetas.** `[D]` = dato verificable en un fichero o transcripción (se indica la fuente). `[I]` = inferencia mía a partir de datos. `[O]` = opinión o valoración cualitativa. Donde algo no se puede medir con la evidencia disponible, se dice «no medible».

---

## 1. Resumen ejecutivo

1. `[D]` El sistema desplegó 44 invocaciones de subagentes antes de este informe: 24 `validator`, 11 `rf-designer`, 7 `em-solver` (todos Sonnet 5.5) y 2 `design-reviewer` (Fable 5.2). El orquestador (Opus 5.5, esfuerzo medium) hizo 730 llamadas a la API en la sesión principal. Todos los modelos de los jsonl coinciden con lo que declaran `CLAUDE.md` y `.claude/agents/*.md`.
2. `[D]` Se ejecutaron 31 rondas FDTD con orquestación Claude hasta la 036 y una más (037) con propuesta de Fable. El mejor diseño por criterio de S11 sigue siendo P01_MS2 (ronda 027/028, antes de Fable): peor S11 en canal −10,42 dB, η 0,73–0,76. Ninguna ronda posterior (29–37) lo supera en S11, eficiencia y ganancia a la vez.
3. `[D]` Fable intervino solo 2 veces (ambas el 2026-11-16, 1 844 s y 109 479 tokens de salida en total, el 4,8 % de los tokens de salida del proyecto). Diagnosticó que PS4 «adapta por pérdidas» y propuso PS5. En la ronda 037, la η pasó de 0,244 a 0,639 como mínimo y el valle desapareció del canal, pero el peor S11 empeoró de −10,66 a −6,87 dB.
4. `[D]` Aciertos y fallos de predicción de Fable en 037: η (0,62–0,70 previsto, 0,639–0,688 real) acertada. Peor S11 (≈ −9,4 dB previsto, −6,87 real) y posición del mínimo inferior (7,93–8,01 GHz previsto, 8,065 real) fallidas. Con una sola ronda prospectiva no hay precisión estimable.
5. `[D]` El `validator` (Sonnet) obligó al orquestador (Opus) a retirar o matizar afirmaciones en al menos 7 mensajes al propietario (13–15 nov) y bloqueó el puerto MSL en la ronda 6. En 24 auditorías no hubo ningún BLOQUEAR sobre una ronda completa, salvo el del puerto MSL.
6. `[D]` Hipótesis pre-registradas: 9 de 24 cumplidas con criterio estricto (37,5 %). Es una medida de lo arriesgado de las hipótesis y de la dificultad del problema, no de la calidad de un modelo.
7. `[I]` Con n = 2 intervenciones de Fable, sin grupo de control, con Fable entrando tarde y con información acumulada, no se puede atribuir causalidad. Lo que sí se afirma: Fable aportó un diagnóstico cuantitativo coherente con los datos, cerró opciones de diseño (ahorrando probablemente rondas) y cometió fallos de predicción numérica.
8. `[D]` UWBLab: el repo clonado es superficial (1 commit). El historial en `docs/PROGRESS.md` (autodeclarado por el orquestador) muestra Fable orquestando, Opus revisando y Sonnet ejecutando. No hay forma de comparar modelos sobre la misma tarea ni de verificar el reparto en el repo.
9. `[D]` Coste: sin precios en los datos. Solo tokens y tiempos de pared (§6).
10. `[O]` Uso recomendado: Opus para decisiones y síntesis, Sonnet para ejecución y auditoría acotada, Fable para asesoría puntual de alto apalancamiento. Para el TFG, documentar con A/B controlado (§7).

---

## 2. Arquitectura del sistema

### 2.1 Roles y modelos `[D]`

Fuente: `/home/user/TFG_Beamforming_FBD/CLAUDE.md`, `.claude/agents/*.md`, `.claude/settings.json`, y los campos `message.model` y `effort` de los jsonl.

| Rol | Modelo | Esfuerzo | Permisos | Verificado en jsonl |
|---|---|---|---|---|
| Orquestador (sesión principal) | Claude Opus 5.5 | medium | todo | 1 548 mensajes con `claude-opus-5-5`; `effort: medium` |
| `rf-designer` | Sonnet 5.5 | high | edita ficheros | `claude-sonnet-5-5` |
| `em-solver` | Sonnet 5.5 | high | edita y ejecuta | `claude-sonnet-5-5` |
| `validator` | Sonnet 5.5 | high | solo lectura y tests | `claude-sonnet-5-5` |
| `design-reviewer` | Fable 5.2 | high | solo lectura | `claude-fable-5-2`; `effort: high` |
| Línea base previa: Codex | GPT-6 Astra (orquestador), Sol (rf, em), Luna (validator) | medium/high | `.codex/` | solo config y reportes; no hay telemetría (el propio informe lo dice) |

45 de los 46 jsonl de subagentes registran `effort: high`; uno registra `medium` (no he identificado cuál es ni por qué).

### 2.2 Reglas de orquestación `[D]`

- Máximo 3 subagentes a la vez; el `validator` solo tras tener resultados; `rf-designer` y `em-solver` no editan el mismo fichero.
- Límites de campaña: máximo 3 geometrías nuevas, 1 FDTD por ejecución, 2 refinamientos por candidato; máximo 2 vCPU en la primera prueba; estimación de RAM, malla y tiempo antes de cada FDTD.
- Hipótesis pre-registradas en `variants/*.json` (`pre_registered_hypothesis`) antes de cada simulación, con regla de decisión. Dos mallas para aceptar un resultado (regla de convergencia por pares de malla).
- Estados de evidencia permitidos (`GEOMETRY_ONLY`, `EM_SIMULATED`, `HFSS_VALIDATED`, `MEASURED`) y prohibición de inventar curvas.
- Flujo de revisión con Fable, decisión del propietario del 2026-11-14: preguntar si se simula ya en HFSS; solo entonces lanzar `design-reviewer` sobre ese diseño concreto; repartir sus correcciones a `rf-designer` y `em-solver`; listar al final de cada mensaje los diseños pendientes de revisión.
- Regla del propietario (2026-11-05): el orquestador debe ser siempre Opus 5.5; si la sesión es otro modelo, no se ejecuta FDTD (`automation_policy.json`, `claude_routine.history`).

### 2.3 Desviaciones respecto del diseño `[D]`

- Las rondas 8–11, 17 y 19 (2026-11-03 y 05) las orquestó Sonnet 5.5 (routine con selector de modelo distinto): sin subagentes, sin `validator` (reportes `claude_run_008.md`… `claude_run_011.md`, `_017`, `_019`). Doce commits llevan `Co-Authored-By: Claude Sonnet 5.5` y corresponden a esas rondas. El 2026-11-05 el propietario impuso Opus.
- En rondas 21–23 los tipos de agente del repo «no estaban disponibles» y el orquestador diseñó y simuló en secuencia (reportes 021–023).
- `design-reviewer` se creó el 2026-11-14 (commit `7647407`), pero el propietario dijo ese día «Aún no quiero que Fable los revise»; se usó por primera vez el 2026-11-16.

### 2.4 Cronología por fases `[D]`

| Fase | Fechas (2026) | Quién | Rondas | FDTD |
|---|---|---|---|---|
| 0. Codex | 03-nov, antes de 11:22 | Astra/Sol/Luna | campaña inicial `CH9-INITIAL` | 1 solve P01 (P01_OPENEMS_001, peor S11 −1,94 dB), solver instalado por Codex; campaña inicial «BLOCKED / EM_NOT_RUN» |
| 1. Opus + Sonnet | 03-nov | Opus, rf/em/validator | 2–7 | 6 FDTD (P01 y puerto MSL) |
| 1b. Sonnet orquestador | 03-nov | Sonnet 5.5 | 8–11 | 3 FDTD (hexágono P03_MS3→MS5; la 11 no lanza FDTD) |
| 2. Opus + Sonnet | 04–05-nov | Opus, rf/em/validator | 12–20 | 6 FDTD (U-slot con sonda ideal; xfine) |
| 3. Opus + Sonnet | 05 y 13-nov | Opus | 21–28 | 8 FDTD; P01_MS2 −10,42 dB |
| 4. Opus + Sonnet | 13–16-nov | Opus (+ propietario) | 29–36 | 8 FDTD; MS4, IN1, PS1–PS4 |
| 5. Con Fable | 16-nov | Opus + Fable | 37 | 1 FDTD (US3_PS5) |

(Recuento de FDTD desde `automation_policy.json`: 31 solves hasta la ronda 36; la 37 suma una más. Rondas sin FDTD: 1, 11, 17, 19, 20.)

---

## 3. Metodología de evaluación

Las métricas se definen con lo que se puede extraer. Cada una lleva su cálculo y sus limitaciones.

| # | Métrica | Cómo se calcula | Limitaciones |
|---|---|---|---|
| M1 | Rondas FDTD por fase | `claude_routine.history[].em_solves_executed` agrupado por rondas | Una ronda no es una unidad de esfuerzo homogénea; las fases tienen problemas distintos |
| M2 | Tasa de hipótesis pre-registradas cumplidas | Recuento de H0/H1/H2 en `variants/*.json` frente a lo que dicen los reportes `claude_run_*.md`; «cumplida solo formalmente» cuenta como no cumplida | Recuento propio; hipótesis de dificultad muy variable; algunas se escribieron esperando que fallaran |
| M3 | Correcciones del validator al orquestador | Handbacks de los 24 jsonl de `validator` y mensajes del orquestador al propietario que dicen «corrijo / retiro» | Solo cuento retractaciones explícitas; gravedad según etiquetas del propio validator, que no usa siempre el mismo formato; las del 03–05 nov, en español, las he buscado con menos exhaustividad |
| M4 | Errores detectados por cada rol | Handbacks de validator y de Fable; correcciones que ellos piden | No hay verdad de campo: un «error detectado» es un error según el detector; no se mide lo que no se detectó |
| M5 | Precisión de predicciones (modelo guía vs EM) por autor | Predicción numérica escrita antes del resultado (JSON de la variante o mensaje del orquestador) frente a `run_numeric.json` y `nf2ff_summary.json` | Los modelos guía no firman autor en los JSON: no puedo separar Opus de Sonnet; Fable solo tiene 1 predicción prospectiva |
| M6 | Tokens y tiempo por invocación y por modelo | Campo `message.usage` de cada jsonl, **deduplicado por `message.id`** (cada bloque de contenido repite el mismo `usage`; sumar sin deduplicar infla ×2 aprox.); duración = último − primer timestamp | Duración incluye esperas (FDTD, tests); caché leída domina; sin precios |
| M7 | Calidad de la propuesta (mejora EM tras la intervención) | Métricas de `run_numeric.json` y `nf2ff_summary.json`, recomputadas por mí desde `s11_complex.csv` y `s11_wideband.csv` | Malla base única en PS4/PS5, FR4 homogéneo, puerto ideal; 037 aún sin `validator` |

Reproducibilidad: los jsonl se procesaron con un script en el directorio temporal de la sesión; los totales de §6 se pueden recomputar de las rutas del Anexo B.

---

## 4. Resultados por tier

### 4.1 Opus 5.5 (orquestación, decisiones, errores propios detectados por otros)

**Volumen `[D]`.** 730 llamadas únicas a la API, 850 926 tokens de salida, 337,3 M de caché leída, 9,7 M de caché creada, 1 568 de entrada no cacheada; 700 llamadas a herramientas, de ellas 538 Bash y 46 lanzamientos de subagentes. 152 commits `ClCo` con `Co-Authored-By: Claude Opus 5.5`. La sesión abarca de 2026-11-03T11:22Z a 2026-11-16T07:06Z (reloj de pared, con largos periodos de inactividad).

**Decisiones propias que los datos respaldan `[D]/[I]`:**
- Fijó una regla de convergencia por pares de malla (|ΔΓ| ≤ 0,03) antes de simular y registró también los fallos: US3_MS3 fine «falla la regla de dos mallas» (ronda 24); P01_MS1 «BOUNDED_SENSITIVITY_PASS (márgenes ajustados)»; P01_MS2 pasa la regla.
- Corrigió el rumbo con datos: después de P01_MS1 (−8,34 dB), subir el transformador de 6,6 a 7,1 mm llevó a P01_MS2 (−10,42 dB, −10,36 fina). Aun así, el modelo guía que usó para elegir 7,1 mm predijo −9,18 dB (error ≈1,2 dB) y el validator lo calificó de «no predictivo» (gravedad alta).
- En la ronda 36 predijo correctamente, antes de simular, que H2 fallaría cerca de 8,17 GHz: el valle de η real quedó en 8,137 GHz (η 0,244).
- El 2026-11-15 (antes de Fable) recomendó cerrar la vía del parásito y quedarse con P01_MS2 («el camino del parásito no ha producido nada mejor que P01_MS2»); el propietario decidió seguir con el parásito enterrado.
- Instrumentó artifacts/gráficas, reportes, estado de campaña y commits por ronda (217 commits `ClCo` en la rama).

**Errores propios detectados por otros `[D]`:**

| Fecha | Detector | Qué se corrigió |
|---|---|---|
| 03-nov | el propio Opus (mensaje de 14:00 UTC) | «Con Q≈13 no se llega a −10 dB» era un límite de su modelo guía, no físico; la ronda 27 (P01_MS2, −10,42 dB) es compatible con esa corrección; no he verificado la Q de P01_MS2 |
| 13-nov | validator (R27) | modelo guía `feed_retune_guide`: −9,18 dB previsto frente a −10,42 real; error medio 2,9 dB dentro del canal; no extrapolar |
| 13-nov | validator (R29, 1 alta, 3 media, 4 baja) | «el pico de 10,3 GHz es el modo de la U» no está respaldado; «H1 cumplida» solo formalmente; «misma malla» → «mismo perfil, 3 celdas en la ranura» |
| 14-nov | validator (R30) | energía final −49,23 dB mal calculada (el log del solver da −51,41 dB); el mismo método estaba en R29 (−50,08) |
| 15-nov | validator (análisis 1×5) | el 22°/18° del informe salía de P01_MS1 y no de P01_MS2, y no estaba guardado; precisión de 2 decimales en rejilla de 5° |
| 15-nov | validator (barrido de paso) | tres afirmaciones falsas en parte: el peor caso no siempre está en el borde superior; el S activo a 30–45° sí depende del paso |
| 15-nov | validator (R31) | «cumple −6 dB» era de una corrida truncada; con el decaimiento completo, −5,96 dB; la «banda de 625 MHz» está casi toda fuera del canal |
| 15-nov | validator (R33) | «invertir la pila arregla la η» era demasiado fuerte (respuesta desplazada 0,9 GHz abajo, η sin medir fuera del canal) |
| 15-nov | validator (R34) | «mejor resultado de la familia U» → «aceptable, no mejor que P01_MS2» |
| 16-nov | validator (R36, 4 media, 4 baja) | JSON de PS4 mezcla datos de la versión no simulada y de la simulada; cifras de banda de la rejilla de 5 MHz en vez de 1 MHz; «adaptación por pérdidas» es correlación, no mecanismo probado |

`[D]` Siete mensajes del orquestador contienen una sección de correcciones explícitas al propietario (11-13T19:21, 11-14T20:33, 11-15T13:06, 11-15T17:00, 11-15T18:21, 11-15T19:44, 11-15T20:06). Es un mínimo.

`[I]` Los errores del orquestador son sobre todo de **sobreinterpretación** (atribución de mecanismo, «cumple» en el umbral, cifra no reproducible) y de **procedencia** (de qué fichero sale una cifra), no de números mal medidos. Las cifras que reproduce el validator coinciden casi siempre con los ficheros del solver.

`[D]` Rondas 8–11 con Sonnet orquestando (sin validator): P03_MS3, MS4 y MS5 mejoraron el peor S11 de −5,48 a −6,01 y −6,50 dB cambiando una variable por ronda y no declararon viabilidad (incertidumbre de puerto ≈1,5 dB). Ninguna se auditó de forma independiente. `[I]` Con esto no se puede decir que Sonnet orqueste peor que Opus: no hay comparación sobre la misma tarea.

### 4.2 Sonnet 5.5 (rf-designer, em-solver, validator)

**Volumen `[D]`** (deduplicado; 44 invocaciones hasta las 07:05Z; las dos posteriores —este informe y un `em-solver` en curso— se excluyen):

| Rol | Invocaciones | Llamadas API | Salida (tokens) | Duración total (s) | Media por invocación (s) |
|---|---|---|---|---|---|
| `validator` | 24 | 332 | 408 642 | 3 508 | 146 |
| `rf-designer` | 11 | 188 | 456 245 | 3 718 | 338 |
| `em-solver` | 7 | 230 | 455 278 | 3 787 | 541 |

**`validator` `[D]`.** Veredictos de las 24 auditorías: 21 «APROBAR CON RESERVAS» y 3 «OK con observaciones» (rondas 33, 34 y 36; el formato cambió el 15-nov), con un solo BLOQUEAR real: el puerto MSL de la ronda 6 (`PORT_INVALID` en ε_eff, Z_line y NF2FF de P02_MS1). Cada auditoría recomputó las cifras desde CSV y XML, regeneró hashes y ejecutó los tests (de 20 a 117). Conclusión de P02_MS1 «no cumple −6 dB» aprobada con reservas; métricas de NF2FF de esa ronda marcadas como inválidas.
`[I]` La tasa «aprobar con reservas» es casi uniforme: el validator casi nunca emite un veredicto binario negativo. Su valor está en las reservas concretas, no en el veredicto.

**Hallazgos de alta gravedad detectados por el validator en trabajo de Sonnet `[D]`:**
- R6: extracción de Z_line/β del puerto MSL mal condicionada con |Γ|≈0,92 (código del `em-solver`): eficiencia, ganancia y retardo de grupo de P02_MS1 inválidos; campaña a BLOCKED hasta corregir.
- R7: tras la corrección, ε_eff por tramos (147 de 501 puntos con fallback) dio un salto espurio de 0,46 ns en el retardo; el «rizado 220 ps» no debe citarse.
- R18: «convergencia» de S11 con sonda ideal mal planteada (Ls crece como ln(1/Δ)); el cambio de malla es una inductancia en serie.

**`rf-designer` y `em-solver` `[D]`:** 11 diseños de variante (hexágono, U-slot, inset, parásito enterrado, pila invertida, PS4, PS5) y 7 extensiones del código de openEMS (microstrip, puerto MSL, sonda, parásito enterrado, capa activa enterrada). Los tests del repositorio crecieron de 4 a 117 (omitiendo 15). La versión de PS4 de `rf-designer` (cambio pequeño, +12 MHz) se descartó por decisión del propietario, que prefirió desplazar ambos modos; quedó como alternativa no simulada (`variants/US3_PS4_rf_designer_alternative.json`).
`[D]` El validator confirmó la matemática de la corrección del puerto en R7 (tests sintéticos con |Γ|=0,92, error <1e-6) aunque halló el problema de ε_eff por tramos; en la ronda 33 comprobó que el cambio de código de la capa activa enterrada (`42453de`) no altera los XML de US3_MS3, US3_PS1 y P01_MS2 (hashes idénticos).

**Predicciones del lado Opus/Sonnet `[D]/[I]`** (modelo guía + hipótesis; sin autor identificable en los JSON; ver también §5.2):

| Ronda | Predicción previa | Resultado | Valoración |
|---|---|---|---|
| 023 US3_MS3 | −7,55 dB | −8,18 dB | 0,6 dB, mejor de lo previsto |
| 027 P01_MS2 | −9,3 dB (banda +20 %) | −10,42 dB (banda +6 %) | 1,1 dB; H2 no cumplida |
| 029 US3_MS4 | modo de la U baja ≈2,9 GHz | baja 0,2–0,3 GHz; el modo del parche baja 1,1 GHz | fallo grande |
| 030 P01_IN1 | ≤ −6 dB | −2,06 dB | fallo |
| 031 US3_PS1 | ≤ −8,5 dB, η ≥ 0,55 | −6,02 dB, η 0,23 | fallo |
| 033 US3_PS2 | ≤ −8 dB, η ≥ 0,6 | −2,73 dB; resonancia 0,9 GHz abajo | fallo |
| 034 US3_PS3 | −6,3…−10 dB | −7,59 dB (035: −8,10) | dentro |
| 036 US3_PS4 | modos +141 / +136 MHz; banda ≈7,63–8,25 GHz; H2 fallará | +150 / +130 MHz; banda 7,631–8,245 GHz; η 0,244 en 8,137 GHz | muy buena |

### 4.3 Fable 5.2 (las intervenciones concretas)

**Intervención 1: asesoría de diseño sobre US3_PS4 (2026-11-16T05:25–05:43Z, 1 071 s, 76 120 tokens de salida, 25 llamadas API, 30 usos de herramientas).**
- Encargo: el propietario pidió «cuando consigas un S11 comparable a US3_PS1 con las resonancias mejor centradas, utiliza a Fable». El orquestador (Opus) redactó el encargo con los datos de la ronda 036 y su hipótesis de adaptación por pérdidas (Q_d≈59, Q_rad≈200).
- `[D]` Veredicto: PS4 «NO SIMULAR en HFSS»; no se puede conservar el S11 de PS4 y cumplir η ≥ 0,55; propuesta US3_PS5 con dos cambios muy desiguales (parche 6,302 → 6,18 mm; parásito 7,46 → 7,05 mm; feed ajustado), con hipótesis H0/H1/H2 pre-registradas y dimensiones exactas verificadas con `prepare` en malla base y fina.
- `[D]` Aportó un modelo de dos resonadores acoplados (GUIDE_MODEL en el scratchpad, fuera del repo) ajustado a |S11| y a η de 032 y 036: Q_rad≈19, Q_d≈47, κ≈0,19 GHz, Q_ext≈10; resonador oscuro con Q_rad≈200; para η ≥ 0,55 con Q_d≈47 hace falta Q_r ≤ 38 en cada modo; con un FR4 de tan δ ≤ 0,004 sería viable.
- `[D]` Descartó con argumentos las opciones del encargo: mover z del parásito, voladizo en ±y, anchura Wp, ranuras en el parásito, vía parásito–parche, reducir κ.
- `[D]` Recomendó no gastar una ronda en el diagnóstico tan δ = 0 («el balance de potencia ya implica disipación»; PS5 es el experimento que discrimina).
- `[D]` Separó firme / apoyado en modelo / especulativo; dio probabilidades (≈80 % para la asignación de modos); estimó recursos de la FDTD (≈700 s, 0,5 GB, 2 CPU; real 776,5 s y 0,488 GB); propuso qué medir (η en 11 puntos, retardo de grupo, H3 con puntos NF2FF fuera del canal).
- `[D]` Alternativa y riesgos: US3_PS6 (transformador 6,6 → 7,1 mm) y la nota «si PS5 falla H2, cerraría la vía del parásito y mantendría P01_MS2».

**Intervención 2: verificación de los scripts HFSS de US3_PS4 (06:51–07:04Z, 773 s, 33 359 tokens de salida, 23 llamadas, 27 usos de herramientas).**
- `[D]` Veredicto «LISTO CON CORRECCIONES MENORES»; tests 117 OK; mismo SHA que `em/US3_PS4_OPENEMS_036/variant.json`; scripts generados idénticos byte a byte a una regeneración con PyAEDT 1.9.0 descargado (sin instalar); ensayo en seco con AEDT simulado.
- `[D]` Ocho correcciones: setup adaptativo demasiado laxo para dos resonancias (ΔS 0,02→0,01; MultiFrequency), 3 puntos de campo no muestrean el valle de η (3→11), tres exportadores que no valen cambiando solo `DESIGN` (`RESTORE_ARR_D`, `FIELDS_ARR_D_MM`, `ARR_D_MM`), ausencia de tests para el parásito, documentación y cabeceras desfasadas, comprobaciones de la lámina interna en AEDT, JSON de PS4 con textos obsoletos, pre-registrar el criterio del contraste HFSS (desfase esperado HFSS − openEMS de −60 a −75 MHz, extrapolado de P01_MS1 y US3_MS3).
- `[D]` El orquestador asignó las correcciones a un `em-solver` (en curso al cerrar este informe).
- `[I]` Parte de las correcciones solapa con lo que el `validator` ya había visto en la ronda 36 (ítem 7: JSON mezcla versiones). Las correcciones sobre los exportadores se verificaron por ensayo en seco, no en AEDT: están **sin confirmar en el HFSS real**.

**Resultado EM de la propuesta (ronda 037, US3_PS5_OPENEMS_037, malla base, convergida a −51,95 dB en 34 372 pasos, 776,5 s) `[D]`:**

Cifras recomputadas por mí desde `s11_complex.csv`, `s11_wideband.csv`, `run_numeric.json` y `nf2ff_summary.json`; la ronda 037 aún no ha pasado por `validator`.

| Magnitud | Predicción de Fable | Resultado 037 | Valoración |
|---|---|---|---|
| Mínimo inferior de S11 (H0) | 7,93–8,01 GHz | 8,065 GHz (−22,7 dB) | fuera (+55 MHz sobre el límite; +239 MHz respecto a PS4, frente a ≈ +85 esperado) |
| Rasgo superior (H0) | 8,45–8,60 GHz (mínimo o lazo) | sin mínimo local de \|S11\| entre 8,3 y 10,5 GHz en `s11_wideband.csv` (−5,3 dB en 8,48 GHz) | no observado como mínimo; lazo en Smith no comprobado |
| Peor S11 en canal (H1 ≤ −8 dB) | ≈ −9,4 (rango −8,2…−9,7) | −6,87 dB en 7,7376 GHz | falla H1: 2,5 dB peor que el central y 1,3 dB fuera del rango |
| Banda −10 dB | no declarada; «−10 dB no esperado» | 7,85–8,324 GHz | no cubre el borde inferior |
| η en 11 puntos (H2 ≥ 0,55) | 0,62–0,70, sin valle | 0,639–0,688, sin valle | acertada |
| Ganancia realizada broadside (H2 ≥ 2 dBi) | ≥ 3,3 dBi esperados | 2,99–4,25 dBi | H2 cumple; 1 punto (2,99) por debajo de lo esperado |
| Dmax a ≤ 20° de broadside | cumple | θ = 15–20° | cumple (20° en el límite) |
| Recursos de la FDTD | ≈700 s, 0,5 GB, 2 CPU | 776,5 s, 0,488 GB | acertada (+11 % en tiempo) |

`[I]` La predicción de Fable falla en frecuencia, no en física: el valle de η desapareció del canal como predijo, pero la posición del modo brillante se desvió ≈ 150 MHz respecto a su modelo, y eso desplaza el mínimo y deja el borde inferior mal cubierto. Fable había avisado de un posible término cruzado (riesgo 3: «el brillante puede subir unas decenas de MHz»); la desviación real fue mayor. Fable también avisó de que −0,41 mm en Lp es 3× el paso calibrado (riesgo 2).
`[D]` Sobre la limitación de lo medido: solo hay 11 puntos NF2FF en 7,7376–8,2368 GHz. El valle de η podría haberse desplazado fuera del canal; no hay puntos fuera para verlo (la opción 8 de Fable, puntos extra NF2FF, no se implementó).
`[D]` Retrospectiva: el modelo de Fable ajustado solo con la ronda 032 «predice» 036 con mínimos en 7,83/8,175 GHz (real 7,825/8,16), peor caso −11,8 dB (real −10,8 en rejilla de 5 MHz) y η con error ≤ 0,08; reproduce US3_MS3 sin ajustarlo (−16,5 dB vs −16,4). `[I]` Es una validación a posteriori, con 036 ya conocido: no cuenta como predicción prospectiva.

### 4.4 Línea base: Codex `[D]`

Fuente: `reports/first_campaign*.md`, `codex_*.md`, `.codex/config.toml`, git log. Codex (GPT-6 Astra orquestador; Sol y Luna subagentes) generó P01/P02/P03 solo como geometría (`GEOMETRY_ONLY`), cuatro tests, un solve de P01 (`P01_OPENEMS_001`, peor S11 −1,94 dB, sin convergencia de malla) y herramientas de análisis (20 tests al terminar su sesión). La campaña inicial quedó en «BLOCKED / EM_NOT_RUN» y sin herramienta de automatización. El `validator` de Codex (Luna) emitió 3 hallazgos (2 de gravedad media, 1 baja) sobre la geometría y 5 salvedades sobre la especificación EM.
`[I]` No es comparable con las fases Claude: distinto vendor, sin solver al principio, ventana de una sesión y reglas aún sin madurar. Solo sirve como punto de partida (0 rondas EM convergentes) y para constatar que la infraestructura de solver y de reglas de evidencia nació en Codex y se reutilizó.

### 4.5 UWBLab `[D]/[I]`

Repo: `/home/user/uwblab`. **Es un clon superficial** (`git rev-parse --is-shallow-repository` → true; 1 commit, `0ac97a5`, 2026-11-12, con `Co-Authored-By: Claude Fable 5.2`). No hay historial de commits ni transcripciones.

Lo que consta en `docs/PROGRESS.md` (historial redactado por el orquestador, autodeclarado):
- Diseño: orquestador Fable 5.2, revisor Opus 5.5, ejecutores Sonnet 5.5, definidos en `.claude/agents/uwb-executor.md` (sonnet) y `uwb-reviewer.md` (opus); CLAUDE.md dice «sesión principal, idealmente Fable 5.2» y el spec señala que la tarea programada no permite elegir el modelo.
- T1 la hizo Opus 5.5 como orquestador interactivo; el resto, Fable 5.2 (8 entradas del historial, una de ellas de rutina programada).
- Rendimiento del ciclo ejecutor→revisor: T2, T3, T6, M1–M9 (lote de 3), A1 y A2 aprobadas a la primera (6 de 10 unidades); T4, T5 y T7 en la ronda 2 (3); F1 en la ronda 3 (1). T4 tuvo 3 fallos de reconexión corregidos. La prueba D3 en dispositivo falló una vez; de D1–D5, cuatro OK (D2: iPhone 14 con cámara rota), una pendiente.
- El diseño de hardware lo escribió un Sonnet, lo revisó Opus (`docs/hardware/2026-11-12-revision-opus.md`): «APROBADO CON CORRECCIONES… la recomendación de compra no es fiable», 17 correcciones (la compra pasa de 2 × DWM3001CDK a un kit QM33120WDK1), las corrigió otro Sonnet y lo releyó el orquestador (Fable). PROGRESS.md cita 17 correcciones; no he contado los puntos del fichero de revisión.
- Qué no se puede saber desde el repo: qué porcentaje de los errores de Sonnet fue detectado por Opus frente a Fable (Fable orquesta, no revisa); cuántas veces corrigió Fable al ejecutor sin pasar por Opus; tokens y tiempos por modelo; si el modelo declarado en cada fila del historial es el real (se declara; solo un commit tiene Co-Authored-By). La sesión de UWBLab no está disponible aquí y no hay jsonl.
- `[I]` El tier Fable se usó aquí como **orquestador**, no como revisor: la comparación con el proyecto de antenas (revisor puntual) no es del mismo rol. El revisor «fuerte» de UWBLab es Opus, no Fable.

### 4.6 Hipótesis pre-registradas (M2) `[D]`

Fuente: `variants/*.json` (`pre_registered_hypothesis`) y los reportes de ronda. Cuento «cumplida solo formalmente» como no cumplida. La ronda 037 es mi lectura de los ficheros, sin auditoría.

| Ronda | Diseño | Hipótesis cumplidas / totales | Notas |
|---|---|---|---|
| 022 | US3_MS2 | 1 / 2 | H1 «no se confirma en conjunto» |
| 023 | US3_MS3 | 1 / 2 | η 0,65–0,67 < 0,70 |
| 025 | P01_MS1 | 1 / 2 | H2 refutada |
| 027 | P01_MS2 | 1 / 2 | H1 «por poco» (+6 % vs +20 % previsto) |
| 029 | US3_MS4 | 0 / 2 | H1 solo formal, H2 no evaluable (validator) |
| 030 | P01_IN1 | 0 / 2 | H1 −2,06 dB; H2 solo formal |
| 031 | US3_PS1 | 0 / 2 | |
| 033 | US3_PS2 | 0 / 2 | |
| 034 | US3_PS3 | 2 / 2 | con 1,6 dB y 0,054 de holgura |
| 036 | US3_PS4 | 2 / 3 | H0 y H1 sí; H2 fallo **previsto** por el orquestador |
| 037 | US3_PS5 (Fable) | 1 / 3 | H2 sí; H0 y H1 no |
| **Total** | | **9 / 24 (37,5 %)** | |

`[I]` La métrica mezcla hipótesis de dificultad muy dispar y está influida por que el orquestador escribe hipótesis que a veces espera ver fallar. Sirve para ver que el sistema **registra y evalúa honestamente los fallos** (nunca se declara cumplida una hipótesis sin matiz cuando el validator la discute), no para clasificar modelos. Fable aporta 1 ronda (3 hipótesis).

---

## 5. Comparación «solo Opus (+Sonnet)» frente a «con Fable»

### 5.1 Lo que se observa `[D]`

| | Antes de Fable (rondas 1–36) | Con Fable (ronda 37) |
|---|---|---|
| Rondas | 36 (31 FDTD) | 1 FDTD, tras 2 invocaciones |
| Fallos de diseño que bloquearon la ruta | MS4 (−1,37 dB), IN1 (−2,06), PS1 (−5,96; η 0,225), PS2 (−2,73), PS3 (−8,10; no mejor que P01_MS2) | — |
| Mejor diseño global | P01_MS2: −10,42 dB, η 0,73–0,76, gain 4,3–4,8 dBi (027/028, 13-nov) | sin cambio (037 no lo supera) |
| Diseño PS4 (Opus + Sonnet + decisión del propietario) | −10,66 dB, pero η 0,244 y gain −0,48 dBi en el canal | |
| Diseño PS5 (propuesta de Fable) | | −6,87 dB; η 0,639–0,688; gain 2,99–4,25 dBi |

Comparación EM directa de las tres alternativas, mismas condiciones de solver (openEMS 0.37.0, malla base, FR4 εr 4,4 tan δ 0,017, h 2,07 mm, puerto de 50 Ω en el borde):

| Diseño (ronda) | Peor S11 en canal | Banda −10 dB contigua (GHz) | η en el canal | Ganancia realizada broadside (dBi) |
|---|---|---|---|---|
| P01_MS2 (027) | −10,42 | 7,724–8,306 | 0,728–0,761 | 4,30–4,78 |
| US3_PS1 (032) | −5,96 | 7,49–8,115 (casi toda por debajo del canal) | 0,225–0,638 | −0,78 a 4,13 |
| US3_PS3 (035) | −8,10 | 7,814–8,157 | 0,665–0,747 | 3,80–4,79 |
| US3_PS4 (036) | −10,66 | 7,631–8,245 | 0,244–0,677 | −0,48 a 4,33 |
| **US3_PS5 (037, Fable)** | **−6,87** | 7,85–8,324 | **0,639–0,688** | **2,99–4,25** |

`[D]` PS5 frente a PS4: η mínima +0,395, ganancia mínima +3,47 dB, peor S11 3,8 dB peor. PS5 frente a P01_MS2: peor S11 3,5 dB peor, η 0,07–0,09 menor, ganancia mínima 1,3 dB menor. Fable había anticipado «el −10 dB no lo espero» y que, si PS5 falla H2, cerraría la vía del parásito enterrado y mantendría P01_MS2.

### 5.2 Confusores `[D]/[I]`

1. **Tamaño muestral.** Fable: 2 invocaciones y 1 simulación prospectiva. Cualquier tasa es no significativa.
2. **Entrada tardía.** Fable llegó con 36 rondas de datos, el modelo guía acumulado, las rondas 031–036 (misma familia PS) y el diagnóstico del orquestador en el encargo (η = P_rad/P_acc, hipótesis de adaptación por pérdidas, Q_d≈59). El encargo de Opus ya contenía parte de la respuesta. No hay un contrafactual de Opus resolviendo el mismo problema con el mismo encargo.
3. **Problemas distintos.** Antes de Fable: sintonizar una resonancia y adaptar (problemas de optimización local, con fórmulas de línea). Con Fable: separar mecanismos en un sistema acoplado de dos resonadores. No son equiparables en dificultad.
4. **El propietario dirigía las decisiones.** Eligió el hexágono y el U-slot (11-03), el parásito enterrado (11-15), «desplazar ambos modos» en PS4 (11-15/16), el uso de Fable (11-14, 11-15, 11-16), y pedir los scripts HFSS de PS4 para contrastarlo aunque Fable dijera «NO SIMULAR» (a 2026-11-16 aún no simulado en HFSS). Fable no eligió su propia agenda.
5. **Información asimétrica y encuadre.** Fable recibió un encargo redactado por Opus, con las opciones a considerar; su respuesta está condicionada por ese marco.
6. **Rol distinto.** El validator de Sonnet audita resultados ya obtenidos; Fable diseña y predice. No miden lo mismo.
7. **Costes distintos** (§6): Fable ≈ 15 min y ≈ 55 mil tokens de salida por invocación frente a ≈ 2,4 min y ≈ 17 mil de un validator.
8. **Datos que se modifican:** hubo cambios de herramientas durante el proyecto (mesh hints, 60 000 pasos, opción de capa activa), que cambian las líneas base entre rondas; la comparación 034 vs 035 es un ejemplo documentado por el validator.
9. **Expectativa del propietario.** El propietario ha dicho que Fable «ha sido de gran ayuda»; el informe no puede verificarlo con cifras de resultado.

### 5.3 Lo que sí se puede afirmar `[D]/[I]`

- **Afirmable (dato):** en la ronda 037 la η mínima del canal pasó de 0,244 a 0,639 y la ganancia mínima de −0,48 a 2,99 dBi con el diseño propuesto por Fable; el peor S11 pasó de −10,66 a −6,87 dB; ninguna ronda 29–37 mejora a P01_MS2 en conjunto.
- **Afirmable (dato):** la predicción cualitativa de Fable (el valle de η sale del canal si el modo superior sube ≈ 400 MHz y el brillante se conserva) se cumplió en los 11 puntos medidos. Las predicciones numéricas de S11 y de posición de mínimo fallaron (2,5 dB; +55 a +150 MHz).
- **Afirmable (dato):** Fable emitió 8 correcciones sobre los scripts HFSS (la nº 3 reúne varios defectos funcionales de los exportadores, verificados en seco, no en AEDT), y 1 de sus 2 informes recomendó **no** simular un diseño en HFSS.
- **Inferencia razonable:** el modelo de Fable aporta un **límite de diseño cuantificado** (con tan δ = 0,017 no hay dos modos que radien a la vez dentro del canal) que el orquestador solo sospechaba, y evitó la ronda de diagnóstico tan δ = 0 que sí se había planteado. Si el mecanismo era el supuesto, ahorró una ronda; si no, queda sin probar (el validator ya había dicho que la pérdida era «correlación, no mecanismo»).
- **Inferencia razonable:** Fable sirve para decisiones de alto apalancamiento y bajo número de iteraciones (diagnóstico, descarte de opciones, verificación previa a un paso caro como HFSS). No hay evidencia de que mejore la velocidad de convergencia numérica de una optimización local.
- **No afirmable:** que Fable «mejora el desarrollo del proyecto» en términos medibles; que Fable es mejor que Opus; que PS5 es un buen diseño (no mejora a P01_MS2); la causalidad de cualquier diferencia entre fases.
- **`[O]` Valoración cualitativa.** Fable muestra el comportamiento más próximo a un revisor científico: ajusta y reporta un modelo, separa firme/apoyado/especulativo, da riesgos con número, rechaza una opción pedida con argumento y recomienda parar. Su debilidad visible fue numérica: rango demasiado estrecho para S11 (−8,2…−9,7 frente a −6,87). Opus muestra un comportamiento sólido de orquestador (reglas ex ante, registro, recomendar cerrar vías), con sobreinterpretaciones frecuentes que el validator corrigió. Sonnet cumple como ejecutor y como auditor reproducible, sin hacer bloqueos globales.

---

## 6. Coste `[D]`

**Aviso:** los datos no contienen precios por token. No se calcula coste monetario. Los tokens de salida son lo más comparable; la caché leída domina el volumen de entrada y su precio, que difiere según modelo, no consta aquí. Los datos son únicos por `message.id` (si se suma `usage` por línea de jsonl, los valores se duplican o triplican). La duración es el tiempo de pared entre el primer y el último mensaje, e incluye esperas de herramientas (FDTD, tests).

| Modelo / rol | Invocaciones | Llamadas API | Entrada no cacheada | Salida | Caché leída | Caché creada | Duración total (s) | Duración media (s) |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5, orquestador (sesión) | 1 sesión | 730 | 1 568 | 850 926 | 337 309 748 | 9 697 263 | (12,8 días de pared, con inactividad) | — |
| Sonnet 5.5, `validator` | 24 | 332 | 664 | 408 642 | 14 049 691 | 1 368 920 | 3 508 | 146 |
| Sonnet 5.5, `rf-designer` | 11 | 188 | 378 | 456 245 | 11 699 945 | 912 252 | 3 718 | 338 |
| Sonnet 5.5, `em-solver` | 7 | 230 | 462 | 455 278 | 24 621 845 | 978 225 | 3 787 | 541 |
| Fable 5.2, `design-reviewer` | 2 | 48 | 94 | 109 479 | 4 242 727 | 385 156 | 1 845 | 922 |
| **Subagentes (sin este informe)** | **44** | **798** | **1 598** | **1 429 644** | **54 614 208** | **3 644 553** | **12 858** | **292** |

Derivados:
- Fable ≈ 4,8 % de los tokens de salida del proyecto (109 479 de 2 280 570) y ≈ 1,1 % de la caché leída (4,24 M de 391,9 M). Opus ≈ 37 % de la salida.
- Salida por llamada API: Opus 1 166; validator 1 231; em-solver 1 979; rf-designer 2 427; Fable 2 281.
- Una invocación de Fable = 54,7 k tokens de salida y 922 s; un validator, 17,0 k y 146 s: ≈ 3,2× y ≈ 6,3×. Por unidad de tarea (un diseño propuesto frente a una auditoría de ronda) no hay denominador común.
- Excluidos: este informe (Sonnet 5.5, 34 llamadas, 23 222 tokens de salida a la hora del recuento, en curso) y un `em-solver` aplicando las correcciones de Fable, en curso.
- Sin medir: tiempo de CPU de las 31 FDTD (≈ 191–1 189 s de pared cada una, 2 vCPU, ≤ 0,5 GB: dato de `run_numeric.json`), pero no forman parte del coste de modelo.

---

## 7. Recomendaciones para el TFG

### 7.1 Cómo documentarlo

1. **Modelo por mensaje.** Citar los identificadores exactos (`claude-opus-5-5`, `claude-sonnet-5-5`, `claude-fable-5-2`) y esfuerzo, con la fuente (campos `message.model` y `effort` de los jsonl). No basta con el frontmatter: se detectaron sesiones con Sonnet orquestando por el selector de modelo (rondas 8–11, 17, 19).
2. **Persistir la telemetría.** Los jsonl están en `/root/.claude/…` y no se versionan; copiar a un directorio del TFG (no al repo del código si hay datos privados) un resumen por invocación (modelo, tokens deduplicados, duración, tarea, veredicto). El script de este informe puede servir de punto de partida.
3. **Persistir los modelos guía.** El modelo de dos resonadores de Fable vive en `/tmp/.../scratchpad/tcmt/` fuera del repo; ni el de Fable ni el de rf-designer están firmados. Guardar los scripts en `antenna_design/analysis/` con cabecera `predicted_by`, `model`, `date`, `commit_before_result`.
4. **Registrar autoría de cada predicción** (`predicted_by: model/role`) y la fecha antes del resultado. Hoy no se puede separar Opus de Sonnet en las hipótesis.
5. **Separar «cumple» de «cumple formalmente»** en los JSON de hipótesis y usar etiquetas de severidad homogéneas en los handbacks del validator (crítica/alta/media/baja), para poder contar.
6. **Distinguir mecanismo de correlación** en los textos (el validator lo reclamó con la η de PS4).
7. **Declarar los confusores** de §5 en la memoria del TFG y no usar la tasa 9/24 como métrica de modelo.
8. **UWBLab:** si se quiere evaluar, guardar el historial git completo y las transcripciones; el clon actual es superficial.

### 7.2 Qué tier para qué `[O]`

| Tarea | Tier sugerido | Evidencia a favor |
|---|---|---|
| Orquestación, registro, reglas, decisiones y comunicación con el propietario | Opus 5.5 | 730 llamadas; reglas ex ante; recomendó cerrar la vía del parásito; con sobreinterpretaciones corregidas por validator |
| Ejecución repetible (scripts, extensiones de solver, JSON de variantes) y auditoría de reproducibilidad | Sonnet 5.5 | validator reproduce cifras desde CSV/XML en ≈ 2,4 min; rf/em producen 18 invocaciones con 117 tests finales |
| Diagnóstico de un fallo que no cede, descarte de opciones, verificación previa a un paso caro (HFSS) | Fable 5.2, bajo demanda | 2 invocaciones; diagnóstico cuantitativo coherente con los datos; recomendó no simular PS4 en HFSS; 8 correcciones a scripts |
| Predicción numérica de S11 | ninguno por sí solo: calibrar con un barrido barato | Opus/Sonnet: 4 de 8 aceptables; Fable: 1 prospectiva con fallo en S11 |
| Auditoría final de memoria o de afirmaciones de alto impacto | un tier distinto del que escribió | los errores corregidos fueron de sobreinterpretación del orquestador |

### 7.3 Experimento controlado para una comparación justa

Pregunta: ¿añadir un revisor Fable a un ciclo Opus + Sonnet mejora los resultados de diseño por unidad de esfuerzo?

1. **Congelar un punto de decisión.** Elegir estados del repositorio (commit) con problema abierto y resultado conocido que Fable no ha visto (p. ej. 3 estados: tras R29, tras R31, tras R33). El estado debe incluir solo lo anterior (git checkout al commit previo, sin transcripciones posteriores).
2. **Brazos** (misma tarea, mismo encargo literal, mismo presupuesto de rondas FDTD y de tokens): A = Opus orquestador + Sonnet ejecutores (sin revisor); B = A + validator; C = A + design-reviewer Fable; D = Fable orquestador. Repetir cada brazo n ≥ 5 veces por estado (el modelo es estocástico).
3. **Encargo idéntico y sin pistas:** no incluir la hipótesis del orquestador en el encargo del revisor (en este proyecto sí estaba).
4. **Pre-registro** (antes de ver resultados): métricas primarias (peor S11 en canal, η mínima, ganancia mínima, rondas FDTD hasta cumplir S11 ≤ −6 dB e η ≥ 0,55), error de predicción por brazo (|pred − real| en dB y MHz), tokens de salida totales, y tiempo de pared.
5. **Ciego:** un evaluador (otro validator o el propietario) puntúa sin conocer el brazo.
6. **Análisis:** comparación emparejada por estado; intervalos de confianza por bootstrap; reportar tamaños de efecto, no solo p. Registrar errores y retracciones de cada brazo (misma tabla que §4.1).
7. **Versión barata (sin FDTD):** back-testing de predicciones. Pedir a cada tier que prediga S11 de la ronda N dado el estado N−1 y comparar con el resultado real ya existente. Con 031–037 hay 6–7 casos y se puede ejecutar sin simular (coste de tokens solo).
8. **Presupuesto FDTD:** con el 1 FDTD ≈ 13 min en 2 vCPU y 4 brazos × 5 repeticiones × 3 estados = 60 FDTD ≈ 13 h; requiere consentimiento del propietario (el repo limita a 1 FDTD por ejecución).

---

## 8. Limitaciones generales (a incluir en la memoria)

- No hay verdad de campo: HFSS del propietario cubre solo P01_MS1, US3_MS3, P01_MS2 y el array; ni US3_PS4 ni US3_PS5 se han simulado aún en HFSS. Todo lo que diga «mejor» se refiere a openEMS, malla base, un solo solver, FR4 homogéneo, puerto ideal.
- US3_PS5 y las predicciones de Fable se evalúan con una sola ronda y sin auditoría del validator (037).
- Las predicciones de Opus/Sonnet no tienen autor individual en los JSON; asigno al «lado Opus/Sonnet».
- No se mide la calidad de lo que no se detectó (falsos negativos del validator y de Fable).
- Duraciones incluyen espera de herramientas; los tokens de caché no se pueden convertir a coste sin precios.
- UWBLab: sin historial ni transcripciones; las afirmaciones se limitan a lo que el propio orquestador escribió en `PROGRESS.md`.
- El evaluador es un Sonnet 5.5 que evalúa también a Sonnet; posible sesgo de autoevaluación. El orquestador Opus escribió el encargo de este informe.

---

## Anexo A. Invocaciones de subagentes

Orden cronológico (UTC). «Llamadas» = llamadas API únicas; «Sal.» = tokens de salida; «Dur.» = segundos de pared. El resultado de los `validator` es su veredicto textual. Las filas marcadas con asterisco tienen una nota debajo.

| # | Fecha (UTC) | Rol | Modelo | Tarea | Llamadas | Sal. | Dur. (s) | Resultado |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-03 11:53 | em-solver | sonnet-5-5 | P01 mesh refinement FDTD | 6 | 8714 | 75 | entregado |
| 2 | 2026-11-03 12:11 | validator | sonnet-5-5 | Audit P01_OPENEMS_002 results | 13 | 18650 | 164 | APROBAR CON RESERVAS |
| 3 | 2026-11-03 12:19 | rf-designer | sonnet-5-5 | P01_R1 resonant-length retune | 6 | 7190 | 65 | entregado |
| 4 | 2026-11-03 12:19 | em-solver | sonnet-5-5 | Generic patch openEMS script | 30 | 40735 | 354 | entregado |
| 5 | 2026-11-03 12:31 | validator | sonnet-5-5 | Audit P01_R1_OPENEMS_003 | 13 | 13318 | 133 | APROBAR CON RESERVAS |
| 6 | 2026-11-03 12:36 | rf-designer | sonnet-5-5 | P01_R2 matching design point | 8 | 18130 | 153 | entregado |
| 7 | 2026-11-03 12:46 | validator | sonnet-5-5 | Audit P01_R2 and viability | 18 | 15892 | 166 | APROBAR CON RESERVAS |
| 8 | 2026-11-03 13:06 | validator | sonnet-5-5 | Audit P01_R2 fine-mesh check | 9 | 7064 | 80 | APROBAR CON RESERVAS |
| 9 | 2026-11-03 18:00 | rf-designer | sonnet-5-5 | P02/P03 microstrip-fed variants | 13 | 53149 | 428 | entregado |
| 10 | 2026-11-03 18:00 | em-solver | sonnet-5-5 | Add microstrip feed to script | 56 | 151501 | 1189 | puerto MSL con fallo (lo detecta validator a6c3e0) |
| 11 | 2026-11-03 18:28 | validator | sonnet-5-5 | Audit P02_MS1 run and port | 23 | 42495 | 358 | veredicto en texto (ver handback); BLOQUEAR puerto MSL (alta); conclusión física P02_MS1 aprobada con reservas |
| 12 | 2026-11-03 18:37 | em-solver | sonnet-5-5 | Fix MSL port post-processing | 47 | 103294 | 1050 | corrección del puerto, auditada por ac8c29 |
| 13 | 2026-11-03 18:37 | rf-designer | sonnet-5-5 | Revise P03 hexagonal variant | 16 | 39737 | 312 | entregado |
| 14 | 2026-11-03 19:04 | validator | sonnet-5-5 | Audit port fix and P03_MS2 run | 35 | 42082 | 371 | veredicto en texto (ver handback); puerto corregido aprobado con reservas; hallazgo alta: ε_eff por tramos |
| 15 | 2026-11-04 19:55 | rf-designer | sonnet-5-5 | U-slot family design (probe, 2.07 mm) | 16 | 40842 | 291 | entregado |
| 16 | 2026-11-04 19:55 | em-solver | sonnet-5-5 | Check probe+slot+NF2FF path | 39 | 61576 | 463 | entregado |
| 17 | 2026-11-04 20:16 | validator | sonnet-5-5 | Audit round 12 (US0, script) | 34 | 35785 | 316 | APROBAR CON RESERVAS |
| 18 | 2026-11-04 20:25 | validator | sonnet-5-5 | Audit round 13 (US0 fine) | 8 | 8906 | 68 | APROBAR CON RESERVAS |
| 19 | 2026-11-04 20:33 | validator | sonnet-5-5 | Audit round 14 (US1 fine) | 11 | 10189 | 120 | veredicto en texto (ver handback) |
| 20 | 2026-11-04 20:41 | validator | sonnet-5-5 | Audit round 15 (US2 fine) | 6 | 6938 | 77 | APROBAR CON RESERVAS |
| 21 | 2026-11-04 20:49 | validator | sonnet-5-5 | Audit round 16 (US3 fine) | 12 | 14271 | 132 | veredicto en texto (ver handback) |
| 22 | 2026-11-05 09:03 | validator | sonnet-5-5 | Audit round 18 (US3 xfine) | 14 | 11587 | 110 | APROBAR CON RESERVAS; MESH_SENSITIVE correcto; Ls ∝ ln(1/Δ) con sonda ideal |
| 23 | 2026-11-13 16:16 | validator | sonnet-5-5 | Audit round 27 (P01_MS2) | 11 | 13473 | 104 | APROBAR CON RESERVAS; modelo guía no predictivo (alta); resultados 027 respaldados |
| 24 | 2026-11-13 16:33 | validator | sonnet-5-5 | Audit round 28 (P01_MS2 fine) | 7 | 7081 | 52 | APROBAR CON RESERVAS |
| 25 | 2026-11-13 19:18 | validator | sonnet-5-5 | Auditar ronda 29 US3_MS4 | 12 | 14615 | 118 | APROBAR CON RESERVAS; 1 alta, 3 media, 4 baja; dos retractaciones del orquestador |
| 26 | 2026-11-14 13:28 | rf-designer | sonnet-5-5 | Diseñar P01 con inset | 18 | 28865 | 238 | entregado |
| 27 | 2026-11-14 20:31 | validator | sonnet-5-5 | Auditar ronda 30 P01_IN1 | 12 | 14094 | 110 | APROBAR CON RESERVAS; energía final −49,23 mal calculada (solver: −51,41 dB) |
| 28 | 2026-11-15 13:01 | validator | sonnet-5-5 | Auditar análisis HFSS array 1×5 | 17 | 33408 | 261 | APROBAR CON RESERVAS; análisis 1×5 reproducible; 22°/18° de otro elemento |
| 29 | 2026-11-15 16:57 | validator | sonnet-5-5 | Audit HFSS array pitch sweep | 16 | 19681 | 143 | APROBAR CON RESERVAS; 3 afirmaciones del orquestador falsas en parte |
| 30 | 2026-11-15 17:59 | em-solver | sonnet-5-5 | openEMS: buried parasitic patch support | 30 | 48446 | 365 | entregado |
| 31 | 2026-11-15 17:59 | rf-designer | sonnet-5-5 | Design U-slot + buried parasitic | 10 | 38220 | 299 | entregado |
| 32 | 2026-11-15 18:17 | validator | sonnet-5-5 | Audit round 31 US3_PS1 | 14 | 28770 | 226 | APROBAR CON RESERVAS; «cumple −6 dB» de corrida truncada; banda 625 MHz engañosa |
| 33 | 2026-11-15 18:34 | validator | sonnet-5-5 | Audit round 32 diagnostic re-run | 6 | 5903 | 43 | APROBAR CON RESERVAS |
| 34 | 2026-11-15 19:43 | em-solver | sonnet-5-5 | openEMS: buried driven layer support | 22 | 41012 | 288 | entregado |
| 35 | 2026-11-15 19:43 | rf-designer | sonnet-5-5 | Design inverted stacked U-slot | 36 | 88198 | 715 | entregado |
| 36 | 2026-11-15 19:43 | validator | sonnet-5-5 | Audit round 32 (relaunch) | 5 | 4421 | 32 | APROBAR CON RESERVAS |
| 37 | 2026-11-15 20:04 | validator | sonnet-5-5 | Audit round 33 US3_PS2 | 14 | 14062 | 115 | OK con observaciones; «invertir la pila arregla η» demasiado fuerte |
| 38 | 2026-11-15 20:04 | rf-designer | sonnet-5-5 | Refinement 1 of US3_PS2 | 29 | 76390 | 647 | entregado |
| 39 | 2026-11-15 20:23 | validator | sonnet-5-5 | Audit round 34 US3_PS3 | 12 | 15458 | 117 | OK con observaciones; PS3 aceptable, no mejor que P01_MS2 |
| 40 | 2026-11-15 20:58 | rf-designer | sonnet-5-5 | Design US3_PS4 (resized buried parasitic) | 29 | 58794 | 515 | entregado |
| 41 | 2026-11-16 05:25 | design-reviewer | fable-5-2 | Fable: help fix US3_PS4 efficiency | 25 | 76120 | 1071 | NO SIMULAR PS4 en HFSS; propone US3_PS5 y modelo de 2 resonadores |
| 42 | 2026-11-16 05:25 | validator | sonnet-5-5 | Audit round 36 US3_PS4 | 10 | 10499 | 80 | OK con observaciones; JSON de PS4 mezcla versiones; η por pérdidas = correlación |
| 43 | 2026-11-16 06:50 | rf-designer | sonnet-5-5 | Create US3_PS5 from Fable spec | 7 | 6730 | 50 | crea US3_PS5.json a partir de la spec de Fable |
| 44 | 2026-11-16 06:51 | design-reviewer | fable-5-2 | Fable: verify US3_PS4 HFSS scripts | 23 | 33359 | 773 | LISTO CON CORRECCIONES MENORES (8 correcciones); sin AEDT real |
| 45 | 2026-11-16 07:06 | general-purpose | sonnet-5-5 | Report: AI model tiers performance | 34 | 23222 | 185 | este informe (en curso; excluido de los totales) |
| 46 | 2026-11-16 07:06 | em-solver | sonnet-5-5 | Apply Fable HFSS script corrections | 24 | 28383 | 184 | aplica correcciones de Fable (en curso; excluido) |

Notas del anexo A:
- Las dos auditorías de la ronda 32 (11-15 18:34 y 19:43) corresponden a un relanzamiento tras reinicio del proceso de la sesión (mensaje del sistema 19:41Z); la segunda dura 32 s.
- Las filas 4 y 17/18 (11-03 y 11-04) incluyen en «Dur.» el tiempo de FDTD o de tests que el subagente esperaba.
- Las dos últimas filas están en curso en el momento del recuento y se excluyen de los totales de §6.
- Sesión principal (Opus): 1 sesión, 730 llamadas únicas, 2026-11-03T11:22Z a 2026-11-16T07:06Z. Los mensajes de usuario humano suman 114 (muchos son mensajes del sistema, hooks o hand-backs; el recuento no distingue entre ellos).

## Anexo B. Fuentes

Repositorio de antenas (rama `codex/uwb-ch9-antenna-design`), prefijo `/home/user/TFG_Beamforming_FBD/`:
- Reglas y agentes: `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`, `.claude/agents/{rf-designer,em-solver,validator,design-reviewer}.md`, `.codex/config.toml`, `.codex/agents/*.toml`.
- Estado de campaña: `antenna_design/campaign_state.json` (`em_runs`, `history`, `designs`), `antenna_design/automation_policy.json` (`claude_routine.history`).
- Informes: `antenna_design/reports/claude_run_001.md` … `claude_run_036.md` (no existe `claude_run_035.md` ni `claude_run_037.md`), `claude_hfss_review_2026-11-13.md`, `claude_hfss_array_1x5_2026-11-15.md`, `codex_*.md`, `first_campaign*.md`.
- Variantes: `antenna_design/variants/*.json` (`pre_registered_hypothesis`), en especial `US3_PS1`…`US3_PS5`, `US3_PS4_rf_designer_alternative`.
- Resultados EM: `antenna_design/em/<ID>/{run_numeric.json,nf2ff_summary.json,s11_complex.csv,s11_wideband.csv,solver_log.txt,openEMS_run_stats.txt}` para `US3_MS3_OPENEMS_023`, `P01_MS2_OPENEMS_027`, `US3_PS1_OPENEMS_032`, `US3_PS2_OPENEMS_033`, `US3_PS3_OPENEMS_035`, `US3_PS4_OPENEMS_036`, `US3_PS5_OPENEMS_037`.
- `git log` de la rama: 217 commits con `ClCo`; `Co-Authored-By`: Opus 5.5 en 152, Sonnet 5.5 en 12 (rondas 8–11, 17, 19), Sonnet 4.6 en 48 (historial previo no relacionado con antenas).
- Transcripción de la sesión principal: `/root/.claude/projects/-home-user-TFG-Beamforming-FBD/9e909d13-45ad-58a7-a812-96fd33b3cfd9.jsonl` (usada con scripts, sin leerla entera).
- Transcripciones de subagentes: `/root/.claude/projects/-home-user-TFG-Beamforming-FBD/9e909d13-45ad-58a7-a812-96fd33b3cfd9/subagents/agent-*.jsonl` y sus `.meta.json` (tipo de agente y descripción). Hand-backs extraídos del bloque `SubagentHandback` de cada jsonl.
- Informes de Fable en esa carpeta: `agent-ab5a771c9e562990c.jsonl` (asesoría de diseño), `agent-a14cad17a50c483e4.jsonl` (verificación de scripts HFSS).
- Modelo guía de Fable (fuera del repo, temporal): `/tmp/claude-0/-home-user-TFG-Beamforming-FBD/9e909d13-45ad-58a7-a812-96fd33b3cfd9/scratchpad/tcmt/{m2.py,pred.py,joint.json}`. Citado por el propio Fable; no lo he abierto.

Repositorio UWBLab, prefijo `/home/user/uwblab/` (solo lectura, clon superficial, 1 commit): `CLAUDE.md`, `docs/PROGRESS.md`, `docs/ROADMAP.md`, `docs/superpowers/specs/2026-11-11-uwblab-design.md`, `docs/superpowers/plans/2026-11-11-uwblab-fase1.md`, `docs/hardware/2026-11-12-revision-opus.md`, `.claude/agents/uwb-executor.md`, `uwb-reviewer.md`.

Método de extracción: scripts en Python sobre los jsonl, con deduplicación por `message.id` (por bloque de contenido se repite el `usage`), recómputo de S11, banda y mínimos desde los CSV, y comparación con `run_numeric.json` y `nf2ff_summary.json`.

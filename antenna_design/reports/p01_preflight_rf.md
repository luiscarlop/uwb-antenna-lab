# P01: preflight RF para la única prueba EM autorizada

Fecha: 2026-11-03. Referencia revisada: commit
`069b30ee952db66827f45303064299dab0881116`, rama
`codex/uwb-ch9-antenna-design`. Fuentes: `em/p01_model_spec.json`,
`em/prepare_p01.py`, `em/p01_mesh.csv`, `em/solver_diagnosis.json`,
`designs.py` y tutorial oficial conservado en
`/tmp/openems-official-Simple_Patch_Antenna.py` durante la primera campaña.

**Revisión analítica y de configuración; no se ejecutó ninguna simulación.**
La especificación V1 todavía es declarativa: no acredita que las API, la
discretización o el puerto hayan sido aceptados por openEMS. Esta revisión no
modifica las geometrías ni declara resultados S11. Se comunicaron directamente
las correcciones al especialista EM, que prepara las API Python verificadas.

## Dictamen y corrección principal

El P01 rectangular con puerto concentrado vertical ideal es una primera prueba
reproducible y coherente con el tutorial oficial. Conservar W = 11.421266514 mm,
L = 8.280015708 mm, alimentación (0, −1.821603456), h = 1.6 mm y placa
26 × 26 mm. Para esta prueba conservar masa continua, sin pin ni apertura de
masa: su lanzamiento es ideal y debe llevar un ID distinto del futuro modelo
con conector físico.

La malla V1 requiere suavizar las transiciones en z: el CSV tiene paso 0.2 mm
en el sustrato y pasos de 0.78125/0.795238 mm en aire inmediatamente adyacente.
La mayor razón entre pasos vecinos es 3.97619. Proponer razón máxima 1.4,
conservando las interfaces z = 0 y 1.6 y al menos las ocho celdas a través del
sustrato. Recalcular celdas, paso temporal y RAM después de este cambio y de
cualquier refinamiento de bordes: la cifra V1 de 1,641,804 celdas ya no será
necesariamente la cifra del modelo ejecutado.

## Geometría, pérdidas y precedencia

Unidad global: `mesh.SetDeltaUnit(1e-3)`; coordenadas en mm. Las cantidades
`thickness` de la propiedad de lámina y conductividad se expresan en SI según
la API; verificar esa convención en la versión instalada, sin convertir 35 µm
en 0.035 m por confundir unidades de geometría y de material.

| Objeto | Coordenadas propuestas, mm | Material/prioridad |
| --- | --- | --- |
| Sustrato | caja [−13,−13,0] a [13,13,1.6] | εr 4.4, κ = 0.0332372248755 S/m, prioridad 0 |
| Masa | lámina z = 0, x/y entre −13 y 13 | cobre liso, σ = 5.8e7 S/m, espesor de propiedad 35e−6 m, prioridad 10 |
| Parche | lámina z = 1.6, x = ±5.710633257, y = ±4.140007854 | misma propiedad de cobre, prioridad 10 |
| Puerto | segmento (0,−1.821603456,0) a (0,−1.821603456,1.6) | puerto 1, eje z, R = 50 Ω, prioridad 5 |

Para pérdidas dieléctricas usar el modelo V1 explícito de κ constante, calculado
con `2*pi*f0*EPS0*epsilon_r*tan_delta`. Su tan δ equivale a 0.017 en f0 y
varía como f0/f. No describir ese modelo como tan δ constante en toda la banda
ni como una curva medida de FR4. No incluir máscara ni rugosidad sin parámetros
y geometría adicionales; declarar ambas ausentes.

La implementación preferida es `CSX.AddConductingSheet` con σ y espesor
anteriores y primitivas planas `AddBox` para parche y masa. El especialista EM
debe comprobar la firma instalada y que el XML contiene láminas conductoras
con esos valores. Esto permite modelar pérdidas mediante una aproximación de
lámina sin discretizar 35 µm de volumen. No añadir líneas z separadas 0.035 mm
para representar el espesor si se usa esa propiedad de lámina.

Si la versión instalada no soporta la propiedad, una caja de material de
conductividad finita y grosor geométrico cero no constituye un sustituto
verificado. Una alternativa PEC explícita sólo produciría una prueba ideal
sin pérdidas de cobre: debe identificarse como cambio de modelo y no conservar
una afirmación de pérdidas metálicas. Resolver la elección en el preflight,
antes de consumir la única ejecución.

## Puerto y conexión eléctrica

El tutorial oficial utiliza un puerto de extensión transversal cero entre masa
y parche. El equivalente para P01 es, una vez comprobada la firma instalada:

```python
start = [0.0, -1.8216034557658907, 0.0]
stop = [0.0, -1.8216034557658907, 1.6]
port = FDTD.AddLumpedPort(
    1, 50.0, start, stop, 'z', 1.0, priority=5, edges2grid='xy'
)
```

Confirmar que x = 0, y = −1.821603456, z = 0 y z = 1.6 están en la malla
final y que el puerto contacta las dos láminas. El centro queda a 2.318404398
mm del borde más próximo del parche. La prioridad 10 de metal conserva las
superficies de contacto frente al puerto 5 y al dieléctrico 0.

No superponer al mismo segmento un cilindro PEC o de cobre que puentee masa y
parche: cortocircuitaría este modelo de fuente ideal. No quitar cobre de la
masa bajo el segmento: el puerto necesita ese terminal de retorno. Las
dimensiones de pin/taladro/antipad propuestas en `first_campaign_rf.md`
corresponden al futuro lanzamiento coaxial, no a esta prueba.

Guardar tensión/corriente totales, incidentes y reflejadas con sus unidades y
convención. Usar `port.CalcPort(...)`, `S11 = uf_ref / uf_inc` y
`Zin = uf_tot / if_tot` conforme a la API comprobada. La resistencia de 50 Ω
normaliza el puerto; no demuestra que la antena esté adaptada a 50 Ω. Declarar
ausencia de deembedding y que no existe un plano de conector físico validado.

## Malla y fronteras antes de lanzar

1. Mantener fronteras `PML_8` en las seis caras y dominio inicial x/y = ±35,
   z = [−25,35] mm. Las ocho celdas absorbentes forman parte del dominio.
   En el CSV V1 su cara interior queda en x/y = ±31 y z = −18.75/28.638095,
   dejando aire entre placa y PML de 18 mm lateralmente y 18.75/27.038095 mm
   por debajo/encima de los metales. Recalcular esos márgenes con la malla
   definitiva y comprobar que metal, dieléctrico y puerto no ocupan PML.
2. Mantener paso máximo xy ≤0.5 mm y aire z ≤0.8 mm. A f0 + 1 GHz =
   8.9872 GHz, λ en el dieléctrico de εr 4.4 es aproximadamente 15.90 mm;
   los pasos V1 dan una discretización inicial razonable, sin certificar
   independencia de malla. La revisión debe cubrir la banda de excitación,
   además de los puntos de postproceso 7.5–8.5 GHz.
3. Aplicar el suavizado con razón máxima 1.4, manteniendo todas las interfaces
   y coordenadas de puerto. Verificar estrictamente creciente cada eje,
   ausencia de celdas diminutas accidentales y razón real entre pasos vecinos.
   El argumento de suavizado no sustituye esa comprobación numérica.
4. Refinar los bordes del parche y masa con el mecanismo oficial
   `FDTD.AddEdges2Grid(dirs='xy', properties=..., metal_edge_res=0.25)` si lo
   admite la versión instalada. Comprobar su política efectiva de
   discretización de bordes, incluidas las posiciones de líneas respecto de
   los cantos; no asumir que el XML V1 implementa ya la regla de tercios.
   Conservar geometría y simetría x; registrar cualquier posición efectiva de
   borde distinta de la nominal. Suavizar después y verificar de nuevo.
5. Inspeccionar el XML y la geometría discretizada mediante las herramientas
   de preprocesado disponibles, sin ejecutar un FDTD de ensayo. Registrar
   posición de interfaces, prioridades y número/ubicación de puerto. Una API
   que construya el objeto no prueba por sí sola que el metal esté conectado
   al puerto en la discretización final.

Los márgenes de aire anteriores son un punto de partida. Sólo una simulación
con una malla y un dominio no certifica convergencia espacial ni de PML.

## Ejecución limitada y evidencia exigible

Mantener excitación gaussiana (f0 = 7.9872 GHz, fc = 1 GHz), criterio de energía
1e−5 y máximo 30,000 pasos, con hasta dos hilos y límite de tiempo de pared
explícito del coordinador. Con la malla V1 el máximo de Courant calculado es
aproximadamente 0.5715 ps y el registro máximo 17.1449 ns; éstos son límites
analíticos del borrador, no tiempo de paso/registro observado. Sustituirlos por
los valores emitidos por el solver y comprobar si termina por decaimiento,
por límite de pasos, por tiempo de pared o por error. Reestimar recursos tras
la corrección de malla.

Procesar 7.5–8.5 GHz y añadir explícitamente 7.7376 y 8.2368 GHz, además de f0.
Una rejilla DTFT de 1 MHz no crea resolución física de 1 MHz. Guardar CSV
complejo, incidentes no nulos, impedancia y energía terminal. Comprobar S11 en
todos los puntos del canal; si se informa cobertura, identificar que corresponde
a la rejilla muestreada y examinar máximos locales. No confundir un mínimo
puntual con cumplimiento sobre la banda.

Si la instalación y los límites permiten preparar un monitor NF2FF en esta
misma ejecución, situarlo en aire, cerrado, encerrando toda la placa y fuera
de PML, y conservar el centro de fase/unidades. Su ausencia no invalida un
diagnóstico de puerto, pero deja sin evaluar ganancia, eficiencia, patrones
complejos, fase y retardo de grupo radiado. No presentar la derivada de fase de
S11 como retardo de grupo radiado ni inferir buena respuesta temporal de la
adaptación sola.

Conclusión de preflight: proceder con el modelo ideal descrito sólo tras
verificar instalación/API, corregir la transición z y registrar malla/recursos
finales. La evidencia seguirá siendo GEOMETRY_ONLY hasta disponer de una
ejecución real con archivos y logs; una única ejecución, aunque complete,
deberá declarar la convergencia espacial pendiente.

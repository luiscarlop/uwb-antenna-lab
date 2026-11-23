# Postprocesado de antenas — pruebas exclusivamente sintéticas

Este módulo no ejecuta solvers y no busca automáticamente resultados de campañas. Durante su desarrollo no se aplicó a ningún resultado real. Claude decide cuándo aplicarlo a datos EM validados.

Desde `antenna_design/`:

```bash
python -m analysis s11 /ruta/entrada.csv --out /ruta/nuevo_resumen.json --z0 50 --max-gap-hz 1000000
python -m analysis radiated /ruta/campo.csv --out /ruta/nuevo_retardo.json --reference 'Etheta/sqrt(Pinc), theta=90,phi=0, r=1m, exp(+jwt), referencia puerto'
python -m unittest discover -s tests -p test_analysis.py -v
```

Los caminos son ejemplos, no comandos ejecutados sobre datos reales. La salida debe ser nueva; nunca sobrescribe una entrada ni otro resumen.

## CSV de puerto y métricas

Cabecera mínima: `frequency_hz,s11_real,s11_imag`. Frecuencia positiva, finita, creciente y sin duplicados. Se admiten columnas adicionales. Valores complejos normalizados a una impedancia real positiva z0, por defecto50Ω. Si el solver usa otra referencia o impedancia compleja, renormalizar correctamente antes; no basta cambiar la etiqueta.

- S11(dB)=20log10|Gamma|; Gamma=0 produce −Infinity.
- Z=z0(1+Gamma)/(1−Gamma); Gamma=1 devuelve impedancia indefinida (`null`), nunca un número finito artificial.
- VSWR=(1+|Gamma|)/(1−|Gamma|) para |Gamma|<1; en1 es infinito; >1 devuelve null y marca posible actividad/error de pasividad.
- En JSON los infinitos son cadenas `Infinity`/`-Infinity`; no se emite NaN ni JSON no estándar. Impedancia compleja se serializa en real/imag.

## Cobertura de TODO el canal

Banda7.7376–8.2368GHz. Se examinan todos los puntos interiores y ambos extremos. Si hay datos a ambos lados, los extremos faltantes se interpolan en S11 complejo, no en dB. Bajo esa interpolación lineal, el máximo de |Gamma| en cada segmento está en un extremo, por convexidad de la norma.

- `FAIL`: existe al menos un punto evaluado que supera el umbral. Un mínimo profundo no compensa un fallo en otra frecuencia.
- `INSUFFICIENT_DATA`: falta cobertura de los bordes o se incumple la separación máxima solicitada, sin un fallo ya observado.
- `PASS_INTERPOLATED`: todos los segmentos de la representación lineal cumplen, condicionado a esa aproximación. **No es una certificación de cobertura continua del dispositivo**.

Siempre se devuelve `continuous_band_verified=false`; ni una cuadrícula densa ni interpolar extremos prueba ausencia de resonancias estrechas, convergencia temporal/espacial o exactitud de solver. `max_source_gap_hz` informa la máxima separación de datos originales que afecta a la banda. Es conveniente que Claude exija extremos exactos y defina su límite de separación; sin `--max-gap-hz` no se presume uno universal.

## Campo radiado y retardo

Cabecera mínima: `frequency_hz,field_real,field_imag`. Un archivo corresponde a UNA polarización, dirección angular, distancia y referencia. La entrada debe representar transferencia compleja radiada H(f), normalizada a la misma excitación en todas las frecuencias. No mezclar Etheta/Ephi, ángulos o realizaciones; no usar amplitud/potencia en lugar de campo complejo. Para ganancia escalar no existe fase suficiente.

Convención exp(+jωt): tau=−d arg(H)/dω. El módulo desenvuelve fase, usa derivada interior de tres puntos para pasos no uniformes y derivada unilateral de primer orden en extremos. Ripple=max(tau)−min(tau) sobre el intervalo de entrada. Media reportada es aritmética de muestras, no integral ponderada en frecuencia. Para un ripple de canal usar `--band-hz 7737600000 8236800000` (API: `band=BAND_HZ`). Exige al menos tres muestras dentro de la banda y ambos extremos exactos; no interpola fase ni extrapola campos. La derivada se calcula antes de recortar, aprovechando muestras exteriores como apoyo en los extremos. Añade `frequency_weighted_mean_delay_s`, media integrada por trapecios para cuadrículas no uniformes; `mean_delay_s` mantiene la media aritmética por compatibilidad.

Se exige `field_kind='radiated_transfer'` en API y referencia no vacía. No puede descubrir si alguien ha etiquetado erróneamente S11 como campo: la procedencia es responsabilidad del usuario. Rechaza nulos o amplitudes inferiores a1e−6 del pico, porque la fase es inestable cerca de un cero; se pueden analizar regiones válidas por separado. Rechaza saltos exactamente ambiguos deπ. El desenvolvimiento presupone incremento verdadero entre muestras menor queπ: aliasing de fase puede pasar inadvertido y exige muestreo más fino.

El retardo incluye tiempo de propagación r/c y fase de fuente/puerto si no se eliminan antes. Una distancia constante añade retardo constante; cambios de distancia, ángulo o referencia contaminan también el ripple. La fase del S11 no es retardo de grupo radiado.

## Verificación

16 pruebas con datos generados en memoria/CSV temporales: carga adaptada, abierto/corto, impedancia compleja, VSWR, datos inválidos, extremos ausentes, notch que falla cobertura, interpolación compleja, límite de huecos, igualdad de umbral, retardo conocido con fase envuelta, dispersión cuadrática, nulos y rechazo de S11. Ninguna lee em/ ni outputs/.

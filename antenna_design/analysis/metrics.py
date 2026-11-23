"""Complex-port and radiated-field metrics (standard library only).

Conventions: real, positive reference impedance; phasors exp(+j omega t).
A frequency grid never proves continuous-band or solver convergence.
"""
import cmath
import csv
import math

BAND_HZ = (7_737_600_000.0, 8_236_800_000.0)


def _validated(frequency, values):
    f, v = list(frequency), [complex(x) for x in values]
    if len(f) != len(v) or len(f) < 2:
        raise ValueError('Need at least two paired samples')
    if any(not math.isfinite(x) or x <= 0 for x in f):
        raise ValueError('Frequencies must be finite and positive Hz')
    if any(b <= a for a, b in zip(f, f[1:])):
        raise ValueError('Frequencies must strictly increase; no duplicate or mixed-angle rows')
    if any(not math.isfinite(x.real) or not math.isfinite(x.imag) for x in v):
        raise ValueError('Complex samples must be finite')
    return f, v


def read_complex_csv(path, real_column='s11_real', imag_column='s11_imag'):
    """Read frequency_hz and chosen complex columns; reject unsorted/mixed data."""
    with open(path, newline='') as stream:
        rows = list(csv.DictReader(stream))
    try:
        return _validated([float(r['frequency_hz']) for r in rows],
                          [complex(float(r[real_column]), float(r[imag_column])) for r in rows])
    except (KeyError, TypeError) as exc:
        raise ValueError('Missing required CSV columns') from exc


def s11_metrics(s11, z0=50.0):
    if not math.isfinite(z0) or z0 <= 0:
        raise ValueError('z0 must be real, finite and positive')
    result = []
    for gamma in s11:
        gamma = complex(gamma)
        if not math.isfinite(gamma.real) or not math.isfinite(gamma.imag):
            raise ValueError('Non-finite S11')
        rho = abs(gamma)
        # |Gamma|>1 may be active or inconsistent data: no negative VSWR.
        result.append({'s11_db': 20 * math.log10(rho) if rho else -math.inf,
                       'impedance_ohm': z0 * (1 + gamma) / (1 - gamma) if gamma != 1 else None,
                       'vswr': (1 + rho) / (1 - rho) if rho < 1 else (math.inf if rho == 1 else None),
                       'passivity_violation': rho > 1})
    return result


def _at(f, v, target):
    for i, x in enumerate(f):
        if x == target:
            return v[i]
        if x > target and i:
            a = (target - f[i-1]) / (x - f[i-1])
            return v[i-1] * (1-a) + v[i] * a
    raise ValueError('Cannot extrapolate band edge')


def band_coverage(frequency, s11, band=BAND_HZ, thresholds=(-6.0, -10.0), max_gap_hz=None):
    """Whole requested band under piecewise-linear COMPLEX S11 assumption.

All segments must satisfy threshold; a resonance minimum is insufficient.
The norm of a line segment is convex, so its maximum is at an endpoint.
PASS_INTERPOLATED is conditional, never validated continuous-band coverage.
"""
    f, v = _validated(frequency, s11)
    lo, hi = band
    if not 0 < lo < hi or not all(math.isfinite(x) for x in band):
        raise ValueError('Invalid band')
    if max_gap_hz is not None and (not math.isfinite(max_gap_hz) or max_gap_hz <= 0):
        raise ValueError('max_gap_hz must be positive')
    if any(not math.isfinite(t) or t >= 0 for t in thresholds):
        raise ValueError('Thresholds must be finite negative dB')
    covered = f[0] <= lo and f[-1] >= hi
    relevant_gaps = [b-a for a,b in zip(f,f[1:]) if b > lo and a < hi]
    gap = max(relevant_gaps, default=None)
    adequate = covered and (max_gap_hz is None or gap <= max_gap_hz)
    # Evaluate only the covered portion; never invent missing edge values.
    points = [(x,y) for x,y in zip(f,v) if lo <= x <= hi]
    if covered:
        points = [(lo,_at(f,v,lo))] + [(x,y) for x,y in points if lo<x<hi] + [(hi,_at(f,v,hi))]
    worst = max((abs(y) for _,y in points), default=None)
    worst_db = None if worst is None else (20*math.log10(worst) if worst else -math.inf)
    checks = {}
    for threshold in thresholds:
        failed = worst is not None and worst > 10**(threshold/20) * (1+1e-12)
        checks[str(threshold)] = ('FAIL' if failed else 'PASS_INTERPOLATED' if adequate else 'INSUFFICIENT_DATA')
    return {'band_hz': list(band), 'data_spans_band': covered,
            'exact_edges_present': [lo in f, hi in f], 'max_source_gap_hz': gap,
            'max_gap_requirement_hz': max_gap_hz, 'evaluated_points': len(points),
            'worst_s11_db': worst_db, 'thresholds_db': checks,
            'continuous_band_verified': False,
            'assumption': 'piecewise-linear complex S11; unresolved spectral structure and numerical convergence remain unverified'}


def radiated_group_delay(frequency, field, *, field_kind, reference, amplitude_floor_relative=1e-6, band=None):
    """-d(arg(H))/d(2*pi*f), same angle/polarization/reference for every row.

H must be a complex RADIATED transfer field normalized to the same excitation.
No S11 input. Caller must remove/calibrate source and propagation phase as needed.
Phase unwrap requires adjacent true increments < pi; aliasing cannot be inferred.
"""
    if field_kind != 'radiated_transfer' or not reference.strip():
        raise ValueError('Require radiated_transfer and documented phase/excitation reference')
    f,v = _validated(frequency, field)
    if len(f) < 3:
        raise ValueError('At least three field samples required')
    if not 0 < amplitude_floor_relative < 1:
        raise ValueError('Invalid amplitude floor')
    if band is not None:
        lo, hi = band
        if not all(math.isfinite(x) for x in band) or not 0 < lo < hi:
            raise ValueError('Invalid delay band')
        if lo not in f or hi not in f:
            raise ValueError('Delay band requires exact sampled endpoints; no phase interpolation')
        if sum(lo <= x <= hi for x in f) < 3:
            raise ValueError('Delay band requires at least three samples')
    peak = max(map(abs,v))
    if peak == 0 or any(abs(x) <= peak*amplitude_floor_relative for x in v):
        raise ValueError('Field null/low amplitude makes phase delay unreliable; split valid regions')
    phases = [cmath.phase(v[0])]
    for a,b in zip(v,v[1:]):
        delta = cmath.phase(b/a)
        if abs(abs(delta)-math.pi) < 1e-10:
            raise ValueError('Ambiguous pi phase increment; refine frequency sampling')
        phases.append(phases[-1]+delta)
    slopes = [(phases[i+1]-phases[i])/(f[i+1]-f[i]) for i in range(len(f)-1)]
    deriv = [slopes[0]]
    for i in range(1,len(f)-1):
        left,right=f[i]-f[i-1],f[i+1]-f[i]
        deriv.append((right*slopes[i-1]+left*slopes[i])/(left+right))
    deriv.append(slopes[-1])
    delay = [-x/(2*math.pi) for x in deriv]
    # Differentiate before cropping: guard samples support band-edge derivatives.
    source_range = [f[0], f[-1]]
    if band is not None:
        selected = [(x,t) for x,t in zip(f,delay) if lo <= x <= hi]
        f,delay = map(list,zip(*selected))
    mean_integral = sum((b-a)*(u+v)/2 for a,b,u,v in zip(f,f[1:],delay,delay[1:]))/(f[-1]-f[0])
    return {'frequency_hz': f, 'delay_s': delay, 'ripple_peak_to_peak_s': max(delay)-min(delay),
            'evaluation_band_hz': [f[0],f[-1]], 'source_range_hz': source_range,
            'frequency_weighted_mean_delay_s': mean_integral,
            'mean_delay_s': sum(delay)/len(delay), 'reference': reference,
            'edge_derivative': 'one-sided first order; interior nonuniform three-point',
            'caveat': 'Unwrap assumes true adjacent phase change < pi; delay includes unremoved propagation/source reference'}

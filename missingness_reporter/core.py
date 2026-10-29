"""Missingness matrix, per-column/row summaries, patterns, co-missingness and simple MAR checks."""
import math
import statistics
from collections import Counter

MISSING = {"", "na", "n/a", "nan", "null", "none", ".", "-", "-99", "-999", "missing"}


def missing_matrix(rows, codes=MISSING):
    return [[(v.strip().lower() in codes) for v in r] for r in rows]


def column_summary(header, m):
    n = len(m)
    out = []
    for j, h in enumerate(header):
        k = sum(1 for r in m if j < len(r) and r[j])
        out.append({"column": h, "missing": k, "percent": round(100.0 * k / n, 1) if n else 0.0})
    return sorted(out, key=lambda x: -x["missing"])


def row_summary(m):
    counts = Counter(sum(r) for r in m)
    return {"complete_rows": counts.get(0, 0), "rows": len(m),
            "complete_percent": round(100.0 * counts.get(0, 0) / len(m), 1) if m else 0.0,
            "distribution": dict(sorted(counts.items()))}


def patterns(header, m, top=10):
    """Most common missingness patterns as (count, [missing columns])."""
    c = Counter(tuple(j for j, x in enumerate(r) if x) for r in m)
    return [(n, [header[j] for j in pat]) for pat, n in c.most_common(top)]


def co_missingness(header, m, min_count=1):
    """Pairs of columns that are missing together; phi correlation of missing indicators."""
    out = []
    n = len(m)
    for a in range(len(header)):
        for b in range(a + 1, len(header)):
            both = sum(1 for r in m if r[a] and r[b])
            if both < min_count:
                continue
            pa = sum(1 for r in m if r[a]) / n
            pb = sum(1 for r in m if r[b]) / n
            pab = both / n
            denom = math.sqrt(pa * (1 - pa) * pb * (1 - pb))
            phi = (pab - pa * pb) / denom if denom else 0.0
            out.append((header[a], header[b], both, round(phi, 3)))
    return sorted(out, key=lambda x: (-x[3], -x[2]))


def _welch_t(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    vx, vy = statistics.variance(x), statistics.variance(y)
    se = math.sqrt(vx / len(x) + vy / len(y))
    return (mx - my) / se if se else 0.0


def little_mcar_hint(header, rows, m, min_group=5):
    """For each column with missing values and each numeric column, compare the numeric column's mean
    between rows where the first is missing vs observed (Welch t). Large |t| suggests data are not MCAR.
    This is a screening heuristic, not Little's formal MCAR test."""
    numeric = []
    for j in range(len(header)):
        vals = [r[j] for r, mr in zip(rows, m) if not mr[j]]
        try:
            [float(v) for v in vals]
            if vals:
                numeric.append(j)
        except ValueError:
            pass
    hints = []
    for a in range(len(header)):
        if not any(r[a] for r in m):
            continue
        for b in numeric:
            if a == b:
                continue
            miss = [float(rows[i][b]) for i in range(len(rows)) if m[i][a] and not m[i][b]]
            obs = [float(rows[i][b]) for i in range(len(rows)) if not m[i][a] and not m[i][b]]
            if len(miss) >= min_group and len(obs) >= min_group:
                t = _welch_t(miss, obs)
                if abs(t) > 2:
                    hints.append({"missing_in": header[a], "differs": header[b], "t": round(t, 2),
                                  "mean_when_missing": round(statistics.fmean(miss), 3),
                                  "mean_when_observed": round(statistics.fmean(obs), 3)})
    return sorted(hints, key=lambda h: -abs(h["t"]))


def report(header, rows, codes=MISSING):
    m = missing_matrix(rows, codes)
    return {"columns": column_summary(header, m), "rows": row_summary(m), "patterns": patterns(header, m),
            "co_missing": co_missingness(header, m, 2)[:10], "mar_hints": little_mcar_hint(header, rows, m)}


def to_markdown(rep, title="Missing data report"):
    r = rep["rows"]
    out = ["# %s" % title, "", "%d of %d rows complete (%.1f%%)." % (r["complete_rows"], r["rows"], r["complete_percent"]),
           "", "## Missing values per column", "", "| Column | Missing | % | |", "|---|---|---|---|"]
    for c in rep["columns"]:
        out.append("| %s | %d | %.1f | %s |" % (c["column"], c["missing"], c["percent"], "#" * int(c["percent"] // 5)))
    out += ["", "## Most common patterns", "", "| Rows | Missing columns |", "|---|---|"]
    for n, cols in rep["patterns"]:
        out.append("| %d | %s |" % (n, ", ".join(cols) or "(complete)"))
    if rep["co_missing"]:
        out += ["", "## Columns missing together", ""]
        out += ["- %s & %s: %d rows (phi %.2f)" % c for c in rep["co_missing"]]
    if rep["mar_hints"]:
        out += ["", "## Possible non-random missingness", ""]
        out += ["- when **%s** is missing, mean **%s** = %s vs %s (t = %.2f)" % (
            h["missing_in"], h["differs"], h["mean_when_missing"], h["mean_when_observed"], h["t"]) for h in rep["mar_hints"]]
    return "\n".join(out) + "\n"

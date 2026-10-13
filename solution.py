import csv
from datetime import datetime

def parse_iso(ts):
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)

def load_data(filepath='device_alerts.csv'):
    with open(filepath, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        te = parse_iso(r['event_ts'])
        ts = parse_iso(r['synced_ts'])
        # drift_min: event timestamp relative to cloud synced timestamp (in minutes)
        r['drift_min'] = (te.timestamp() - ts.timestamp()) / 60.0
        r['signal_dbm'] = float(r['signal_dbm'])
        r['retry_count'] = float(r['retry_count'])
    return rows

def is_flagged_s1(r):
    return r['drift_min'] >= 15.0

def is_flagged_s2(r):
    return (r['drift_min'] >= 15.0) or (r['signal_dbm'] <= 5.0 and r['retry_count'] >= 70.0)

def is_flagged_s3(r):
    # Plant-tailored policy
    if r['plant_code'] == '一号总装厂':
        return (r['drift_min'] >= 15.0) or (r['signal_dbm'] <= 3.0 and r['retry_count'] >= 25.0)
    else:
        return (r['drift_min'] >= 15.0) or (r['signal_dbm'] <= 5.0 and r['retry_count'] >= 70.0)

def evaluate_policy(rows):
    labeled = [r for r in rows if r['is_valid_dispatch'] in ('0', '1')]
    total_invalid = sum(1 for r in labeled if r['is_valid_dispatch'] == '0')
    base_cost = total_invalid * 90

    def calc_metrics(rule_fn):
        defer = [r for r in labeled if rule_fn(r)]
        caught_fa = sum(1 for r in defer if r['is_valid_dispatch'] == '0')
        missed_fa = total_invalid - caught_fa
        cost = missed_fa * 90 + len(defer) * 10
        saved = base_cost - cost
        return {
            'deferred': len(defer),
            'caught': caught_fa,
            'missed': missed_fa,
            'cost': cost,
            'saved': saved,
            'pct_saved': saved / base_cost * 100.0
        }

    return base_cost, calc_metrics(is_flagged_s1), calc_metrics(is_flagged_s2), calc_metrics(is_flagged_s3)

def evaluate_all_strategies(rows):
    labeled = [r for r in rows if r['is_valid_dispatch'] in ('0', '1')]
    total_labeled = len(labeled)
    total_valid = sum(1 for r in labeled if r['is_valid_dispatch'] == '1')
    total_invalid = sum(1 for r in labeled if r['is_valid_dispatch'] == '0')
    base_cost, s1, s2, s3 = evaluate_policy(rows)

    print(f"Total labeled: {total_labeled} (Valid: {total_valid}, False alarms: {total_invalid})")
    print(f"Baseline Loss (100% direct dispatch): {base_cost} units")
    print("=" * 60)

    names = [
        ("Strategy 1: Single-Factor Drift (drift >= 15m)", s1),
        ("Strategy 2: Global Dual-Factor (drift >= 15m OR (sig <= 5 AND retry >= 70))", s2),
        ("Strategy 3: Plant-Adaptive Multi-Factor (Tailored for 一号总装厂)", s3),
    ]

    for name, res in names:
        print(f"[{name}]")
        print(f"  Deferred for review: {res['deferred']}/{total_labeled} ({res['deferred']/total_labeled*100:.2f}%)")
        print(f"  Intercepted false alarms: {res['caught']}/{total_invalid} ({res['caught']/total_invalid*100:.2f}%)")
        print(f"  Missed false alarms (wasted dispatch): {res['missed']}")
        print(f"  Total Loss: {res['cost']} units (Saved: {res['saved']} units, -{res['pct_saved']:.2f}%)")
        print("-" * 60)

    # Strategy 3 Breakdown by Plant
    print("\n--- Strategy 3 Breakdown by Plant ---")
    plants = sorted(set(r['plant_code'] for r in rows))
    for p in plants:
        p_rows = [r for r in labeled if r['plant_code'] == p]
        p_fa = sum(1 for r in p_rows if r['is_valid_dispatch'] == '0')
        p_flagged = [r for r in p_rows if is_flagged_s3(r)]
        p_caught = sum(1 for r in p_flagged if r['is_valid_dispatch'] == '0')
        p_base = p_fa * 90
        p_cost = (p_fa - p_caught) * 90 + len(p_flagged) * 10
        p_saved = p_base - p_cost
        print(f"{p.ljust(8)}: Total={len(p_rows):3d}, FA={p_fa:2d}, Intercepted={p_caught:2d} ({p_caught/p_fa*100:5.1f}%), Base={p_base:4d}, Cost={p_cost:4d}, Saved={p_saved:4d} ({p_saved/p_base*100:5.1f}%)")

    # Unlabeled data inference
    unlabeled = [r for r in rows if r['is_valid_dispatch'] == '']
    s3_unlabeled_flagged = [r for r in unlabeled if is_flagged_s3(r)]
    print(f"\n--- Unlabeled Alert Inferences (Total {len(unlabeled)}) ---")
    print(f"Recommended Deferred/High-Risk: {len(s3_unlabeled_flagged)} alerts")
    for r in s3_unlabeled_flagged:
        print(f"  Alert ID {r['alert_id']}: Plant={r['plant_code']}, Cat={r['device_category']}, Drift={r['drift_min']:.1f}m, Signal={r['signal_dbm']}, Retry={r['retry_count']}")

if __name__ == '__main__':
    data = load_data()
    evaluate_all_strategies(data)

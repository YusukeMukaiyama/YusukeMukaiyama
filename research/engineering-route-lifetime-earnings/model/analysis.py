"""Scenario, sensitivity and break-even analysis on top of model.py. Writes results/*.csv and results.json."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from model import *

OUT = os.path.join(HERE, '..', 'results'); os.makedirs(OUT, exist_ok=True)
R = {}

def tot(p, lo=15, hi=65):
    return float(p[(AGES >= lo) & (AGES < hi)].sum())

def cum_cross(p_early, p_late, c_early=None, c_late=None):
    """age from which cumulative(late) stays >= cumulative(early)."""
    a = np.cumsum(p_early - (0 if c_early is None else c_early))
    b = np.cumsum(p_late - (0 if c_late is None else c_late))
    d = b - a
    if d[-1] < 0:
        return None
    i = len(d) - 1
    while i > 0 and d[i - 1] >= 0:
        i -= 1
    return int(AGES[i])

def irr(cf):
    lo, hi = -0.5, 0.5
    f = lambda r: np.sum(cf / (1 + r) ** np.arange(len(cf)))
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        m = (lo + hi) / 2
        if f(lo) * f(m) <= 0: hi = m
        else: lo = m
    return m

# ------------------------------------------------------------------ main cases
cases = {}
for case in ['case1', 'case2', 'case3']:
    P, meta = route_profiles(case)
    ret = ASSUME['retire_case2'] if case == 'case2' else ASSUME['retire_case1']
    S = summarize(P, ret)
    cases[case] = (P, ret, S)
    S.round(3).to_csv(os.path.join(OUT, f'summary_{case}.csv'))
    pd.DataFrame({NAMES[r]: P[r] for r in ROUTES}, index=AGES).round(4).to_csv(os.path.join(OUT, f'profile_{case}.csv'))

# 高専 method range (case1)
rng = {}
for m in ['m1', 'm2', 'avg']:
    P, _ = route_profiles('case1', kosen_method=m)
    rng[m] = tot(P['B'])
R['kosen_method_range_case1'] = rng

# ------------------------------------------------------------------ expected value incl. employment risk (case1)
P1, ret1, S1 = cases['case1']
ev = {}
for r in ROUTES:
    pe = P1[r] * realization_profile(r)
    ev[NAMES[r]] = dict(lifetime_ev=tot(pe), retire_ev=ret1[r] * ASSUME['retire_expected_factor'],
                        total_ev=tot(pe) + ret1[r] * ASSUME['retire_expected_factor'])
R['expected_value_case1'] = ev
pd.DataFrame(ev).T.round(2).to_csv(os.path.join(OUT, 'expected_value_case1.csv'))

# ------------------------------------------------------------------ crossovers (case1, gross; and net of direct costs)
pairs = [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D')]
cross = {}
for case in ['case1', 'case2', 'case3']:
    P, ret, _ = cases[case]
    for e, l in pairs:
        cross[f'{case}:{e}->{l}'] = dict(
            gross=cum_cross(P[e], P[l]),
            net_of_tuition=cum_cross(P[e], P[l], cost_profile(e), cost_profile(l)),
            net_of_tuition_living=cum_cross(P[e], P[l], cost_profile(e, True), cost_profile(l, True)))
R['crossover'] = cross

# ------------------------------------------------------------------ 編入 (B->C) investment analysis
inv = {}
for prem in [1.0, 1.03, ASSUME['national_premium_C'], 1.10, 1.15]:
    P, _ = route_profiles('case1')
    C = P['D'] * prem
    for living in [False, True]:
        cf = (C - P['B']) - (cost_profile('C', living) - cost_profile('B', living))
        cfr = cf.copy()
        key = f'prem{prem:.3f}_living{int(living)}'
        inv[key] = dict(
            diff_lifetime_gross=tot(C) - tot(P['B']),
            diff_with_retire=tot(C) + ASSUME['retire_case1']['C'] - tot(P['B']) - ASSUME['retire_case1']['B'],
            net_after_costs=float(cf.sum()) + ASSUME['retire_case1']['C'] - ASSUME['retire_case1']['B'],
            breakeven_age=cum_cross(P['B'], C, cost_profile('B', living), cost_profile('C', living)),
            npv2=npv(cf, 0.02) + (ASSUME['retire_case1']['C'] - ASSUME['retire_case1']['B']) / 1.02 ** 45,
            npv3=npv(cf, 0.03) + (ASSUME['retire_case1']['C'] - ASSUME['retire_case1']['B']) / 1.03 ** 45,
            irr=irr(np.append(cf, 0) + np.append(np.zeros(len(cf)), ASSUME['retire_case1']['C'] - ASSUME['retire_case1']['B'])))
R['transfer_investment'] = inv
# by case
for case in ['case2', 'case3']:
    P, ret, _ = cases[case]
    cf = (P['C'] - P['B']) - (cost_profile('C') - cost_profile('B'))
    R['transfer_investment'][case] = dict(diff_lifetime_gross=tot(P['C']) - tot(P['B']),
                                          diff_with_retire=tot(P['C']) + ret['C'] - tot(P['B']) - ret['B'],
                                          breakeven_age=cum_cross(P['B'], P['C'], cost_profile('B'), cost_profile('C')),
                                          npv2=npv(cf, 0.02))

# ------------------------------------------------------------------ sensitivity
def scen_totals(P, ret, mod=None):
    out = {}
    for r in ROUTES:
        p = P[r].copy(); rr = ret[r]
        if mod: p, rr = mod(r, p, rr)
        out[r] = dict(gross=tot(p), total=tot(p) + rr)
    return out

JILPT_SAME_FIRM = {'A': 256.7 / 215.6, 'B': 273.0 / 238.5, 'C': 289.7 / 262.8, 'D': 289.7 / 262.8}  # ユースフル労働統計2025 表21-3/21-1 (男性, 2024)

def growth(g):
    return lambda r, p, rr: (apply_growth(p, g), rr * (1 + g) ** (60 - 15))

def job_change(r, p, rr, bump=0.08):
    p = p.copy(); p[AGES >= 30] *= (1 + bump); return p, rr * 0.6

def same_firm(r, p, rr):
    return p * JILPT_SAME_FIRM[r], rr

def yakushoku_teinen(r, p, rr):
    p = p.copy(); cut = 0.90 if r in ('C', 'D') else 0.95
    p[(AGES >= 55) & (AGES < 60)] *= cut
    p59 = p[AGES == 59][0]
    p[AGES >= 60] = 0.55 * p59
    return p, rr

def stem_premium(r, p, rr):
    if r in ('C', 'D'):
        return p * 1.05, rr
    return p, rr

sens = {}
for case in ['case1', 'case2', 'case3']:
    P, ret, _ = cases[case]
    S = {}
    S['基準(2026年水準・実質成長0%)'] = scen_totals(P, ret)
    S['実質賃金 +0.5%/年'] = scen_totals(P, ret, growth(0.005))
    S['実質賃金 +1.0%/年'] = scen_totals(P, ret, growth(0.010))
    S['実質賃金 −0.5%/年'] = scen_totals(P, ret, growth(-0.005))
    S['同一企業で定年まで(標準労働者型)'] = scen_totals(P, ret, same_firm)
    S['30歳で転職し+8%（退職金6割）'] = scen_totals(P, ret, job_change)
    S['30歳で転職し+15%（IT想定・退職金6割）'] = scen_totals(P, ret, lambda r, p, rr: job_change(r, p, rr, 0.15))
    S['役職定年(55歳)・再雇用(60歳で59歳時の55%)'] = scen_totals(P, ret, yakushoku_teinen)
    if case == 'case1':
        S['理系(C・D)にさらに+5%の専攻プレミアム'] = scen_totals(P, ret, stem_premium)
    sens[case] = S
# large firm, regular employee until 65 (定年65: 60-64も1000人以上の正社員無期の水準)
def to65_large():
    P, _ = route_profiles('case2')
    out = {}
    for r, edu in zip(ROUTES, ['高校', 'kosen', '大学', '大学']):
        p = P[r].copy()
        if edu == 'kosen':
            reg = census('reg', '産業計', '高専・短大', '1000+'); s = S_LARGE['６０～６４歳']; k = KR.loc['６０～６４歳', 'k']
            v1 = float(to2026(reg.loc[['６０～６４歳']]).iloc[0]) / (s + (1 - s) * k)
            un = census('reg', '産業計', '大学', '1000+'); v2 = float(to2026(un.loc[['６０～６４歳']]).iloc[0]) * KR.loc['６０～６４歳', 'r_mean']
            v = (v1 + v2) / 2
        else:
            reg = census('reg', '産業計', edu, '1000+'); v = float(to2026(reg.loc[['６０～６４歳']]).iloc[0])
        p[AGES >= 60] = v
        out[r] = dict(gross=tot(p), total=tot(p) + ASSUME['retire_case2'][r])
    return out
sens['case2']['大企業の正社員のまま65歳まで(定年65歳型)'] = to65_large()
R['sensitivity'] = sens

# ------------------------------------------------------------------ same-ability comparison
P1, ret1, _ = cases['case1']; P2, ret2, _ = cases['case2']
hi = {'A': (P2['A'], ret2['A']), 'B': (P1['B'], ret1['B']), 'C': (P1['C'], ret1['C']), 'D': (P1['D'] * ASSUME['national_premium_C'], ret1['D'])}
mid = {'A': (P1['A'], ret1['A']), 'D': (P1['D'] * 0.95, ret1['D'] * 0.95)}
R['same_ability'] = {
    'high': {r: dict(gross=tot(v[0]), total=tot(v[0]) + v[1]) for r, v in hi.items()},
    'mid': {r: dict(gross=tot(v[0]), total=tot(v[0]) + v[1]) for r, v in mid.items()},
}
# tiers for D and C (multiplicative assumptions on D-typical)
TIERS = {'旧帝大・難関国公立': 1.15, '地方国公立': 1.05, '私立理工系(中堅)': 0.98, '私立理工系(入試難易度低)': 0.92}
R['tiers'] = {t: dict(D_gross=tot(P1['D'] * m), D_total=tot(P1['D'] * m) + ret1['D'], C_gross=tot(P1['D'] * m),
                      vs_B=tot(P1['D'] * m) + ret1['D'] - tot(P1['B']) - ret1['B']) for t, m in TIERS.items()}

# decade table / medians for main table
R['cases'] = {c: cases[c][2].round(3).to_dict(orient='index') for c in cases}
R['assume'] = {k: v for k, v in ASSUME.items()}
R['costs'] = COSTS; R['living_away'] = LIVING_AWAY
R['kosen_ratios'] = KR.round(4).to_dict(orient='index')

json.dump(R, open(os.path.join(OUT, 'results.json'), 'w'), ensure_ascii=False, indent=1, default=float)

if __name__ == '__main__':
    pd.set_option('display.width', 250)
    for c in cases:
        print('==', c); print(cases[c][2].round(1).to_string())
    print('kosen method range', {k: round(v, 1) for k, v in rng.items()})
    print('EV', pd.DataFrame(ev).T.round(1).to_string())
    print('crossover'); [print(' ', k, v) for k, v in cross.items()]
    print('transfer'); [print(' ', k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in inv.items()]
    for case in sens:
        print('== sens', case)
        df = pd.DataFrame({k: {r: v[r]['total'] for r in ROUTES} for k, v in sens[case].items()}).T
        print(df.round(1).to_string())
    print('same ability', json.dumps(R['same_ability'], ensure_ascii=False, default=lambda x: round(x, 1)))
    print('tiers', json.dumps(R['tiers'], ensure_ascii=False, default=lambda x: round(x, 1)))

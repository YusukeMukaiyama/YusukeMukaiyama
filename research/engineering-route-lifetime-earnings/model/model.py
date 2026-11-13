"""Lifetime-earnings model: 工業高校 / 高専 / 高専→大学編入 / 普通科→理工系大学 (male, Japan, 2026 wage level).

All money in 百万円 (million yen), 2026 nominal wage level unless noted.
Ages: a student who is 15 in 2026; earnings counted from work start through age 64 (= until the 65th birthday).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from inputs import census, kosen_ratios, kosen_share_large, BANDS, sh_stat, HERE

AGES = np.arange(15, 65)            # 15..64
ROUTES = ['A', 'B', 'C', 'D']
NAMES = {'A': 'A 工業高校卒', 'B': 'B 高専卒', 'C': 'C 高専→大学編入卒', 'D': 'D 普通科→理工系大学卒'}
START = {'A': 18, 'B': 20, 'C': 22, 'D': 22}

# ------------------------------------------------------------------ assumptions (all explicit)
ASSUME = dict(
    g_month_2026=0.030,      # 2025年6月→2026年水準の月例賃金ベースアップ (2026春闘 連合5.01% − 定昇分 ≈ 3%)
    g_bonus_2y=0.062,        # 賞与: 2024年支給額→2026年 (≈3.0-3.1%×2年)
    g_start_2026=0.035,      # 初任給 2025→2026
    first_year_bonus_months=1.0,   # 入社1年目の賞与 (所定内給与の月数)
    start_pay_2025={'高校': 210.1, '高専・短大': 241.4, '大学': 264.9},          # 千円, 男, 規模計 (新規学卒者表)
    start_pay_2025_1000={'高校': 218.2, '高専・短大': 247.3, '大学': 274.4},
    national_premium_C=1.065,      # C(国立中心の編入先) vs D典型(私大8割): 濱中(2017)国公立/私立比から院卒構成を補正して推計
    retire_case1={'A': 13.83, 'B': 18.0, 'C': 18.96, 'D': 18.96},   # 定年まで勤続した場合 (就労条件総合調査2023ベース)
    retire_case2={'A': 15.39, 'B': 20.0, 'C': 20.86, 'D': 20.86},   # 1000人以上 (JILPT表16-2の規模間格差で換算)
    retire_expected_factor=0.70,   # 期待値: 制度のある企業比率×勤続短縮の割引 (仮定)
)

# industry weights at first job (学校基本調査 令和7年度, 男) -> census sheet names
IND_MAP = {'建設業': 'Ｄ建設業', '製造業': 'Ｅ製造業', '電気・ガス・熱供給・水道業': 'Ｆ電気・ガス・熱供給・水道業',
           '情報通信業': 'Ｇ情報通信業', '運輸業，郵便業': 'Ｈ運輸業，郵便業', '卸売業，小売業': 'Ｉ卸売業，小売業',
           '金融業，保険業': 'Ｊ金融業，保険業', '不動産業，物品賃貸業': 'Ｋ不動産業，物品賃貸業',
           '学術研究，専門・技術サービス業': 'Ｌ学術研究，専門・技術サービス業', '宿泊業，飲食サービス業': 'Ｍ宿泊業，飲食サービス業',
           '生活関連サービス業，娯楽業': 'Ｎ生活関連サービス業，娯楽業', '教育，学習支援業': 'Ｏ教育，学習支援業',
           '医療，福祉': 'Ｐ医療，福祉', '複合サービス事業': 'Ｑ複合サービス事業', 'サービス業（他に分類されないもの）': 'Ｒサービス業（他に分類されないもの）'}
W_A = {'建設業': 18.3, '製造業': 53.6, '電気・ガス・熱供給・水道業': 3.5, '情報通信業': 1.0, '運輸業，郵便業': 4.8,
       '卸売業，小売業': 4.1, '学術研究，専門・技術サービス業': 2.7, 'サービス業（他に分類されないもの）': 4.6, 'その他': 7.4}
W_D_counts = {'建設業': 6749, '製造業': 10383, '電気・ガス・熱供給・水道業': 578, '情報通信業': 9052, '運輸業，郵便業': 917,
              '卸売業，小売業': 1847, '金融業，保険業': 447, '不動産業，物品賃貸業': 593, '学術研究，専門・技術サービス業': 2343,
              '宿泊業，飲食サービス業': 168, '生活関連サービス業，娯楽業': 197, '教育，学習支援業': 609, '医療，福祉': 252,
              '複合サービス事業': 75, 'サービス業（他に分類されないもの）': 3639, 'その他': 1822 + 305 + 43 + 18 + 60}
W_D = {k: 100 * v / sum(W_D_counts.values()) for k, v in W_D_counts.items()}

# ------------------------------------------------------------------ helpers
def to2026(df):
    """annual (百万円) at 2026 level from census row (kimatte 千円/月, bonus 千円/年)."""
    return (df.kimatte * 12 * (1 + ASSUME['g_month_2026']) + df.bonus * (1 + ASSUME['g_bonus_2y'])) / 1000.0

def band_points(edu, table_reg='reg', industry='産業計', size='規模計'):
    """(mean_age, annual_2026) per band; <=59 from 正社員無期, 60-64 from 一般労働者計 (再雇用・有期を含むフルタイム)."""
    reg = census(table_reg, industry, edu, size)
    allw = census('all', industry, edu, size)
    pts = {}
    for b in BANDS:
        src = allw if b == '６０～６４歳' else reg
        if pd.notna(src.loc[b, 'kimatte']):
            pts[b] = (float(src.loc[b, 'age']), float(to2026(src.loc[[b]]).iloc[0]))
    return pts

def ratio_series(points_num, points_den):
    return {b: points_num[b][1] / points_den[b][1] for b in points_num if b in points_den}

def build_profile(pts, start_age, first_year):
    """Single-age profile 15..64.  first year = explicit; ages up to 57 interpolate between band mean ages;
    55-59 band held flat from its mean age to 59; 60-64 = band value (定年後の段差を表現)."""
    prof = np.zeros(len(AGES))
    order = [b for b in BANDS if b in pts and b != '６０～６４歳']
    xs = [start_age] + [pts[b][0] for b in order if pts[b][0] > start_age + 0.5]
    ys = [first_year] + [pts[b][1] for b in order if pts[b][0] > start_age + 0.5]
    x59 = pts['５５～５９歳'][0]
    for i, a in enumerate(AGES):
        if a < start_age:
            continue
        if a >= 60:
            prof[i] = pts['６０～６４歳'][1]
        elif a >= x59:
            prof[i] = pts['５５～５９歳'][1]
        else:
            prof[i] = np.interp(a, xs, ys)
    return prof

def first_year_pay(edu, size='規模計', youngest_ratio=1.08):
    sp = (ASSUME['start_pay_2025'] if size == '規模計' else ASSUME['start_pay_2025_1000'])[edu]
    sp26 = sp * (1 + ASSUME['g_start_2026'])
    return (sp26 * youngest_ratio * 12 + sp26 * ASSUME['first_year_bonus_months']) / 1000.0

def industry_adjust(edu, weights, size='規模計'):
    """ratio (by band) of industry-mix-weighted profile to 産業計 profile, using 正社員無期 tables."""
    base = band_points(edu, size=size)
    acc = {b: 0.0 for b in base}
    tot = sum(weights.values())
    for ind, w in weights.items():
        if ind in IND_MAP:
            p = band_points(edu, industry=IND_MAP[ind], size=size)
        else:
            p = base
        for b in base:
            v = p.get(b, base[b])[1]
            acc[b] += w / tot * v
    out = {b: acc[b] / base[b][1] for b in base}
    if '５５～５９歳' in out:                       # 60-64 の産業別値は標本が薄く不安定なため 55-59 の値で据え置く
        out['６０～６４歳'] = out['５５～５９歳']
    return out

# ------------------------------------------------------------------ 高専 profile (two methods)
KR = kosen_ratios()
S_LARGE = kosen_share_large()

def kosen_points(industry='産業計', size='規模計', method='avg'):
    hs = band_points('高専・短大', industry=industry, size=size)
    un = band_points('大学', industry=industry, size=size)
    out = {}
    for b in hs:
        if b == '～１９歳':
            continue
        s = KR.loc[b, 's'] if size == '規模計' else S_LARGE[b]
        k = KR.loc[b, 'k']
        b1 = hs[b][1] / (s + (1 - s) * k)                        # 方法1: 賃金構造「高専・短大」から短大分を補正
        b2 = un[b][1] * KR.loc[b, 'r_mean'] if b in un else b1    # 方法2: 賃金構造「大学」×就業構造の高専/大学比
        v = {'m1': b1, 'm2': b2, 'avg': 0.5 * (b1 + b2)}[method]
        out[b] = (hs[b][0], v)
    return out

# ------------------------------------------------------------------ route profiles
def route_profiles(case='case1', kosen_method='avg'):
    if case == 'case1':
        size, ind = '規模計', '産業計'
    elif case == 'case2':
        size, ind = '1000+', '産業計'
    elif case == 'case3':
        size, ind = '規模計', 'Ｇ情報通信業'
    hs = band_points('高校', industry=ind, size=size)
    un = band_points('大学', industry=ind, size=size)
    kp = kosen_points(industry=ind, size=size, method=kosen_method)
    if case == 'case1':
        adjA = industry_adjust('高校', W_A); adjD = industry_adjust('大学', W_D)
    else:
        adjA = {b: 1.0 for b in hs}; adjD = {b: 1.0 for b in un}
    ptsA = {b: (hs[b][0], hs[b][1] * adjA.get(b, 1.0)) for b in hs}
    ptsD = {b: (un[b][0], un[b][1] * adjD.get(b, 1.0)) for b in un}
    sz = '規模計' if size == '規模計' else '1000'
    fyA = first_year_pay('高校', size=size) * adjA.get('～１９歳', 1.0)
    fyB = first_year_pay('高専・短大', size=size) * 1.0
    fyD = first_year_pay('大学', size=size) * adjD.get('２０～２４歳', 1.0)
    P = {}
    P['A'] = build_profile(ptsA, 18, fyA)
    P['B'] = build_profile(kp, 20, fyB)
    P['D'] = build_profile(ptsD, 22, fyD)
    prem = ASSUME['national_premium_C'] if case == 'case1' else 1.0
    P['C'] = P['D'] * prem
    meta = dict(adjA=adjA, adjD=adjD)
    return P, meta

# median/mean ratios (就業構造, pooled) by route education
def medmean_profile(route):
    col = {'A': 'medmean_高校', 'B': 'medmean_高専', 'C': 'medmean_大学', 'D': 'medmean_大学'}[route]
    r = np.ones(len(AGES))
    lo = {'２０～２４歳': 15, '２５～２９歳': 25, '３０～３４歳': 30, '３５～３９歳': 35, '４０～４４歳': 40,
          '４５～４９歳': 45, '５０～５４歳': 50, '５５～５９歳': 55, '６０～６４歳': 60}
    for b, a0 in lo.items():
        a1 = 25 if b == '２０～２４歳' else a0 + 5
        r[(AGES >= a0) & (AGES < a1)] = KR.loc[b, col]
    return r

def realization_profile(route):
    """expected per-capita income / regular-employee mean (就業構造: 就業率×全有業者平均 ÷ 正規平均)."""
    rz = pd.read_csv(os.path.join(HERE, 'realization.csv'))
    edu = {'A': '高校', 'B': '高専', 'C': '大学', 'D': '大学'}[route]
    piv = rz.pivot(index='age', columns='edu', values='factor')
    # 高専 is noisy: use 大学's age shape scaled to 高専's 25-59 average level
    core = [i for i in piv.index if i not in ('20～24歳', '60～64歳')]
    if edu == '高専':
        ser = piv['大学'] * (piv.loc[core, '高専'].mean() / piv.loc[core, '大学'].mean())
    else:
        ser = piv[edu]
    r = np.ones(len(AGES))
    for b, v in ser.items():
        a0 = int(b.split('～')[0]); a1 = a0 + 5
        if a0 == 20: a0 = 15
        r[(AGES >= a0) & (AGES < a1)] = v
    return r

# ------------------------------------------------------------------ taxes (2026 rules, single, no dependents)
def kyuyo_kojo(x):
    if x <= 1.9: return 0.65
    if x <= 3.6: return x * 0.3 + 0.08
    if x <= 6.6: return x * 0.2 + 0.44
    if x <= 8.5: return x * 0.1 + 1.10
    return 1.95

def income_tax(t):
    br = [(1.95, .05, 0), (3.30, .10, .0975), (6.95, .20, .4275), (9.00, .23, .636), (18.0, .33, 1.536), (40.0, .40, 2.796), (1e9, .45, 4.796)]
    if t <= 0: return 0.0
    for lim, rate, ded in br:
        if t <= lim:
            return (t * rate - ded) * 1.021

def net_income(gross, age, bonus_share=0.22):
    """gross annual (百万円) -> take-home. Social insurance employee share (2026): 健保5.0%, 介護0.8%(40-64),
    厚生年金9.15% (標準報酬月額上限65万・賞与150万×2回), 雇用0.5%, 子ども子育て支援金0.115%."""
    if gross <= 0: return 0.0
    monthly = gross * (1 - bonus_share) / 12; bonus = gross * bonus_share
    pen_base = min(monthly, 0.65) * 12 + min(bonus, 3.0)
    si = gross * (0.050 + 0.005 + 0.00115 + (0.008 if age >= 40 else 0)) + pen_base * 0.0915
    kyuyo = gross - kyuyo_kojo(gross)
    basic = 0.95 if kyuyo <= 1.32 else 0.58
    it = income_tax(max(0, kyuyo - si - basic))
    rt = max(0, kyuyo - si - 0.43) * 0.10 + 0.006
    return gross - si - it - rt

def retirement_net(R, years):
    ded = 0.4 * min(years, 20) + 0.7 * max(years - 20, 0)
    taxable = max(0, R - ded) / 2
    return R - income_tax(taxable) - taxable * 0.10

# ------------------------------------------------------------------ education direct costs (百万円, 2026 prices)
COSTS = {   # tuition & fees only (授業料・入学料・施設費). 生活費の追加分は別記
    'A': 0.0,                                  # 公立工業高校: 就学支援金で授業料実質無償
    'B': 0.0846 + 0.2346 * 2,                  # 国立高専: 入学料 + 4-5年次授業料 (1-3年は就学支援金)
    'C': 0.0846 + 0.2346 * 2 + 0.282 + 0.5358 * 2,  # + 国立大学3年次編入: 入学料 + 授業料2年
    'D': 0.8 * (0.245362 + (1.195313 + 0.161378) * 4) + 0.2 * (0.282 + 0.5358 * 4),  # 私立理科系8割/国公立2割
}
LIVING_AWAY = {'A': 0.0, 'B': 0.0, 'C': 0.8 * 2, 'D': 0.5 * 0.8 * 4}  # 下宿の追加生活費(年80万円、Dは半数が下宿と仮定)
COST_AGE = {'A': [], 'B': [15, 18, 19], 'C': [15, 18, 19, 20, 21], 'D': [18, 19, 20, 21]}

def cost_profile(route, include_living=False):
    c = np.zeros(len(AGES))
    total = COSTS[route] + (LIVING_AWAY[route] if include_living else 0)
    ages = COST_AGE[route]
    if ages:
        for a in ages:
            c[AGES == a] += total / len(ages)
    return c

# ------------------------------------------------------------------ summaries
def summarize(P, retire, med=True):
    rows = {}
    for r in ROUTES:
        p = P[r]
        pm = p * medmean_profile(r)
        def dec(lo, hi): return p[(AGES >= lo) & (AGES < hi)].mean()
        tenure = 60 - START[r]
        net = sum(net_income(p[i], a) for i, a in enumerate(AGES))
        rows[NAMES[r]] = {
            '就業開始': START[r],
            '20代平均年収': p[(AGES >= max(20, START[r])) & (AGES < 30)].mean(),
            '30代平均年収': dec(30, 40), '40代平均年収': dec(40, 50), '50代平均年収': dec(50, 60), '60-64平均年収': dec(60, 65),
            '累積額面(〜64歳,平均)': p.sum(),
            '累積額面(推計中央値)': pm.sum(),
            '退職金': retire[r],
            '退職金込み': p.sum() + retire[r],
            '手取り(退職金込み)': net + retirement_net(retire[r], tenure),
            '直接学費': COSTS[r],
        }
    return pd.DataFrame(rows).T

def crossover(p1, p2, cost1=None, cost2=None):
    """first age at which cumulative(p2) >= cumulative(p1) permanently (p2 starts later)."""
    c1 = np.cumsum(p1 - (cost1 if cost1 is not None else 0)); c2 = np.cumsum(p2 - (cost2 if cost2 is not None else 0))
    diff = c2 - c1
    for i in range(len(AGES)):
        if np.all(diff[i:] >= 0):
            return int(AGES[i]) if diff[i] >= 0 and (i == 0 or diff[i - 1] < 0 or True) else None
    return None

def apply_growth(p, g):
    return p * (1 + g) ** (AGES - 15)

def npv(x, r):
    return float(np.sum(x / (1 + r) ** (AGES - 15)))

if __name__ == '__main__':
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
    for case in ['case1', 'case2', 'case3']:
        P, meta = route_profiles(case)
        ret = ASSUME['retire_case2'] if case == 'case2' else ASSUME['retire_case1']
        print('=====', case)
        print(summarize(P, ret).round(2).to_string())

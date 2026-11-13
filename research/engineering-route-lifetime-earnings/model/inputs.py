"""Derive model inputs from parsed statistics.

Sources
- wage2025.csv : 令和7年賃金構造基本統計調査 (parsed by parse_wage.py)
    table 40421145 = 雇用形態別 第1表 正社員・正職員のうち雇用期間の定め無し (by industry sheet)
    table 40420843 = 一般 第1表 (一般労働者 all employment forms, by industry sheet)
- shugyo40.pkl : 令和4年就業構造基本調査 第40表 (所得×教育×年齢×雇用形態)
- sh000040077274.pkl : 同 第16表 (従業者規模×教育×年齢×雇用形態)
- sh000040077305.pkl : 同 第44表 (正規 職業×教育×年齢×所得)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from shugyo_stats import stats, num

HERE = os.path.dirname(os.path.abspath(__file__))
BANDS = ['～１９歳', '２０～２４歳', '２５～２９歳', '３０～３４歳', '３５～３９歳', '４０～４４歳',
         '４５～４９歳', '５０～５４歳', '５５～５９歳', '６０～６４歳']
BAND_LO = dict(zip(BANDS, [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]))

# ---------------------------------------------------------------- wage census
def census(table='reg', industry='産業計', edu='大学', size='規模計', sex='M'):
    d = pd.read_csv(os.path.join(HERE, 'wage2025.csv'))
    t = {'reg': 40421145, 'all': 40420843}[table]
    d = d[(d.table == t) & (d.industry == industry) & (d['sex'] == sex) & (d['size'] == size) & (d.edu == edu) & (d.band.isin(BANDS))]
    d = d.set_index('band').reindex(BANDS)
    for c in ['age', 'kimatte', 'shoteinai', 'bonus', 'n10']:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['annual'] = (d.kimatte * 12 + d.bonus) / 1000.0     # 百万円/年 (2025調査: 月額=2025年6月, 賞与=2024年)
    return d[['age', 'kimatte', 'shoteinai', 'bonus', 'annual', 'n10']]

# ------------------------------------------------------------ 就業構造基本調査
SH = pd.read_pickle(os.path.join(HERE, 'shugyo40.pkl'))
E40 = {'高校': '12_高校・旧制中（卒業者）', '短大': '16_短大（卒業者）', '高専': '17_高専（卒業者）',
       '大学': '18_大学（卒業者）', '大学院': '19_大学院（卒業者）'}
SH_AGE = {'２０～２４歳': ['02_20～24歳'], '２５～２９歳': ['03_25～29歳'], '３０～３４歳': ['04_30～34歳'],
          '３５～３９歳': ['05_35～39歳'], '４０～４４歳': ['06_40～44歳'], '４５～４９歳': ['07_45～49歳'],
          '５０～５４歳': ['08_50～54歳'], '５５～５９歳': ['09_55～59歳'], '６０～６４歳': ['10_60～64歳']}
# pooled windows (to reduce sampling noise for 高専, n≈150-250 per 5-yr band)
POOL = {'２０～２４歳': ['02_20～24歳', '03_25～29歳'],
        '２５～２９歳': ['03_25～29歳', '04_30～34歳'],
        '３０～３４歳': ['03_25～29歳', '04_30～34歳', '05_35～39歳'],
        '３５～３９歳': ['04_30～34歳', '05_35～39歳', '06_40～44歳'],
        '４０～４４歳': ['05_35～39歳', '06_40～44歳', '07_45～49歳'],
        '４５～４９歳': ['06_40～44歳', '07_45～49歳', '08_50～54歳'],
        '５０～５４歳': ['07_45～49歳', '08_50～54歳', '09_55～59歳'],
        '５５～５９歳': ['08_50～54歳', '09_55～59歳'],
        '６０～６４歳': ['10_60～64歳']}

def sh_counts(ages, edu, status='22_うち正規の職員・従業員'):
    s = SH[(SH.sex == '1_男') & (SH.marital == '0_総数') & (SH.age.isin(ages)) & (SH.status == status) & (SH.income != '00_総数')]
    c = s.groupby('income')[E40[edu]].apply(lambda x: sum(num(v) for v in x)).sort_index()
    return c.values

def sh_stat(band, edu, pooled=True):
    ages = POOL[band] if pooled else SH_AGE[band]
    m, med, q1, q3, N = stats(sh_counts(ages, edu))
    return dict(mean=m, median=med, q1=q1, q3=q3, N=N)

def kosen_ratios():
    """r = 高専/大学 (mean), k = 短大/高専 (mean), med ratios, all pooled windows; s = 高専 share of 高専+短大 (male regular)."""
    rows = []
    for b in SH_AGE:
        st = {e: sh_stat(b, e) for e in ['高校', '短大', '高専', '大学']}
        raw = {e: sh_stat(b, e, pooled=False) for e in ['短大', '高専']}
        s = raw['高専']['N'] / (raw['高専']['N'] + raw['短大']['N'])
        rows.append(dict(band=b, r_mean=st['高専']['mean'] / st['大学']['mean'],
                         r_med=st['高専']['median'] / st['大学']['median'],
                         k=st['短大']['mean'] / st['高専']['mean'], s=s,
                         medmean_高校=st['高校']['median'] / st['高校']['mean'],
                         medmean_高専=st['高専']['median'] / st['高専']['mean'],
                         medmean_大学=st['大学']['median'] / st['大学']['mean'],
                         n_kosen=raw['高専']['N']))
    return pd.DataFrame(rows).set_index('band')

def kosen_share_large():
    """高専 share among (高専+短大) male regular employees in 1000+ firms, by age (第16表)."""
    d = pd.read_pickle(os.path.join(HERE, 'sh000040077274.pkl'))
    d = d[(d['男女'] == '1_男') & (d['配偶関係'] == '0_総数') & (d['従業者規模'] == '11_1000人以上')]
    out = {}
    for b, ages in SH_AGE.items():
        x = d[d['年齢'].isin(ages)]
        k = x[x['教育'] == '17_高専（卒業者）']['12_うち正規の職員・従業員'].map(num).sum()
        t = x[x['教育'] == '16_短大（卒業者）']['12_うち正規の職員・従業員'].map(num).sum()
        out[b] = k / (k + t)
    return pd.Series(out)

if __name__ == '__main__':
    pd.set_option('display.width', 220)
    kr = kosen_ratios()
    kr['s_1000'] = kosen_share_large()
    print(kr.round(3).to_string())

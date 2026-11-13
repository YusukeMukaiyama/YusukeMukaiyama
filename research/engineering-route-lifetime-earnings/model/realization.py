import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, re
from shugyo_stats import stats, num
HERE=os.path.dirname(os.path.abspath(__file__))
pop=pd.read_pickle(os.path.join(HERE,'sh000040077243.pkl')); pop=pop[pop['男女']=='1_男']
t40=pd.read_pickle(os.path.join(HERE,'shugyo40.pkl'))
EDU40={'高校':'12_高校・旧制中（卒業者）','高専':'17_高専（卒業者）','大学':'18_大学（卒業者）','短大':'16_短大（卒業者）'}
AGES=['02_20～24歳','03_25～29歳','04_30～34歳','05_35～39歳','06_40～44歳','07_45～49歳','08_50～54歳','09_55～59歳','10_60～64歳']
rows=[]
for a in AGES:
    band=a.split('_')[1]
    for e,col in EDU40.items():
        # population
        key=[k for k in pop['年齢・教育'].unique() if k.endswith('（'+band+'）') and e in k and '卒業者' in k]
        if not key: continue
        pr=pop[pop['年齢・教育']==key[0]].iloc[0]
        P=num(pr['0_総数']); W=num(pr['1_有業者'])
        res={}
        for st in ['0_総数','22_うち正規の職員・従業員']:
            s=t40[(t40.sex=='1_男')&(t40.marital=='0_総数')&(t40.age==a)&(t40.status==st)&(t40.income!='00_総数')].sort_values('income')
            m,med,q1,q3,N=stats([num(x) for x in s[col]])
            res[st]=(m,N)
        exp_pc=(W/P)*res['0_総数'][0]
        rows.append(dict(age=band,edu=e,emp_rate=W/P,reg_share_of_pop=res['22_うち正規の職員・従業員'][1]/P,
                         mean_all=res['0_総数'][0],mean_reg=res['22_うち正規の職員・従業員'][0],factor=exp_pc/res['22_うち正規の職員・従業員'][0],key=key[0]))
r=pd.DataFrame(rows)
r.to_csv(os.path.join(HERE,'realization.csv'),index=False)
pd.set_option('display.width',200)
for v in ['emp_rate','reg_share_of_pop','factor']:
    print(v); print(r.pivot(index='age',columns='edu',values=v).round(3)[['高校','短大','高専','大学']].to_string())

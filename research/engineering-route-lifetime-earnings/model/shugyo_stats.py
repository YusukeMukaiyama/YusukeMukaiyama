import os
import pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
df=pd.read_pickle(os.path.join(HERE,'shugyo40.pkl'))
EDU={'高校':'12_高校・旧制中（卒業者）','短大':'16_短大（卒業者）','高専':'17_高専（卒業者）','大学':'18_大学（卒業者）','大学院':'19_大学院（卒業者）'}
B=[(0,50),(50,100),(100,150),(150,200),(200,250),(250,300),(300,400),(400,500),(500,600),(600,700),(700,800),(800,900),(900,1000),(1000,1250),(1250,1500),(1500,None)]
def num(x):
    if x in ('-',None,''): return 0.0
    return float(x)
def stats(counts):
    c=np.array(counts,float); N=c.sum()
    if N==0: return (np.nan,)*5
    # mean with midpoints; top bracket: Pareto alpha estimated from last two brackets -> fallback 1900
    mids=[(a+b)/2 for a,b in B[:-1]]
    # pareto for top: use ratio of counts >=1250 vs >=1500
    n1250=c[-2]+c[-1]; n1500=c[-1]
    top=1900.0
    if n1500>0 and n1250>n1500:
        alpha=np.log(n1250/n1500)/np.log(1500/1250)
        if alpha>1.2: top=1500*alpha/(alpha-1)
    mids.append(min(top,3000))
    mean=(c*np.array(mids)).sum()/N
    def q(p):
        cum=np.cumsum(c); t=p*N
        i=np.searchsorted(cum,t)
        lo,hi=B[i]; prev=cum[i-1] if i>0 else 0
        if hi is None: return float('nan')
        return lo+(hi-lo)*(t-prev)/c[i]
    return mean,q(0.5),q(0.25),q(0.75),N
def table(sex='1_男',status='22_うち正規の職員・従業員'):
    sub=df[(df.sex==sex)&(df.marital=='0_総数')&(df.status==status)]
    out=[]
    for age in sub.age.unique():
        s=sub[(sub.age==age)&(sub.income!='00_総数')].sort_values('income')
        for k,col in EDU.items():
            m,med,q1,q3,N=stats([num(x) for x in s[col]])
            out.append(dict(age=age,edu=k,mean=m,median=med,q1=q1,q3=q3,N=N))
    return pd.DataFrame(out)
if __name__=='__main__':
    t=table()
    t.to_csv(os.path.join(HERE,'shugyo_male_regular.csv'),index=False)
    pd.set_option('display.width',250)
    for v in ['mean','median','N']:
        print(v); print(t.pivot(index='age',columns='edu',values=v)[list(EDU)].round(0).to_string())

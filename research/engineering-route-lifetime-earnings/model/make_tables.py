import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
import analysis as AN
def oku(x): return f'{x/100:.2f}億円'
def md(df): return df.to_markdown()
out=[]
for c,title in [('case1','ケース1'),('case2','ケース2'),('case3','ケース3')]:
    S=AN.cases[c][2]
    t=pd.DataFrame({
      '就業開始':[f"{int(v)}歳" for v in S['就業開始']],
      '20代':S['20代平均年収'].map('{:.2f}'.format),'30代':S['30代平均年収'].map('{:.2f}'.format),
      '40代':S['40代平均年収'].map('{:.2f}'.format),'50代':S['50代平均年収'].map('{:.2f}'.format),
      '60〜64歳':S['60-64平均年収'].map('{:.2f}'.format),
      '賃金計(平均)':S['累積額面(〜64歳,平均)'].map(oku),'賃金計(推計中央値)':S['累積額面(推計中央値)'].map(oku),
      '退職金':S['退職金'].map('{:.1f}'.format),'退職金込み':S['退職金込み'].map(oku),'手取り概算':S['手取り(退職金込み)'].map(oku)},index=S.index)
    out.append(f'### {title}\n\n'+md(t)+'\n')
# sensitivity tables
for c in ['case1','case2','case3']:
    s=AN.R['sensitivity'][c]
    df=pd.DataFrame({k:{NAMES[r]:f"{v[r]['total']/100:.2f}" for r in ROUTES} for k,v in s.items()}).T
    out.append(f'### 感度分析 {c}（退職金込み・億円）\n\n'+md(df)+'\n')
ev=pd.DataFrame(AN.R['expected_value_case1']).T
out.append('### 期待値（雇用リスク込み）\n\n'+md(ev.map(lambda x: f'{x/100:.2f}'))+'\n')
open(os.path.join(HERE,'..','results','tables.md'),'w').write('\n'.join(out))
print('\n'.join(out))

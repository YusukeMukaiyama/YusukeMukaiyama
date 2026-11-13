"""Convert 令和4年就業構造基本調査 Excel tables (downloaded by run_all.sh) to pickles used by the model."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl, pandas as pd
from load_shugyo import load
HERE = os.path.dirname(os.path.abspath(__file__))
raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'raw')
# 第40表 (所得×教育×年齢×雇用形態): flat column names used by shugyo_stats.py
wb = openpyxl.load_workbook(os.path.join(raw, '000040077301.xlsx'), read_only=True, data_only=True)
rows = list(wb.worksheets[0].iter_rows(values_only=True))
hdr = rows[6]
data = [r for r in rows[9:] if r[0] is not None]
cols = ['l1', 'area', 'l2', 'sex', 'l3', 'marital', 'l4', 'age', 'l5', 'status', 'l6', 'income'] + [str(h) for h in hdr[12:]]
pd.DataFrame(data, columns=cols).to_pickle(os.path.join(HERE, 'shugyo40.pkl'))
# 第16表 (従業者規模), 第44表 (職業), 第2-1表 (就業状態)
for sid in ['000040077274', '000040077305', '000040077243']:
    load(os.path.join(raw, sid + '.xlsx')).to_pickle(os.path.join(HERE, 'sh' + sid + '.pkl'))
print('built pickles')

import openpyxl, pandas as pd, sys
def load(path):
    wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
    ws=wb.worksheets[0]
    rows=list(ws.iter_rows(values_only=True))
    for i,r in enumerate(rows[:20]):
        if r and any(str(x).startswith('項目名') for x in r if x): hi=i
        if r and r[0]=='階層レベル': di=i
    hdr=rows[hi]; dimrow=rows[di]
    k=[j for j,x in enumerate(hdr) if x=='項目名'][0]
    dimidx=list(range(1,k+1,2))
    cols=[str(dimrow[j]) for j in dimidx]+[str(h) for h in hdr[k+1:]]
    data=[[r[j] for j in dimidx]+list(r[k+1:]) for r in rows[di+1:] if r[0] is not None]
    return pd.DataFrame(data,columns=cols)
if __name__=='__main__':
    for p in sys.argv[1:]:
        df=load(p)
        out=p.split('/')[-1].replace('.xlsx','.pkl')
        df.to_pickle(out)
        print(p, df.shape); print(df.columns.tolist()[:12])
        for c in df.columns[:7]:
            u=df[c].unique(); print(' ',c,len(u),list(u)[:40])

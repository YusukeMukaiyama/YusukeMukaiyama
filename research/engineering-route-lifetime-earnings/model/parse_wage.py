import openpyxl, sys, re, csv
EDU={'学歴計','中学','高校','専門学校','高専・短大','大学','大学院','不明'}
SIZES=['規模計','1000+','100-999','10-99']
FIELDS=['age','tenure','hours','ot','kimatte','shoteinai','bonus','n10']
def norm(s): return re.sub(r'[\s　]','',str(s))
def parse(path, out, tag):
    wb=openpyxl.load_workbook(path,data_only=True,read_only=True)
    for ws in wb.worksheets:
        sex=None; edu=None
        for row in ws.iter_rows(values_only=True):
            lab=row[2] if len(row)>2 else None
            if lab is None: continue
            raw=str(lab); n=norm(raw)
            if '\n' in raw:
                a,b=[norm(x) for x in raw.split('\n',1)]
                sex={'男女計':'T','男':'M','女':'F'}.get(a,sex); edu=b; band='計'
            elif n in EDU:
                edu=n; band='計'
            else:
                band=n
            for si,sz in enumerate(SIZES):
                vals=row[3+si*8:3+si*8+8]
                if len(vals)<8: continue
                rec=[tag,ws.title,sex,edu,band,sz]+[None if v in ('-',None,'－','…') else v for v in vals]
                out.writerow(rec)
w=csv.writer(open(sys.argv[2],'w',newline=''))
w.writerow(['table','industry','sex','edu','band','size']+FIELDS)
for p in sys.argv[3:]:
    parse(p,w,p.split('/')[-1].split('.')[0])

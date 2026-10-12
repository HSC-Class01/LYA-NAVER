"""Open DART NAVER collector. Never logs API keys or request URLs."""
import os, json, re, io, zipfile, time, argparse
from pathlib import Path
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent
METRICS=json.loads((BASE/'config/metrics.json').read_text())
CODES={3:'11013',6:'11012',9:'11014',12:'11011'}
def load(p,default):
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.tmp'); temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(p)
def num(v):
 if v is None: return None
 s=str(v).replace(',','').replace(' ','').replace('−','-').strip()
 if s.startswith('(') and s.endswith(')'): s='-'+s[1:-1]
 return int(s) if re.fullmatch(r'-?\d+',s) else None
def norm(v): return re.sub(r'\s+','',v or '')
def ratio(a,b): return round(a/b*100,4) if a is not None and b is not None and b>0 else None
class Dart:
 def __init__(self,key): self.key=key; self.session=requests.Session()
 def request(self,endpoint,**params):
  for n in range(5):
   try:
    response=self.session.get('https://opendart.fss.or.kr/api/'+endpoint,params={'crtfc_key':self.key,**params},timeout=(15,120))
    if response.status_code==429 or response.status_code>=500:
     time.sleep(2**n); continue
    if response.status_code!=200: raise RuntimeError('DART HTTP status '+str(response.status_code))
    time.sleep(.2); return response
   except (requests.Timeout,requests.ConnectionError): time.sleep(2**n)
  raise RuntimeError('DART network request failed after retries')
 def json(self,endpoint,**params):
  for n in range(4):
   obj=self.request(endpoint,**params).json(); status=obj.get('status')
   if status=='000': return obj
   if status=='013': return {'list':[],'total_page':0,'status':'013'}
   if status in ('800','900'): time.sleep(2**n); continue
   raise RuntimeError('DART API error '+str(status)+' (check key, IP restrictions, quota)')
  raise RuntimeError('DART temporarily unavailable')
 def archive(self,endpoint,**params):
  content=self.request(endpoint,**params).content
  if not zipfile.is_zipfile(io.BytesIO(content)):
   soup=BeautifulSoup(content,'xml'); status=soup.find('status')
   raise RuntimeError('DART archive failed: '+(status.text if status else 'invalid ZIP'))
  return content
 def corporation(self):
  raw=self.archive('corpCode.xml')
  z=zipfile.ZipFile(io.BytesIO(raw)); soup=BeautifulSoup(z.read(z.namelist()[0]),'xml')
  for entry in soup.find_all('list'):
   if entry.stock_code and entry.stock_code.text.strip()=='035420': return entry.corp_code.text.strip()
  raise RuntimeError('NAVER stock code 035420 not found')
def period(item):
 name=item['report_nm']; m=re.search(r'\((\d{4})\.(\d{2})\)',name)
 if not m: return None
 year,month=map(int,m.groups())
 if year<2010 or month not in CODES: return None
 if not any(x in name for x in ['사업보고서','반기보고서','분기보고서']): return None
 return year,month

def extract(rows,month):
 values={}; evidence={}; issues=[]
 for metric,(sj,alt,ids,names) in METRICS.items():
  candidates=[r for r in rows if r.get('sj_div') in [sj,alt] and r.get('currency','KRW')=='KRW']
  selected=[]
  for statement in [sj,alt]:
   if statement is None: continue
   pool=[r for r in candidates if r.get('sj_div')==statement]
   selected=[r for r in pool if r.get('account_id') in ids]
   if not selected: selected=[r for r in pool if norm(r.get('account_nm')) in list(map(norm,names))]
   if selected: break
  # Ambiguous matches are not silently selected.
  field='thstrm_amount'
  if month!=12 and sj in ('IS','CIS'): field='thstrm_add_amount'
  amounts={num(r.get(field)) for r in selected}; amounts.discard(None)
  value=next(iter(amounts)) if len(amounts)==1 else None
  # Q1 YTD equals three-month figure; later quarters may not use it as YTD.
  if value is None and month==3 and len(selected)==1: value=num(selected[0].get('thstrm_amount')); field='thstrm_amount'
  values[metric]=value
  evidence[metric]=[{'account_id':r.get('account_id'),'account_nm':r.get('account_nm'),'statement':r.get('sj_div'),'field':field,'raw':r.get(field)} for r in selected]
  if value is None: issues.append(metric+': missing or ambiguous')
 return values,evidence,issues

def analyze(records):
 by={(r['year'],r['month'],r['basis']):r for r in records}
 for r in records:
  v=r['values']; prev=by.get((r['year']-1,r['month'],r['basis']))
  pv=prev['values'] if prev else {}
  v['operating_margin']=ratio(v.get('operating_profit'),v.get('revenue'))
  v['net_margin']=ratio(v.get('net_income'),v.get('revenue'))
  v['debt_equity']=ratio(v.get('liabilities'),v.get('equity'))
  v['current_ratio']=ratio(v.get('current_assets'),v.get('current_liabilities'))
  old=pv.get('revenue'); current=v.get('revenue')
  v['revenue_yoy']=ratio(current-old,old) if current is not None and old is not None else None
  # Annual only; average opening/closing total equity/assets, not parent-only equity.
  for key,den in [('roe','equity'),('roa','assets')]:
   a=v.get(den); b=pv.get(den)
   v[key]=ratio(v.get('net_income'),(a+b)/2) if r['month']==12 and a is not None and b is not None else None
 return records

def legacy_tables(raw,receipt):
 z=zipfile.ZipFile(io.BytesIO(raw)); out=[]
 for name in z.namelist():
  if not name.lower().endswith(('.xml','.html','.htm')): continue
  content=z.read(name)
  try: text=content.decode('utf-8')
  except UnicodeDecodeError: text=content.decode('euc-kr',errors='replace')
  soup=BeautifulSoup(text,'html.parser')
  for i,t in enumerate(soup.find_all('table')):
   txt=t.get_text(' ',strip=True)
   if not any(x in norm(txt) for x in ['자산총계','영업수익','영업이익','매출액','현금흐름']): continue
   out.append({'receipt':receipt,'file':name,'table':i,'context':str(t.find_previous())[:1500], 'rows':[[c.get_text(' ',strip=True) for c in row.find_all(['td','th','te'])] for row in t.find_all('tr')], 'status':'REQUIRES_REVIEW','reason':'Confirm consolidated scope, units, reporting period and restatements before using numbers'})
 return out

def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--full',action='store_true'); args=parser.parse_args()
 key=os.environ.get('DART_API_KEY','').strip()
 if len(key)!=40: raise SystemExit('Set DART_API_KEY to your 40-character Open DART key. Do not commit it.')
 dart=Dart(key); corp=dart.corporation(); today=datetime.now(timezone.utc).date()
 path=BASE/'data/filings.json'; old=load(path,[]); filings={x['rcept_no']:x for x in old}
 # Re-scan every receipt year: catches corrections to older fiscal periods.
 for year in range(2010,today.year+1):
  page=1
  while True:
   obj=dart.json('list.json',corp_code=corp,bgn_de=f'{year}0101',end_de=min(f'{year}1231',today.strftime('%Y%m%d')),pblntf_ty='A',last_reprt_at='N',page_count=100,page_no=page)
   for item in obj.get('list',[]):
    if period(item): filings[item['rcept_no']]=item
   if page>=int(obj.get('total_page',0)): break
   page+=1
 ordered=sorted(filings.values(),key=lambda x:x['rcept_no']); latest={}
 for item in ordered:
  p=period(item)
  # Withdrawn reports are excluded from financial selection, but retained in archive.
  if '철' not in item.get('rm',''): latest[p]=item
  receipt=item['rcept_no']; archive=BASE/f'data/reports/{receipt}.zip'
  if not archive.exists():
   content=dart.archive('document.xml',rcept_no=receipt); archive.parent.mkdir(parents=True,exist_ok=True); archive.write_bytes(content)
  if p[0]<2015:
   target=BASE/f'data/legacy_candidates/{receipt}.json'
   if not target.exists(): save(target,legacy_tables(archive.read_bytes(),receipt))
 records=[]; status=[]
 for (year,month),item in sorted(latest.items()):
  receipt=item['rcept_no']; target=BASE/f'data/raw/{year}-{month:02}.json'
  cache=load(target,{})
  if year<2015:
   status.append({'year':year,'month':month,'receipt':receipt,'status':'원문 저장 · 수치 검증 필요'}); continue
  if args.full or cache.get('selected_receipt')!=receipt or not cache.get('rows'):
   obj=dart.json('fnlttSinglAcntAll.json',corp_code=corp,bsns_year=year,reprt_code=CODES[month],fs_div='CFS'); basis='CFS'
   if not obj.get('list'):
    obj=dart.json('fnlttSinglAcntAll.json',corp_code=corp,bsns_year=year,reprt_code=CODES[month],fs_div='OFS'); basis='OFS'
   cache={'selected_receipt':receipt,'basis':basis,'rows':obj.get('list',[])}; save(target,cache)
  rows=cache['rows']
  if not rows:
   status.append({'year':year,'month':month,'receipt':receipt,'status':'API 데이터 없음 · 다음 실행 재조회'}); continue
  api_receipts=sorted(set(r.get('rcept_no','') for r in rows))
  values,evidence,issues=extract(rows,month)
  record={'year':year,'month':month,'category':'annual' if month==12 else 'Half-year' if month==6 else 'quarterly','basis':cache['basis'],'receipt':receipt,'api_receipts':api_receipts,'values':values,'evidence':evidence,'issues':issues,'verified_legacy':False}
  if api_receipts!=[receipt]: record['issues'].append('API 접수번호와 원문 접수번호 불일치: 정정 반영 여부 확인')
  records.append(record); status.append({'year':year,'month':month,'receipt':receipt,'status':'수치 추출 완료' if not record['issues'] else '추출 완료 · 일부 검토 필요'})
 for r in load(BASE/'data/manual_verified.json',[]):
  if not (2010<=r['year']<2015 and r['month'] in CODES and r.get('verified') is True and r.get('reviewer') and r.get('source_note')): raise ValueError('Invalid reviewed legacy record')
  r['category']='annual' if r['month']==12 else 'Half-year' if r['month']==6 else 'quarterly'
  r['verified_legacy']=True; r.setdefault('issues',[]); r.setdefault('evidence',{})
  records.append(r)
 records=analyze(sorted(records,key=lambda x:(x['year'],x['month'])))
 save(path,ordered)
 payload={'updated_at':datetime.now(timezone.utc).isoformat(),'records':records,'coverage':status,'peers':load(BASE/'config/peers.json',[]),'disclaimer':'2010–2014는 원문 표 추출 후 수동 검증 필요. 2013 분할·회계기준·연결범위 변화에 주의. 중간보고서 손익과 현금흐름은 연초 누적. ROE/ROA는 연간 총자본/총자산 평균 기준.'}
 save(BASE/'data/dashboard.json',payload)
 import build_site
 build_site.build(payload)
 print(f'Collected {len(ordered)} filings; {len(records)} financial periods. No secrets stored.')
if __name__=='__main__': main()

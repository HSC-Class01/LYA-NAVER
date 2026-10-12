import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
def build(payload=None):
 if payload is None:
  p=BASE/'data/dashboard.json'
  payload=json.loads(p.read_text()) if p.exists() else {'updated_at':None,'records':[],'coverage':[],'peers':json.loads((BASE/'config/peers.json').read_text()),'disclaimer':'DART API 키 등록 후 최초 수집을 실행하세요. 재무수치 샘플을 실제 데이터처럼 표시하지 않습니다. 2010–2014 원문 수치는 검증 필요.'}
 template=(BASE/'web/template.html').read_text(encoding='utf-8')
 data=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
 out=BASE/'docs'; out.mkdir(exist_ok=True)
 (out/'index.html').write_text(template.replace('__DATA__',data),encoding='utf-8')
if __name__=='__main__': build()

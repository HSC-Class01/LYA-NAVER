[![🔗 대시보드 바로가기](assets/dashboard-badge.svg)](https://hsc-class01.github.io/LYA-NAVER/)

# NAVER DART Financial Agent

2010년 사업연도부터 NAVER(035420)의 사업·반기·분기보고서 원문을 저장하고, 정기공시 재무수치와 재무비율을 분석하는 GitHub Pages 프로젝트입니다.

**배포 전 상태:** 이 ZIP은 소스 코드이며 DART 실데이터 수집이나 GitHub 배포가 아직 실행되지 않았습니다. 위 링크는 배포 후 사용할 예정 주소입니다. 첨부 지표 파일/배지 이미지가 전달되지 않아 표준 지표와 기본 SVG 배지를 사용했습니다.

## 빠른 설치 (GitHub 웹 업로드)
1. ZIP 압축을 풀고 **내부 파일/폴더를 저장소 루트**에 업로드합니다. ZIP 자체나 상위 폴더를 업로드하지 마세요. 기본 브랜치를 `main`으로 설정하세요.
2. Settings → Secrets and variables → Actions → New repository secret. 이름 `DART_API_KEY`, 값은 Open DART에서 발급받은 **40자리 인증키**입니다. API 키를 README/코드/웹에 넣지 마세요.
3. Settings → Actions → General → Workflow permissions → **Read and write permissions**. 조직 정책이나 main 브랜치 보호가 봇 push를 막으면 관리자의 허용이 필요합니다.
4. Settings → Pages → Build and deployment → Source: **GitHub Actions**.
5. 저장소 Add file → Create new file. 이름 **`.github/workflows/monthly.yml`**을 정확히 입력하고 `workflows/monthly.yml`의 내용을 붙여 넣어 main에 커밋하세요. 일반 `workflows/` 안에서는 Actions가 실행되지 않습니다.
6. Actions → NAVER DART monthly update → Run workflow. 초기 수집은 수분~수십 분 걸릴 수 있습니다. 완료 후 deploy 작업의 링크를 확인하세요.
7. 저장소 오른쪽 About → 톱니바퀴 → Website에 `https://hsc-class01.github.io/LYA-NAVER/` 입력 → Save changes. About은 저장소 메타데이터라 ZIP만으로 변경되지 않습니다.

## 로컬 Git 설치 대안
```bash
python -m pip install -r requirements.txt
python install_workflow.py
python -m unittest discover -s tests -v
git add .
git commit -m "Install NAVER DART agent"
git push origin main
```
API 키는 GitHub Secret에만 저장하면 됩니다. 로컬 수집이 필요한 경우 터미널 환경변수 `DART_API_KEY`를 설정하고 `python agent.py`를 실행하세요. `gh`가 이미 설치되고 인증된 사용자 PC에서는 About 링크도 다음으로 설정 가능합니다:
```bash
gh repo edit HSC-Class01/LYA-NAVER --homepage https://hsc-class01.github.io/LYA-NAVER/
```

## 자동 업데이트
- 매월 **1일 10:17 KST** (`17 1 1 * *`, UTC) 실행. 정각 혼잡을 피한 시간입니다. GitHub 스케줄은 지연될 수 있어 실행시각을 보장하지 않습니다.
- 2010년부터 모든 접수연도의 목록을 재조회하여 과거 사업연도 정정보고서도 탐지합니다.
- 접수번호별 원문 ZIP은 1회 저장. 같은 회계기간의 새 접수번호가 생기면 구조화 재무수치를 다시 조회합니다.
- 과거 데이터까지 다시 가져오려면 Run workflow의 `full_refresh` 체크.
- 공개 저장소는 장기간 활동이 없으면 예약 실행이 비활성화될 수 있습니다. Actions 화면에서 확인하세요.
- 분기 보고서 공시 직후가 아니라 다음 매월 1일에 반영됩니다. 필요시 수동 실행하세요.

## 2010–2014: 원문과 수치의 차이 (중요)
Open DART 전체 재무제표 API는 **2015년 이후**만 제공합니다. 2010–2014 원문 ZIP과 재무 관련 표 후보는 자동 수집하지만, 단위/연결 범위/당기 열을 검증하기 전 수치를 자동 확정하지 않습니다. 이 구간의 **완전 자동 재무수치 백필은 구현 완료 상태가 아닙니다**. 검증 후 `data/manual_verified.json`에 다음 형태로 등록하면 자동 재계산됩니다. 예시 값은 임의 숫자로 채우지 마세요.
```json
[
  {
    "year": 2010,
    "month": 12,
    "basis": "CFS",
    "receipt": "실제 14자리 접수번호",
    "verified": true,
    "reviewer": "검토자",
    "source_note": "원문 파일/표/당기 열/단위 및 연결 범위 검증 기록",
    "values": {"revenue": null, "operating_profit": null, "net_income": null, "assets": null, "liabilities": null, "equity": null}
  }
]
```
수치는 **원(KRW)** 정수로 등록합니다. 보고서가 백만원 단위라면 원으로 환산하세요. 기존 NHN의 2013년 인적분할 및 회계기준/연결 범위 변화 때문에 2010년부터 단순 성장률 비교는 주의가 필요합니다.

## 분석 기준
- 기본 연결 CFS, 연결 데이터가 아예 없으면 OFS 별도. 대시보드에서 별도 필터로 분리합니다.
- 주요 수치: 매출, 영업이익, 순이익(전체 연결), 자산/부채/자본, 유동자산/유동부채, 현금성자산, 영업/투자/재무 현금흐름.
- 영업이익률=영업이익/매출×100, 순이익률=순이익/매출×100.
- 부채비율=총부채/총자본×100, 유동비율=유동자산/유동부채×100.
- ROE=전체 순이익/평균 총자본×100, ROA=전체 순이익/평균 총자산×100. 연간만 계산, 지배주주 ROE가 아닙니다.
- 평균 분모는 전년 동일범위 기말과 당년 기말. 분모 0/음수 또는 전기 결측은 비율 미표시.
- 매출 YoY는 동일 보고기간·동일 CFS/OFS 간 비교. 전기 매출이 0/음수면 미표시.
- **Half-year는 6개월 누적, quarterly는 Q1 3개월/Q3 9개월 누적**. 반기 Q2와 연간 Q4 단독 분기 수치를 생성하지 않습니다.
- 중간 손익은 `thstrm_add_amount` 누적을 사용. Q1만 누적 누락시 3개월 값 사용. 현금흐름은 보고서의 연초 누적.
- 계정 ID 우선, 계정명 정확 일치 보완. 누락/모호한 매핑은 null로 남깁니다. 표의 `—`는 0이 아닙니다.
- 대시보드 금액은 억원, 다운로드 CSV는 원. API 원본/계정매핑 근거/접수번호를 함께 저장합니다.
- 정정 원문과 재무 API 접수번호가 다르면 검토 경고. API 정정 반영 지연시 `full_refresh`로 재확인하세요.
- PER/PBR/시가총액은 주가 소스가 없으므로 계산하지 않습니다. FCF도 CAPEX 구성 검증 없이 추정하지 않습니다.

## 구조
`agent.py`: API 수집/정정 탐지/재무 추출/비율 계산. `config/metrics.json`: 매핑 확장. `data/reports/`: 원문 ZIP. `data/raw/`: API 원본. `data/legacy_candidates/`: 과거 표 후보. `docs/index.html`: 배포 파일(데이터 내장). `web/template.html`: 디자인 원본. `workflows/monthly.yml`: 숨김 경로 없이 배포한 워크플로우 템플릿.

대시보드는 상단 KPI 및 4개 추이 차트, 하단 annual/Half-year/quarterly 각각의 테이블, 검증 상태, 국내 비교기업 표로 구성됩니다. Chart.js CDN에는 인터넷이 필요합니다. 의존 라이브러리가 실패해도 테이블은 동작합니다. HTML은 정적으로 점검했으며 실제 브라우저 시각 검증은 미실행입니다.

## 오류 점검
| 증상 | 조치 |
|---|---|
| Actions 항목이 없음 | `.github/workflows/monthly.yml` 정확한 경로와 main 브랜치 확인 |
| 키 오류 010/011/901 | 키 발급/유효성/계정 상태 확인 |
| IP 오류 012 | DART IP 제한 설정 확인. 공유 runner는 고정 IP가 아닙니다 |
| 요청 제한 020 | 한도 확인 후 재실행. 무한 재시도하지 않음 |
| git push 403 | Actions 쓰기 권한, 조직 정책, 브랜치 보호 확인 |
| Pages 404/배포 실패 | Pages Source=GitHub Actions, 공개 설정/요금제 및 environment 정책 확인 |
| 초기 실행 timeout | 저장 완료된 원문은 다음 실행에 재사용. Actions 수동 재실행 |
| 금액 누락 | data/raw 및 config/metrics의 계정명/누적필드 검토 |

소스·단위·비율 및 단위테스트는 점검했지만 **사용자 키로 실 API 테스트 및 GitHub 실제 배포는 아직 하지 않았습니다**. YAML 문법 검증은 계정권한/외부 API/Pages 설정 오류까지 보장하지 않습니다. 공개 저장소는 데이터도 공개되며 보고서 ZIP 누적 저장은 저장소 용량을 증가시킵니다. 원문 파일이 GitHub 단일 파일 한도를 넘는다면 LFS/외부 저장소로 변경해야 합니다.

## 국내 Peer Firms
| 기업 | 종목 | 비교 영역 | 비교시 유의 |
|---|---|---|---|
| [카카오](https://www.kakaocorp.com/) | 035720 | 플랫폼·광고·커머스·콘텐츠 | 핵심 비교기업, 사업구성 차이 |
| [NHN](https://www.nhn.com/company?tab=domesticCorporation&subTab=paymentAd) | 181710 | 결제·클라우드·커머스·게임 | 부문 비교용, 2013 분할 전후 주의 |
| [카페24](https://www.cafe24.com/) | 042000 | 커머스 플랫폼·판매자 솔루션 | 커머스 부문 비교용 |
| [쿠팡](https://ir.aboutcoupang.com/) | NYSE: CPNG | 국내 전자상거래 | 미국 상장 모회사, DART 연결비교 제외 |

Peer table은 사업영역 기반 정성 비교군이며 공식 peer 지정이나 자동 재무 비교 결과가 아닙니다.

## 공식 API 문서
- [공시검색](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)
- [원문 파일](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003)
- [전체 재무제표·2015년 이후 제공](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020)

# RSI 기반 주식 매매 시뮬레이션 시스템

이 프로젝트는 네이버 주식 API를 사용하여 10분종가 데이터를 수집하고, RSI(Relative Strength Index) 지표를 기반으로 한 매매 시뮬레이션을 수행하는 종합적인 주식 분석 도구입니다.

## 🚀 주요 기능

### 📊 데이터 수집 및 분석
- **10분종가 데이터 수집**: 네이버 주식 API를 통한 실시간 데이터 수집
- **RSI 지표 계산**: 다양한 기간 설정으로 RSI 계산
- **데이터 시각화**: 가격 차트와 RSI 차트 생성

### 🌐 웹 인터페이스
- **실시간 차트 뷰어**: 주가 및 RSI 차트를 웹에서 실시간 확인
- **종목 검색 기능**: 종목코드/종목명으로 빠른 검색 및 자동완성
- **반응형 디자인**: 모바일/데스크톱 모든 기기에서 최적화된 UI
- **인터랙티브 차트**: Chart.js 기반의 상호작용 가능한 차트

### 🤖 자동화된 매매 시뮬레이션
- **단일 종목 시뮬레이션**: 특정 종목에 대한 RSI 기반 매매 시뮬레이션
- **자동 파라미터 최적화**: oversold 25-35, overbought 65-75 범위에서 최적 파라미터 탐색
- **전체 종목 시뮬레이션**: 모든 종목에 대한 대규모 시뮬레이션
- **HTML 보고서 생성**: 시각적이고 상세한 분석 보고서

### 📈 고급 분석 기능
- **포트폴리오 가치 추적**: 실시간 포트폴리오 가치 변화 모니터링
- **수익률 분석**: 최대/최소 수익률, 평균 매수/매도가 분석
- **거래 통계**: 매수/매도 횟수, 거래 패턴 분석

## 📁 프로젝트 구조

```
rsi/
├── 📄 get_minute10.py                    # 10분종가 데이터 수집
├── 📄 calculate_rsi.py                   # RSI 지표 계산
├── 📄 calculate_rsi_with_previous.py     # 전일자 데이터 활용 RSI 계산
├── 📄 visualize_rsi.py                   # RSI 시각화
├── 📄 rsi_trading_simulation.py          # 기본 RSI 매매 시뮬레이션
├── 📄 rsi_trading_simulation_final.py    # 최종 RSI 매매 시뮬레이션
├── 📄 fix_encoding.py                    # 인코딩 수정 도구
├── 📄 config.json                        # 설정 파일
├── 📄 stock_rsi_chart.html               # 웹 차트 뷰어
├── 📄 README.md                          # 프로젝트 문서
└── 📁 data/
    ├── 📁 000020/                        # 종목별 데이터 폴더
    ├── 📁 000040/
    ├── 📁 000050/
    │   ├── 📄 stock_data_000050_20250718.json    # 원본 주식 데이터
    │   ├── 📄 rsi_data_000050_20250718.json      # RSI 계산 결과
    │   └── 📁 charts/                             # 차트 및 보고서
    │       ├── 📄 rsi_trading_final_chart_000050_20250718_*.png
    │       ├── 📄 rsi_auto_simulation_report_000050_20250718_*.html
    │       └── 📄 rsi_auto_simulation_results_000050_20250718_*.json
    ├── 📄 data_stock_all_fixed.csv       # 전체 종목 목록
    └── 📁 result/                        # 전체 종목 시뮬레이션 결과
```

## ⚙️ 설치 및 설정

### 1. 필수 패키지 설치

```bash
pip install pandas numpy matplotlib requests
```

### 2. 설정 파일 확인

`config.json` 파일에서 API 설정과 수집 시간을 확인하세요:

```json
{
    "time_settings": {
        "start_time": "09:00",
        "end_time": "20:00",
        "interval_minutes": 10
    },
    "api_settings": {
        "base_url": "https://api.stock.naver.com/chart/domestic/item",
        "endpoint": "minute10",
        "request_delay_seconds": 0.5
    }
}
```

## 🎯 사용법

### 0. 데이터 준비 및 인코딩 수정

```bash
# 전체 종목 json 생성 (data/data_stock_all_fixed.csv 기반)
python create_stock_json.py

# 인코딩 오류 데이터 일괄 수정
python fix_encoding.py
```

### 1. 웹 인터페이스 실행

#### 웹서버 시작

```bash
python -m http.server 8000
```

#### 웹 브라우저에서 접속

브라우저에서 다음 URL로 접속하세요:
```
http://localhost:8000/stock_rsi_chart.html
```

#### 웹 인터페이스 기능
- 종목 검색(자동완성), 날짜 선택, 실시간 차트, 상세 정보 확인 가능
- 반드시 웹서버를 통해 접근해야 하며, 데이터 범위(2025년 7월 11~18일) 내에서만 지원

### 2. 데이터 수집

```bash
# 단일 종목, 단일 날짜
python get_minute10.py 20250718 20250718 005930

# 여러 날짜, 여러 종목
python get_minute10.py 20250717 20250719 005930 000660
```

- 시작일/종료일: YYYYMMDD 형식
- 종목코드: 6자리(예: 005930)
- 결과: data/000660/stock_data_000660_20250718.json 등 생성

### 3. RSI 계산

```bash
# 단일 종목 RSI 계산
python calculate_rsi.py --stock_code 005930 --date 20250718

# 모든 종목 RSI 계산
python calculate_rsi.py --all

# 전일자 데이터 활용 (단일 종목)
python calculate_rsi_with_previous.py --stock_code 005930 --date 20250721

# 전일자 데이터 활용 (전 종목)
python calculate_rsi_with_previous.py --all

# 전일자 데이터 활용 (전 종목, 특정 날짜)
python calculate_rsi_with_previous.py --all --date 20250721
```

- `--all` 옵션을 사용하면 전체 종목에 대해 한 번에 실행할 수 있습니다.
- 결과 파일은 각 종목별 data/{종목코드}/rsi_data_{종목코드}_{날짜}.json 형태로 생성됩니다.

### 4. RSI 시각화

```bash
python visualize_rsi.py --stock_code 005930 --date 20250716
python visualize_rsi.py --all
```

- 결과: data/000660/charts/rsi_trading_final_chart_000660_20250718_*.png 등 생성

### 5. RSI 매매 시뮬레이션

```bash
# 기본
python rsi_trading_simulation_final.py

# 특정 종목/날짜
python rsi_trading_simulation_final.py --stock_code 005930 --date 20250718

# 자동 파라미터 최적화
python rsi_trading_simulation_final.py --stock_code 005930 --date 20250721 --auto_simulate --no_charts

# 전체 종목
python rsi_trading_simulation_final.py --all_stocks --date 20250721 --auto_simulate --no_charts
```

- 결과: data/000660/rsi_auto_simulation_report_000660_20250718_*.html, data/all_stocks_simulation_results_20250711_20250718_*.json 등 생성

### 6. 기타

- 데이터/결과 파일 인코딩 오류 발생 시 fix_encoding.py로 일괄 수정
- 종목 목록/구조 변경 시 create_stock_json.py로 재생성

## 📊 시뮬레이션 옵션

### 기본 시뮬레이션 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--stock_code`, `-s` | 종목코드 | 226950 |
| `--date`, `-d` | 날짜 (YYYYMMDD) | 20250718 |
| `--capital`, `-c` | 초기자본 (원) | 10,000,000 |
| `--oversold` | RSI 과매도 기준 | 40 |
| `--overbought` | RSI 과매수 기준 | 60 |

### 자동 시뮬레이션 옵션

| 옵션 | 설명 |
|------|------|
| `--auto_simulate` | oversold 25-35, overbought 65-75 범위에서 자동 시뮬레이션 |
| `--all_stocks` | 전체 종목에 대해 20250711~20250718 기간 시뮬레이션 |

## 📈 시뮬레이션 결과

### 출력 파일

#### 단일 종목 시뮬레이션
- **JSON 보고서**: `data/{종목코드}/rsi_trading_final_report_{종목코드}_{날짜}_{시간}.json`
- **차트 이미지**: `data/{종목코드}/charts/rsi_trading_final_chart_{종목코드}_{날짜}_{시간}.png`

#### 자동 시뮬레이션
- **JSON 결과**: `data/{종목코드}/rsi_auto_simulation_results_{종목코드}_{날짜}_{시간}.json`
- **HTML 보고서**: `data/{종목코드}/rsi_auto_simulation_report_{종목코드}_{날짜}_{시간}.html`

#### 전체 종목 시뮬레이션
- **JSON 결과**: `data/all_stocks_simulation_results_{시작일}_{종료일}_{시간}.json`

### 결과 분석 항목

#### 수익률 분석
- **최종 수익률**: 전체 거래 기간 수익률
- **최대 수익률**: 거래 중 최고 수익률
- **최대 손실률**: 거래 중 최저 손실률
- **평균 매수가/매도가**: 거래 가격 분석

#### 거래 통계
- **총 거래 횟수**: 매수/매도 총 횟수
- **매수 횟수**: 매수 신호 발생 횟수
- **매도 횟수**: 매도 신호 발생 횟수
- **포트폴리오 가치 변화**: 실시간 자산 가치 추적

#### RSI 분석
- **RSI 범위**: 최소/최대 RSI 값
- **과매수/과매도 구간**: RSI 기준별 발생 횟수
- **평균/중간값 RSI**: RSI 분포 분석

## 🎨 HTML 보고서

자동 시뮬레이션 시 생성되는 HTML 보고서는 다음과 같은 정보를 포함합니다:

### 📊 시뮬레이션 요약
- 총 시뮬레이션 횟수
- oversold/overbought 범위
- 최고 수익률

### 🏆 최고 수익률 결과
- 최적 RSI 기준값
- 상세한 수익률 분석
- 거래 통계

### 📋 전체 결과 테이블
- 수익률 순 정렬된 모든 결과
- 상세한 거래 정보
- 시각적 수익/손실 표시

### 📈 RSI 분석
- RSI 분포 통계
- 과매수/과매도 구간 분석

## 🔧 고급 기능

### 데이터 자동 준비

시뮬레이션 실행 시 필요한 데이터가 없으면 자동으로 생성합니다:

1. **10분가격 데이터 확인**: `get_minute10.py` 자동 실행
2. **RSI 데이터 확인**: `calculate_rsi.py` 자동 실행
3. **전일자 데이터 활용**: RSI 계산 시 전일자 데이터 활용 가능

### 한글 폰트 지원

Windows 환경에서 한글 폰트를 자동으로 설정하여 차트와 보고서에서 한글이 올바르게 표시됩니다.

### 에러 처리

- **파일 없음 처리**: 필요한 데이터 파일이 없으면 자동 생성
- **API 오류 처리**: 네트워크 오류 시 재시도 로직
- **데이터 검증**: 수집된 데이터의 유효성 검사

## 📝 사용 예시

### 0. 데이터 준비 및 인코딩 수정

```bash
python create_stock_json.py
python fix_encoding.py
```

### 1. 데이터 수집 및 RSI 계산

```bash
python get_minute10.py 20250718 20250718 005930
python calculate_rsi.py --stock_code 005930 --date 20250718
```

### 2. RSI 시각화 및 시뮬레이션

```bash
python visualize_rsi.py --stock_code 005930 --date 20250718
python rsi_trading_simulation_final.py --stock_code 005930 --date 20250718
```

### 3. 자동 최적화/전체 종목 분석

```bash
python rsi_trading_simulation_final.py --stock_code 005930 --date 20250718 --auto_simulate
python rsi_trading_simulation_final.py --all_stocks
```

### 4. 결과 파일 예시

- data/000660/rsi_data_000660_20250718.json
- data/000660/charts/rsi_trading_final_chart_000660_20250718_*.png
- data/000660/rsi_auto_simulation_report_000660_20250718_*.html
- data/all_stocks_simulation_results_20250711_20250718_*.json

## 🚨 주의사항

1. **API 호출 제한**: 네이버 API 호출 시 서버 부하를 고려하여 적절한 대기 시간 설정
2. **데이터 정확성**: 수집된 데이터의 정확성을 항상 확인
3. **시뮬레이션 한계**: 과거 데이터 기반 시뮬레이션이므로 실제 투자 결과와 다를 수 있음
4. **저장 공간**: 전체 종목 시뮬레이션 시 많은 저장 공간 필요
5. **웹 인터페이스**: 반드시 웹서버를 통해 접근해야 하며, 로컬 파일 접근 시 CORS 오류 발생
6. **데이터 범위**: 웹 인터페이스는 2025년 7월 11일~18일 데이터만 지원

## 📞 지원

프로젝트 관련 문의사항이나 버그 리포트는 이슈를 통해 제출해주세요.

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 투자에 사용하기 전에 충분한 검증이 필요합니다. 

import pandas as pd
import os

codes = pd.read_csv('data/data_stock_all_fixed.csv')['code']
for code in codes:
    os.system(f'python get_minute10.py 20250718 20250718 {code:06d}') 
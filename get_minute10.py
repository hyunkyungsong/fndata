import requests
import json
import sys
import os
from datetime import datetime, timedelta
import argparse

def load_config(config_file='config.json'):
    """
    설정 파일을 로드하는 함수
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"설정 파일 {config_file}을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError as e:
        print(f"설정 파일 형식이 올바르지 않습니다: {e}")
        return None

def get_stock_data(start_date, end_date, stock_code, config):
    """
    네이버 주식 API에서 10분종가 데이터를 가져오는 함수
    """
    headers = config['headers'].copy()
    headers['referer'] = f'https://finance.naver.com/item/fchart.naver?code={stock_code}'

    params = {
        'startDateTime': start_date,
        'endDateTime': end_date,
    }

    url = f"{config['api_settings']['base_url']}/{stock_code}/{config['api_settings']['endpoint']}"
    
    # 로그 설정에 따라 출력
    if config['log_settings']['show_api_url']:
        print(f"    API 요청 URL: {url}")
    if config['log_settings']['show_request_params']:
        print(f"    요청 파라미터: {params}")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"    HTTP 상태 코드: {response.status_code}")
        
        response.raise_for_status()
        
        # 응답 데이터 로그 출력
        response_data = response.json()
        
        if config['log_settings']['show_response_structure']:
            print(f"    응답 데이터 타입: {type(response_data)}")
            if isinstance(response_data, dict):
                print(f"    응답 데이터 키: {list(response_data.keys())}")
            elif isinstance(response_data, list):
                print(f"    응답 데이터는 리스트 형태, 길이: {len(response_data)}")
        
        # 응답 데이터 처리
        if isinstance(response_data, dict) and 'chartDomesticList' in response_data:
            # 기존 구조: {'chartDomesticList': [...]}
            data_list = response_data['chartDomesticList']
            print(f"    chartDomesticList 개수: {len(data_list)}")
            if data_list and config['log_settings']['show_sample_data']:
                print(f"    첫 번째 데이터 샘플: {data_list[0]}")
            return response_data
        elif isinstance(response_data, list):
            # 새로운 구조: [...] (직접 배열)
            print(f"    직접 배열 형태, 데이터 개수: {len(response_data)}")
            if response_data and config['log_settings']['show_sample_data']:
                print(f"    첫 번째 데이터 샘플: {response_data[0]}")
            # chartDomesticList 형태로 변환하여 반환
            return {'chartDomesticList': response_data}
        else:
            if config['log_settings']['show_response_structure']:
                print(f"    예상하지 못한 응답 형태: {response_data}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"    API 요청 중 오류 발생: {e}")
        if hasattr(e, 'response') and e.response is not None and config['log_settings']['show_error_details']:
            print(f"    오류 응답 상태 코드: {e.response.status_code}")
            print(f"    오류 응답 내용: {e.response.text}")
        return None

# def generate_time_slots(config):
#     """
#     설정에 따라 시간 슬롯을 생성하는 함수 (현재 사용하지 않음)
#     """
#     time_slots = []
#     start_time = datetime.strptime(config['time_settings']['start_time'], '%H:%M')
#     end_time = datetime.strptime(config['time_settings']['end_time'], '%H:%M')
#     interval = config['time_settings']['interval_minutes']
#     
#     current_time = start_time
#     while current_time <= end_time:
#         time_slots.append(current_time.strftime('%H%M'))
#         current_time += timedelta(minutes=interval)
#     
#     return time_slots

def collect_data_for_date_range(start_date, end_date, stock_code, config):
    """
    지정된 날짜 범위에 대해 설정에 따라 데이터를 수집하는 함수
    """
    # 날짜 범위 생성
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    print(f"시간 설정: {config['time_settings']['start_time']} ~ {config['time_settings']['end_time']}")
    print(f"수집 방식: 시작시간부터 종료시간까지 1회 수집")
    print(f"종목코드: {stock_code}")
    print(f"날짜 범위: {start_date} ~ {end_date}")
    print("=" * 50)
    
    # 날짜 리스트 생성
    date_list = []
    current_dt = start_dt
    while current_dt <= end_dt:
        date_list.append(current_dt.strftime('%Y%m%d'))
        current_dt += timedelta(days=1)
    total_dates = len(date_list)

    all_data = {}

    for idx, date_str in enumerate(date_list, 1):
        print(f"[{idx}/{total_dates}] 날짜 {date_str} 처리 중...")
        
        # 시작시간과 종료시간 설정
        start_datetime = f"{date_str}{config['time_settings']['start_time'].replace(':', '')}"
        end_datetime = f"{date_str}{config['time_settings']['end_time'].replace(':', '')}"
        
        print(f"  전체 시간대 {config['time_settings']['start_time']}~{config['time_settings']['end_time']} 데이터 수집 중...")
        print(f"    요청 시간 범위: {start_datetime} ~ {end_datetime}")
        
        # API 호출 (1회만)
        data = get_stock_data(start_datetime, end_datetime, stock_code, config)
        
        if data and 'chartDomesticList' in data and data['chartDomesticList']:
            daily_data = data['chartDomesticList']
            all_data[date_str] = daily_data
            print(f"    데이터 {len(daily_data)}개 수집 완료")
        else:
            print(f"    데이터 없음")
        
        print("=" * 50)
    
    return all_data

def save_data_by_date_and_stock(all_data, stock_code, start_date, end_date, config):
    """
    수집된 데이터를 일별, 종목별로 JSON 파일로 저장하는 함수
    """
    if not all_data:
        print(f"종목코드 {stock_code}에 대한 데이터가 없습니다.")
        return
    
    # data 폴더 생성
    data_dir = config['output_settings']['data_directory']
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"'{data_dir}' 폴더를 생성했습니다.")
    
    for date_str, day_data in all_data.items():
        filename = f"{config['output_settings']['file_prefix']}_{stock_code}_{date_str}.json"
        
        # 날짜별 폴더 생성 (변경)
        date_folder = os.path.join(data_dir, date_str)
        os.makedirs(date_folder, exist_ok=True)
        
        filepath = os.path.join(date_folder, filename)
        
        # 저장할 데이터 구조
        save_data = {
            'stock_code': stock_code,
            'date': date_str,
            'start_date': start_date,
            'end_date': end_date,
            'data_count': len(day_data),
            'collection_settings': {
                'start_time': config['time_settings']['start_time'],
                'end_time': config['time_settings']['end_time'],
                'interval_minutes': config['time_settings']['interval_minutes']
            },
            'data': day_data
        }
        
        with open(filepath, 'w', encoding=config['output_settings']['encoding']) as f:
            json.dump(save_data, f, ensure_ascii=False, indent=config['output_settings']['indent'])
        
        print(f"파일 저장 완료: {filepath} (데이터 {len(day_data)}개)")

def main():
    parser = argparse.ArgumentParser(description='네이버 주식 10분종가 데이터 수집')
    parser.add_argument('start_date', help='시작일 (YYYYMMDD 형식)')
    parser.add_argument('end_date', help='종료일 (YYYYMMDD 형식)')
    parser.add_argument('stock_code', nargs='?', help='종목코드 (예: 005930)')
    parser.add_argument('--all_stock', action='store_true', help='전체 종목 데이터 수집')
    parser.add_argument('--config', default='config.json', help='설정 파일 경로 (기본값: config.json)')
    
    args = parser.parse_args()
    
    # 설정 파일 로드
    config = load_config(args.config)
    if not config:
        print("설정 파일을 로드할 수 없어 프로그램을 종료합니다.")
        return
    
    # 입력값 검증
    try:
        datetime.strptime(args.start_date, '%Y%m%d')
        datetime.strptime(args.end_date, '%Y%m%d')
    except ValueError:
        print("날짜 형식이 올바르지 않습니다. YYYYMMDD 형식으로 입력해주세요.")
        return
    
    if args.all_stock:
        # 전체 종목 코드 읽기 (data/data_stock_all_fixed.csv)
        import pandas as pd
        stock_list_path = os.path.join('data', 'data_stock_all_fixed.csv')
        if not os.path.exists(stock_list_path):
            print(f"전체 종목 코드 파일이 존재하지 않습니다: {stock_list_path}")
            return
        df = pd.read_csv(stock_list_path)
        # 'code' 또는 '종목코드' 컬럼 자동 인식
        code_col = 'code' if 'code' in df.columns else ('종목코드' if '종목코드' in df.columns else None)
        if code_col is None:
            print('CSV 파일에 종목코드 컬럼이 없습니다. (code 또는 종목코드)')
            return
        codes = df[code_col].astype(str).str.zfill(6)
        print(f"전체 {len(codes)}개 종목 데이터 수집 시작...")
        for idx, code in enumerate(codes, 1):
            print(f"[{idx}/{len(codes)}] 종목코드: {code}")
            all_data = collect_data_for_date_range(args.start_date, args.end_date, code, config)
            if all_data:
                save_data_by_date_and_stock(all_data, code, args.start_date, args.end_date, config)
            else:
                print(f"  {code} 데이터 없음")
        print("전체 종목 데이터 수집이 완료되었습니다.")
    else:
        if not args.stock_code:
            print("종목코드를 입력하거나 --all_stock 옵션을 사용하세요.")
            return
        print(f"종목코드: {args.stock_code}")
        print(f"시작일: {args.start_date}")
        print(f"종료일: {args.end_date}")
        print(f"설정 파일: {args.config}")
        print("데이터 수집을 시작합니다...")
        # 데이터 수집
        all_data = collect_data_for_date_range(args.start_date, args.end_date, args.stock_code, config)
        if all_data:
            # 데이터를 일별, 종목별로 저장
            save_data_by_date_and_stock(all_data, args.stock_code, args.start_date, args.end_date, config)
            print("데이터 수집 및 저장이 완료되었습니다.")
        else:
            print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import glob

def calculate_rsi_with_previous_data(current_prices, previous_prices, period=14):
    """
    전일자 데이터를 활용하여 RSI(Relative Strength Index) 계산
    
    Args:
        current_prices (list): 현재일 가격 리스트
        previous_prices (list): 전일자 가격 리스트
        period (int): RSI 계산 기간 (기본값: 14)
    
    Returns:
        list: RSI 값 리스트
    """
    # 전일자 데이터와 현재일 데이터 결합
    all_prices = previous_prices + current_prices
    
    if len(all_prices) < period + 1:
        return [None] * len(current_prices)
    
    # 가격 변화 계산
    deltas = np.diff(all_prices)
    
    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 초기 평균 계산 (전일자 데이터 포함)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # 현재일 데이터에 대한 RSI 계산
    rsi_values = []
    
    # 전일자 데이터 이후부터 RSI 계산
    for i in range(len(previous_prices), len(all_prices) - 1):
        # 지수이동평균 방식으로 평균 업데이트
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

def find_previous_data_file(stock_code, current_date, max_lookback=7):
    """
    전일자(가장 가까운 이전 거래일) 데이터 파일을 찾는 함수
    토/일/공휴일 등 비거래일은 자동으로 건너뜀

    Args:
        stock_code (str): 종목 코드
        current_date (str): 현재일 (YYYYMMDD 형식)
        max_lookback (int): 최대 며칠 전까지 찾을지 (기본 7일)

    Returns:
        str: 전일자 데이터 파일 경로 또는 None
    """
    current_dt = datetime.strptime(current_date, '%Y%m%d')
    for i in range(1, max_lookback + 1):
        previous_dt = current_dt - pd.Timedelta(days=i)
        previous_date = previous_dt.strftime('%Y%m%d')
        previous_file = f"stock_data_{stock_code}_{previous_date}.json"
        previous_path = os.path.join('data', previous_date, previous_file)  # <--- 변경
        if os.path.exists(previous_path):
            return previous_path
    print(f"전일자 데이터 파일을 찾을 수 없습니다: {stock_code} {current_date} 기준 {max_lookback}일 내")
    return None

def process_stock_data_with_previous(file_path, rsi_period=14):
    """
    전일자 데이터를 활용하여 주식 데이터 파일을 읽어서 RSI를 계산하고 결과를 저장
    
    Args:
        file_path (str): 주식 데이터 파일 경로
        rsi_period (int): RSI 계산 기간
    """
    try:
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stock_code = data['stock_code']
        date = data['date']
        
        print(f"처리 중: {stock_code} ({date})")
        
        # 현재일 가격 데이터 추출
        current_prices = [item['currentPrice'] for item in data['data']]
        timestamps = [item['localDateTime'] for item in data['data']]
        
        # 전일자 데이터 찾기
        previous_file = find_previous_data_file(stock_code, date)
        previous_prices = []
        
        if previous_file:
            print(f"  전일자 데이터 활용: {os.path.basename(previous_file)}")
            with open(previous_file, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
            previous_prices = [item['currentPrice'] for item in previous_data['data']]
            print(f"  전일자 데이터 포인트: {len(previous_prices)}개")
        else:
            print("  전일자 데이터 없음 - 기본 RSI 계산 사용")
        
        # RSI 계산 (전일자 데이터 활용)
        if previous_prices:
            rsi_values = calculate_rsi_with_previous_data(current_prices, previous_prices, rsi_period)
        else:
            # 전일자 데이터가 없는 경우 기본 계산 사용
            rsi_values = calculate_rsi(current_prices, rsi_period)
        
        # 결과 데이터 생성
        result_data = []
        for i, (timestamp, price, rsi) in enumerate(zip(timestamps, current_prices, rsi_values)):
            result_item = {
                'localDateTime': timestamp,
                'currentPrice': price,
                'rsi': rsi,
                'rsi_period': rsi_period
            }
            result_data.append(result_item)
        
        # 결과 저장
        output_data = {
            'stock_code': stock_code,
            'date': date,
            'rsi_period': rsi_period,
            'data_count': len(result_data),
            'calculation_settings': {
                'rsi_period': rsi_period,
                'calculation_method': 'exponential_moving_average',
                'previous_data_used': previous_file is not None
            },
            'data': result_data
        }
        
        # 출력 파일명 생성
        output_filename = f"rsi_data_{stock_code}_{date}.json"
        
        # 일자별 폴더 생성
        date_folder = f"data/{date}"
        os.makedirs(date_folder, exist_ok=True)
        
        output_path = os.path.join(date_folder, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        
        print(f"RSI 계산 완료: {output_filename}")
        
        # RSI 통계 출력
        valid_rsi = [r for r in rsi_values if r is not None]
        if valid_rsi:
            print(f"  RSI 통계:")
            print(f"    최소값: {min(valid_rsi):.2f}")
            print(f"    최대값: {max(valid_rsi):.2f}")
            print(f"    평균값: {np.mean(valid_rsi):.2f}")
            print(f"    과매수 구간(>70): {sum(1 for r in valid_rsi if r > 70)}개")
            print(f"    과매도 구간(<30): {sum(1 for r in valid_rsi if r < 30)}개")
            print(f"    유효한 RSI 값: {len(valid_rsi)}개 (전체: {len(rsi_values)}개)")
        
        return output_data
        
    except Exception as e:
        print(f"오류 발생 ({file_path}): {str(e)}")
        return None

def calculate_rsi(prices, period=14):
    """
    기본 RSI 계산 함수 (기존 코드와 동일)
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    # 가격 변화 계산
    deltas = np.diff(prices)
    
    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 초기 평균 계산
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi_values = [None] * period  # 초기 period개는 None
    
    # RSI 계산
    for i in range(period, len(prices)):
        # 지수이동평균 방식으로 평균 업데이트
        avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

def process_all_stock_data_with_previous(data_dir='data', rsi_period=14, target_date=None):
    """
    data 디렉토리의 모든 주식 데이터 파일에 대해 전일자 데이터를 활용한 RSI 계산
    특정 날짜(target_date)가 주어지면 해당 날짜의 파일만 처리
    Args:
        data_dir (str): 데이터 디렉토리 경로
        rsi_period (int): RSI 계산 기간
        target_date (str): 처리할 날짜 (YYYYMMDD) 또는 None
    """
    # data 디렉토리 내의 모든 일자 폴더 찾기
    date_folders = []
    if os.path.exists(data_dir):
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path):
                date_folders.append(item_path)
    
    if not date_folders:
        print("처리할 일자 폴더를 찾을 수 없습니다.")
        return
    
    # 각 일자 폴더에서 stock_data_*.json 파일들 찾기
    stock_files = []
    for folder in date_folders:
        if target_date:
            if os.path.basename(folder) != target_date:
                continue
            pattern = os.path.join(folder, f'stock_data_*_{target_date}.json')
        else:
            pattern = os.path.join(folder, 'stock_data_*.json')
        files = glob.glob(pattern)
        stock_files.extend(files)
    
    if not stock_files:
        if target_date:
            print(f"{target_date}에 해당하는 주식 데이터 파일을 찾을 수 없습니다.")
        else:
            print("처리할 주식 데이터 파일을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(stock_files)}개의 주식 데이터 파일을 처리합니다.")
    print(f"RSI 계산 기간: {rsi_period}")
    if target_date:
        print(f"대상 날짜: {target_date}")
    print("전일자 데이터를 활용한 RSI 계산을 시작합니다.")
    print("-" * 50)
    
    results = []
    for file_path in stock_files:
        result = process_stock_data_with_previous(file_path, rsi_period)
        if result:
            results.append(result)
        print()
    
    print(f"처리 완료: {len(results)}개 파일")
    
    # 전체 통계 생성
    if results:
        create_summary_report(results)

def create_summary_report(results):
    """
    RSI 계산 결과에 대한 요약 보고서 생성
    
    Args:
        results (list): RSI 계산 결과 리스트
    """
    summary_data = {
        'calculation_date': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'total_files_processed': len(results),
        'rsi_period': results[0]['rsi_period'] if results else 14,
        'calculation_method': 'with_previous_data',
        'files': []
    }
    
    for result in results:
        stock_code = result['stock_code']
        date = result['date']
        
        # RSI 통계 계산
        valid_rsi = [item['rsi'] for item in result['data'] if item['rsi'] is not None]
        
        file_summary = {
            'stock_code': stock_code,
            'date': date,
            'data_count': result['data_count'],
            'previous_data_used': result['calculation_settings'].get('previous_data_used', False),
            'rsi_stats': {
                'min': min(valid_rsi) if valid_rsi else None,
                'max': max(valid_rsi) if valid_rsi else None,
                'mean': np.mean(valid_rsi) if valid_rsi else None,
                'overbought_count': sum(1 for r in valid_rsi if r > 70),
                'oversold_count': sum(1 for r in valid_rsi if r < 30),
                'valid_count': len(valid_rsi)
            }
        }
        summary_data['files'].append(file_summary)
    
    # 요약 보고서 저장
    summary_filename = f"rsi_summary_with_previous_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path = os.path.join('data', summary_filename)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=4)
    
    print(f"요약 보고서 생성: {summary_filename}")

def process_specific_stock_date(stock_code, date, rsi_period=14):
    """
    특정 종목과 날짜에 대한 RSI 계산
    
    Args:
        stock_code (str): 종목 코드
        date (str): 날짜 (YYYYMMDD 형식)
        rsi_period (int): RSI 계산 기간
    """
    # 파일 경로 생성
    file_path = os.path.join('data', date, f'stock_data_{stock_code}_{date}.json')
    
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return None
    
    print(f"특정 종목 RSI 계산: {stock_code} ({date})")
    print("=" * 50)
    
    return process_stock_data_with_previous(file_path, rsi_period)

if __name__ == "__main__":
    import argparse
    
    # 명령행 인수 파서 설정
    parser = argparse.ArgumentParser(description='전일자 데이터를 활용한 RSI 계산')
    parser.add_argument('--stock_code', type=str, help='종목 코드 (예: 005930)')
    parser.add_argument('--date', type=str, help='날짜 (YYYYMMDD 형식, 예: 20250716)')
    parser.add_argument('--period', type=int, default=14, help='RSI 계산 기간 (기본값: 14)')
    parser.add_argument('--all', action='store_true', help='모든 종목 데이터 처리')
    
    args = parser.parse_args()
    
    # 기본 RSI 기간
    RSI_PERIOD = args.period
    
    print("전일자 데이터를 활용한 RSI 지표 계산을 시작합니다.")
    print(f"RSI 계산 기간: {RSI_PERIOD}")
    print("=" * 60)
    
    if args.stock_code and args.date:
        # 특정 종목과 날짜에 대한 RSI 계산
        process_specific_stock_date(args.stock_code, args.date, RSI_PERIOD)
    elif args.all:
        # 모든 주식 데이터 파일 처리
        # 날짜가 지정되면 해당 날짜만 처리
        process_all_stock_data_with_previous(rsi_period=RSI_PERIOD, target_date=args.date)
    else:
        print("사용법:")
        print("  특정 종목 계산: python calculate_rsi_with_previous.py --stock_code 005930 --date 20250716")
        print("  모든 종목 계산: python calculate_rsi_with_previous.py --all")
        print("  특정 날짜 전체 종목 계산: python calculate_rsi_with_previous.py --all --date 20250716")
        print("  RSI 기간 변경: python calculate_rsi_with_previous.py --stock_code 005930 --date 20250716 --period 21")
    
    print("\nRSI 계산이 완료되었습니다!")
    print("결과 파일은 'data' 디렉토리에 저장되었습니다.") 
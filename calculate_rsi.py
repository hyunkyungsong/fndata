import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import argparse

def calculate_rsi_with_previous_data(current_prices, previous_prices=None, period=14):
    """
    전일자 데이터를 활용하여 RSI(Relative Strength Index) 계산
    
    Args:
        current_prices (list): 현재 날짜의 가격 리스트
        previous_prices (list): 전일자 가격 리스트 (선택사항)
        period (int): RSI 계산 기간 (기본값: 14)
    
    Returns:
        list: RSI 값 리스트
    """
    # 전일자 데이터가 있으면 결합
    if previous_prices:
        all_prices = previous_prices + current_prices
        print(f"  전일자 데이터 활용: 전일 {len(previous_prices)}개 + 당일 {len(current_prices)}개 = 총 {len(all_prices)}개")
    else:
        all_prices = current_prices
        print(f"  전일자 데이터 없음: 당일 {len(current_prices)}개만 사용")
    
    if len(all_prices) < period + 1:
        print(f"  경고: 데이터 부족 (필요: {period + 1}개, 보유: {len(all_prices)}개)")
        return [None] * len(current_prices)
    
    # 가격 변화 계산
    deltas = np.diff(all_prices)
    
    # 상승/하락 분리
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 초기 평균 계산
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # 전체 데이터에 대한 RSI 계산
    rsi_values_all = [None] * period  # 초기 period개는 None
    
    # RSI 계산
    for i in range(period, len(all_prices)):
        # 지수이동평균 방식으로 평균 업데이트
        avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values_all.append(rsi)
    
    # 전일자 데이터가 있으면 당일 데이터 부분만 반환
    if previous_prices:
        return rsi_values_all[len(previous_prices):]
    else:
        return rsi_values_all

def get_previous_date_data(stock_code, current_date, data_dir='data'):
    """
    전영업일 데이터를 가져오는 함수 (주말, 공휴일 고려)
    
    Args:
        stock_code (str): 종목코드
        current_date (str): 현재 날짜 (YYYYMMDD 형식)
        data_dir (str): 데이터 디렉토리
    
    Returns:
        list: 전영업일 가격 데이터 (없으면 None)
    """
    try:
        # 현재 날짜를 datetime 객체로 변환
        current_dt = datetime.strptime(current_date, '%Y%m%d')
        
        # 최대 7일 전까지 확인 (주말 고려)
        for days_back in range(1, 8):
            previous_dt = current_dt - timedelta(days=days_back)
            previous_date = previous_dt.strftime('%Y%m%d')
            
            # 전영업일 파일 경로
            previous_file = os.path.join(data_dir, stock_code, f'stock_data_{stock_code}_{previous_date}.json')
            
            if os.path.exists(previous_file):
                print(f"  전영업일 데이터 파일 발견: {previous_date} ({days_back}일 전)")
                with open(previous_file, 'r', encoding='utf-8') as f:
                    previous_data = json.load(f)
                
                # 전영업일 가격 데이터 추출 (최근 14개 데이터 사용)
                previous_prices = [item['currentPrice'] for item in previous_data['data']]
                # 최근 14개만 사용 (RSI 계산에 충분한 데이터)
                if len(previous_prices) > 14:
                    previous_prices = previous_prices[-14:]
                
                print(f"  전영업일 가격 데이터 {len(previous_prices)}개 로드 완료")
                return previous_prices
        
        print(f"  전영업일 데이터 파일 없음: 최근 7일 내 데이터 확인 완료")
        return None
            
    except Exception as e:
        print(f"  전영업일 데이터 로드 중 오류: {str(e)}")
        return None

def process_stock_data(file_path, rsi_period=14, use_previous_data=True):
    """
    주식 데이터 파일을 읽어서 RSI를 계산하고 결과를 저장
    
    Args:
        file_path (str): 주식 데이터 파일 경로
        rsi_period (int): RSI 계산 기간
        use_previous_data (bool): 전일자 데이터 사용 여부
    """
    try:
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stock_code = data['stock_code']
        date = data['date']
        
        print(f"처리 중: {stock_code} ({date})")
        
        # 현재 날짜의 가격 데이터 추출
        current_prices = [item['currentPrice'] for item in data['data']]
        timestamps = [item['localDateTime'] for item in data['data']]
        
        # 전일자 데이터 가져오기
        previous_prices = None
        if use_previous_data:
            previous_prices = get_previous_date_data(stock_code, date)
        
        # RSI 계산 (전일자 데이터 활용)
        rsi_values = calculate_rsi_with_previous_data(current_prices, previous_prices, rsi_period)
        
        # 결과 데이터 생성
        result_data = []
        for i, (timestamp, price, rsi) in enumerate(zip(timestamps, current_prices, rsi_values)):
            result_item = {
                'localDateTime': timestamp,
                'currentPrice': price,
                'rsi': rsi,
                'rsi_period': rsi_period,
                'calculation_method': 'with_previous_data' if previous_prices else 'current_data_only'
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
                'used_previous_data': previous_prices is not None,
                'previous_data_count': len(previous_prices) if previous_prices else 0
            },
            'data': result_data
        }
        
        # 출력 파일명 생성
        output_filename = f"rsi_data_{stock_code}_{date}.json"
        
        # 종목별 폴더 생성
        stock_folder = f"data/{stock_code}"
        os.makedirs(stock_folder, exist_ok=True)
        
        output_path = os.path.join(stock_folder, output_filename)
        
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
        
        return output_data
        
    except Exception as e:
        print(f"오류 발생 ({file_path}): {str(e)}")
        return None

def process_all_stock_data(data_dir='data', rsi_period=14):
    """
    data 디렉토리의 모든 주식 데이터 파일에 대해 RSI를 계산
    
    Args:
        data_dir (str): 데이터 디렉토리 경로
        rsi_period (int): RSI 계산 기간
    """
    # stock_data_*.json 파일들 찾기
    pattern = os.path.join(data_dir, 'stock_data_*.json')
    stock_files = glob.glob(pattern)
    
    if not stock_files:
        print("처리할 주식 데이터 파일을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(stock_files)}개의 주식 데이터 파일을 처리합니다.")
    print(f"RSI 계산 기간: {rsi_period}")
    print("-" * 50)
    
    results = []
    for file_path in stock_files:
        result = process_stock_data(file_path, rsi_period)
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
            'rsi_stats': {
                'min': min(valid_rsi) if valid_rsi else None,
                'max': max(valid_rsi) if valid_rsi else None,
                'mean': np.mean(valid_rsi) if valid_rsi else None,
                'overbought_count': sum(1 for r in valid_rsi if r > 70),
                'oversold_count': sum(1 for r in valid_rsi if r < 30)
            }
        }
        summary_data['files'].append(file_summary)
    
    # 요약 보고서 저장
    summary_filename = f"rsi_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path = os.path.join('data', summary_filename)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=4)
    
    print(f"요약 보고서 생성: {summary_filename}")

def process_specific_stock_data(stock_code, date, rsi_period=14, use_previous_data=True):
    """
    특정 종목코드와 날짜에 대한 주식 데이터 파일을 읽어서 RSI를 계산하고 결과를 저장
    
    Args:
        stock_code (str): 종목코드
        date (str): 날짜 (YYYYMMDD 형식)
        rsi_period (int): RSI 계산 기간
        use_previous_data (bool): 전일자 데이터 사용 여부
    """
    # 입력 파일명 생성
    input_filename = f"stock_data_{stock_code}_{date}.json"
    input_path = os.path.join('data', stock_code, input_filename)
    
    if not os.path.exists(input_path):
        print(f"파일을 찾을 수 없습니다: {input_path}")
        return None
    
    return process_stock_data(input_path, rsi_period, use_previous_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='주식 데이터로 RSI 지표 계산')
    parser.add_argument('--date', help='날짜 (YYYYMMDD 형식, 예: 20250717)')
    parser.add_argument('--stock_code', help='종목코드 (예: 005930)')
    parser.add_argument('--rsi_period', type=int, default=14, help='RSI 계산 기간 (기본값: 14)')
    parser.add_argument('--all', action='store_true', help='모든 주식 데이터 파일 처리')
    parser.add_argument('--no_previous_data', action='store_true', help='전일자 데이터 사용하지 않음')
    
    args = parser.parse_args()
    
    # 기본 RSI 기간 (14일이 표준)
    RSI_PERIOD = args.rsi_period
    USE_PREVIOUS_DATA = not args.no_previous_data
    
    print("종목별 10분 가격 데이터로 RSI 지표 계산을 시작합니다.")
    print(f"RSI 계산 기간: {RSI_PERIOD}")
    print(f"전일자 데이터 사용: {'예' if USE_PREVIOUS_DATA else '아니오'}")
    print("=" * 60)
    
    if args.all:
        # 모든 주식 데이터 파일 처리
        process_all_stock_data(rsi_period=RSI_PERIOD)
    elif args.date and args.stock_code:
        # 특정 종목과 날짜에 대한 처리
        print(f"종목코드: {args.stock_code}")
        print(f"날짜: {args.date}")
        print("-" * 50)
        
        result = process_specific_stock_data(args.stock_code, args.date, RSI_PERIOD, USE_PREVIOUS_DATA)
        if result:
            print(f"\nRSI 계산이 완료되었습니다!")
            print(f"결과 파일: data/rsi_data_{args.stock_code}_{args.date}.json")
        else:
            print("RSI 계산에 실패했습니다.")
    else:
        print("사용법:")
        print("  특정 종목과 날짜: python calculate_rsi.py --date 20250717 --stock_code 005930")
        print("  전일자 데이터 없이: python calculate_rsi.py --date 20250717 --stock_code 005930 --no_previous_data")
        print("  모든 파일 처리: python calculate_rsi.py --all")
        print("  RSI 기간 변경: python calculate_rsi.py --date 20250717 --stock_code 005930 --rsi_period 21") 
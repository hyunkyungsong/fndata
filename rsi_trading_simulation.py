import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
import argparse

# 한글 폰트 설정
rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_rsi_data(stock_code, date):
    """
    RSI 데이터 파일을 로드하는 함수
    
    Args:
        stock_code (str): 종목 코드
        date (str): 날짜 (YYYYMMDD 형식)
    
    Returns:
        dict: RSI 데이터
    """
    file_path = f"data/rsi_data_{stock_code}_{date}.json"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"RSI 데이터 파일을 찾을 수 없습니다: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def simulate_rsi_trading(rsi_data, initial_capital=10000000, rsi_oversold=30, rsi_overbought=70):
    """
    RSI 기반 매매 시뮬레이션
    
    Args:
        rsi_data (dict): RSI 데이터
        initial_capital (int): 초기 자본금 (원)
        rsi_oversold (int): 과매도 기준 (기본값: 30)
        rsi_overbought (int): 과매수 기준 (기본값: 70)
    
    Returns:
        dict: 시뮬레이션 결과
    """
    data = rsi_data['data']
    stock_code = rsi_data['stock_code']
    date = rsi_data['date']
    
    # 시뮬레이션 변수 초기화
    capital = initial_capital  # 현금
    shares = 0  # 보유 주식 수
    total_value = initial_capital  # 총 자산가치
    trades = []  # 거래 기록
    portfolio_values = []  # 포트폴리오 가치 기록
    
    # 첫 번째 유효한 RSI 값 찾기
    start_idx = 0
    for i, item in enumerate(data):
        if item['rsi'] is not None:
            start_idx = i
            break
    
    # 시뮬레이션 실행
    for i in range(start_idx, len(data)):
        item = data[i]
        current_price = item['currentPrice']
        rsi = item['rsi']
        timestamp = item['localDateTime']
        
        if rsi is None:
            continue
        
        # 매수 신호 (과매도)
        if rsi < rsi_oversold and capital > 0:
            # 전액 매수
            shares_to_buy = capital // current_price
            if shares_to_buy > 0:
                cost = shares_to_buy * current_price
                capital -= cost
                shares += shares_to_buy
                
                trades.append({
                    'timestamp': timestamp,
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares_to_buy,
                    'cost': cost,
                    'rsi': rsi,
                    'capital': capital,
                    'shares_held': shares
                })
        
        # 매도 신호 (과매수)
        elif rsi > rsi_overbought and shares > 0:
            # 전량 매도
            revenue = shares * current_price
            capital += revenue
            
            trades.append({
                'timestamp': timestamp,
                'action': 'SELL',
                'price': current_price,
                'shares': shares,
                'revenue': revenue,
                'rsi': rsi,
                'capital': capital,
                'shares_held': 0
            })
            
            shares = 0
        
        # 현재 포트폴리오 가치 계산
        current_portfolio_value = capital + (shares * current_price)
        portfolio_values.append({
            'timestamp': timestamp,
            'price': current_price,
            'rsi': rsi,
            'capital': capital,
            'shares': shares,
            'portfolio_value': current_portfolio_value
        })
    
    # 마지막 거래일 종가로 모든 주식 매도 (청산)
    if shares > 0:
        final_price = data[-1]['currentPrice']
        final_revenue = shares * final_price
        capital += final_revenue
        
        trades.append({
            'timestamp': data[-1]['localDateTime'],
            'action': 'FINAL_SELL',
            'price': final_price,
            'shares': shares,
            'revenue': final_revenue,
            'rsi': data[-1]['rsi'],
            'capital': capital,
            'shares_held': 0
        })
    
    # 수익률 계산
    final_value = capital
    profit = final_value - initial_capital
    profit_rate = (profit / initial_capital) * 100
    
    # 거래 통계
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    sell_trades = [t for t in trades if t['action'] in ['SELL', 'FINAL_SELL']]
    
    # 평균 매수/매도 가격
    avg_buy_price = np.mean([t['price'] for t in buy_trades]) if buy_trades else 0
    avg_sell_price = np.mean([t['price'] for t in sell_trades]) if sell_trades else 0
    
    result = {
        'stock_code': stock_code,
        'date': date,
        'initial_capital': initial_capital,
        'final_value': final_value,
        'profit': profit,
        'profit_rate': profit_rate,
        'rsi_oversold': rsi_oversold,
        'rsi_overbought': rsi_overbought,
        'total_trades': len(trades),
        'buy_trades': len(buy_trades),
        'sell_trades': len(sell_trades),
        'avg_buy_price': avg_buy_price,
        'avg_sell_price': avg_sell_price,
        'trades': trades,
        'portfolio_values': portfolio_values
    }
    
    return result

def create_trading_report(simulation_result):
    """
    거래 시뮬레이션 보고서 생성
    
    Args:
        simulation_result (dict): 시뮬레이션 결과
    
    Returns:
        dict: 보고서 데이터
    """
    report = {
        'summary': {
            'stock_code': simulation_result['stock_code'],
            'date': simulation_result['date'],
            'initial_capital': simulation_result['initial_capital'],
            'final_value': simulation_result['final_value'],
            'profit': simulation_result['profit'],
            'profit_rate': simulation_result['profit_rate'],
            'rsi_oversold': simulation_result['rsi_oversold'],
            'rsi_overbought': simulation_result['rsi_overbought']
        },
        'trading_statistics': {
            'total_trades': simulation_result['total_trades'],
            'buy_trades': simulation_result['buy_trades'],
            'sell_trades': simulation_result['sell_trades'],
            'avg_buy_price': simulation_result['avg_buy_price'],
            'avg_sell_price': simulation_result['avg_sell_price']
        },
        'trades': simulation_result['trades'],
        'portfolio_values': simulation_result['portfolio_values']
    }
    
    return report

def save_trading_report(report, filename=None):
    """
    거래 보고서를 JSON 파일로 저장
    
    Args:
        report (dict): 보고서 데이터
        filename (str): 파일명 (None이면 자동 생성)
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/rsi_trading_report_{report['summary']['stock_code']}_{report['summary']['date']}_{timestamp}.json"
    
    os.makedirs('data', exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    print(f"거래 보고서 저장 완료: {filename}")
    return filename

def print_trading_summary(report):
    """
    거래 시뮬레이션 요약 출력
    
    Args:
        report (dict): 보고서 데이터
    """
    summary = report['summary']
    stats = report['trading_statistics']
    
    print("=" * 60)
    print("RSI 기반 매매 시뮬레이션 결과")
    print("=" * 60)
    print(f"종목코드: {summary['stock_code']}")
    print(f"거래일자: {summary['date']}")
    print(f"초기자본: {summary['initial_capital']:,}원")
    print(f"최종자산: {summary['final_value']:,}원")
    print(f"수익금액: {summary['profit']:,}원")
    print(f"수익률: {summary['profit_rate']:.2f}%")
    print()
    print(f"RSI 과매도 기준: {summary['rsi_oversold']}")
    print(f"RSI 과매수 기준: {summary['rsi_overbought']}")
    print()
    print(f"총 거래 횟수: {stats['total_trades']}회")
    print(f"매수 횟수: {stats['buy_trades']}회")
    print(f"매도 횟수: {stats['sell_trades']}회")
    print(f"평균 매수가: {stats['avg_buy_price']:,.0f}원")
    print(f"평균 매도가: {stats['avg_sell_price']:,.0f}원")
    print("=" * 60)

def create_trading_chart(report, save_path=None):
    """
    거래 시뮬레이션 차트 생성
    
    Args:
        report (dict): 보고서 데이터
        save_path (str): 저장 경로 (None이면 자동 생성)
    """
    portfolio_values = report['portfolio_values']
    trades = report['trades']
    
    # 데이터 준비
    timestamps = [pv['timestamp'] for pv in portfolio_values]
    prices = [pv['price'] for pv in portfolio_values]
    rsi_values = [pv['rsi'] for pv in portfolio_values]
    portfolio_values_list = [pv['portfolio_value'] for pv in portfolio_values]
    
    # 매수/매도 포인트 분리
    buy_points = [(t['timestamp'], t['price']) for t in trades if t['action'] == 'BUY']
    sell_points = [(t['timestamp'], t['price']) for t in trades if t['action'] in ['SELL', 'FINAL_SELL']]
    
    # 차트 생성
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
    
    # 1. 가격 차트
    ax1.plot(timestamps, prices, 'b-', linewidth=1, label='주가')
    
    # 매수/매도 포인트 표시
    if buy_points:
        buy_times, buy_prices = zip(*buy_points)
        ax1.scatter(buy_times, buy_prices, color='red', marker='^', s=100, label='매수', zorder=5)
    
    if sell_points:
        sell_times, sell_prices = zip(*sell_points)
        ax1.scatter(sell_times, sell_prices, color='green', marker='v', s=100, label='매도', zorder=5)
    
    ax1.set_title(f'RSI 기반 매매 시뮬레이션 - {report["summary"]["stock_code"]} ({report["summary"]["date"]})')
    ax1.set_ylabel('주가 (원)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. RSI 차트
    ax2.plot(timestamps, rsi_values, 'purple', linewidth=1, label='RSI')
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='과매수 (70)')
    ax2.axhline(y=30, color='blue', linestyle='--', alpha=0.7, label='과매도 (30)')
    ax2.set_ylabel('RSI')
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 포트폴리오 가치 차트
    ax3.plot(timestamps, portfolio_values_list, 'orange', linewidth=1, label='포트폴리오 가치')
    ax3.axhline(y=report['summary']['initial_capital'], color='gray', linestyle='--', alpha=0.7, label='초기자본')
    ax3.set_ylabel('포트폴리오 가치 (원)')
    ax3.set_xlabel('시간')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # x축 레이블 회전
    for ax in [ax1, ax2, ax3]:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = f"data/charts/rsi_trading_chart_{report['summary']['stock_code']}_{report['summary']['date']}_{timestamp}.png"
    
    os.makedirs('data/charts', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"차트 저장 완료: {save_path}")
    
    plt.show()

def main():
    """
    메인 함수 - RSI 기반 매매 시뮬레이션 실행
    """
    parser = argparse.ArgumentParser(description='RSI 기반 매매 시뮬레이션')
    parser.add_argument('--date', required=True, help='날짜 (YYYYMMDD 형식, 예: 20250717)')
    parser.add_argument('--stock_code', required=True, help='종목코드 (예: 005930)')
    parser.add_argument('--initial_capital', type=int, default=10000000, help='초기 자본금 (기본값: 10000000)')
    parser.add_argument('--rsi_oversold', type=int, default=30, help='RSI 과매도 기준 (기본값: 30)')
    parser.add_argument('--rsi_overbought', type=int, default=70, help='RSI 과매수 기준 (기본값: 70)')
    
    args = parser.parse_args()
    
    # 시뮬레이션 파라미터
    stock_code = args.stock_code
    date = args.date
    initial_capital = args.initial_capital
    
    print(f"RSI 기반 매매 시뮬레이션 시작")
    print(f"종목코드: {stock_code}")
    print(f"거래일자: {date}")
    print(f"초기자본: {initial_capital:,}원")
    print(f"RSI 과매도 기준: {args.rsi_oversold}")
    print(f"RSI 과매수 기준: {args.rsi_overbought}")
    print("-" * 50)
    
    try:
        # RSI 데이터 로드
        rsi_data = load_rsi_data(stock_code, date)
        print(f"RSI 데이터 로드 완료: {len(rsi_data['data'])}개 데이터 포인트")
        
        # 시뮬레이션 실행
        simulation_result = simulate_rsi_trading(
            rsi_data=rsi_data,
            initial_capital=initial_capital,
            rsi_oversold=args.rsi_oversold,
            rsi_overbought=args.rsi_overbought
        )
        
        # 보고서 생성
        report = create_trading_report(simulation_result)
        
        # 결과 출력
        print_trading_summary(report)
        
        # 보고서 저장
        report_filename = save_trading_report(report)
        
        # 차트 생성
        create_trading_chart(report)
        
        print(f"\n시뮬레이션 완료!")
        print(f"보고서 파일: {report_filename}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 
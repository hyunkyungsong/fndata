import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
import argparse
import sys
import subprocess
import glob

# 한글 폰트 설정 개선 한다
plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# Windows 환경에서 한글 폰트 설정
if os.name == 'nt':  # Windows
    try:
        # Windows에서 사용 가능한 한글 폰트들
        font_list = ['Malgun Gothic', 'NanumGothic', 'NanumBarunGothic', 'Dotum', 'Gulim']
        for font in font_list:
            try:
                plt.rcParams['font.family'] = font
                # 테스트용 텍스트로 폰트 확인
                fig, ax = plt.subplots(figsize=(1, 1))
                ax.text(0.5, 0.5, '가나다라', fontsize=12)
                plt.close(fig)
                print(f"한글 폰트 설정 완료: {font}")
                break
            except:
                continue
    except:
        print("한글 폰트 설정 실패, 기본 폰트 사용")
else:  # Linux/Mac
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']

def check_and_create_data(stock_code, date):
    """
    필요한 데이터 파일들이 존재하는지 확인하고, 없으면 자동으로 생성
    
    Args:
        stock_code (str): 종목 코드
        date (str): 날짜 (YYYYMMDD 형식)
    
    Returns:
        bool: 데이터 준비 완료 여부
    """
    print("=" * 60)
    print("데이터 준비 상태 확인 중...")
    print("=" * 60)
    
    # 1. 10분가격 데이터 확인
    stock_data_file = f"data/{date}/stock_data_{stock_code}_{date}.json"
    if not os.path.exists(stock_data_file):
        print(f"❌ 10분가격 데이터 파일이 없습니다: {stock_data_file}")
        print("📥 10분가격 데이터를 수집합니다...")
        
        try:
            # get_minute10.py 실행
            cmd = f"python get_minute10.py {date} {date} {stock_code}"
            print(f"실행 명령: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 10분가격 데이터 수집 완료")
            else:
                print(f"❌ 10분가격 데이터 수집 실패: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 10분가격 데이터 수집 중 오류: {str(e)}")
            return False
    else:
        print(f"✅ 10분가격 데이터 파일 존재: {stock_data_file}")
    
    # 2. RSI 데이터 확인
    rsi_data_file = f"data/{date}/rsi_data_{stock_code}_{date}.json"
    if not os.path.exists(rsi_data_file):
        print(f"❌ RSI 데이터 파일이 없습니다: {rsi_data_file}")
        print("📊 RSI 데이터를 생성합니다...")
        
        try:
            # calculate_rsi.py 실행 (전일자 데이터 활용)
            cmd = f"python calculate_rsi.py --stock_code {stock_code} --date {date}"
            print(f"실행 명령: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ RSI 데이터 생성 완료 (전일자 데이터 활용)")
            else:
                print(f"❌ RSI 데이터 생성 실패: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ RSI 데이터 생성 중 오류: {str(e)}")
            return False
    else:
        print(f"✅ RSI 데이터 파일 존재: {rsi_data_file}")
        # 기존 RSI 파일에서 전일자 데이터 사용 여부 확인
        try:
            with open(rsi_data_file, 'r', encoding='utf-8') as f:
                rsi_data = json.load(f)
                used_previous = rsi_data.get('calculation_settings', {}).get('used_previous_data', False)
                if used_previous:
                    print("  📈 전일자 데이터를 활용한 RSI 계산됨")
                else:
                    print("  📊 당일 데이터만 사용한 RSI 계산됨")
        except:
            print("   RSI 계산 방식 확인 불가")
    
    print("=" * 60)
    print("✅ 모든 데이터 준비 완료!")
    print("=" * 60)
    return True

def load_rsi_data(stock_code, date):
    """
    RSI 데이터 파일을 로드하는 함수
    
    Args:
        stock_code (str): 종목 코드
        date (str): 날짜 (YYYYMMDD 형식)
    
    Returns:
        dict: RSI 데이터
    """
    file_path = f"data/{date}/rsi_data_{stock_code}_{date}.json"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"RSI 데이터 파일을 찾을 수 없습니다: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def analyze_rsi_distribution(rsi_data):
    """
    RSI 분포 분석
    
    Args:
        rsi_data (dict): RSI 데이터
    
    Returns:
        dict: RSI 분석 결과
    """
    rsi_values = [item['rsi'] for item in rsi_data['data'] if item['rsi'] is not None]
    
    if not rsi_values:
        return None
    
    analysis = {
        'min_rsi': min(rsi_values),
        'max_rsi': max(rsi_values),
        'mean_rsi': np.mean(rsi_values),
        'median_rsi': np.median(rsi_values),
        'std_rsi': np.std(rsi_values),
        'oversold_count': sum(1 for r in rsi_values if r < 30),
        'overbought_count': sum(1 for r in rsi_values if r > 70),
        'neutral_count': sum(1 for r in rsi_values if 30 <= r <= 70),
        'total_count': len(rsi_values)
    }
    
    return analysis

# config.json 옵션 로드
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
trade_settings = config.get('trade_settings', {})

def simulate_rsi_trading_final(rsi_data, initial_capital=10000000, rsi_oversold=40, rsi_overbought=60):
    """
    최종 RSI 기반 매매 시뮬레이션 (현실적인 기준 사용)
    
    Args:
        rsi_data (dict): RSI 데이터
        initial_capital (int): 초기 자본금 (원)
        rsi_oversold (int): 과매도 기준 (기본값: 40)
        rsi_overbought (int): 과매수 기준 (기본값: 60)
    
    Returns:
        dict: 시뮬레이션 결과
    """
    data = rsi_data['data']
    stock_code = rsi_data['stock_code']
    date = rsi_data['date']

    # 10분 가격 데이터 로드 (openPrice 사용)
    stock_data_file = f"data/{date}/stock_data_{stock_code}_{date}.json"
    if not os.path.exists(stock_data_file):
        raise FileNotFoundError(f"10분 가격 데이터 파일을 찾을 수 없습니다: {stock_data_file}")
    with open(stock_data_file, 'r', encoding='utf-8') as f:
        stock_data_json = json.load(f)
        stock_data = stock_data_json['data']
    # localDateTime -> openPrice 매핑
    open_price_map = {item['localDateTime']: item['openPrice'] for item in stock_data}

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

    i = start_idx
    buy_price_type = trade_settings.get('buy_price_type', 'open')
    sell_price_type = trade_settings.get('sell_price_type', 'close')
    slippage = trade_settings.get('slippage', 0.0)
    buy_execution_timing = trade_settings.get('buy_execution_timing', 'next')
    sell_execution_timing = trade_settings.get('sell_execution_timing', 'next')

    while i < len(data):
        item = data[i]
        rsi = item['rsi']
        timestamp = item['localDateTime']
        current_price = item['currentPrice']

        if rsi is None:
            i += 1
            continue

        # 매수 신호 (과매도)
        if rsi < rsi_oversold and capital > 0:
            # 매수 캔들 인덱스 결정
            buy_idx = i if buy_execution_timing == 'current' else i + 1
            if buy_idx < len(data):
                buy_item = data[buy_idx]
                buy_timestamp = buy_item['localDateTime']
                # 가격 타입 결정
                if buy_price_type == 'open':
                    buy_price = open_price_map.get(buy_timestamp, buy_item.get('currentPrice'))
                elif buy_price_type == 'close':
                    buy_price = buy_item.get('currentPrice')
                elif buy_price_type == 'high':
                    buy_price = buy_item.get('highPrice', buy_item.get('currentPrice'))
                elif buy_price_type == 'low':
                    buy_price = buy_item.get('lowPrice', buy_item.get('currentPrice'))
                else:
                    buy_price = buy_item.get('currentPrice')
                # 슬리피지 적용
                buy_price = buy_price * (1 + slippage)
                shares_to_buy = capital // buy_price
                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_price
                    capital -= cost
                    shares += shares_to_buy
                    trades.append({
                        'timestamp': buy_timestamp,
                        'action': 'BUY',
                        'price': buy_price,
                        'shares': shares_to_buy,
                        'cost': cost,
                        'rsi': rsi,
                        'capital': capital,
                        'shares_held': shares
                    })
                i = buy_idx  # 신호 발생 시점에 따라 인덱스 이동
                continue
            else:
                break

        # 매도 신호 (과매수)
        elif rsi > rsi_overbought and shares > 0:
            sell_idx = i if sell_execution_timing == 'current' else i + 1
            if sell_idx < len(data):
                sell_item = data[sell_idx]
                sell_timestamp = sell_item['localDateTime']
                # 가격 타입 결정
                if sell_price_type == 'open':
                    sell_price = open_price_map.get(sell_timestamp, sell_item.get('currentPrice'))
                elif sell_price_type == 'close':
                    sell_price = sell_item.get('currentPrice')
                elif sell_price_type == 'high':
                    sell_price = sell_item.get('highPrice', sell_item.get('currentPrice'))
                elif sell_price_type == 'low':
                    sell_price = sell_item.get('lowPrice', sell_item.get('currentPrice'))
                else:
                    sell_price = sell_item.get('currentPrice')
                # 슬리피지 적용
                sell_price = sell_price * (1 - slippage)
                revenue = shares * sell_price
                capital += revenue
                trades.append({
                    'timestamp': sell_timestamp,
                    'action': 'SELL',
                    'price': sell_price,
                    'shares': shares,
                    'revenue': revenue,
                    'rsi': rsi,
                    'capital': capital,
                    'shares_held': 0
                })
                shares = 0
                i = sell_idx  # 신호 발생 시점에 따라 인덱스 이동
                continue
            else:
                break

        # 현재 포트폴리오 가치 계산 (현재 캔들 기준)
        current_portfolio_value = capital + (shares * current_price)
        portfolio_values.append({
            'timestamp': timestamp,
            'price': current_price,
            'rsi': rsi,
            'capital': capital,
            'shares': shares,
            'portfolio_value': current_portfolio_value
        })
        i += 1

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

    # 최대/최소 포트폴리오 가치
    portfolio_values_list = [pv['portfolio_value'] for pv in portfolio_values]
    max_portfolio_value = max(portfolio_values_list) if portfolio_values_list else initial_capital
    min_portfolio_value = min(portfolio_values_list) if portfolio_values_list else initial_capital

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
        'max_portfolio_value': max_portfolio_value,
        'min_portfolio_value': min_portfolio_value,
        'max_profit_rate': ((max_portfolio_value - initial_capital) / initial_capital) * 100,
        'max_loss_rate': ((min_portfolio_value - initial_capital) / initial_capital) * 100,
        'trades': trades,
        'portfolio_values': portfolio_values
    }

    return result

def create_final_trading_report(simulation_result, rsi_analysis):
    """
    최종 거래 시뮬레이션 보고서 생성
    
    Args:
        simulation_result (dict): 시뮬레이션 결과
        rsi_analysis (dict): RSI 분석 결과
    
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
            'avg_sell_price': simulation_result['avg_sell_price'],
            'max_portfolio_value': simulation_result['max_portfolio_value'],
            'min_portfolio_value': simulation_result['min_portfolio_value'],
            'max_profit_rate': simulation_result['max_profit_rate'],
            'max_loss_rate': simulation_result['max_loss_rate']
        },
        'rsi_analysis': rsi_analysis,
        'trades': simulation_result['trades'],
        'portfolio_values': simulation_result['portfolio_values']
    }
    
    return report

def print_final_trading_summary(report):
    """
    최종 거래 시뮬레이션 요약 출력
    
    Args:
        report (dict): 보고서 데이터
    """
    summary = report['summary']
    stats = report['trading_statistics']
    rsi_analysis = report['rsi_analysis']
    
    print("=" * 70)
    print("RSI 기반 매매 시뮬레이션 최종 결과")
    print("=" * 70)
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
    print()
    
    if rsi_analysis:
        print("RSI 분석:")
        print(f"  RSI 범위: {rsi_analysis['min_rsi']:.2f} ~ {rsi_analysis['max_rsi']:.2f}")
        print(f"  평균 RSI: {rsi_analysis['mean_rsi']:.2f}")
        print(f"  중간값 RSI: {rsi_analysis['median_rsi']:.2f}")
        print(f"  과매도 구간(<30): {rsi_analysis['oversold_count']}회")
        print(f"  과매수 구간(>70): {rsi_analysis['overbought_count']}회")
        print(f"  중립 구간(30-70): {rsi_analysis['neutral_count']}회")
    
    print("=" * 70)

def create_final_trading_chart(report, save_path=None):
    """
    최종 거래 시뮬레이션 차트 생성
    
    Args:
        report (dict): 보고서 데이터
        save_path (str): 저장 경로 (None이면 자동 생성)
    """
    from datetime import datetime
    # 한글 폰트 재설정 (차트 생성 시)
    plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
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
    
    ax1.set_title(f'RSI 기반 매매 시뮬레이션 (최종) - {report["summary"]["stock_code"]} ({report["summary"]["date"]})')
    ax1.set_ylabel('주가 (원)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. RSI 차트
    ax2.plot(timestamps, rsi_values, 'purple', linewidth=1, label='RSI')
    ax2.axhline(y=report['summary']['rsi_overbought'], color='red', linestyle='--', alpha=0.7, 
                label=f'과매수 ({report["summary"]["rsi_overbought"]})')
    ax2.axhline(y=report['summary']['rsi_oversold'], color='blue', linestyle='--', alpha=0.7, 
                label=f'과매도 ({report["summary"]["rsi_oversold"]})')
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
        stock_code = report['summary']['stock_code']
        stock_folder = f"data/{stock_code}/charts"
        os.makedirs(stock_folder, exist_ok=True)
        save_path = f"{stock_folder}/rsi_trading_final_chart_{stock_code}_{report['summary']['date']}_{timestamp}.png"
    
    # 기존 charts 폴더도 유지 (하위 호환성)
    os.makedirs('data/charts', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"차트 저장 완료: {save_path}")
    
    # 차트 창 닫기 (화면에 표시하지 않음)
    plt.close()

def create_html_report(auto_results_data, rsi_analysis):
    """
    자동 시뮬레이션 결과를 HTML 보고서로 생성
    
    Args:
        auto_results_data (dict): 자동 시뮬레이션 결과 데이터
        rsi_analysis (dict): RSI 분석 결과
    
    Returns:
        str: HTML 내용
    """
    from datetime import datetime
    stock_code = auto_results_data['stock_code']
    date = auto_results_data['date']
    initial_capital = auto_results_data['initial_capital']
    results = auto_results_data['results']
    best_result = auto_results_data['best_result']
    
    # HTML 템플릿
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSI 자동 시뮬레이션 결과 - {stock_code}</title>
    <link rel="stylesheet" href="report_style.css">  <!-- 여기서 경로 수정 -->
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RSI 자동 시뮬레이션 결과</h1>
            <p>종목코드: {stock_code} | 거래일자: {date} | 초기자본: {initial_capital:,}원</p>
        </div>
        
        <div class="content">
            <div class="summary-section">
                <h2>📊 시뮬레이션 요약</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <h3>총 시뮬레이션</h3>
                        <p>{len(results)}회</p>
                    </div>
                    <div class="summary-item">
                        <h3>oversold 범위</h3>
                        <p>25 ~ 35</p>
                    </div>
                    <div class="summary-item">
                        <h3>overbought 범위</h3>
                        <p>65 ~ 75</p>
                    </div>
                    <div class="summary-item">
                        <h3>최고 수익률</h3>
                        <p class="{'profit-positive' if best_result['profit_rate'] > 0 else 'profit-negative'}">{best_result['profit_rate']:.2f}%</p>
                    </div>
                </div>
            </div>
            
            <div class="best-result">
                <h2>🏆 최고 수익률 결과</h2>
                <div class="best-result-grid">
                    <div class="best-result-item">
                        <h4>oversold</h4>
                        <p>{best_result['oversold']}</p>
                    </div>
                    <div class="best-result-item">
                        <h4>overbought</h4>
                        <p>{best_result['overbought']}</p>
                    </div>
                    <div class="best-result-item">
                        <h4>수익률</h4>
                        <p class="{'profit-positive' if best_result['profit_rate'] > 0 else 'profit-negative'}">{best_result['profit_rate']:.2f}%</p>
                    </div>
                    <div class="best-result-item">
                        <h4>수익금</h4>
                        <p class="{'profit-positive' if best_result['profit'] > 0 else 'profit-negative'}">{int(best_result['profit']):,}원</p>
                    </div>
                    <div class="best-result-item">
                        <h4>총 거래횟수</h4>
                        <p>{best_result['total_trades']}회</p>
                    </div>
                    <div class="best-result-item">
                        <h4>매수횟수</h4>
                        <p>{best_result['buy_trades']}회</p>
                    </div>
                    <div class="best-result-item">
                        <h4>매도횟수</h4>
                        <p>{best_result['sell_trades']}회</p>
                    </div>
                    <div class="best-result-item">
                        <h4>평균 매수가</h4>
                        <p>{best_result['avg_buy_price']:,.0f}원</p>
                    </div>
                    <div class="best-result-item">
                        <h4>평균 매도가</h4>
                        <p>{best_result['avg_sell_price']:,.0f}원</p>
                    </div>
                    <div class="best-result-item">
                        <h4>최대 수익률</h4>
                        <p class="profit-positive">{best_result['max_profit_rate']:.2f}%</p>
                    </div>
                    <div class="best-result-item">
                        <h4>최대 손실률</h4>
                        <p class="profit-negative">{best_result['max_loss_rate']:.2f}%</p>
                    </div>
                </div>
            </div>
    """
    
    # RSI 분석 섹션 추가
    if rsi_analysis:
        html_content += f"""
            <div class="rsi-analysis">
                <h3>📈 RSI 분석</h3>
                <div class="rsi-grid">
                    <div class="rsi-item">
                        <h4>RSI 범위</h4>
                        <p>{rsi_analysis['min_rsi']:.2f} ~ {rsi_analysis['max_rsi']:.2f}</p>
                    </div>
                    <div class="rsi-item">
                        <h4>평균 RSI</h4>
                        <p>{rsi_analysis['mean_rsi']:.2f}</p>
                    </div>
                    <div class="rsi-item">
                        <h4>중간값 RSI</h4>
                        <p>{rsi_analysis['median_rsi']:.2f}</p>
                    </div>
                    <div class="rsi-item">
                        <h4>과매도 구간</h4>
                        <p>{rsi_analysis['oversold_count']}회</p>
                    </div>
                    <div class="rsi-item">
                        <h4>과매수 구간</h4>
                        <p>{rsi_analysis['overbought_count']}회</p>
                    </div>
                    <div class="rsi-item">
                        <h4>중립 구간</h4>
                        <p>{rsi_analysis['neutral_count']}회</p>
                    </div>
                </div>
            </div>
        """
    
    # 결과 테이블 추가
    html_content += f"""
            <h2>📋 전체 시뮬레이션 결과 (수익률 순)</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>oversold</th>
                        <th>overbought</th>
                        <th>수익률</th>
                        <th>수익금</th>
                        <th>총 거래횟수</th>
                        <th>매수횟수</th>
                        <th>매도횟수</th>
                        <th>평균 매수가</th>
                        <th>평균 매도가</th>
                        <th>최대 수익률</th>
                        <th>최대 손실률</th>
                        <th>차트</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, result in enumerate(results, 1):
        profit_class = "profit-positive" if result['profit_rate'] > 0 else "profit-negative"
        # chart_link 필드 사용
        if 'chart_link' in result and result['chart_link']:
            chart_link = f'<a href="{result["chart_link"]}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: bold;">📊 차트보기</a>'
        else:
            chart_link = ""
        
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{result['oversold']}</td>
                        <td>{result['overbought']}</td>
                        <td class="{profit_class}">{result['profit_rate']:.2f}%</td>
                        <td class="{profit_class}">{int(result['profit']):,}원</td>
                        <td>{result['total_trades']}회</td>
                        <td>{result['buy_trades']}회</td>
                        <td>{result['sell_trades']}회</td>
                        <td>{result['avg_buy_price']:,.0f}원</td>
                        <td>{result['avg_sell_price']:,.0f}원</td>
                        <td class="profit-positive">{result['max_profit_rate']:.2f}%</td>
                        <td class="profit-negative">{result['max_loss_rate']:.2f}%</td>
                        <td>{chart_link}</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            
            <h2>📊 차트 갤러리 (상위 10개 결과)</h2>
            <div class="chart-gallery" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
    """
    
    # 상위 10개 결과의 차트만 표시
    top_results = results[:10]
    for i, result in enumerate(top_results):
        if 'chart_json_filename' in result and result['chart_json_filename']:
            json_filename = result['chart_json_filename']
            html_content += f"""
                <div class="chart-item" style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 10px 0; color: #333; text-align: center;">
                        #{i+1} - oversold: {result['oversold']}, overbought: {result['overbought']}
                    </h4>
                    <p style="margin: 0 0 10px 0; text-align: center; font-weight: bold; color: {'#4caf50' if result['profit_rate'] > 0 else '#f44336'};">
                        수익률: {result['profit_rate']:.2f}%
                    </p>
                    <div style="text-align: center;">
                        <a href=\"chart_viewer.html?code={stock_code}&date={date}&oversold={result["oversold"]}&overbought={result["overbought"]}\" target=\"_blank\" style=\"display: inline-block; padding: 8px 16px; background: #667eea; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;\">
                            📊 차트보기
                        </a>
                    </div>
                </div>
            """
    
    html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
            <p>RSI 자동 시뮬레이션 결과 보고서</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content

def main():
    """
    메인 함수 - 최종 RSI 기반 매매 시뮬레이션 실행
    """
    from datetime import datetime
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='RSI 기반 매매 시뮬레이션')
    parser.add_argument('--stock_code', '-s', type=str, default='226950',
                       help='종목코드 (기본값: 226950)')
    parser.add_argument('--date', '-d', type=str, default='20250718',
                       help='날짜 (YYYYMMDD 형식, 기본값: 20250718)')
    parser.add_argument('--capital', '-c', type=int, default=10000000,
                       help='초기자본 (원, 기본값: 10000000)')
    parser.add_argument('--oversold', type=int, default=40,
                       help='RSI 과매도 기준 (기본값: 40)')
    parser.add_argument('--overbought', type=int, default=60,
                       help='RSI 과매수 기준 (기본값: 60)')
    parser.add_argument('--auto_simulate', action='store_true',
                       help='oversold 25-35, overbought 65-75 범위에서 1단위씩 자동 시뮬레이션')
    parser.add_argument('--all_stocks', action='store_true',
                       help='전체 종목에 대해 20250711~20250718 기간 동안 시뮬레이션 실행')
    parser.add_argument('--no_charts', action='store_true',
                       help='차트 생성하지 않음 (자동 시뮬레이션에서만 적용)')
    
    args = parser.parse_args()
    
    # 전체 종목 시뮬레이션 모드
    if args.all_stocks:
        print("=" * 80)
        print("전체 종목 RSI 시뮬레이션 시작")
        print("=" * 80)
        
        # 전체 종목 데이터 로드
        try:
            stock_data = pd.read_csv('data/data_stock_all_fixed.csv', encoding='utf-8')
            print(f"전체 종목 데이터 로드 완료: {len(stock_data)}개 종목")
        except Exception as e:
            print(f"전체 종목 데이터 로드 실패: {str(e)}")
            sys.exit(1)
        
        # 시뮬레이션 기간 설정
        if args.date:
            date_list = [args.date]
            start_date = end_date = args.date  # 추가!
        else:
            # 기존처럼 8일 전체
            start_date = '20250711'
            end_date = '20250718'
            # 날짜 리스트 생성
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            date_list = []
            current_dt = start_dt
            while current_dt <= end_dt:
                date_list.append(current_dt.strftime('%Y%m%d'))
                current_dt += timedelta(days=1)
        
        print(f"시뮬레이션 기간: {start_date} ~ {end_date} ({len(date_list)}일)")
        print("=" * 80)
        
        # 전체 결과 저장용
        all_stock_results = []
        successful_stocks = 0
        failed_stocks = 0
        
        # 각 종목에 대해 시뮬레이션 실행
        for idx, row in stock_data.iterrows():
            stock_code = str(row['종목코드']).zfill(6)
            stock_name = row['종목명']
            
            print(f"\n[{idx+1}/{len(stock_data)}] {stock_code} {stock_name} 처리 중...")
            
            stock_results = []
            
            # 각 날짜에 대해 시뮬레이션
            for date in date_list:
                try:
                    print(f"  {date} 시뮬레이션 중...")
                    
                    # 데이터 준비
                    if not check_and_create_data(stock_code, date):
                        print(f"    ❌ {date} 데이터 준비 실패")
                        continue
                    
                    # RSI 데이터 로드
                    rsi_data = load_rsi_data(stock_code, date)
                    
                    # 자동 시뮬레이션 (oversold 25-35, overbought 65-75)
                    best_result = None
                    best_profit_rate = -999
                    
                    for oversold in range(25, 36):
                        for overbought in range(65, 76):
                            try:
                                simulation_result = simulate_rsi_trading_final(
                                    rsi_data=rsi_data,
                                    initial_capital=args.capital,
                                    rsi_oversold=oversold,
                                    rsi_overbought=overbought
                                )
                                
                                if simulation_result['profit_rate'] > best_profit_rate:
                                    best_profit_rate = simulation_result['profit_rate']
                                    best_result = {
                                        'date': date,
                                        'oversold': oversold,
                                        'overbought': overbought,
                                        'profit_rate': simulation_result['profit_rate'],
                                        'profit': simulation_result['profit'],
                                        'total_trades': simulation_result['total_trades'],
                                        'buy_trades': simulation_result['buy_trades'],
                                        'sell_trades': simulation_result['sell_trades']
                                    }
                            except Exception as e:
                                continue
                    
                    if best_result:
                        stock_results.append(best_result)
                        print(f"    ✅ {date} 최고 수익률: {best_result['profit_rate']:.2f}%")
                    else:
                        print(f"    ❌ {date} 시뮬레이션 실패")
                        
                except Exception as e:
                    print(f"    ❌ {date} 오류: {str(e)}")
                    continue
            
            # 종목별 결과 정리
            if stock_results:
                # 최고 수익률 결과 선택
                best_stock_result = max(stock_results, key=lambda x: x['profit_rate'])
                
                all_stock_results.append({
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'best_result': best_stock_result,
                    'all_results': stock_results
                })
                
                successful_stocks += 1
                print(f"  ✅ {stock_code} {stock_name} 완료 - 최고 수익률: {best_stock_result['profit_rate']:.2f}%")
            else:
                failed_stocks += 1
                print(f"  ❌ {stock_code} {stock_name} 실패")
        
        # 전체 결과 정리 및 저장
        print("\n" + "=" * 80)
        print("전체 종목 시뮬레이션 완료")
        print("=" * 80)
        print(f"성공: {successful_stocks}개 종목")
        print(f"실패: {failed_stocks}개 종목")
        print(f"총 처리: {len(stock_data)}개 종목")
        
        # 수익률 기준 정렬
        all_stock_results.sort(key=lambda x: x['best_result']['profit_rate'], reverse=True)
        
        # 상위 20개 결과 출력
        print(f"\n상위 20개 종목 (수익률 순):")
        print(f"{'순위':<4} {'종목코드':<8} {'종목명':<15} {'수익률':<8} {'수익금':<12} {'거래횟수':<8} {'날짜':<10}")
        print("-" * 80)
        
        for i, result in enumerate(all_stock_results[:20], 1):
            best = result['best_result']
            print(f"{i:<4} {result['stock_code']:<8} {result['stock_name']:<15} "
                  f"{best['profit_rate']:<8.2f}% {best['profit']:<12,}원 {best['total_trades']:<8}회 {best['date']:<10}")
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f"./data/all_stocks_simulation_results_{start_date}_{end_date}.json"
        
        final_results = {
            'simulation_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_stocks': len(stock_data),
                'successful_stocks': successful_stocks,
                'failed_stocks': failed_stocks
            },
            'results': all_stock_results
        }
        
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=4)
        
        print(f"\n전체 종목 시뮬레이션 결과 저장 완료: {result_filename}")
        
        return
    
    # 시뮬레이션 파라미터
    stock_code = args.stock_code
    date = args.date
    initial_capital = args.capital
    
    # 자동 시뮬레이션 모드
    if args.auto_simulate:
        print("=" * 80)
        print("자동 RSI 기준값 시뮬레이션 시작")
        print("=" * 80)
        print(f"종목코드: {stock_code}")
        print(f"거래일자: {date}")
        print(f"초기자본: {initial_capital:,}원")
        print(f"oversold 범위: 25 ~ 35")
        print(f"overbought 범위: 65 ~ 75")
        print(f"차트 생성: {'비활성화' if args.no_charts else '활성화'}")
        print("=" * 80)
        
        # 데이터 준비 (한 번만)
        if not check_and_create_data(stock_code, date):
            print("데이터 준비 실패로 인해 시뮬레이션을 중단합니다.")
            sys.exit(1)

        # RSI 데이터 로드 (한 번만)
        rsi_data = load_rsi_data(stock_code, date)
        print(f"RSI 데이터 로드 완료: {len(rsi_data['data'])}개 데이터 포인트")
        
        # RSI 분석 (한 번만)
        rsi_analysis = analyze_rsi_distribution(rsi_data)
        
        # 결과 저장용 리스트
        all_results = []
        chart_files = []  # 차트 파일 경로 저장용
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 차트 저장 폴더 생성
        charts_folder = f"data/{stock_code}/charts"
        os.makedirs(charts_folder, exist_ok=True)
        
        # oversold 25-35, overbought 65-75 범위에서 시뮬레이션
        for oversold in range(25, 36):  # 25 ~ 35
            for overbought in range(65, 76):  # 65 ~ 75
                print(f"\n--- 시뮬레이션 {len(all_results) + 1}/121 ---")
                print(f"oversold: {oversold}, overbought: {overbought}")
                
                try:
                    # 시뮬레이션 실행
                    simulation_result = simulate_rsi_trading_final(
                        rsi_data=rsi_data,
                        initial_capital=initial_capital,
                        rsi_oversold=oversold,
                        rsi_overbought=overbought
                    )
                    
                    # 보고서 생성
                    report = create_final_trading_report(simulation_result, rsi_analysis)
                    
                    # 차트 생성 및 저장 (--no_charts 옵션이 없을 때만)
                    chart_filename = None
                    chart_json_filename = None
                    if not args.no_charts:
                        chart_filename = f"rsi_trading_chart_{stock_code}_{date}_oversold{oversold}_overbought{overbought}_{timestamp}.png"
                        chart_path = f"{charts_folder}/{chart_filename}"
                        try:
                            create_final_trading_chart(report, save_path=chart_path)
                            print(f"  ✅ 차트 생성 완료: {chart_filename}")
                        except Exception as chart_error:
                            print(f"  ⚠️ 차트 생성 실패: {str(chart_error)}")
                            chart_filename = None
                        # report를 json으로도 저장
                        if chart_filename:
                            chart_json_filename = chart_filename.replace('.png', '.json')
                            chart_json_path = f"{charts_folder}/{chart_json_filename}"
                            try:
                                with open(chart_json_path, 'w', encoding='utf-8') as f:
                                    json.dump(report, f, ensure_ascii=False, indent=4)
                                print(f"  ✅ 차트 데이터 저장 완료: {chart_json_filename}")
                            except Exception as json_error:
                                print(f"  ⚠️ 차트 데이터 저장 실패: {str(json_error)}")
                                chart_json_filename = None
                        chart_files.append({
                            'oversold': oversold,
                            'overbought': overbought,
                            'chart_path': chart_filename,
                            'chart_json': chart_json_filename,
                            'profit_rate': simulation_result['profit_rate']
                        })
                    else:
                        chart_files.append({
                            'oversold': oversold,
                            'overbought': overbought,
                            'chart_path': None,
                            'chart_json': None,
                            'profit_rate': simulation_result['profit_rate']
                        })
                        print(f"  ⏭️ 차트 생성 건너뜀 (--no_charts 옵션)")
                    
                    # 결과 저장
                    result_summary = {
                        'oversold': oversold,
                        'overbought': overbought,
                        'profit_rate': simulation_result['profit_rate'],
                        'profit': simulation_result['profit'],
                        'total_trades': simulation_result['total_trades'],
                        'buy_trades': simulation_result['buy_trades'],
                        'sell_trades': simulation_result['sell_trades'],
                        'avg_buy_price': simulation_result['avg_buy_price'],
                        'avg_sell_price': simulation_result['avg_sell_price'],
                        'max_profit_rate': simulation_result['max_profit_rate'],
                        'max_loss_rate': simulation_result['max_loss_rate'],
                        'chart_filename': chart_filename,
                        'chart_json_filename': chart_json_filename,
                        # 매수/매도 거래 가격 및 시간 리스트 추가
                        'buy_prices': [t['price'] for t in simulation_result['trades'] if t['action'] == 'BUY'],
                        'buy_times': [t['timestamp'] for t in simulation_result['trades'] if t['action'] == 'BUY'],
                        'sell_prices': [t['price'] for t in simulation_result['trades'] if t['action'] in ['SELL', 'FINAL_SELL']],
                        'sell_times': [t['timestamp'] for t in simulation_result['trades'] if t['action'] in ['SELL', 'FINAL_SELL']],
                        # 차트 링크 추가
                        'chart_link': f'chart_viewer.html?code={stock_code}&date={date}&oversold={oversold}&overbought={overbought}'
                    }
                    
                    all_results.append(result_summary)
                    
                    print(f"  수익률: {simulation_result['profit_rate']:.2f}%")
                    print(f"  거래횟수: {simulation_result['total_trades']}회")
                    
                except Exception as e:
                    print(f"  오류 발생: {str(e)}")
                    continue
        
        # 결과 정렬 (수익률 기준 내림차순)
        all_results.sort(key=lambda x: x['profit_rate'], reverse=True)
        
        # 최종 결과 출력
        print("\n" + "=" * 80)
        print("자동 시뮬레이션 최종 결과 (수익률 순)")
        print("=" * 80)
        
        print(f"{'순위':<4} {'oversold':<9} {'overbought':<10} {'수익률':<8} {'수익금':<12} {'거래횟수':<8}")
        print("-" * 80)
        
        for i, result in enumerate(all_results[:20], 1):  # 상위 20개만 출력
            print(f"{i:<4} {result['oversold']:<9} {result['overbought']:<10} "
                  f"{result['profit_rate']:<8.2f}% {result['profit']:<12,}원 {result['total_trades']:<8}회")
        
        # 최고 수익률 결과 상세 출력
        if all_results:
            best_result = all_results[0]
            print(f"\n🏆 최고 수익률 결과:")
            print(f"  oversold: {best_result['oversold']}")
            print(f"  overbought: {best_result['overbought']}")
            print(f"  수익률: {best_result['profit_rate']:.2f}%")
            print(f"  수익금: {int(best_result['profit']):,}원")
            print(f"  총 거래횟수: {best_result['total_trades']}회")
            print(f"  매수횟수: {best_result['buy_trades']}회")
            print(f"  매도횟수: {best_result['sell_trades']}회")
            print(f"  평균 매수가: {best_result['avg_buy_price']:,.0f}원")
            print(f"  평균 매도가: {best_result['avg_sell_price']:,.0f}원")
            print(f"  최대 수익률: {best_result['max_profit_rate']:.2f}%")
            print(f"  최대 손실률: {best_result['max_loss_rate']:.2f}%")
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_folder = "./result"
        os.makedirs(result_folder, exist_ok=True)
        
        auto_result_filename = f"{result_folder}/rsi_auto_simulation_results_{stock_code}_{date}.json"
        
        auto_results_data = {
            'stock_code': stock_code,
            'date': date,
            'initial_capital': initial_capital,
            'simulation_range': {
                'oversold_min': 25,
                'oversold_max': 35,
                'overbought_min': 65,
                'overbought_max': 75
            },
            'total_simulations': len(all_results),
            'results': all_results,
            'best_result': all_results[0] if all_results else None,
            'chart_files': chart_files
        }
        
        with open(auto_result_filename, 'w', encoding='utf-8') as f:
            json.dump(auto_results_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n자동 시뮬레이션 결과 저장 완료: {auto_result_filename}")
        
        # HTML 보고서 생성 및 저장
        html_content = create_html_report(auto_results_data, rsi_analysis)
        os.makedirs('./result', exist_ok=True)
        html_filename = f"./result/rsi_auto_simulation_report_{stock_code}_{date}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"자동 시뮬레이션 HTML 보고서 저장 완료: {html_filename}")
        
    else:
        # 기존 단일 시뮬레이션 모드
        rsi_oversold = args.oversold
        rsi_overbought = args.overbought
        
        print(f"최종 RSI 기반 매매 시뮬레이션 시작")
        print(f"종목코드: {stock_code}")
        print(f"거래일자: {date}")
        print(f"초기자본: {initial_capital:,}원")
        print(f"RSI 과매도 기준: {rsi_oversold}")
        print(f"RSI 과매수 기준: {rsi_overbought}")
        print("-" * 50)
        
        try:
            # 데이터 준비
            if not check_and_create_data(stock_code, date):
                print("데이터 준비 실패로 인해 시뮬레이션을 중단합니다.")
                sys.exit(1)

            # RSI 데이터 로드
            rsi_data = load_rsi_data(stock_code, date)
            print(f"RSI 데이터 로드 완료: {len(rsi_data['data'])}개 데이터 포인트")
            
            # RSI 분석
            rsi_analysis = analyze_rsi_distribution(rsi_data)
            if rsi_analysis:
                print(f"RSI 분석 완료:")
                print(f"  RSI 범위: {rsi_analysis['min_rsi']:.2f} ~ {rsi_analysis['max_rsi']:.2f}")
                print(f"  과매도 구간: {rsi_analysis['oversold_count']}회")
                print(f"  과매수 구간: {rsi_analysis['overbought_count']}회")
            
            # 시뮬레이션 실행 (사용자 지정 기준 사용)
            simulation_result = simulate_rsi_trading_final(
                rsi_data=rsi_data,
                initial_capital=initial_capital,
                rsi_oversold=rsi_oversold,
                rsi_overbought=rsi_overbought
            )
            
            # 보고서 생성
            report = create_final_trading_report(simulation_result, rsi_analysis)
            
            # 결과 출력
            print_final_trading_summary(report)
            
            # 보고서 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 결과 저장 폴더 생성
            result_folder = "data/20250721"
            os.makedirs(result_folder, exist_ok=True)
            
            report_filename = f"{result_folder}/rsi_trading_final_report_{stock_code}_{date}_{timestamp}.json"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=4)
            
            print(f"최종 거래 보고서 저장 완료: {report_filename}")
            
            # 차트 생성
            create_final_trading_chart(report)
            
            print(f"\n시뮬레이션 완료!")
            print(f"보고서 파일: {report_filename}")
            
        except FileNotFoundError as e:
            print(f"오류: {str(e)}")
            print(f"사용 가능한 데이터 파일을 확인해주세요.")
            print(f"데이터 디렉토리: data/")
            sys.exit(1)
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main() 
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import numpy as np
import os
import glob
import argparse

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_rsi_data(file_path):
    """
    RSI 데이터 파일을 로드하여 DataFrame으로 변환
    
    Args:
        file_path (str): RSI 데이터 파일 경로
    
    Returns:
        pd.DataFrame: RSI 데이터가 포함된 DataFrame
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 데이터를 DataFrame으로 변환
    df_data = []
    for item in data['data']:
        # 시간 문자열을 datetime으로 변환
        time_str = item['localDateTime']
        dt = datetime.strptime(time_str, '%Y%m%d%H%M%S')
        
        df_data.append({
            'datetime': dt,
            'price': item['currentPrice'],
            'rsi': item['rsi']
        })
    
    df = pd.DataFrame(df_data)
    df['stock_code'] = data['stock_code']
    df['date'] = data['date']
    
    return df

def plot_rsi_and_price(df, stock_code, save_path=None):
    """
    RSI와 가격을 함께 플롯
    
    Args:
        df (pd.DataFrame): RSI 데이터가 포함된 DataFrame
        stock_code (str): 주식 코드
        save_path (str): 저장 경로 (None이면 화면에 표시)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # 가격 차트
    ax1.plot(df['datetime'], df['price'], 'b-', linewidth=2, label='현재가')
    ax1.set_title(f'{stock_code} - 10분 가격 차트', fontsize=14, fontweight='bold')
    ax1.set_ylabel('가격 (원)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # RSI 차트
    valid_rsi = df[df['rsi'].notna()]
    ax2.plot(valid_rsi['datetime'], valid_rsi['rsi'], 'r-', linewidth=2, label='RSI')
    
    # RSI 기준선 추가
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='과매수 (70)')
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='과매도 (30)')
    ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='중립 (50)')
    
    ax2.set_title(f'{stock_code} - RSI (14기간)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('RSI', fontsize=12)
    ax2.set_xlabel('시간', fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # x축 시간 포맷 설정
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"차트 저장: {save_path}")
    else:
        plt.show()
    
    plt.close()

def create_rsi_analysis_report(df, stock_code):
    """
    RSI 분석 보고서 생성
    
    Args:
        df (pd.DataFrame): RSI 데이터가 포함된 DataFrame
        stock_code (str): 주식 코드
    
    Returns:
        dict: 분석 결과
    """
    valid_rsi = df[df['rsi'].notna()]
    
    if len(valid_rsi) == 0:
        return None
    
    # 기본 통계
    rsi_stats = {
        'min': valid_rsi['rsi'].min(),
        'max': valid_rsi['rsi'].max(),
        'mean': valid_rsi['rsi'].mean(),
        'std': valid_rsi['rsi'].std()
    }
    
    # 과매수/과매도 구간 분석
    overbought = valid_rsi[valid_rsi['rsi'] > 70]
    oversold = valid_rsi[valid_rsi['rsi'] < 30]
    
    # RSI 추세 분석
    rsi_trend = '상승' if valid_rsi['rsi'].iloc[-1] > valid_rsi['rsi'].iloc[0] else '하락'
    
    # 가격과 RSI 상관관계
    price_rsi_corr = valid_rsi['price'].corr(valid_rsi['rsi'])
    
    # datetime을 문자열로 변환
    overbought_records = []
    for _, row in overbought.iterrows():
        overbought_records.append({
            'datetime': row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
            'price': row['price'],
            'rsi': row['rsi']
        })
    
    oversold_records = []
    for _, row in oversold.iterrows():
        oversold_records.append({
            'datetime': row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
            'price': row['price'],
            'rsi': row['rsi']
        })
    
    analysis = {
        'stock_code': stock_code,
        'date': df['date'].iloc[0],
        'total_data_points': len(df),
        'valid_rsi_points': len(valid_rsi),
        'rsi_stats': rsi_stats,
        'overbought_count': len(overbought),
        'oversold_count': len(oversold),
        'rsi_trend': rsi_trend,
        'price_rsi_correlation': price_rsi_corr,
        'overbought_periods': overbought_records,
        'oversold_periods': oversold_records
    }
    
    return analysis

def visualize_all_rsi_data(data_dir='data'):
    """
    모든 RSI 데이터를 시각화하고 분석 보고서 생성
    
    Args:
        data_dir (str): 데이터 디렉토리 경로
    """
    # data 디렉토리 내의 모든 종목 폴더 찾기
    stock_folders = []
    if os.path.exists(data_dir):
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path):
                stock_folders.append(item_path)
    
    if not stock_folders:
        print("처리할 종목 폴더를 찾을 수 없습니다.")
        return
    
    # 각 종목 폴더에서 rsi_data_*.json 파일들 찾기
    rsi_files = []
    for folder in stock_folders:
        pattern = os.path.join(folder, 'rsi_data_*.json')
        files = glob.glob(pattern)
        rsi_files.extend(files)
    
    if not rsi_files:
        print("시각화할 RSI 데이터 파일을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(rsi_files)}개의 RSI 데이터 파일을 시각화합니다.")
    
    # 차트 저장 디렉토리 생성
    charts_dir = os.path.join(data_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    all_analyses = []
    
    for file_path in rsi_files:
        try:
            # 데이터 로드
            df = load_rsi_data(file_path)
            stock_code = df['stock_code'].iloc[0]
            date = df['date'].iloc[0]
            
            print(f"처리 중: {stock_code} ({date})")
            
            # 차트 생성 및 저장
            chart_filename = f"rsi_chart_{stock_code}_{date}.png"
            
            # 종목별 charts 폴더 생성
            stock_charts_dir = os.path.join(data_dir, stock_code, 'charts')
            os.makedirs(stock_charts_dir, exist_ok=True)
            
            chart_path = os.path.join(stock_charts_dir, chart_filename)
            plot_rsi_and_price(df, stock_code, chart_path)
            
            # 기존 charts 폴더에도 복사 (하위 호환성)
            legacy_chart_path = os.path.join(charts_dir, chart_filename)
            import shutil
            shutil.copy2(chart_path, legacy_chart_path)
            
            # 분석 보고서 생성
            analysis = create_rsi_analysis_report(df, stock_code)
            if analysis:
                all_analyses.append(analysis)
                
                # 분석 결과 출력
                print(f"  RSI 분석 결과:")
                print(f"    최소값: {analysis['rsi_stats']['min']:.2f}")
                print(f"    최대값: {analysis['rsi_stats']['max']:.2f}")
                print(f"    평균값: {analysis['rsi_stats']['mean']:.2f}")
                print(f"    과매수 구간: {analysis['overbought_count']}개")
                print(f"    과매도 구간: {analysis['oversold_count']}개")
                print(f"    RSI 추세: {analysis['rsi_trend']}")
                print(f"    가격-RSI 상관관계: {analysis['price_rsi_correlation']:.3f}")
            
            print()
            
        except Exception as e:
            print(f"오류 발생 ({file_path}): {str(e)}")
    
    # 전체 분석 보고서 생성
    if all_analyses:
        create_comprehensive_report(all_analyses, charts_dir)

def create_comprehensive_report(analyses, charts_dir):
    """
    종합 분석 보고서 생성
    
    Args:
        analyses (list): 개별 분석 결과 리스트
        charts_dir (str): 차트 디렉토리 경로
    """
    # 종합 통계 계산
    all_rsi_values = []
    for analysis in analyses:
        all_rsi_values.extend([
            analysis['rsi_stats']['min'],
            analysis['rsi_stats']['max'],
            analysis['rsi_stats']['mean']
        ])
    
    comprehensive_report = {
        'report_date': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'total_stocks_analyzed': len(analyses),
        'overall_rsi_stats': {
            'min': min(all_rsi_values),
            'max': max(all_rsi_values),
            'mean': np.mean(all_rsi_values)
        },
        'trend_summary': {
            'upward_trend': sum(1 for a in analyses if a['rsi_trend'] == '상승'),
            'downward_trend': sum(1 for a in analyses if a['rsi_trend'] == '하락')
        },
        'signal_summary': {
            'total_overbought': sum(a['overbought_count'] for a in analyses),
            'total_oversold': sum(a['oversold_count'] for a in analyses)
        },
        'detailed_analyses': analyses
    }
    
    # 보고서 저장
    report_filename = f"rsi_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(charts_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_report, f, ensure_ascii=False, indent=4)
    
    print(f"종합 분석 보고서 생성: {report_filename}")
    
    # 요약 출력
    print("\n=== 종합 분석 결과 ===")
    print(f"분석된 종목 수: {comprehensive_report['total_stocks_analyzed']}")
    print(f"전체 RSI 범위: {comprehensive_report['overall_rsi_stats']['min']:.2f} ~ {comprehensive_report['overall_rsi_stats']['max']:.2f}")
    print(f"상승 추세 종목: {comprehensive_report['trend_summary']['upward_trend']}개")
    print(f"하락 추세 종목: {comprehensive_report['trend_summary']['downward_trend']}개")
    print(f"총 과매수 신호: {comprehensive_report['signal_summary']['total_overbought']}개")
    print(f"총 과매도 신호: {comprehensive_report['signal_summary']['total_oversold']}개")

def visualize_specific_rsi_data(stock_code, date, data_dir='data'):
    """
    특정 종목코드와 날짜에 대한 RSI 데이터를 시각화
    
    Args:
        stock_code (str): 종목코드
        date (str): 날짜 (YYYYMMDD 형식)
        data_dir (str): 데이터 디렉토리 경로
    """
    # RSI 데이터 파일 경로 (종목별 폴더 구조 고려)
    rsi_filename = f"rsi_data_{stock_code}_{date}.json"
    rsi_file_path = os.path.join(data_dir, stock_code, rsi_filename)
    
    if not os.path.exists(rsi_file_path):
        print(f"RSI 데이터 파일을 찾을 수 없습니다: {rsi_file_path}")
        return None
    
    try:
        # 데이터 로드
        df = load_rsi_data(rsi_file_path)
        
        print(f"처리 중: {stock_code} ({date})")
        
        # 차트 저장 디렉토리 생성
        charts_dir = os.path.join(data_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 차트 생성 및 저장
        chart_filename = f"rsi_chart_{stock_code}_{date}.png"
        
        # 종목별 charts 폴더 생성
        stock_charts_dir = os.path.join(data_dir, stock_code, 'charts')
        os.makedirs(stock_charts_dir, exist_ok=True)
        
        chart_path = os.path.join(stock_charts_dir, chart_filename)
        plot_rsi_and_price(df, stock_code, chart_path)
        
        # 기존 charts 폴더에도 복사 (하위 호환성)
        legacy_chart_path = os.path.join(charts_dir, chart_filename)
        import shutil
        shutil.copy2(chart_path, legacy_chart_path)
        
        # 분석 보고서 생성
        analysis = create_rsi_analysis_report(df, stock_code)
        if analysis:
            print(f"  RSI 분석 결과:")
            print(f"    최소값: {analysis['rsi_stats']['min']:.2f}")
            print(f"    최대값: {analysis['rsi_stats']['max']:.2f}")
            print(f"    평균값: {analysis['rsi_stats']['mean']:.2f}")
            print(f"    과매수 구간: {analysis['overbought_count']}개")
            print(f"    과매도 구간: {analysis['oversold_count']}개")
            print(f"    RSI 추세: {analysis['rsi_trend']}")
            print(f"    가격-RSI 상관관계: {analysis['price_rsi_correlation']:.3f}")
        
        return analysis
        
    except Exception as e:
        print(f"오류 발생 ({rsi_file_path}): {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RSI 데이터 시각화 및 분석')
    parser.add_argument('--date', help='날짜 (YYYYMMDD 형식, 예: 20250717)')
    parser.add_argument('--stock_code', help='종목코드 (예: 005930)')
    parser.add_argument('--all', action='store_true', help='모든 RSI 데이터 파일 시각화')
    
    args = parser.parse_args()
    
    print("RSI 데이터 시각화 및 분석을 시작합니다.")
    print("=" * 60)
    
    if args.all:
        # 모든 RSI 데이터 시각화
        visualize_all_rsi_data()
    elif args.date and args.stock_code:
        # 특정 종목과 날짜에 대한 시각화
        print(f"종목코드: {args.stock_code}")
        print(f"날짜: {args.date}")
        print("-" * 50)
        
        result = visualize_specific_rsi_data(args.stock_code, args.date)
        if result:
            print(f"\nRSI 시각화가 완료되었습니다!")
            print(f"차트 파일: data/charts/rsi_chart_{args.stock_code}_{args.date}.png")
        else:
            print("RSI 시각화에 실패했습니다.")
    else:
        print("사용법:")
        print("  특정 종목과 날짜: python visualize_rsi.py --date 20250717 --stock_code 005930")
        print("  모든 파일 시각화: python visualize_rsi.py --all")
    
    print("\nRSI 시각화 및 분석이 완료되었습니다!")
    print("차트와 분석 보고서는 'data/charts' 디렉토리에 저장되었습니다.") 
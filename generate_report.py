import json
import os
from collections import Counter
import sys

def parse_large_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    results = data.get('results', [])
    return summary, results

def main(date_str=None):
    if date_str is None:
        if len(sys.argv) > 1:
            date_str = sys.argv[1]
        else:
            date_str = ''  # 기본값
    input_json = f'data/all_stocks_simulation_results_{date_str}_{date_str}.json'
    output_html = f'result/all_stocks_simulation_report_{date_str}.html'
    summary, results = parse_large_json(input_json)
    total_stocks = int(summary.get('total_stocks', 0))
    successful_stocks = int(summary.get('successful_stocks', 0))
    failed_stocks = int(summary.get('failed_stocks', 0))

    # results에서 직접 통계 계산
    total_profit = 0
    profit_rates = []
    profit_cnt = 0
    loss_cnt = 0
    neutral_cnt = 0
    high_profit = 0
    mid_profit = 0
    low_profit = 0
    for item in results:
        br = item.get('best_result', {})
        profit = br.get('profit', 0)
        profit_rate = br.get('profit_rate', 0)
        total_profit += profit
        profit_rates.append(profit_rate)
        if profit > 0:
            profit_cnt += 1
        elif profit < 0:
            loss_cnt += 1
        else:
            neutral_cnt += 1
        if profit_rate >= 10:
            high_profit += 1
        elif 1 <= profit_rate < 10:
            mid_profit += 1
        elif 0 < profit_rate < 1:
            low_profit += 1
    avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0

    # 통계정보 콘솔 출력
    print("==== 시뮬레이션 통계 정보 ====")
    print(f"총 종목 수: {total_stocks}")
    print(f"성공 종목: {successful_stocks}")
    print(f"실패 종목: {failed_stocks}")
    print(f"총 수익: {int(total_profit):,}원")
    print(f"평균 수익률: {avg_profit_rate:.2f}%")
    print(f"수익 종목: {profit_cnt}")
    print(f"손실 종목: {loss_cnt}")
    print(f"무손익 종목: {neutral_cnt}")
    print(f"고수익 종목(10%↑): {high_profit}")
    print(f"중수익 종목(1~10%): {mid_profit}")
    print(f"저수익 종목(0~1%): {low_profit}")
    print("===========================")

    sorted_results = sorted(results, key=lambda x: x['best_result']['profit_rate'], reverse=True)
    top10 = sorted_results[:10]
    bottom10 = sorted_results[-10:]

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>전체 주식 RSI 시뮬레이션 결과 보고서 ({date_str})</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #667eea; margin-bottom: 15px; font-size: 1.3em; }}
        .card .value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .card .label {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .section {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .section h2 {{ color: #333; margin-bottom: 20px; font-size: 1.8em; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .results-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .results-table th, .results-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .results-table th {{ background-color: #667eea; color: white; font-weight: 600; }}
        .results-table tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .results-table tr:hover {{ background-color: #e9ecef; }}
        .profit-positive {{ color: #28a745; font-weight: bold; }}
        .profit-negative {{ color: #dc3545; font-weight: bold; }}
        .profit-neutral {{ color: #6c757d; font-weight: bold; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 1.5em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; border-top: 1px solid #ddd; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>전체 주식 RSI 시뮬레이션 결과 ({date_str})</h1>
            <p>시뮬레이션 기준일: {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}</p>
        </div>
        <div class="summary-cards">
            <div class="card"><h3>총 종목 수</h3><div class="value">{total_stocks:,}</div><div class="label">분석 대상 종목</div></div>
            <div class="card"><h3>성공 종목</h3><div class="value">{successful_stocks:,}</div><div class="label">시뮬레이션 완료</div></div>
            <div class="card"><h3>실패 종목</h3><div class="value">{failed_stocks:,}</div><div class="label">시뮬레이션 실패</div></div>
            <div class="card"><h3>총 수익</h3><div class="value">{total_profit:,}원</div><div class="label">전체 종목 합계</div></div>
        </div>
        <div class="section">
            <h2>수익률 통계</h2>
            <div class="stats-grid">
                <div class="stat-item"><div class="stat-value">{profit_cnt:,}</div><div class="stat-label">수익 종목</div></div>
                <div class="stat-item"><div class="stat-value">{loss_cnt:,}</div><div class="stat-label">손실 종목</div></div>
                <div class="stat-item"><div class="stat-value">{neutral_cnt:,}</div><div class="stat-label">무손익 종목</div></div>
                <div class="stat-item"><div class="stat-value">{avg_profit_rate:.2f}%</div><div class="stat-label">평균 수익률</div></div>
                <div class="stat-item"><div class="stat-value">{high_profit:,}</div><div class="stat-label">고수익 종목 (10%↑)</div></div>
                <div class="stat-item"><div class="stat-value">{mid_profit:,}</div><div class="stat-label">중수익 종목 (1-10%)</div></div>
                <div class="stat-item"><div class="stat-value">{low_profit:,}</div><div class="stat-label">저수익 종목 (0-1%)</div></div>
            </div>
        </div>
        <div class="section">
            <h2>상위 10개 수익 종목</h2>
            <table class="results-table">
                <thead><tr><th>순위</th><th>종목코드</th><th>종목명</th><th>수익</th><th>수익률</th><th>매매횟수</th><th>매수횟수</th><th>매도횟수</th><th>최적 RSI 설정</th></tr></thead>
                <tbody>'''
    for idx, item in enumerate(top10, 1):
        br = item['best_result']
        html += f'<tr><td>{idx}</td><td>{item["stock_code"]}</td><td>{item["stock_name"]}</td>'
        html += f'<td class="profit-positive">{int(br["profit"]):,}원</td>'
        html += f'<td class="profit-positive">{br["profit_rate"]:.2f}%</td>'
        html += f'<td>{br["total_trades"]}</td><td>{br["buy_trades"]}</td><td>{br["sell_trades"]}</td>'
        html += f'<td>과매도: {br["oversold"]}, 과매수: {br["overbought"]}</td></tr>'
    html += "</tbody></table></div>"

    html += '''<div class="section">
<h2>하위 10개 수익 종목</h2>
<table class="results-table">
<thead><tr><th>순위</th><th>종목코드</th><th>종목명</th><th>수익</th><th>수익률</th><th>매매횟수</th><th>매수횟수</th><th>매도횟수</th><th>최적 RSI 설정</th></tr></thead>
<tbody>'''
    for idx, item in enumerate(bottom10, len(results)-9):
        br = item['best_result']
        profit_class = 'profit-positive' if br['profit'] > 0 else ('profit-negative' if br['profit'] < 0 else 'profit-neutral')
        html += f'<tr><td>{idx}</td><td>{item["stock_code"]}</td><td>{item["stock_name"]}</td>'
        html += f'<td class="{profit_class}">{int(br["profit"]):,}원</td>'
        html += f'<td class="{profit_class}">{br["profit_rate"]:.2f}%</td>'
        html += f'<td>{br["total_trades"]}</td><td>{br["buy_trades"]}</td><td>{br["sell_trades"]}</td>'
        html += f'<td>과매도: {br["oversold"]}, 과매수: {br["overbought"]}</td></tr>'
    html += "</tbody></table></div>"

    html += '''<div class="footer">
<p>© 2024 RSI 시뮬레이션 분석 시스템</p>
<p>이 보고서는 자동으로 생성되었습니다.</p>
</div>
</div>
</body>
</html>'''
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'HTML 보고서가 생성되었습니다: {output_html}')

if __name__ == '__main__':
    main() 
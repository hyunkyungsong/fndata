import json
import os
from datetime import datetime

# HTML 템플릿 (Chart.js 포함, 데이터는 {{...}}로 치환)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSI 계산 결과 보고서</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: #667eea; margin-bottom: 15px; font-size: 1.3em; }
        .card .value { font-size: 2em; font-weight: bold; color: #333; }
        .card .label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .section { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
        .section h2 { color: #333; margin-bottom: 20px; font-size: 1.8em; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
        .rsi-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .rsi-table th, .rsi-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .rsi-table th { background-color: #667eea; color: white; font-weight: 600; }
        .rsi-table tr:nth-child(even) { background-color: #f8f9fa; }
        .rsi-table tr:hover { background-color: #e9ecef; }
        .rsi-oversold { color: #28a745; font-weight: bold; }
        .rsi-overbought { color: #dc3545; font-weight: bold; }
        .rsi-neutral { color: #6c757d; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-item { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; border-top: 1px solid #ddd; margin-top: 30px; }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header h1 { font-size: 2em; }
            .summary-cards { grid-template-columns: 1fr; }
            .rsi-table { font-size: 0.9em; }
            .rsi-table th, .rsi-table td { padding: 8px; }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 RSI 계산 결과 보고서</h1>
            <p>Relative Strength Index 계산 및 분석 결과</p>
        </div>
        <div class="summary-cards">
            <div class="card">
                <h3>📈 종목코드</h3>
                <div class="value">{{stock_code}}</div>
                <div class="label">분석 대상 종목</div>
            </div>
            <div class="card">
                <h3>📅 분석 날짜</h3>
                <div class="value">{{date}}</div>
                <div class="label">데이터 수집 일자</div>
            </div>
            <div class="card">
                <h3>📊 데이터 포인트</h3>
                <div class="value">{{data_count}}</div>
                <div class="label">분석된 데이터 수</div>
            </div>
            <div class="card">
                <h3>⚙️ RSI 기간</h3>
                <div class="value">{{rsi_period}}</div>
                <div class="label">RSI 계산 기간</div>
            </div>
        </div>
        <div class="section">
            <h2>📊 RSI 통계 분석</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{{min_rsi}}</div>
                    <div class="stat-label">최소 RSI</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{max_rsi}}</div>
                    <div class="stat-label">최대 RSI</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{avg_rsi}}</div>
                    <div class="stat-label">평균 RSI</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{median_rsi}}</div>
                    <div class="stat-label">중간값 RSI</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{oversold_count}}</div>
                    <div class="stat-label">과매도 구간(<30)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{overbought_count}}</div>
                    <div class="stat-label">과매수 구간(>70)</div>
                </div>
            </div>
        </div>
        <div class="section">
            <h2>📈 RSI 값 상세 데이터</h2>
            <table class="rsi-table">
                <thead>
                    <tr>
                        <th>시간</th>
                        <th>가격</th>
                        <th>RSI</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>
                    {{rsi_table_rows}}
                </tbody>
            </table>
        </div>
        <div class="section">
            <h2>📊 RSI 분포 분석</h2>
            <div class="chart-container">
                <canvas id="rsiChart"></canvas>
            </div>
        </div>
        <div class="section">
            <h2>💹 주가 차트</h2>
            <div class="chart-container">
                <canvas id="priceChart"></canvas>
            </div>
        </div>
        <div class="section">
            <h2>🔍 RSI 신호 분석</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{{buy_signals}}</div>
                    <div class="stat-label">매수 신호</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{sell_signals}}</div>
                    <div class="stat-label">매도 신호</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{neutral_signals}}</div>
                    <div class="stat-label">중립 신호</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{signal_ratio}}%</div>
                    <div class="stat-label">신호 발생 비율</div>
                </div>
            </div>
        </div>
        <div class="section">
            <h2>📋 계산 설정</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{{calculation_method_kr}}</div>
                    <div class="stat-label">계산 방법</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{calculation_method}}</div>
                    <div class="stat-label">평균 방식</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{previous_data_used}}</div>
                    <div class="stat-label">전일자 데이터</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">우수</div>
                    <div class="stat-label">데이터 품질</div>
                </div>
            </div>
        </div>
        <div class="footer">
            <p>📅 생성일시: <span id="generation-time">{{generation_time}}</span></p>
            <p>📊 RSI 계산 결과 보고서</p>
        </div>
    </div>
    <script>
        // RSI/가격 데이터 embed
        const rsiData = {{rsi_json}};
        const priceData = {{price_json}};
        // RSI 차트
        const rsiLabels = rsiData.map(d => d.time);
        const rsiValues = rsiData.map(d => d.rsi);
        const ctxRsi = document.getElementById('rsiChart').getContext('2d');
        new Chart(ctxRsi, {
            type: 'line',
            data: {
                labels: rsiLabels,
                datasets: [{
                    label: 'RSI',
                    data: rsiValues,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102,126,234,0.1)',
                    fill: true,
                    tension: 0.2,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true },
                    title: { display: false }
                },
                scales: {
                    y: { min: 0, max: 100 }
                }
            }
        });
        // 주가 차트
        const priceLabels = priceData.map(d => d.time);
        const priceValues = priceData.map(d => d.price);
        const ctxPrice = document.getElementById('priceChart').getContext('2d');
        new Chart(ctxPrice, {
            type: 'line',
            data: {
                labels: priceLabels,
                datasets: [{
                    label: '주가',
                    data: priceValues,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220,53,69,0.1)',
                    fill: true,
                    tension: 0.2,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true },
                    title: { display: false }
                }
            }
        });
    </script>
</body>
</html>
'''

def get_median(lst):
    n = len(lst)
    s = sorted(lst)
    return (s[n//2] if n % 2 == 1 else (s[n//2-1] + s[n//2]) / 2) if n else 0

def main(stock_code, date, output_path):
    rsi_path = f"./data/{date}/rsi_data_{stock_code}_{date}.json"
    stock_path = f"./data/{date}/stock_data_{stock_code}_{date}.json"
    # 데이터 로드
    with open(rsi_path, encoding='utf-8') as f:
        rsi_json = json.load(f)
    with open(stock_path, encoding='utf-8') as f:
        stock_json = json.load(f)
    # rsi 데이터 정제
    rsi_data = rsi_json['data']
    rsi_list = [d['rsi'] for d in rsi_data]
    min_rsi = min(rsi_list)
    max_rsi = max(rsi_list)
    avg_rsi = sum(rsi_list) / len(rsi_list)
    median_rsi = get_median(rsi_list)
    oversold_count = sum(1 for r in rsi_list if r < 30)
    overbought_count = sum(1 for r in rsi_list if r > 70)
    buy_signals = oversold_count
    sell_signals = overbought_count
    neutral_signals = len(rsi_list) - buy_signals - sell_signals
    signal_ratio = round((buy_signals + sell_signals) / len(rsi_list) * 100, 1)
    # rsi 테이블
    rsi_table_rows = ''
    for d in rsi_data:
        t = d['localDateTime'][8:10] + ':' + d['localDateTime'][10:12] + ':' + d['localDateTime'][12:14]
        price = f"{int(d['currentPrice']):,}원"
        rsi = f"{d['rsi']:.2f}"
        if d['rsi'] < 30:
            status = '<span class="rsi-oversold">과매도</span>'
        elif d['rsi'] > 70:
            status = '<span class="rsi-overbought">과매수</span>'
        else:
            status = '<span class="rsi-neutral">중립</span>'
        rsi_table_rows += f'<tr><td>{t}</td><td>{price}</td><td>{rsi}</td><td>{status}</td></tr>'
    # rsi/price 차트용 데이터
    rsi_chart_data = [
        {
            'time': d['localDateTime'][8:10] + ':' + d['localDateTime'][10:12],
            'rsi': round(d['rsi'], 2)
        } for d in rsi_data
    ]
    price_chart_data = [
        {
            'time': d['localDateTime'][8:10] + ':' + d['localDateTime'][10:12],
            'price': d['currentPrice']
        } for d in stock_json['data']
    ]
    # 계산 설정
    calc_method = rsi_json['calculation_settings']['calculation_method']
    calc_method_kr = '지수이동평균' if 'exponential' in calc_method else '단순이동평균'
    previous_data_used = '사용' if rsi_json['calculation_settings'].get('previous_data_used') else '미사용'
    # 템플릿 치환
    html = HTML_TEMPLATE
    html = html.replace('{{stock_code}}', rsi_json['stock_code'])
    html = html.replace('{{date}}', rsi_json['date'])
    html = html.replace('{{data_count}}', str(rsi_json['data_count']))
    html = html.replace('{{rsi_period}}', str(rsi_json['rsi_period']))
    html = html.replace('{{min_rsi}}', f"{min_rsi:.2f}")
    html = html.replace('{{max_rsi}}', f"{max_rsi:.2f}")
    html = html.replace('{{avg_rsi}}', f"{avg_rsi:.2f}")
    html = html.replace('{{median_rsi}}', f"{median_rsi:.2f}")
    html = html.replace('{{oversold_count}}', str(oversold_count))
    html = html.replace('{{overbought_count}}', str(overbought_count))
    html = html.replace('{{buy_signals}}', str(buy_signals))
    html = html.replace('{{sell_signals}}', str(sell_signals))
    html = html.replace('{{neutral_signals}}', str(neutral_signals))
    html = html.replace('{{signal_ratio}}', str(signal_ratio))
    html = html.replace('{{calculation_method_kr}}', calc_method_kr)
    html = html.replace('{{calculation_method}}', calc_method)
    html = html.replace('{{previous_data_used}}', previous_data_used)
    html = html.replace('{{generation_time}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html = html.replace('{{rsi_table_rows}}', rsi_table_rows)
    html = html.replace('{{rsi_json}}', json.dumps(rsi_chart_data, ensure_ascii=False))
    html = html.replace('{{price_json}}', json.dumps(price_chart_data, ensure_ascii=False))
    # 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'보고서가 생성되었습니다: {output_path}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='RSI 계산 결과 보고서 생성기')
    parser.add_argument('--stock', required=True, help='종목코드')
    parser.add_argument('--date', required=True, help='일자 (YYYYMMDD)')
    parser.add_argument('--output', default='result/rsi_calculation_report.html', help='저장 경로')
    args = parser.parse_args()
    main(args.stock, args.date, args.output) 
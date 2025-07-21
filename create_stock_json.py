import pandas as pd
import json
import os

def create_stock_json():
    """CSV 파일을 읽어서 전체 종목 정보를 JSON 파일로 변환"""
    
    # CSV 파일 읽기
    csv_file = 'data/data_stock_all_fixed.csv'
    output_file = 'stock_list.json'
    
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # 종목 정보를 딕셔너리 리스트로 변환
        stocks = []
        for _, row in df.iterrows():
            stock_info = {
                'code': str(row['종목코드']),
                'name': row['종목명'],
                'market': row['시장구분'],
                'sector': row['소속부'],
                'price': row['종가'],
                'change': row['대비'],
                'change_rate': row['등락률'],
                'open': row['시가'],
                'high': row['고가'],
                'low': row['저가'],
                'volume': row['거래량'],
                'amount': row['거래대금'],
                'market_cap': row['시가총액'],
                'shares': row['상장주식수']
            }
            stocks.append(stock_info)
        
        # JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stocks, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(stocks)}개 종목 정보가 {output_file}에 저장되었습니다.")
        print(f"📁 파일 위치: {os.path.abspath(output_file)}")
        
        # 샘플 데이터 출력
        print("\n📋 샘플 데이터:")
        for i, stock in enumerate(stocks[:5]):
            print(f"  {i+1}. {stock['name']} ({stock['code']}) - {stock['price']:,}원")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    create_stock_json() 
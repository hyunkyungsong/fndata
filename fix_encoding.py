import pandas as pd
import chardet

def detect_encoding(file_path):
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def fix_csv_encoding(input_file, output_file, source_encoding='cp949', target_encoding='utf-8'):
    """CSV 파일의 인코딩을 수정합니다."""
    try:
        # 원본 인코딩으로 파일 읽기
        df = pd.read_csv(input_file, encoding=source_encoding)
        
        # 새로운 인코딩으로 저장
        df.to_csv(output_file, encoding=target_encoding, index=False)
        print(f"파일이 {target_encoding} 인코딩으로 저장되었습니다: {output_file}")
        
        # 결과 확인을 위해 첫 몇 줄 출력
        print("\n변환된 파일의 첫 5줄:")
        print(df.head())
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    input_file = "data/data_stock_all.csv"
    output_file = "data/data_stock_all_fixed.csv"
    
    # 인코딩 감지
    detected_encoding = detect_encoding(input_file)
    print(f"감지된 인코딩: {detected_encoding}")
    
    # 인코딩 수정 (CP949에서 UTF-8로)
    fix_csv_encoding(input_file, output_file, 'cp949', 'utf-8') 
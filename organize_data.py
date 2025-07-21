import os
import shutil
import glob

def organize_data_by_stock():
    """종목별로 데이터를 폴더에 정리하는 함수"""
    
    # 종목 코드 리스트
    stock_codes = ['005930', '034020', '226950', '358570']
    
    # 현재 작업 디렉토리 확인
    current_dir = os.getcwd()
    print(f"현재 작업 디렉토리: {current_dir}")
    
    # data 디렉토리로 이동
    data_dir = os.path.join(current_dir, 'data')
    if not os.path.exists(data_dir):
        print("data 디렉토리를 찾을 수 없습니다.")
        return
    
    os.chdir(data_dir)
    print(f"data 디렉토리로 이동: {os.getcwd()}")
    
    # 각 종목별로 폴더 생성 및 파일 이동
    for stock_code in stock_codes:
        # 폴더가 없으면 생성
        if not os.path.exists(stock_code):
            os.makedirs(stock_code)
            print(f"{stock_code} 폴더 생성됨")
        
        # 해당 종목 코드가 포함된 파일들 찾기
        pattern = f"*{stock_code}*"
        files = glob.glob(pattern)
        
        print(f"\n{stock_code} 종목 파일 정리:")
        for file in files:
            if os.path.isfile(file):  # 파일인 경우만 이동
                try:
                    destination = os.path.join(stock_code, file)
                    shutil.move(file, destination)
                    print(f"  이동됨: {file} -> {destination}")
                except Exception as e:
                    print(f"  오류: {file} - {e}")
    
    # charts 폴더의 파일들도 정리
    charts_dir = os.path.join(data_dir, 'charts')
    if os.path.exists(charts_dir):
        print(f"\ncharts 폴더 정리: {charts_dir}")
        os.chdir(charts_dir)
        
        for stock_code in stock_codes:
            # charts 폴더 내에서 해당 종목 폴더 생성
            charts_stock_dir = os.path.join('..', stock_code, 'charts')
            if not os.path.exists(charts_stock_dir):
                os.makedirs(charts_stock_dir)
                print(f"{stock_code} charts 폴더 생성됨")
            
            # 해당 종목 코드가 포함된 파일들 찾기
            pattern = f"*{stock_code}*"
            files = glob.glob(pattern)
            
            print(f"\n{stock_code} 종목 차트 파일 정리:")
            for file in files:
                if os.path.isfile(file):  # 파일인 경우만 이동
                    try:
                        destination = os.path.join(charts_stock_dir, file)
                        shutil.move(file, destination)
                        print(f"  이동됨: {file} -> {destination}")
                    except Exception as e:
                        print(f"  오류: {file} - {e}")
        
        os.chdir(data_dir)  # charts 폴더에서 나가기
    
    print("\n데이터 정리 완료!")

if __name__ == "__main__":
    organize_data_by_stock() 
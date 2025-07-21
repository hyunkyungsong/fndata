import os
import shutil
import sys

# 이동할 날짜 문자열
if len(sys.argv) < 2:
    print("사용법: python move_files.py <YYYYMMDD>")
    sys.exit(1)
TARGET_DATE = sys.argv[1]
# 데이터 루트 경로
DATA_ROOT = os.path.join("data")
# 이동 대상 폴더
DEST_DIR = os.path.join(DATA_ROOT, TARGET_DATE)

# 이동 대상 폴더가 없으면 생성
os.makedirs(DEST_DIR, exist_ok=True)

# data/ 하위의 종목코드 폴더 순회
for code in os.listdir(DATA_ROOT):
    code_path = os.path.join(DATA_ROOT, code)
    if not os.path.isdir(code_path):
        continue
    # 종목코드 폴더 내 파일 순회
    for fname in os.listdir(code_path):
        if TARGET_DATE in fname:
            src = os.path.join(code_path, fname)
            dst = os.path.join(DEST_DIR, fname)
            print(f"Moving {src} -> {dst}")
            shutil.move(src, dst) 
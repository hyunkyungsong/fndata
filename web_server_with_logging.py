from flask import Flask, send_from_directory, request, jsonify
import logging
import os
import json
from datetime import datetime
import time

# 로깅 설정
def setup_logging():
    # 로그 디렉토리 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 로그 파일명 (날짜별)
    log_filename = f'logs/web_server_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 로거 설정
    logger = logging.getLogger('web_server')
    logger.setLevel(logging.DEBUG)
    
    # 파일 핸들러 (상세 로그)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러 (요약 로그)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터 설정
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Flask 앱 생성
app = Flask(__name__)
logger = setup_logging()

# 요청 전후 로깅 미들웨어
@app.before_request
def log_request():
    logger.info(f"요청 시작: {request.method} {request.url}")
    logger.info(f"클라이언트 IP: {request.remote_addr}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    logger.info(f"요청 헤더: {dict(request.headers)}")
    
    # 요청 시작 시간 기록
    request.start_time = time.time()

@app.after_request
def log_response(response):
    # 응답 시간 계산
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.info(f"응답 시간: {duration:.3f}초")
    
    logger.info(f"응답 상태: {response.status_code}")
    logger.info(f"응답 크기: {len(response.get_data())} bytes")
    logger.info(f"응답 헤더: {dict(response.headers)}")
    logger.info(f"요청 완료: {request.method} {request.url}")
    logger.info("-" * 80)
    
    return response

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 에러: {request.url} - 파일을 찾을 수 없음")
    return jsonify({'error': 'File not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 에러: {request.url} - 서버 내부 오류")
    return jsonify({'error': 'Internal server error'}), 500

# 정적 파일 서빙
@app.route('/')
def index():
    logger.info("메인 페이지 요청")
    return send_from_directory('.', 'stock_rsi_chart.html')

@app.route('/<path:filename>')
def serve_file(filename):
    logger.info(f"파일 요청: {filename}")
    
    # 파일 존재 여부 확인
    if os.path.exists(filename):
        logger.info(f"파일 존재: {filename}")
        return send_from_directory('.', filename)
    else:
        logger.warning(f"파일 없음: {filename}")
        return jsonify({'error': 'File not found'}), 404

# 데이터 디렉토리 서빙
@app.route('/data/<path:filepath>')
def serve_data(filepath):
    logger.info(f"데이터 파일 요청: {filepath}")
    
    # 파일 존재 여부 확인
    data_path = os.path.join('data', filepath)
    if os.path.exists(data_path):
        logger.info(f"데이터 파일 존재: {data_path}")
        return send_from_directory('data', filepath)
    else:
        logger.warning(f"데이터 파일 없음: {data_path}")
        return jsonify({'error': 'Data file not found'}), 404

# 헬스체크 엔드포인트
@app.route('/health')
def health_check():
    logger.info("헬스체크 요청")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running'
    })

# 서버 시작 로그
if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("웹서버 시작")
    logger.info(f"시작 시간: {datetime.now()}")
    logger.info(f"작업 디렉토리: {os.getcwd()}")
    logger.info(f"사용 가능한 파일들: {os.listdir('.')}")
    logger.info("=" * 80)
    
    app.run(host='0.0.0.0', port=8000, debug=False) 
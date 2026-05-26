@echo off
setlocal

:: 파이썬이 설치되어 있는지 확인
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 명령어를 찾을 수 없습니다. Python이 설치되어 있고 환경 변수에 추가되어 있는지 확인해주세요.
    pause
    exit /b 1
)

:: 가상환경 폴더(venv)가 존재하는지 확인
if not exist venv\Scripts\activate (
    echo [venv] 가상환경을 생성합니다...
    python -m venv venv
    
    echo 필수 라이브러리를 설치합니다...
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install pybullet opencv-python numpy mediapipe
) else (
    call venv\Scripts\activate
)

:: 메인 프로그램 실행
echo VirtualHand Simulator를 시작합니다...
python main.py
pause

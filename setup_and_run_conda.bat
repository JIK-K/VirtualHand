@echo off
setlocal

:: Conda가 설치되어 있는지 확인
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Conda 명령어를 찾을 수 없습니다. Anaconda Prompt에서 실행하거나 환경 변수에 Conda를 추가해주세요.
    pause
    exit /b 1
)

:: 가상환경이 존재하는지 확인
call conda env list | findstr /C:"virtualhand_env" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [virtualhand_env] 가상환경을 생성합니다...
    call conda create -y -n virtualhand_env python=3.10
    call conda activate virtualhand_env
    echo 필수 라이브러리를 설치합니다...
    call conda install -y -c conda-forge pybullet opencv numpy mediapipe
) else (
    call conda activate virtualhand_env
)

:: 메인 프로그램 실행
echo VirtualHand Simulator를 시작합니다...
python main.py
pause

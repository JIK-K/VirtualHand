#!/bin/bash

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

echo "==========================================================="
echo "Apple Silicon (M1/M2/M3) 완벽 지원을 위한 Conda 환경 셋업을 시작합니다."
echo "==========================================================="

# Conda(Miniforge)가 설치되어 있는지 확인
if ! command -v conda &> /dev/null; then
    echo "Conda(Miniforge)가 설치되어 있지 않습니다. 자동으로 다운로드 및 설치를 진행합니다..."
    
    # Apple Silicon용 Miniforge 다운로드
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
    
    # 조용히(자동으로) 홈 디렉토리에 설치
    bash Miniforge3-MacOSX-arm64.sh -b -p "$HOME/miniforge3"
    
    # 설치 파일 삭제
    rm Miniforge3-MacOSX-arm64.sh
    
    # 현재 세션에 conda 활성화
    source "$HOME/miniforge3/bin/activate"
    
    # 향후 터미널 실행 시 자동으로 conda를 사용할 수 있게 초기화
    conda init zsh
else
    echo "Conda가 이미 설치되어 있습니다."
    # conda 훅 활성화 (스크립트 내에서 conda activate를 사용하기 위함)
    eval "$(conda shell.bash hook)"
fi

# 기존 환경이 있는지 확인 후 없으면 생성
if ! conda info --envs | grep -q "virtualhand_env"; then
    echo "Conda 가상 환경(virtualhand_env)을 생성합니다..."
    conda create -y -n virtualhand_env python=3.10
fi

# 가상 환경 활성화
echo "가상 환경을 활성화합니다..."
source "$HOME/miniforge3/bin/activate" virtualhand_env 2>/dev/null || conda activate virtualhand_env

# 패키지 설치
# 핵심: pybullet은 반드시 conda-forge 채널에서 미리 컴파일된 버전을 가져옵니다!
echo "컴파일 오류 없는 pybullet 버전을 다운로드합니다..."
conda install -y -c conda-forge pybullet

echo "나머지 패키지(opencv, mediapipe, numpy)를 설치합니다..."
pip install opencv-python mediapipe numpy

# 실행
echo "가상 스켈레톤 물리 손 시뮬레이션을 실행합니다..."
python main.py

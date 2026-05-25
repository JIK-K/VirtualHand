#!/bin/bash

# Conda 초기화 스크립트 로드
source "$(conda info --base)/etc/profile.d/conda.sh"

# 가상환경 활성화 (존재하지 않으면 생성 후 활성화)
if ! conda env list | grep -q 'virtualhand_env'; then
    echo "Creating virtualhand_env conda environment..."
    conda create -y -n virtualhand_env python=3.10
    conda activate virtualhand_env
    echo "Installing requirements..."
    conda install -y -c conda-forge pybullet opencv numpy mediapipe
else
    conda activate virtualhand_env
fi

# 메인 프로그램 실행
echo "Starting VirtualHand Simulator..."
python main.py

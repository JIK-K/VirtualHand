# utils.py
import numpy as np

def map_landmarks_to_bullet(landmarks):
    if not landmarks:
        return None
        
    bullet_positions = []
    
    for lm_x, lm_y, lm_z in landmarks:
        # 1. 카메라 좌표계 반전 (캠은 거울 모드이므로 좌우 뒤집기)
        x_ratio = 1.0 - lm_x
        y_ratio = lm_y
        
        # 2. PyBullet 3D 공간 매핑
        # 카메라 좌/우 -> 로봇 좌/우 (X축)
        bullet_x = (x_ratio - 0.5) * 1.5    # 가동 범위를 조금 더 넓힘 (-0.75m ~ +0.75m)
        
        # 카메라 상/하 -> 로봇 위/아래 (Z축)
        bullet_z = 0.0 + (1.0 - y_ratio) * 1.2 # 위아래 가동 범위도 넓힘 (0.0m ~ 1.2m)
        
        # 손가락의 깊이(MediaPipe Z) -> 로봇 앞/뒤 (Y축)
        # MediaPipe에서 Z가 작을수록 카메라와 가까움 -> 로봇의 Y축은 양수가 앞쪽이므로 역으로 매핑
        bullet_y = 0.5 - (lm_z * 1.0) # 기본 0.5m 깊이에서 손가락 굴곡에 따라 앞뒤로 배치됨
        
        bullet_positions.append([bullet_x, bullet_y, bullet_z])
        
    return bullet_positions
# utils.py
import numpy as np

def map_landmarks_to_bullet(landmarks):
    if not landmarks:
        return None
        
    bullet_positions = []
    
    # 1. 화면상 손 크기 계산 (손목~중지뿌리 거리)
    p0 = landmarks[0]
    p9 = landmarks[9]
    dx = p0[0] - p9[0]
    dy = p0[1] - p9[1]
    hand_size = np.sqrt(dx*dx + dy*dy) + 1e-6
    
    # 사용자 피드백 반영: 앞뒤(깊이) 조절이 너무 어려우므로, 
    # 손의 위치를 바구니가 있는 Y=0.5 라인에 완벽히 '고정'시킵니다. 
    # 이제 카메라 앞뒤로 손을 뻗을 필요 없이 좌우/상하로만 움직이면 무조건 공 위에 손이 위치합니다!
    TARGET_SIZE = 0.15 # 물리 엔진에서 유지할 고정 손 크기 기준
    base_y = 0.5 # 바구니 중앙 깊이로 완벽 고정
    
    # 2. 손목(0번 관절)의 위치를 로봇 공간의 앵커(기준점)로 삼습니다.
    # 민감도 폭풍 증가: 화면 중앙에서 조금만 손을 움직여도 양쪽 바구니(-0.4 ~ 0.4)에 쉽게 닿도록 2.5배 증폭
    base_x = (1.0 - p0[0] - 0.5) * 2.5
    # 상하 이동 민감도 증가 및 바구니 바닥에 손이 쉽게 닿도록 초기 높이(오프셋)를 낮춤
    base_z = -0.05 + (1.0 - p0[1]) * 1.5
    
    # 3. 손 크기가 화면에서 커져도(카메라에 가까워져도) 물리 엔진 상의 손 크기는 고정되도록 스케일 보정
    scale_factor = TARGET_SIZE / hand_size
    
    for lm_x, lm_y, lm_z in landmarks:
        # 손목 좌표 대비 화면 상의 상대적인 X, Y 변위
        rel_x = (1.0 - lm_x) - (1.0 - p0[0])
        rel_y = (1.0 - lm_y) - (1.0 - p0[1])
        
        # 보정된 변위를 손목 기준점에 더해서 최종 좌표 생성
        bullet_x = base_x + (rel_x * 1.5 * scale_factor)
        bullet_z = base_z + (rel_y * 1.2 * scale_factor)
        
        # 깊이(Z)도 스케일 보정
        bullet_y = base_y - (lm_z * 0.8 * scale_factor)
        
        bullet_positions.append([bullet_x, bullet_y, bullet_z])
        
    return bullet_positions
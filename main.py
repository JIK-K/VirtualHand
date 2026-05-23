# main.py
import cv2
import time
from camera_processor import HandTracker
from robot_simulator import RobotSim
from utils import map_landmarks_to_bullet

def main():
    print("=========================================")
    print("카메라를 선택해주세요.")
    print("0: 기본 카메라 (Mac의 경우 연속성 카메라/아이폰)")
    print("1: 내장 웹캠 (MacBook 카메라)")
    print("=========================================")
    cam_input = input("카메라 번호를 입력하세요 (기본값 0): ")
    camera_index = int(cam_input) if cam_input.strip().isdigit() else 0

    tracker = HandTracker(camera_index=camera_index)  # 노트북 캠 & MediaPipe AI 인스턴스 생성
    sim = RobotSim()         # 3D PyBullet 가상 환경 인스턴스 생성
    
    print("=========================================")
    print("가상 스켈레톤 물리 손 시뮬레이션을 시작합니다. 종료하려면 캠 화면에서 'q'를 누르세요.")
    print("=========================================")

    while True:
        # 1. 노트북 캠에서 21개 손가락 마디의 3D 좌표 추출
        success, landmarks_data = tracker.get_hand_frame()
        if not success:
            continue
        
        # 2. 21개 마디 좌표를 PyBullet 3D 물리 공간 좌표로 1:1 변환
        target_positions = map_landmarks_to_bullet(landmarks_data)
        
        if target_positions is not None:
            # 3. 가상 손의 21개 구체(충돌체)들을 물리적으로 이동시킴
            # 사용자가 손을 오므리면 구체들이 모이면서 실제로 공을 잡게 됩니다!
            sim.update_hand(target_positions)

        # 캠 화면이나 PyBullet GUI가 꺼지면 루프 탈출
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 자원 해제 및 종료
    tracker.release()
    sim.disconnect()

if __name__ == "__main__":
    main()
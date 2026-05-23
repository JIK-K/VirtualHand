import cv2
import time
import numpy as np
import mediapipe as mp

class HandTracker:
    def __init__(self, camera_index=0):
        # OpenCV 카메라 초기화
        self.cap = cv2.VideoCapture(camera_index)
        
        # [최신 규격] MediaPipe Tasks Vision API 초기화
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        
        # 설정 로드 (다운로드한 hand_landmarker.task 파일 사용)
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
            running_mode=VisionRunningMode.VIDEO, # 끊김 방지를 위해 비디오 연속 추적 모드 사용
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = HandLandmarker.create_from_options(options)
        
        # 성능 모니터링 변수
        self.prev_time = time.time()
        self.latency = 0.0

    def get_hand_frame(self):
        start_time = time.time()
        success, frame = self.cap.read()
        if not success:
            return False, None, False, 0.0

        # 미디어용 이미지 포맷으로 변환 (BGR -> RGB)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # 최신 AI 모델로 손가락 랜드마크 추론 실행 (비디오 모드는 타임스탬프가 필요)
        timestamp_ms = int(time.time() * 1000)
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        # 수동으로 손가락 뼈대 연결선 정의 (mp.solutions가 arm64에서 미지원됨)
        HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]
        
        # 21개 관절의 3D(x, y, z) 데이터를 담을 리스트
        landmarks_data = None
        
        if detection_result.hand_landmarks:
            # 한 손만 처리
            hand_landmarks = detection_result.hand_landmarks[0]
            h, w, _ = frame.shape
            
            # 21개 마디 데이터 추출
            landmarks_data = [(lm.x, lm.y, lm.z) for lm in hand_landmarks]
            
            # OpenCV로 뼈대 그리기
            # 1. 점 그리기
            points_px = []
            for lm in hand_landmarks:
                px, py = int(lm.x * w), int(lm.y * h)
                points_px.append((px, py))
                cv2.circle(frame, (px, py), 4, (121, 22, 76), -1)
                cv2.circle(frame, (px, py), 2, (250, 44, 250), -1)
            
            # 2. 선 그리기
            for connection in HAND_CONNECTIONS:
                pt1 = points_px[connection[0]]
                pt2 = points_px[connection[1]]
                cv2.line(frame, pt1, pt2, (121, 22, 76), 2)

        # 성능 모니터링 계산
        self.latency = (time.time() - start_time) * 1000
        current_time = time.time()
        fps = 1 / (current_time - self.prev_time) if current_time - self.prev_time > 0 else 30
        self.prev_time = current_time
        
        # 화면에 정보 출력
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(frame, f"Latency: {self.latency:.1f}ms", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if landmarks_data:
            cv2.putText(frame, "Skeleton Mode: ON", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        cv2.imshow("Hand Tracking System", frame)
        
        # 성공여부와 21개 관절 데이터만 반환
        return True, landmarks_data

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
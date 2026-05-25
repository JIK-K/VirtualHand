# VirtualHand Physics Simulator 🖐️🤖

VirtualHand Physics Simulator는 사용자의 웹캠만을 사용하여 가상 3D 공간(PyBullet) 안의 다관절 로봇 손을 실시간으로 조작하고 물리적 상호작용(공 집기, 퍼 담기, 옮기기)을 체험할 수 있는 프로젝트입니다. 별도의 VR 장비나 컨트롤러 없이, 맨손의 움직임만으로 정교한 가상 세계 조작을 목표로 합니다.

## 🚀 데모 (주요 기능)
- **실시간 웹캠 핸드 트래킹**: MediaPipe를 활용해 21개의 손가락 관절(Landmark)을 실시간으로 추적합니다.
- **다관절 물리 시뮬레이션**: 추출된 2D/3D 좌표를 PyBullet 물리 엔진의 21개 관절(Sphere)과 20개 뼈대(Capsule), 그리고 단단한 손바닥(Cylinder)에 1:1로 매핑하여 실제 손처럼 작동하게 합니다.
- **아케이드 스타일 조작 (깊이 고정)**: 2D 카메라의 한계인 앞뒤(깊이) 거리 조절의 어려움을 극복하기 위해, 가상 손의 Y축 깊이를 바구니 중심 라인에 고정하고 좌우(X축)/상하(Z축) 조작 민감도를 증폭시켰습니다. 허공에서 가볍게 손을 움직이는 것만으로도 쉽게 바구니 사이를 오갈 수 있습니다.
- **Soft Hand 물리 제어**: 단단한 강체들이 서로 부딪히며 폭발적으로 튕겨 나가는 현상(물리 글리치)을 방지하기 위해, 손 관절의 강제 이동 힘(`maxForce`)을 줄이고 표면 마찰력(`lateralFriction`)을 극대화하여 실제 손처럼 "부드럽게 감싸 쥐는" 상호작용을 구현했습니다.

## 🛠 사용 기술 (Tech Stack)
- **Language**: Python 3.10
- **Physics Engine**: `pybullet` (실시간 3D 충돌 및 리지드 바디 시뮬레이션)
- **Computer Vision**: `mediapipe` (웹캠 기반 고해상도 핸드 랜드마크 추출), `opencv-python` (카메라 제어 및 화면 렌더링)
- **Math & Vector**: `numpy` (공간 벡터 연산 및 쿼터니언 변환)

## 📁 프로젝트 구조
- `main.py`: 프로그램 실행 진입점. 카메라 입력과 물리 엔진 루프를 병렬/동기화하여 실행합니다.
- `camera_processor.py`: MediaPipe Tasks API를 사용해 영상에서 손의 랜드마크를 추출합니다.
- `robot_simulator.py`: PyBullet을 이용해 양쪽 바구니, 20개의 공, 그리고 다관절 손을 생성하고 물리 연산을 수행합니다.
- `utils.py`: 카메라에서 추출된 손 좌표를 물리 엔진의 3D 공간으로 변환, 스케일링, 역기구학 보정 등을 처리합니다.

## ⚙️ 설치 및 실행 방법 (macOS / Apple Silicon)
PyBullet의 C++ 빌드 호환성을 위해 **Conda 환경** 사용을 권장합니다.

```bash
# 1. 가상환경 생성 및 활성화
conda create -n virtualhand_env python=3.10
conda activate virtualhand_env

# 2. 필수 라이브러리 설치 (conda-forge 활용)
conda install -c conda-forge pybullet opencv numpy mediapipe

# 3. 프로젝트 실행
python main.py
```

## 🎮 조작 방법
- 스크립트를 실행하면 웹캠 화면과 PyBullet 3D 화면이 동시에 열립니다.
- 웹캠 화면에 손을 펴서 보여주면 가상 공간에 로봇 손이 나타납니다.
- 손을 **좌/우/상/하**로 움직여 우측 바구니(시작 바구니)에 있는 붉은 공 위로 손을 이동시킵니다.
- 손가락을 오므려서 공을 **잡거나(Grab)** 손바닥 면을 이용해 **퍼 담은(Scoop)** 뒤, 좌측 바구니(목표 바구니)로 이동하여 공을 떨어뜨립니다.
- 종료하려면 웹캠 화면(OpenCV 창)이 활성화된 상태에서 `q` 키를 누르세요.
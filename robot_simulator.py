# robot_simulator.py
import pybullet as pybullet
import pybullet_data
import time
import numpy as np
import math

class RobotSim:
    def __init__(self):
        # 1. GUI 모드로 PyBullet 물리 엔진 시작
        self.physicsClient = pybullet.connect(pybullet.GUI)
        pybullet.setAdditionalSearchPath(pybullet_data.getDataPath())
        
        # 중력 설정 (지구 중력 -9.81m/s^2)
        pybullet.setGravity(0, 0, -9.81)
        
        # 2. PyBullet 카메라 시점 정면으로 설정 (원상복구)
        pybullet.resetDebugVisualizerCamera(cameraDistance=1.2, cameraYaw=0, cameraPitch=-30, cameraTargetPosition=[0, 0.5, 0.2])
        
        self.planeId = pybullet.loadURDF("plane.urdf")
        
        # 바구니 크기 설정 (넉넉한 직사각형 형태로 원복하되 크게)
        basket_w = 0.45 # 가로세로 폭
        basket_h = 0.15 # 바구니 벽 높이
        wall_t = 0.02   # 벽 두께
        
        # 오른쪽 시작 바구니 (x=0.4)
        self._create_tall_basket(0.4, 0.5, 0.0, basket_w, basket_h, wall_t)
        # 왼쪽 목표 바구니 (x=-0.4)
        self._create_tall_basket(-0.4, 0.5, 0.0, basket_w, basket_h, wall_t)
        
        # 3. 바구니 안에 가득 채울 20개의 큰 공 생성 (크기 적절히 조절)
        self.balls = []
        ball_radius = 0.04  # 크기를 3배(0.055)에서 살짝 줄여서 0.04로 설정
        ball_col_id = pybullet.createCollisionShape(pybullet.GEOM_SPHERE, radius=ball_radius)
        ball_vis_id = pybullet.createVisualShape(pybullet.GEOM_SPHERE, radius=ball_radius, rgbaColor=[1, 0.3, 0.3, 1])
        
        for i in range(20): # 크기가 커졌으므로 20개만 배치해도 가득 찹니다.
            # 시작 바구니(0.4, 0.5) 안에 위치하도록 입체적으로 분산 배치
            bx = 0.4 + (i % 3 - 1) * 0.06
            by = 0.5 + ((i % 9) // 3 - 1) * 0.06
            bz = 0.1 + (i // 9) * 0.06
            ball_id = pybullet.createMultiBody(baseMass=0.05, # 부드러운 손이 쉽게 들 수 있도록 무게 감소
                                               baseCollisionShapeIndex=ball_col_id, 
                                               baseVisualShapeIndex=ball_vis_id, 
                                               basePosition=[bx, by, bz])
            pybullet.changeDynamics(ball_id, -1, lateralFriction=2.0) # 마찰력을 크게 높여 잘 잡히도록 함
            self.balls.append(ball_id)
        
        # 4. 손가락 관절 및 뼈대(캡슐) 복구 (자유자재로 움직이는 진짜 손 형태)
        self.hand_nodes = []
        self.hand_constraints = []
        
        # 핵심 해결책: 부드러운 물리 제어를 위한 설정값 (Soft Hand)
        # maxForce를 확 낮춰서(500->40) 공과 부딪힐 때 튕겨나가는 폭발(글리치) 현상을 완전히 방지합니다.
        joint_force = 40
        bone_force = 30
        palm_force = 100
        friction_val = 2.0 # 마찰력을 최대로 올려 손가락 사이에서 공이 미끄러지지 않게 함
        
        # 4-1. 21개 가상 손가락 관절(Sphere) 생성 (살구색 스킨톤)
        node_col_id = pybullet.createCollisionShape(pybullet.GEOM_SPHERE, radius=0.03)
        node_vis_id = pybullet.createVisualShape(pybullet.GEOM_SPHERE, radius=0.03, rgbaColor=[0.98, 0.8, 0.69, 1])
        
        for i in range(21):
            node_id = pybullet.createMultiBody(baseMass=0.5, 
                                               baseCollisionShapeIndex=node_col_id,
                                               baseVisualShapeIndex=node_vis_id,
                                               basePosition=[0, 0, -1]) 
            pybullet.changeDynamics(node_id, -1, lateralFriction=friction_val)
            self.hand_nodes.append(node_id)
            
            cid = pybullet.createConstraint(parentBodyUniqueId=node_id,
                                            parentLinkIndex=-1,
                                            childBodyUniqueId=-1,
                                            childLinkIndex=-1,
                                            jointType=pybullet.JOINT_FIXED,
                                            jointAxis=[0, 0, 0],
                                            parentFramePosition=[0, 0, 0],
                                            childFramePosition=[0, 0, 0])
            pybullet.changeConstraint(cid, maxForce=joint_force) 
            self.hand_constraints.append(cid)
            
        # 4-2. 손가락 뼈대(Capsule) 생성 (선)
        self.bone_nodes = []
        self.bone_constraints = []
        
        self.HAND_CONNECTIONS = [
            (1, 2), (2, 3), (3, 4),      # 엄지
            (5, 6), (6, 7), (7, 8),      # 검지
            (9, 10), (10, 11), (11, 12), # 중지
            (13, 14), (14, 15), (15, 16),# 약지
            (17, 18), (18, 19), (19, 20),# 새끼
            (0, 1), (0, 5), (0, 9), (0, 13), (0, 17) # 손목 연결
        ]
        
        finger_radius = 0.025 # 굵은 선으로 집기 편하게
        bone_height = 0.04 # 약간 줄여서 마디 밖으로 삐져나오지 않게 함
        
        finger_col_id = pybullet.createCollisionShape(pybullet.GEOM_CAPSULE, radius=finger_radius, height=bone_height)
        finger_vis_id = pybullet.createVisualShape(pybullet.GEOM_CAPSULE, radius=finger_radius, length=bone_height, rgbaColor=[0.98, 0.8, 0.69, 1])
        
        for idx, (i, j) in enumerate(self.HAND_CONNECTIONS):
            bone_id = pybullet.createMultiBody(baseMass=0.2, 
                                               baseCollisionShapeIndex=finger_col_id, 
                                               baseVisualShapeIndex=finger_vis_id, 
                                               basePosition=[0, 0, -1])
            pybullet.changeDynamics(bone_id, -1, lateralFriction=friction_val)
            self.bone_nodes.append(bone_id)
            cid = pybullet.createConstraint(parentBodyUniqueId=bone_id,
                                            parentLinkIndex=-1,
                                            childBodyUniqueId=-1,
                                            childLinkIndex=-1,
                                            jointType=pybullet.JOINT_FIXED,
                                            jointAxis=[0, 0, 0],
                                            parentFramePosition=[0, 0, 0],
                                            childFramePosition=[0, 0, 0])
            pybullet.changeConstraint(cid, maxForce=bone_force)
            self.bone_constraints.append(cid)
            
        # 4-3. 진짜 손바닥 면(Cylinder) 생성 (면)
        palm_radius = 0.055 # 손바닥 반경 5.5cm
        palm_height = 0.025 # 두께 2.5cm
        palm_col = pybullet.createCollisionShape(pybullet.GEOM_CYLINDER, radius=palm_radius, height=palm_height)
        palm_vis = pybullet.createVisualShape(pybullet.GEOM_CYLINDER, radius=palm_radius, length=palm_height, rgbaColor=[0.98, 0.8, 0.69, 1])
        self.palm_body = pybullet.createMultiBody(baseMass=0.5, baseCollisionShapeIndex=palm_col, baseVisualShapeIndex=palm_vis, basePosition=[0, 0, -1])
        pybullet.changeDynamics(self.palm_body, -1, lateralFriction=friction_val)
        self.palm_cid = pybullet.createConstraint(self.palm_body, -1, -1, -1, pybullet.JOINT_FIXED, [0,0,0], [0,0,0], [0,0,0])
        pybullet.changeConstraint(self.palm_cid, maxForce=palm_force)
        
        # 손 부위들끼리는 서로 충돌 무시
        all_hand_parts = self.hand_nodes + self.bone_nodes + [self.palm_body]
        for i in range(len(all_hand_parts)):
            for j in range(len(all_hand_parts)):
                if i != j:
                    pybullet.setCollisionFilterPair(all_hand_parts[i], all_hand_parts[j], -1, -1, 0)
        
        # 리얼타임 물리 연산 활성화
        pybullet.setRealTimeSimulation(1)

    def _create_tall_basket(self, center_x, center_y, center_z, width, height, wall_thickness):
        """특정 위치에 단순하고 넓은 직사각형 바구니를 생성하는 함수"""
        color = [0.4, 0.4, 0.4, 1]
        
        # 바닥 (Base)
        base_col = pybullet.createCollisionShape(pybullet.GEOM_BOX, halfExtents=[width/2, width/2, wall_thickness/2])
        base_vis = pybullet.createVisualShape(pybullet.GEOM_BOX, halfExtents=[width/2, width/2, wall_thickness/2], rgbaColor=color)
        pybullet.createMultiBody(baseMass=0, baseCollisionShapeIndex=base_col, baseVisualShapeIndex=base_vis, basePosition=[center_x, center_y, center_z + wall_thickness/2])
        
        # 4면 벽 (Walls) - 수직 벽 (깔끔하고 가장 확실함)
        wall_col_fb = pybullet.createCollisionShape(pybullet.GEOM_BOX, halfExtents=[width/2, wall_thickness/2, height/2])
        wall_vis_fb = pybullet.createVisualShape(pybullet.GEOM_BOX, halfExtents=[width/2, wall_thickness/2, height/2], rgbaColor=color)
        # 앞 벽 (+y)
        pybullet.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_col_fb, baseVisualShapeIndex=wall_vis_fb, basePosition=[center_x, center_y + width/2 - wall_thickness/2, center_z + height/2 + wall_thickness])
        # 뒤 벽 (-y)
        pybullet.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_col_fb, baseVisualShapeIndex=wall_vis_fb, basePosition=[center_x, center_y - width/2 + wall_thickness/2, center_z + height/2 + wall_thickness])
        
        wall_col_lr = pybullet.createCollisionShape(pybullet.GEOM_BOX, halfExtents=[wall_thickness/2, width/2 - wall_thickness, height/2])
        wall_vis_lr = pybullet.createVisualShape(pybullet.GEOM_BOX, halfExtents=[wall_thickness/2, width/2 - wall_thickness, height/2], rgbaColor=color)
        # 우 벽 (+x)
        pybullet.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_col_lr, baseVisualShapeIndex=wall_vis_lr, basePosition=[center_x + width/2 - wall_thickness/2, center_y, center_z + height/2 + wall_thickness])
        # 좌 벽 (-x)
        pybullet.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_col_lr, baseVisualShapeIndex=wall_vis_lr, basePosition=[center_x - width/2 + wall_thickness/2, center_y, center_z + height/2 + wall_thickness])

    def _get_quaternion_from_vector(self, v):
        """벡터 방향을 향하는 쿼터니언 회전값 계산 (Z축 기준 캡슐용)"""
        v = np.array(v)
        norm = np.linalg.norm(v)
        if norm < 1e-6:
            return [0, 0, 0, 1]
        v = v / norm
        z_axis = np.array([0, 0, 1])
        axis = np.cross(z_axis, v)
        angle = math.acos(np.clip(np.dot(z_axis, v), -1.0, 1.0))
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-6:
            if angle > 0.1:
                return [1, 0, 0, 0]
            else:
                return [0, 0, 0, 1]
        axis = axis / axis_norm
        qx = axis[0] * math.sin(angle/2)
        qy = axis[1] * math.sin(angle/2)
        qz = axis[2] * math.sin(angle/2)
        qw = math.cos(angle/2)
        return [qx, qy, qz, qw]

    def update_hand(self, target_positions):
        """카메라에서 받은 손 랜드마크 3D 좌표를 PyBullet 로봇 손에 반영"""
        if not target_positions or len(target_positions) != 21:
            return
            
        # 1. 21개 관절 위치 갱신
        for i in range(21):
            pybullet.changeConstraint(self.hand_constraints[i], jointChildPivot=target_positions[i])
            
        # 2. 손바닥(면) 위치 및 회전 갱신
        p0 = np.array(target_positions[0])
        p5 = np.array(target_positions[5])
        p17 = np.array(target_positions[17])
        p9 = np.array(target_positions[9])
        
        palm_center = (p0 + p9) / 2.0
        
        # 손바닥 평면의 법선 벡터 계산
        v1 = p17 - p5
        v2 = p0 - p9
        normal = np.cross(v1, v2)
        
        quat_palm = self._get_quaternion_from_vector(normal)
        pybullet.changeConstraint(self.palm_cid, 
                                  jointChildPivot=palm_center.tolist(), 
                                  jointChildFrameOrientation=quat_palm)
                                  
        # 3. 20개 뼈대(캡슐) 위치 및 회전 갱신
        for idx, (i, j) in enumerate(self.HAND_CONNECTIONS):
            ptA = np.array(target_positions[i])
            ptB = np.array(target_positions[j])
            
            midpoint = (ptA + ptB) / 2.0
            direction = ptB - ptA
            quat = self._get_quaternion_from_vector(direction)
            
            pybullet.changeConstraint(self.bone_constraints[idx], 
                                      jointChildPivot=midpoint.tolist(), 
                                      jointChildFrameOrientation=quat)



    def disconnect(self):
        pybullet.disconnect()
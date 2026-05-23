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
        
        # 2. PyBullet 카메라 시점 정면으로 설정 (바구니와 공이 잘 보이도록)
        pybullet.resetDebugVisualizerCamera(cameraDistance=1.2, cameraYaw=0, cameraPitch=-30, cameraTargetPosition=[0, 0.5, 0.2])
        
        self.planeId = pybullet.loadURDF("plane.urdf")
        
        # 바구니 2개 배치 (traybox.urdf)
        self.basket1Id = pybullet.loadURDF("tray/traybox.urdf", [0.3, 0.5, 0.0]) # 오른쪽 (시작 바구니)
        self.basket2Id = pybullet.loadURDF("tray/traybox.urdf", [-0.3, 0.5, 0.0]) # 왼쪽 (목표 바구니)
        
        # 3. 옮길 수 있는 큰 공 바구니 위에 추가
        ball_radius = 0.035
        ball_col_id = pybullet.createCollisionShape(pybullet.GEOM_SPHERE, radius=ball_radius)
        ball_vis_id = pybullet.createVisualShape(pybullet.GEOM_SPHERE, radius=ball_radius, rgbaColor=[1, 0.2, 0.2, 1])
        # 공을 첫 번째 바구니 바로 위에 떨어뜨림
        self.ballId = pybullet.createMultiBody(baseMass=0.5, baseCollisionShapeIndex=ball_col_id, baseVisualShapeIndex=ball_vis_id, basePosition=[0.3, 0.5, 0.3])
        
        # 4. 손가락 관절 및 뼈대(캡슐) 생성
        self.hand_nodes = []
        self.hand_constraints = []
        
        # 21개 가상 손가락 관절(Sphere) 생성
        node_col_id = pybullet.createCollisionShape(pybullet.GEOM_SPHERE, radius=0.018)
        node_vis_id = pybullet.createVisualShape(pybullet.GEOM_SPHERE, radius=0.018, rgbaColor=[0.95, 0.8, 0.7, 1])
        
        for i in range(21):
            node_id = pybullet.createMultiBody(baseMass=1.0, 
                                               baseCollisionShapeIndex=node_col_id,
                                               baseVisualShapeIndex=node_vis_id,
                                               basePosition=[0, 0, -1]) 
            self.hand_nodes.append(node_id)
            
            cid = pybullet.createConstraint(parentBodyUniqueId=node_id,
                                            parentLinkIndex=-1,
                                            childBodyUniqueId=-1,
                                            childLinkIndex=-1,
                                            jointType=pybullet.JOINT_FIXED,
                                            jointAxis=[0, 0, 0],
                                            parentFramePosition=[0, 0, 0],
                                            childFramePosition=[0, 0, 0])
            pybullet.changeConstraint(cid, maxForce=500) 
            self.hand_constraints.append(cid)
            
        # 20개 손가락 뼈대(Capsule) 생성
        self.bone_nodes = []
        self.bone_constraints = []
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]
        
        bone_radius = 0.015
        bone_height = 0.035
        bone_col_id = pybullet.createCollisionShape(pybullet.GEOM_CAPSULE, radius=bone_radius, height=bone_height)
        bone_vis_id = pybullet.createVisualShape(pybullet.GEOM_CAPSULE, radius=bone_radius, length=bone_height, rgbaColor=[0.95, 0.8, 0.7, 1])
        
        for i in range(len(self.HAND_CONNECTIONS)):
            bone_id = pybullet.createMultiBody(baseMass=0.5, 
                                               baseCollisionShapeIndex=bone_col_id, 
                                               baseVisualShapeIndex=bone_vis_id, 
                                               basePosition=[0, 0, -1])
            self.bone_nodes.append(bone_id)
            cid = pybullet.createConstraint(parentBodyUniqueId=bone_id,
                                            parentLinkIndex=-1,
                                            childBodyUniqueId=-1,
                                            childLinkIndex=-1,
                                            jointType=pybullet.JOINT_FIXED,
                                            jointAxis=[0, 0, 0],
                                            parentFramePosition=[0, 0, 0],
                                            childFramePosition=[0, 0, 0])
            pybullet.changeConstraint(cid, maxForce=300)
            self.bone_constraints.append(cid)
            
        # 손 부위들(관절, 뼈대)끼리는 서로 충돌 무시 (자기 손가락끼리 튕기지 않도록)
        all_hand_parts = self.hand_nodes + self.bone_nodes
        for i in range(len(all_hand_parts)):
            for j in range(len(all_hand_parts)):
                if i != j:
                    pybullet.setCollisionFilterPair(all_hand_parts[i], all_hand_parts[j], -1, -1, 0)
        
        # 리얼타임 물리 연산 활성화
        pybullet.setRealTimeSimulation(1)

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
        if not target_positions or len(target_positions) != 21:
            return
            
        # 1. 21개 관절 위치 갱신
        for i in range(21):
            pybullet.changeConstraint(self.hand_constraints[i], jointChildPivot=target_positions[i])
            
        # 2. 20개 뼈대(캡슐) 위치 및 회전 갱신
        for idx, (i, j) in enumerate(self.HAND_CONNECTIONS):
            ptA = np.array(target_positions[i])
            ptB = np.array(target_positions[j])
            
            # 두 관절의 중간 지점
            midpoint = (ptA + ptB) / 2.0
            # 두 관절 사이의 방향 벡터
            direction = ptB - ptA
            # 방향 벡터를 쿼터니언(회전값)으로 변환
            quat = self._get_quaternion_from_vector(direction)
            
            pybullet.changeConstraint(self.bone_constraints[idx], 
                                      jointChildPivot=midpoint.tolist(), 
                                      jointChildFrameOrientation=quat)

    def close_gripper(self):
        pass

    def open_gripper(self):
        pass

    def disconnect(self):
        pybullet.disconnect()
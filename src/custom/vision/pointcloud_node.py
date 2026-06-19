import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField, CameraInfo
from std_msgs.msg import String, Header
from cv_bridge import CvBridge

try:
    import sensor_msgs_py.point_cloud2 as pc2
except ImportError:
    pc2 = None

# Default Fallback Intrinsics
CAMERA_FX = 615.0
CAMERA_FY = 615.0
CAMERA_CX = 320.0
CAMERA_CY = 240.0
DEPTH_SCALE = 0.001  # RealSense: mm → m


class PointCloudNode(Node):
    """
    VS-08: YOLO/SAM 세그멘테이션 결과로 물체 영역 포인트클라우드 추출 후 /object_pointcloud 발행.

    흐름:
      /camera/color/image_raw  ─┐
      /camera/aligned_depth_to_color/image_raw ─┤→ SAM 세그멘테이션 → depth 역투영 → /object_pointcloud
      /object_class (YOLO bbox) ─┘
    """

    def __init__(self):
        super().__init__('pointcloud_node')

        # Intrinsics instance variables
        self.fx = CAMERA_FX
        self.fy = CAMERA_FY
        self.cx = CAMERA_CX
        self.cy = CAMERA_CY

        # Subscribers
        self.sub_color = self.create_subscription(
            Image, '/camera/color/image_raw', self._color_cb, 10)
        self.sub_depth = self.create_subscription(
            Image, '/camera/aligned_depth_to_color/image_raw', self._depth_cb, 10)
        self.sub_cam_info = self.create_subscription(
            CameraInfo, '/camera/depth/camera_info', self._cam_info_cb, 10)
        self.sub_object_class = self.create_subscription(
            String, '/object_class', self._object_class_cb, 10)

        # Publisher
        self.pub_pointcloud = self.create_publisher(PointCloud2, '/object_pointcloud', 10)

        self.bridge = CvBridge()
        self.color_image = None
        self.depth_image = None
        self.latest_bbox = None   # [x1, y1, x2, y2] — detection_node에서 받아야 함
        self.sam = None
        self._load_sam()

        self.get_logger().info('Pointcloud node started')

    # ── 초기화 ────────────────────────────────────────────────

    def _load_sam(self):
        # TODO: SAM 모델 로드
        #   from segment_anything import sam_model_registry, SamPredictor
        #   sam_model = sam_model_registry['vit_h'](checkpoint='sam_vit_h_4b8939.pth')
        #   sam_model.cuda()
        #   self.sam = SamPredictor(sam_model)
        pass

    # ── 콜백 ──────────────────────────────────────────────────

    def _color_cb(self, msg: Image):
        self.color_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

    def _depth_cb(self, msg: Image):
        self.depth_image = self.bridge.imgmsg_to_cv2(msg, '16UC1')

    def _cam_info_cb(self, msg: CameraInfo):
        # camera_info로 수신된 파라미터로 내부파라미터 업데이트
        self.fx, self.fy = msg.k[0], msg.k[4]
        self.cx, self.cy = msg.k[2], msg.k[5]

    def _object_class_cb(self, msg: String):
        # detection_node가 bbox 토픽을 별도 발행하도록 협의 필요.
        # 현재는 클래스 수신 시 최신 이미지로 처리 트리거.
        if self.color_image is not None and self.depth_image is not None:
            self._process()

    # ── 처리 파이프라인 ───────────────────────────────────────

    def _process(self):
        mask = self._get_sam_mask(self.color_image, self.latest_bbox)
        if mask is None:
            return
        cloud_msg = self._depth_to_pointcloud(self.depth_image, mask)
        if cloud_msg is not None:
            self.pub_pointcloud.publish(cloud_msg)

    def _get_sam_mask(self, color_image, bbox_xyxy):
        # TODO: YOLO bbox를 SAM 프롬프트로 사용하여 이진 세그멘테이션 마스크 생성
        #
        # bbox_xyxy: [x1, y1, x2, y2] (픽셀 좌표, detection_node에서 수신)
        #
        #   self.sam.set_image(color_image)
        #   input_box = np.array(bbox_xyxy)
        #   masks, scores, _ = self.sam.predict(
        #       box=input_box[None, :],
        #       multimask_output=False,
        #   )
        #   return masks[0]  # shape (H, W), bool
        return None

    def _depth_to_pointcloud(self, depth_image, mask):
        # 마스크 영역 depth 픽셀을 카메라 내부 파라미터로 3D 좌표 변환
        ys, xs = np.where(mask)
        z = depth_image[ys, xs].astype(np.float32) * DEPTH_SCALE   # mm → m
        valid = z > 0
        xs, ys, z = xs[valid], ys[valid], z[valid]

        if len(z) == 0:
            return None

        x = (xs - self.cx) * z / self.fx
        y = (ys - self.cy) * z / self.fy
        points = np.stack([x, y, z], axis=1)   # shape (N, 3)

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera_color_optical_frame'
        if pc2 is not None:
            return pc2.create_cloud_xyz32(header, points.tolist())
        return None


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

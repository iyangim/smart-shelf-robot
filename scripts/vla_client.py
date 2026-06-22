#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

# Import the custom action message
from custom_interfaces.action import ShelfManipulate

class VlaClient(Node):
    def __init__(self):
        super().__init__('vla_client')
        self._action_client = ActionClient(self, ShelfManipulate, 'shelf_manipulate')

    def send_instruction(self, instruction: str):
        self.get_logger().info(f"⏳ Waiting for '/shelf_manipulate' action server...")
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("❌ Action server not available. Make sure vla_bridge_node is running.")
            return False

        goal_msg = ShelfManipulate.Goal()
        goal_msg.instruction = instruction

        self.get_logger().info(f"📤 Sending high-level instruction: '{instruction}'")
        
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, 
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        return True

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("❌ Instruction goal was rejected by VLA bridge.")
            return

        self.get_logger().info("✅ Goal accepted by VLA bridge. Executing...")
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        pos = feedback.macro_target.pose.position
        self.get_logger().info(
            f"🔄 [FEEDBACK] {feedback.current_status} | "
            f"Target: [{pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}]"
        )

    def get_result_callback(self, future):
        result = future.result().result
        if result.success:
            self.get_logger().info("🏁 [SUCCESS] VLA instruction execution completed successfully.")
        else:
            self.get_logger().error("❌ VLA instruction execution failed.")
        
        # Shut down node after completion
        rclpy.shutdown()
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Test client for ROS 2 VLA bridge")
    parser.add_argument(
        '--instruction', 
        type=str, 
        default="음료 캔을 집어서 첫 번째 매대에 진열해줘",
        help="High-level natural language instruction to send to the VLA node."
    )
    args, unknown = parser.parse_known_args()

    rclpy.init()
    client = VlaClient()
    
    if client.send_instruction(args.instruction):
        rclpy.spin(client)
    else:
        rclpy.shutdown()

if __name__ == '__main__':
    main()

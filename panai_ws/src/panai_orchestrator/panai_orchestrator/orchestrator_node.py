import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from panai_msgs.msg import SessionState
from panai_msgs.srv import StartSession, StopSession
from lifecycle_msgs.srv import ChangeState
from lifecycle_msgs.msg import Transition
import threading
import time
import datetime

class OrchestratorNode(Node):
    def __init__(self):
        super().__init__('orchestrator_node')
        
        self.state_pub = self.create_publisher(SessionState, '/panai/session/state', 10)
        self.cb_group = ReentrantCallbackGroup()
        
        self.start_srv = self.create_service(StartSession, '/panai/session/start', self.start_cb, callback_group=self.cb_group)
        self.stop_srv = self.create_service(StopSession, '/panai/session/stop', self.stop_cb, callback_group=self.cb_group)
        
        self.session_active = False
        self.session_id = ""
        
        self.vision_client = self.create_client(ChangeState, '/vision_node/change_state', callback_group=self.cb_group)
        self.acoustic_client = self.create_client(ChangeState, '/acoustic_bridge_node/change_state', callback_group=self.cb_group)
        
        self.timer = self.create_timer(1.0, self.publish_state)
        
        self.get_logger().info('Orchestrator node started. State: IDLE')
        
        threading.Thread(target=self.init_nodes, daemon=True).start()
        
    def change_node_state(self, client, transition_id):
        if not client.wait_for_service(timeout_sec=2.0):
            self.get_logger().warn(f'Service {client.srv_name} not available.')
            return False
            
        req = ChangeState.Request()
        req.transition.id = transition_id
        future = client.call_async(req)
        try:
            result = future.result()
            return result.success
        except Exception as e:
            self.get_logger().error(f'Failed to change state: {e}')
            return False

    def init_nodes(self):
        self.get_logger().info('Waiting for managed nodes...')
        self.get_logger().info('Orchestrator ready to manage session.')

    def publish_state(self):
        msg = SessionState()
        msg.header.stamp = self.get_clock().now().to_msg()
        # 0=IDLE, 1=ACTIVE, 2=FAULT
        msg.state = 1 if self.session_active else 0
        msg.session_id = self.session_id
        self.state_pub.publish(msg)

    def start_cb(self, request, response):
        if self.session_active:
            self.get_logger().warn('Session already active.')
            response.success = False
            response.session_id = self.session_id
            return response
            
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_active = True
        
        self.get_logger().info(f'Session {self.session_id} started by operator: {request.operator_name}')
        response.success = True
        response.session_id = self.session_id
        self.publish_state()
        return response
        
    def stop_cb(self, request, response):
        if not self.session_active:
            self.get_logger().warn('No active session to stop.')
            response.success = False
            return response
            
        self.get_logger().info(f'Session {self.session_id} stopped.')
        self.session_active = False
        self.session_id = ""
        response.success = True
        self.publish_state()
        return response

def main(args=None):
    rclpy.init(args=args)
    node = OrchestratorNode()
    from rclpy.executors import MultiThreadedExecutor
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

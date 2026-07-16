import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from panai_msgs.msg import HeightEstimate

class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')
        self.height_pub = self.create_publisher(HeightEstimate, '/panai/state/height', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.get_logger().info('Odometry node started, listening to /odom')

    def odom_callback(self, msg: Odometry):
        height_m = msg.pose.pose.position.x
        
        out_msg = HeightEstimate()
        out_msg.header.stamp = self.get_clock().now().to_msg()
        out_msg.height_mm = float(height_m * 1000.0)
        out_msg.source = 'wheel_odom'
        out_msg.confidence = 1.0
        
        self.height_pub.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

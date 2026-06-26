import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time
import struct
import threading

class SerialReader(Node):
    def __init__(self):
        super().__init__('serial_reader')
        self.port = '/dev/ttyACM0'   # CHANGE if needed
        self.baudrate = 115200
        self.running = True
        self.reader = threading.Thread(target=self.read_serial, daemon=True)
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # allow device reset
            self.get_logger().info(f"Serial connected on {self.port}")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None
            
        # publishers
        # self.e1 = self.create_publisher(Float32MultiArray, '/encoders/base', 10)
        # self.e2 = self.create_publisher(Float32MultiArray, '/encoders/prox', 10)
        # self.e3 = self.create_publisher(Float32MultiArray, '/encoders/dist', 10)
        # self.e4 = self.create_publisher(Float32MultiArray, '/encoders/wrist_pitch', 10)
        # self.e5 = self.create_publisher(Float32MultiArray, '/encoders/elbow_pitch', 10)
        self.pub = self.create_publisher(Float32MultiArray, "/physical_encoders")

        self.reader.start()
        self.get_logger().info("STM Serial Reader Ready")
                
    def sync(self):
        self.ser.reset_input_buffer()
        while self.running:
            data = self.ser.read(1)
            if data == b'\x67':
                return
                
    def read_serial(self):
        self.sync()
        while self.running:
            msg_type = self.ser.read(1)
            if msg_type == b'\x00':
                self.pub_sensors()
            elif msg_type == b'\x01':
                self.log_msg()
                
    def pub_sensors(self):
        msg_len = self.ser.read(2) # drain the size segment of the header
        sensor_payload = self.ser.read(msg_len)
        
        if len(sensor_payload) == msg_len:
            values = struct.unpack(f"<8f", sensor_payload)
        
            # e1_reading = Float32MultiArray()
            # e2_reading = Float32MultiArray()
            # e3_reading = Float32MultiArray()
            
            # e1_reading.data = values[0:2]
            # e2_reading.data = values[2:4]
            # e3_reading.data = values[4:6]
            
            # self.e1.publish(e1_reading) 
            # self.e2.publish(e2_reading)
            # self.e3.publish(e3_reading)
            
            encoder_readings = Float32MultiArray()
            encoder_readings.data = values
            self.pub.publish(encoder_readings)
        else:
            print(len(sensor_payload))

    def log_msg(self):
        msg_len = struct.unpack("<H",self.ser.read(2))
        debug_text = self.ser.read(msg_len[0])
        self.get_logger().info(f"Serial-Debug|{debug_text}")
    
    def destroy_node(self):
        self.running = False
        self.reader.join()
        self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SerialReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
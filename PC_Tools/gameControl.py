import serial
import keyboard
import mouse
import threading
from typing import Optional, Tuple
import math

# Global configuration
THRESHOLD_Z = 60000  # Z threshold for activation
THRESHOLD_XY = 16384  # XY threshold for directional controls
CENTER_VALUE = 32767  # Center point of the 16-bit range (65535/2)
MAX_MOUSE_SPEED = 50  # Maximum pixels per update for mouse movement

class SerialMonitor:
    def __init__(self, port: str, control_type: str):
        self.port = port
        self.control_type = control_type  # 'keyboard' or 'mouse'
        self.serial = None
        self.running = False
    
    def parse_data(self, line: str) -> Optional[Tuple[int, int, int]]:
        try:
            parts = line.strip().split()
            x = int(parts[1])
            y = int(parts[3])
            z = int(parts[5])
            return x, y, z
        except (ValueError, IndexError):
            return None
    
    def calculate_mouse_speed(self, value: int) -> float:
        # Calculate distance from center (0 to 32767)
        distance = abs(value - CENTER_VALUE)
        # Convert to a speed multiplier (0.0 to 1.0)
        speed_multiplier = (distance / CENTER_VALUE) ** 2
        return speed_multiplier * MAX_MOUSE_SPEED
    
    def process_keyboard(self, x: int, y: int, z: int):
        if z >= THRESHOLD_Z:
            # Release all keys when Z is above threshold
            for key in ['w', 's', 'a', 'd']:
                keyboard.release(key)
            return
            
        # Check X and Y coordinates and simulate key presses
        if x <= THRESHOLD_XY:
            keyboard.press('a')
        else:
            keyboard.release('a')
            
        if x >= (65535 - THRESHOLD_XY):
            keyboard.press('d')
        else:
            keyboard.release('d')
            
        if y <= THRESHOLD_XY:
            keyboard.press('w')
        else:
            keyboard.release('w')
            
        if y >= (65535 - THRESHOLD_XY):
            keyboard.press('s')
        else:
            keyboard.release('s')
    
    def process_mouse(self, x: int, y: int, z: int):
        if z >= THRESHOLD_Z:
            return
            
        # Calculate X and Y movements based on distance from center
        x_movement = self.calculate_mouse_speed(x)
        y_movement = self.calculate_mouse_speed(y)
        
        # Determine direction
        x_direction = 1 if x > CENTER_VALUE else -1
        y_direction = 1 if y > CENTER_VALUE else -1
        
        # Apply dead zone near center
        if abs(x - CENTER_VALUE) > THRESHOLD_XY:
            mouse.move(x_direction * x_movement, 0, absolute=False)
        if abs(y - CENTER_VALUE) > THRESHOLD_XY:
            mouse.move(0, y_direction * y_movement, absolute=False)
    
    def read_serial(self):
        try:
            self.serial = serial.Serial(self.port, baudrate=115200)
            while self.running:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8')
                    coords = self.parse_data(line)
                    if coords:
                        if self.control_type == 'keyboard':
                            self.process_keyboard(*coords)
                        else:
                            self.process_mouse(*coords)
        except serial.SerialException as e:
            print(f"Error on {self.port}: {e}")
        finally:
            if self.serial:
                self.serial.close()
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.read_serial)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.serial:
            self.serial.close()

def main():
    # Create monitors for keyboard and mouse control
    keyboard_monitor = SerialMonitor('COM3', 'keyboard')
    mouse_monitor = SerialMonitor('COM4', 'mouse')
    
    try:
        # Start both monitors
        print("Starting serial monitors...")
        print("COM3: Keyboard control (WSAD)")
        print("COM4: Mouse control")
        keyboard_monitor.start()
        mouse_monitor.start()
        
        # Keep the main thread running
        print("Press Ctrl+C to exit")
        while True:
            pass
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        keyboard_monitor.stop()
        mouse_monitor.stop()

if __name__ == "__main__":
    main()

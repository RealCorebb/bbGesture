import serial
import keyboard
import win32api
import win32con

import threading
import time
from typing import Optional, Tuple

THRESHOLD_Z = 60000
THRESHOLD_XY = 16384
CENTER_VALUE = 32767
MAX_MOUSE_SPEED = 20

class SerialMonitor:
    def __init__(self, port: str, control_type: str):
        self.port = port
        self.control_type = control_type
        self.serial = None
        self.running = False
        self.buffer = ''

    def parse_data(self, line: str) -> Optional[Tuple[int, int, int]]:
        parts = line.split()
        if len(parts) < 6:
            return None
        try:
            return int(parts[1]), int(parts[3]), int(parts[5])
        except (ValueError, IndexError):
            return None

    def calculate_mouse_speed(self, value: int) -> float:
        distance = abs(value - CENTER_VALUE)
        return (distance / CENTER_VALUE) ** 2 * MAX_MOUSE_SPEED

    def process_keyboard(self, x: int, y: int, z: int):
        if z >= THRESHOLD_Z:
            for key in ['w', 's', 'a', 'd']:
                keyboard.release(key)
            return

        keyboard_state = {
            'a': x <= THRESHOLD_XY,
            'd': x >= (65535 - THRESHOLD_XY),
            's': y <= THRESHOLD_XY,
            'w': y >= (65535 - THRESHOLD_XY)
        }

        for key, state in keyboard_state.items():
            if state:
                keyboard.press(key) if not keyboard.is_pressed(key) else None
            else:
                keyboard.release(key)

    def process_mouse(self, x: int, y: int, z: int):
        if z >= THRESHOLD_Z:
            return

        dx = x - CENTER_VALUE
        dy = y - CENTER_VALUE

        x_speed = self.calculate_mouse_speed(x) * (1 if dx > 0 else -1) if abs(dx) > THRESHOLD_XY else 0
        y_speed = self.calculate_mouse_speed(y) * (-1 if dy > 0 else 1) if abs(dy) > THRESHOLD_XY else 0

        if x_speed or y_speed:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x_speed), int(y_speed), 0, 0)


    def read_serial(self):
        try:
            self.serial = serial.Serial(self.port, baudrate=115200, timeout=0)
            while self.running:
                data = self.serial.read(self.serial.in_waiting or 1)
                self.buffer += data.decode('utf-8', errors='ignore')

                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    coords = self.parse_data(line)
                    if coords:
                        if self.control_type == 'keyboard':
                            print("Keyboard:",line)
                            self.process_keyboard(*coords)
                        else:
                            print("Mouse:",line)
                            self.process_mouse(*coords)
                
                time.sleep(0.001)  # Reduce CPU usage

        except Exception as e:
            print(f"Serial error ({self.port}): {str(e)}")
        finally:
            if self.serial and self.serial.is_open:
                self.serial.close()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.read_serial)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False

def main():
    keyboard_monitor = SerialMonitor('COM15', 'keyboard')
    mouse_monitor = SerialMonitor('COM3', 'mouse')

    try:
        keyboard_monitor.start()
        mouse_monitor.start()
        print("Controllers active. Press CTRL+C to quit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        keyboard_monitor.stop()
        mouse_monitor.stop()

if __name__ == "__main__":
    main()
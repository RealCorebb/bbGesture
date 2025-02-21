import serial
import threading
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController

# Configuration
serial_port = "COM3"  # Change to your correct port
baud_rate = 115200
message_to_detect = "Flick Down to Up"
trigger_action = "left_click"  # Can be 'Q' for keyboard press or 'left_click' for mouse click

# Initialize Serial Communication
ser = serial.Serial(serial_port, baud_rate, timeout=0)  # timeout=0 for non-blocking
mouse = MouseController()
keyboard = KeyboardController()

def handle_serial_data():
    while True:
        # Non-blocking read, it returns b'' if no data
        data = ser.readline().decode("utf-8").strip()
        if data:
            print(f"Received: {data}")
            if data == message_to_detect:
                print(f"Detected: {message_to_detect}")
                
                if trigger_action == "Q":
                    # Press 'Q' on the keyboard
                    keyboard.press("q")
                    keyboard.release("q")
                    print("Pressed Q.")
                elif trigger_action == "left_click":
                    # Perform a left click
                    mouse.click(Button.left)
                    print("Mouse left click.")
                else:
                    print(f"Unknown action: {trigger_action}")

def start_serial_thread():
    # Create and start a new thread to handle serial data
    serial_thread = threading.Thread(target=handle_serial_data, daemon=True)
    serial_thread.start()

if __name__ == "__main__":
    start_serial_thread()
    print("Listening to serial port...")
    
    # Main thread can perform other tasks or just keep alive
    try:
        while True:
            pass  # Main thread does nothing but keeps the program running
    except KeyboardInterrupt:
        print("Program terminated.")
    finally:
        ser.close()

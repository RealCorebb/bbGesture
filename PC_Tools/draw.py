import requests
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import threading
import time

trace_width = 450
trace_height = 250
min_trace_len = 5
z_threshold = 50000

class SerialDrawer:
    def __init__(self, port='COM3', baud_rate=115200):
        # Tkinter setup
        self.root = tk.Tk()
        self.root.title("Serial Drawing")
        
        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.set_aspect(0.55)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        
        # Embed matplotlib in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()
        
        # Serial and drawing variables
        self.line = None
        self.ser = serial.Serial(port, baud_rate)
        self.x_points = []
        self.y_points = []
        self.last_data_time = 0
        self.last_z_high_time = 0
        self.last_z = 0
        self.is_drawing = False
        self.trace_dataX = []
        self.trace_dataY = []
        
        # Threads
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.check_thread = threading.Thread(target=self.check_drawing_state, daemon=True)
        self.serial_thread.start()
        self.check_thread.start()

    def parse_data(self, line):
        try:
            parts = line.strip().split()
            x = int(parts[1])
            y = int(parts[3])
            z = int(parts[5])
            return x, y, z
        except (ValueError, IndexError):
            return None

    def check_drawing_state(self):
        while True:
            current_time = time.time()
            if (current_time - self.last_data_time > 0.3 or 
                (self.last_z > z_threshold and current_time - self.last_z_high_time > 0.3)):
                self.root.after(10, self.end_plot)
            time.sleep(0.1)

    def end_plot(self):
        if(self.is_drawing == True):
            self.is_drawing = False
            if self.line:
                self.line.set_color('green')  # Change the line color to purple
                self.root.after(10, self.safe_draw)  # Ensure the canvas redraws
            print("trace data:")
            if(len(self.trace_dataX) > min_trace_len and len(self.trace_dataY) > min_trace_len):
                trace_data = [self.trace_dataX,self.trace_dataY,[]]
                print(trace_data)
                self.trace_dataX = []
                self.trace_dataY = []
                payload = {
                    "options": "enable_pre_space",
                    "requests": [
                        {
                            "writing_guide": {
                                "writing_area_width": trace_width,
                                "writing_area_height": trace_height
                            },
                            "ink": [trace_data],
                            "language": "zh_CN"
                        }
                    ]
                }

                # Perform the HTTP POST request
                try:
                    response = requests.post(
                        url="https://www.google.com/inputtools/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8",
                        json=payload
                    )
                    if response.status_code == 200:
                        print("Response:", response.json())
                        text = response.json()[1][0][1][0]
                        print("Text:",text)
                    else:
                        print("HTTP Error:", response.status_code, response.text)
                except Exception as e:
                    print("Error during HTTP POST:", str(e))

    def clear_plot(self):
        self.x_points = []
        self.y_points = []
        self.ax.clear()
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        try:
            self.canvas.draw()
        except Exception as e:
            print(f"Error clearing plot: {e}")

    def read_serial(self):
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8').strip()
                    parsed_data = self.parse_data(line)
                    
                    if parsed_data:
                        x, y, z = parsed_data
                        current_time = time.time()
                        self.last_data_time = current_time
                    
                        
                        # Track high Z time
                        if z > z_threshold:
                            self.last_z_high_time = current_time
                        
                        # Drawing logic
                        if z < z_threshold:
                            # Normalize coordinates to 0-1 range
                            norm_x = (x - 0) / 65535
                            norm_y = (y - 0) / 65535

                            
                            tx = int(norm_x * trace_width)
                            ty = 255 - int(norm_y * trace_height)

                            #print(tx,ty)
                            self.trace_dataX.append(tx)
                            self.trace_dataY.append(ty)
                            if self.is_drawing == False:
                                self.is_drawing = True
                                self.clear_plot()
                            self.x_points.append(norm_x)
                            self.y_points.append(norm_y)
                            
            
                            self.line, = self.ax.plot(self.x_points, self.y_points, 'b-')  # Initial line
                            
                            # Update canvas in main thread
                            self.root.after(10, self.safe_draw)
                        
                        self.last_z = z
            except Exception as e:
                print(f"Error in serial reading: {e}")

    def safe_draw(self):
        try:
            self.canvas.draw()
        except Exception as e:
            print(f"Error in drawing: {e}")

    def start(self):
        self.root.mainloop()

# Usage
if __name__ == "__main__":
    drawer = SerialDrawer()
    drawer.start()
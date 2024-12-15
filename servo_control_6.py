import tkinter as tk
from tkinter import messagebox
import serial
import time
import threading
import pygame  # 添加手柄支持

# 初始化串口
try:
    ser = serial.Serial('COM5', 9600, timeout=1)  # 修改为你的Arduino串口号，例如 COM5
    time.sleep(2)  # 等待串口初始化
except:
    messagebox.showerror("错误", "无法打开串口，请检查连接！")
    exit()

# 初始化 Pygame 手柄
pygame.init()
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"检测到手柄: {joystick.get_name()}")
else:
    print("未检测到手柄，请确保手柄已连接。")

class ServoControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("舵机控制程序")
        self.root.geometry("500x550")

        # 默认参数
        self.min_angle = 30
        self.max_angle = 150
        self.speed = 15  # 默认中速
        self.dynamic_mode = False  # 动态模式状态
        self.gamepad_mode = False  # 手柄模式状态

        # 设置 GUI 控件
        self.create_widgets()

        # 启动手柄读取线程
        self.running = True
        if joystick:
            threading.Thread(target=self.read_joystick, daemon=True).start()

    def create_widgets(self):
        # 手柄模式按钮
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(pady=10)
        tk.Label(mode_frame, text="手柄模式:").grid(row=0, column=0)
        self.mode_label = tk.Label(mode_frame, text="关", fg="red")
        self.mode_label.grid(row=0, column=1)
        self.mode_button = tk.Button(mode_frame, text="切换手柄模式", command=self.toggle_gamepad_mode)
        self.mode_button.grid(row=0, column=2)

        # 角度范围设置
        range_frame = tk.Frame(self.root)
        range_frame.pack(pady=10)

        tk.Label(range_frame, text="最小角度:").grid(row=0, column=0)
        self.min_entry = tk.Entry(range_frame, width=5)
        self.min_entry.grid(row=0, column=1)
        self.min_entry.insert(0, str(self.min_angle))

        tk.Label(range_frame, text="最大角度:").grid(row=0, column=2)
        self.max_entry = tk.Entry(range_frame, width=5)
        self.max_entry.grid(row=0, column=3)
        self.max_entry.insert(0, str(self.max_angle))

        tk.Button(range_frame, text="设置范围", command=self.set_angle_range).grid(row=0, column=4, padx=10)

        # 滑块控制角度
        self.angle_slider = tk.Scale(self.root, from_=self.min_angle, to=self.max_angle, orient="horizontal",
                                     length=400, label="滑块控制角度", command=self.update_angle)
        self.angle_slider.pack(pady=10)

        # 输入角度控制
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)
        tk.Label(input_frame, text="输入角度:").grid(row=0, column=0)
        self.angle_entry = tk.Entry(input_frame, width=5)
        self.angle_entry.grid(row=0, column=1)
        tk.Button(input_frame, text="设置角度", command=self.set_angle).grid(row=0, column=2)

        # 动态模式速度选择
        speed_frame = tk.Frame(self.root)
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="选择速度:").grid(row=0, column=0)
        self.speed_var = tk.IntVar(value=15)
        speeds = [("慢速", 30), ("中速", 15), ("快速", 2)]
        for text, value in speeds:
            tk.Radiobutton(speed_frame, text=text, variable=self.speed_var, value=value, command=self.set_speed).grid(row=0, column=value, padx=10)

        # 开启动态模式按钮
        self.dynamic_mode_btn = tk.Button(self.root, text="开启动态模式", command=self.start_dynamic_mode)
        self.dynamic_mode_btn.pack(pady=10)

        # 关闭动态模式按钮
        self.stop_dynamic_btn = tk.Button(self.root, text="关闭动态模式", command=self.stop_dynamic_mode)
        self.stop_dynamic_btn.pack(pady=10)

    def toggle_gamepad_mode(self):
        # 切换手柄模式
        self.gamepad_mode = not self.gamepad_mode
        if self.gamepad_mode:
            self.mode_label.config(text="开", fg="green")
            print("手柄模式已开启")
        else:
            self.mode_label.config(text="关", fg="red")
            print("手柄模式已关闭")

    def set_angle_range(self):
        try:
            self.min_angle = int(self.min_entry.get())
            self.max_angle = int(self.max_entry.get())
            if 0 <= self.min_angle < self.max_angle <= 180:
                self.angle_slider.config(from_=self.min_angle, to=self.max_angle)
                messagebox.showinfo("成功", f"角度范围设置为: {self.min_angle}° - {self.max_angle}°")
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的角度范围（0-180）！")

    def set_speed(self):
        # 设置动态模式速度
        self.speed = self.speed_var.get()
        print(f"动态模式速度设置为: {self.speed}")

    def update_angle(self, value):
        if not self.gamepad_mode:  # 手柄模式关闭时才生效
            angle = int(float(value))
            self.send_to_arduino(angle)

    def set_angle(self):
        if not self.gamepad_mode:  # 手柄模式关闭时才生效
            try:
                angle = int(self.angle_entry.get())
                if self.min_angle <= angle <= self.max_angle:
                    self.angle_slider.set(angle)
                    self.send_to_arduino(angle)
                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", f"请输入有效的角度范围: {self.min_angle} - {self.max_angle}°")

    def start_dynamic_mode(self):
        if not self.gamepad_mode:  # 手柄模式关闭时才生效
            if not self.dynamic_mode:
                self.dynamic_mode = True
                threading.Thread(target=self.dynamic_loop, daemon=True).start()

    def stop_dynamic_mode(self):
        # 关闭动态模式
        self.dynamic_mode = False
        print("动态模式已关闭")
        messagebox.showinfo("动态模式", "动态模式已关闭。")

    def dynamic_loop(self):
        step = 1
        current_angle = self.min_angle
        direction = 1
        while self.dynamic_mode:
            self.send_to_arduino(current_angle)
            time.sleep(self.speed / 1000)
            current_angle += step * direction
            if current_angle >= self.max_angle or current_angle <= self.min_angle:
                direction *= -1

    def read_joystick(self):
        while self.running:
            pygame.event.pump()
            if self.gamepad_mode:  # 仅在手柄模式开启时生效
                z_axis = joystick.get_axis(2)  # 读取 Z轴数值
                mapped_angle = int((z_axis + 1) * (self.max_angle - self.min_angle) / 2 + self.min_angle)
                self.angle_slider.set(mapped_angle)
                self.send_to_arduino(mapped_angle)
            time.sleep(0.1)

    def send_to_arduino(self, angle):
        if ser:
            try:
                ser.write(f"{angle}\n".encode())
                print(f"发送角度: {angle}")
            except:
                messagebox.showerror("错误", "串口通信失败，请检查连接！")

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = ServoControlApp(root)
    root.mainloop()
    pygame.quit()
    if ser:
        ser.close()

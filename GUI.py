import tkinter as tk
import os
import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
import threading
from chat_client_class import Client
import argparse
from PIL import Image, ImageDraw  # 用于手写画布
import numpy as np                # 图像数组处理
from tensorflow import keras 
import requests
from io import BytesIO
def login():
    root = tk.Tk()
    root.title("login")
    root.geometry("300x200")

    
    label_name=tk.Label(root,text="username")
    label_name.place(x=10,y=20)
    entry = tk.Entry(root)
    entry.place(x=10,y=40,width=100)
    
    
    
    def open_new_window(name):
        root.destroy()
        new_window = tk.Tk()
        new_window.geometry("800x550")
        new_window.title(f"chat_box {name}")
        display = tk.Text(new_window, height=20, width=90)
        display.place(x=10, y=10, width=760, height=350)

        scrollbar = tk.Scrollbar(new_window, command=display.yview)
        scrollbar.place(x=770, y=10, height=350)
        display.config(yscrollcommand=scrollbar.set)
        input_box = tk.Entry(new_window, width=40)
        input_box.place(x=10, y=400, width=650, height=30)  # 放置在底部
        
        args = argparse.Namespace(d="127.0.0.1")  # 手动构造命令行参数
        client = Client(args, display,input_box)  # 把 Text 控件传给 client  
        client.enter_input(name)
        
        def send_message():
            msg = input_box.get()  # 获取输入框内容
            if msg:  # 确保不为空
                if msg.lower() == "game":  # 如果输入是 "game"
                    game_button_action()  # 调用游戏启动逻辑
                else:
                    client.enter_input(msg)
                    display.insert('end', f'{name}: {msg}\n')  # 在文本框中显示消息
                input_box.delete(0, 'end')
                display.see('end')  # 滚动到最底部

        send_button = tk.Button(new_window, text="Send", command=send_message)
        send_button.place(x=670, y=400, width=60, height=30)

        button_width = 140
        # time 按钮
        def time_button_action():
            display.insert('end', '[You clicked]: time\n')
            display.see('end')
            client.enter_input("time")
        time_button = tk.Button(new_window, text="time", command=time_button_action)
        time_button.place(x=10, y=450, width=button_width, height=40)

        # who 按钮
        def who_button_action():
            display.insert('end', '[You clicked]: who\n')
            display.see('end')
            client.enter_input("who")
        who_button = tk.Button(new_window, text="who", command=who_button_action)
        who_button.place(x=160, y=450, width=button_width, height=40)

        # connect 按钮
        def connect_button_action():
            pass
        connect_button = tk.Button(new_window, text="connect", command=connect_button_action)
        connect_button.place(x=310, y=450, width=button_width, height=40)

        # search 按钮
        def search_button_action():
            pass
        search_button = tk.Button(new_window, text="search", command=search_button_action)
        search_button.place(x=460, y=450, width=button_width, height=40)

        # CNN 按钮
        def cnn_button_action():
            cnn_window = tk.Toplevel()
            cnn_window.title("Handwriting Recognition (CNN)")
            cnn_window.geometry("500x500")

    # 画布设置
            canvas = tk.Canvas(cnn_window, width=400, height=400, bg="white")
            canvas.pack()

    # 加载预训练模型（应该放在全局或类初始化中）
            from tensorflow import keras
            model = keras.models.load_model("cnn_emnist_62class.keras")

    # 初始化绘图变量
            image = Image.new("L", (400, 400), 255)  # 灰度图像，白底
            draw = ImageDraw.Draw(image)
            last_point = None

    # 绘图函数
            result_label = tk.Label(cnn_window, text="Draw a digit and click Recognize")
            result_label.pack(pady=10)
            
            def paint(event):
                nonlocal last_point
                x, y = event.x, event.y
                r = 8  # 画笔半径
                canvas.create_oval(x-r, y-r, x+r, y+r, fill="black", outline="black")
                draw.ellipse([x-r, y-r, x+r, y+r], fill=0)  # 黑色笔画
                last_point = (x, y)

    # 鼠标移动时连续绘制
            def move(event):
                nonlocal last_point
                if last_point:
                    x, y = event.x, event.y
                    canvas.create_line(last_point[0], last_point[1], x, y, width=16, fill="black",smooth=True,capstyle=tk.ROUND)
                    draw.line([last_point[0], last_point[1], x, y], fill=0, width=30)
                    last_point = (x, y)

            canvas.bind("<B1-Motion>", move)
            canvas.bind("<Button-1>", paint)

    # 识别函数
            def recognize():
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
    
                try:
                    response = requests.post('http://127.0.0.1:50001/predict', files={'image': ('drawing.png', img_byte_arr, 'image/png')})
        
                    if response.status_code == 200:
                        result = response.json()['prediction']
                        result_label.config(text=f"Predicted: {result}")
                        input_box.insert('end',result)
                    else:
                        result_label.config(text=f"Error: {response.text}")
                except Exception as e:
                    result_label.config(text=f"Connection error: {str(e)}")

            btn_frame = tk.Frame(cnn_window)
            btn_frame.pack(pady=10)
    
            def clear():
                nonlocal image, draw
                canvas.delete("all")
                image = Image.new("L", (400, 400), 255)
                draw = ImageDraw.Draw(image)
                result_label.config(text="Draw a digit and click Recognize")
            
            tk.Button(btn_frame, text="Recognize", command=recognize).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Clear", command=clear).pack(side=tk.LEFT, padx=10)
    
        cnn_button = tk.Button(new_window, text="CNN", command=cnn_button_action)
        cnn_button.place(x=610, y=450, width=button_width, height=40)
            
        def game_button_action():
            game_window = tk.Toplevel()
            game_window.title("Select a Game")
            game_window.geometry("300x200")

            # 定义启动游戏的函数
            def launch_game(game_name):
                try:
                    if game_name == "space invader":
                        os.system('python main.py')  # 启动 Space Invader
                    elif game_name == "Tetris":
                        os.system('python Tetris.py')  # 启动 Tetris
                    elif game_name == "Wordle Game":
                        os.system('python "Wordle Game.py"')  # 启动 Wordle Game
                    else:
                        raise ValueError("Unknown game")
                except Exception as e:
                    display.insert('end', f'[Error]: {e}\n')
                    display.see('end')
                finally:
                    game_window.destroy()  # 关闭弹窗

            tk.Button(game_window, text="Space Invader", command=lambda: launch_game("space invader")).place(x=50, y=30, width=200, height=40)
            tk.Button(game_window, text="Tetris", command=lambda: launch_game("Tetris")).place(x=50, y=80, width=200, height=40)
            tk.Button(game_window, text="Wordle Game", command=lambda: launch_game("Wordle Game")).place(x=50, y=130, width=200, height=40)
        
        game_button = tk.Button(new_window, text="game", command=game_button_action)
        game_button.place(x=10, y=500, width=button_width, height=40)
        
        import threading
        threading.Thread(target=client.run_chat, daemon=True).start()
        new_window.mainloop()
       
    def submit_name():
        name=entry.get()
        if name:
            open_new_window(name)
   
    
    submit_button = tk.Button(root, text="submit", command=submit_name)
    submit_button.place(x=110,y=150)
    
    root.mainloop()

if __name__=="__main__":
    login()










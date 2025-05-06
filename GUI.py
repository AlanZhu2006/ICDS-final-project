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
        new_window.geometry("800x500")
        new_window.title(f"chat_box {name}")
        display = tk.Text(new_window, height=20, width=90)
        display.place(x=10, y=10, width=760, height=350)

        scrollbar = tk.Scrollbar(new_window, command=display.yview)
        scrollbar.place(x=770, y=10, height=350)
        display.config(yscrollcommand=scrollbar.set)
        input_box = tk.Entry(new_window, width=40)
        input_box.place(x=10, y=450, width=650, height=30)  # 放置在底部
        
        args = argparse.Namespace(d="127.0.0.1")  # 手动构造命令行参数
        client = Client(args, display,input_box)  # 把 Text 控件传给 client  
        client.enter_input(name)
        
        def send_message():
            msg = input_box.get()  # 获取输入框内容
            if msg:  # 确保不为空
                client.enter_input(msg)
                display.insert('end', f'{name}: {msg}\n')  # 在文本框中显示消息
                input_box.delete(0, 'end')
                display.see('end')  # 滚动到最底部

        send_button = tk.Button(new_window, text="Send", command=send_message)
        send_button.place(x=670, y=450, width=60, height=30)

        button_width = 140
        # time 按钮
        def time_button_action():
            display.insert('end', '[You clicked]: time\n')
            display.see('end')
            client.enter_input("time")
        time_button = tk.Button(new_window, text="time", command=time_button_action)
        time_button.place(x=10, y=370, width=button_width, height=40)

        # who 按钮
        def who_button_action():
            display.insert('end', '[You clicked]: time\n')
            display.see('end')
            client.enter_input("who")
        who_button = tk.Button(new_window, text="who", command=who_button_action)
        who_button.place(x=160, y=370, width=button_width, height=40)

        # connect 按钮
        def connect_button_action():
            pass
        connect_button = tk.Button(new_window, text="connect", command=connect_button_action)
        connect_button.place(x=310, y=370, width=button_width, height=40)

        # search 按钮
        def search_button_action():
            pass
        search_button = tk.Button(new_window, text="search", command=search_button_action)
        search_button.place(x=460, y=370, width=button_width, height=40)

        # CNN 按钮
        def cnn_button_action():
            pass
        cnn_button = tk.Button(new_window, text="CNN", command=cnn_button_action)
        cnn_button.place(x=610, y=370, width=button_width, height=40)
        
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










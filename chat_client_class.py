import time
import socket
import select
import sys
import json
from chat_utils import *
import client_state_machine as csm
import subprocess

import threading

class Client:
    def __init__(self, args, display_widget,input_box):
        self.display_widget = display_widget 
        self.peer = ''
        self.console_input = []
        self.state = S_OFFLINE
        self.system_msg = ''
        self.local_msg = ''
        self.peer_msg = ''
        self.args= args
        self.input_box=input_box
    
    def quit(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def get_name(self):
        return self.name

    def init_chat(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        svr = SERVER if self.args.d == None else (self.args.d, CHAT_PORT)
        self.socket.connect(svr)
        self.sm = csm.ClientSM(self.socket)
    
    def shutdown_chat(self):
        return

    def send(self, msg):
        mysend(self.socket, msg)

    def recv(self):
        return myrecv(self.socket)

    def get_msgs(self):  
        read, write, error = select.select([self.socket], [], [], 0)        #检测服务器（其他客户端发送的）发送给这个client的信息
        my_msg = ''
        peer_msg = []
        #peer_code = M_UNDEF    for json data, peer_code is redundant
        if len(self.console_input) > 0:                                     #如果历史记录里面有信息，直接提取并删除（终端的信息）
            my_msg = self.console_input.pop(0)
        if self.socket in read:
            peer_msg = self.recv()                                          #接受其他客户的信息      
        return my_msg, peer_msg

    def output(self):
        if self.display_widget:
            self.display_widget.insert('end', self.system_msg)
            self.display_widget.see('end')
        else:
            print(self.system_msg)
        self.system_msg = ''

    def login(self):
        my_msg, peer_msg = self.get_msgs()
        if len(my_msg) > 0:
            self.name = my_msg
            msg = json.dumps({"action":"login", "name":self.name})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.state = S_LOGGEDIN
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(self.name)
                self.print_instructions()
                return (True)
            elif response["status"] == 'duplicate':
                self.system_msg += 'Duplicate username, try again'
                return False
        else:               # fix: dup is only one of the reasons
           return(False)

    def print_instructions(self):
        self.system_msg += menu

    def run_chat(self):
        self.init_chat()
        self.system_msg += 'Welcome to ICS chat\n'
        self.system_msg += 'Please enter your name: '
        self.output()
        while self.login() != True:       #保证了在没有登陆的情况下不会进到下一步的welcome里面
            self.output()
        self.system_msg += 'Welcome, ' + self.get_name() + '!'
        self.output()
        while self.sm.get_state() != S_OFFLINE:      #只要在线，就确保了一直接受来自自己终端和客户的信息
            self.proc()                   
            self.output()                            #返回系统的提示
            time.sleep(CHAT_WAIT)
        self.quit()

#==============================================================================
# main processing loop
#==============================================================================
    def proc(self):
        my_msg, peer_msg = self.get_msgs()
        self.system_msg += self.sm.proc(my_msg, peer_msg)
    def enter_input(self, text):
        self.console_input.append(text)

    
    

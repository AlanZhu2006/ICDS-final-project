"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json
import subprocess
import socket
import re
import time
import threading

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.system_msg = ''
        self.game_socket = None
        self.game_started = False
    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action": "connect", "target": peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with ' + self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action": "disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def start_game(self):
        
        try:
            subprocess.Popen(['python', 'go_pygame.py'])
            time.sleep(3)  # 等待游戏端口打开
            self.game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.game_socket.settimeout(5)  # 设置连接超时为5秒
            self.game_socket.connect(('127.0.0.1', 50002))
            self.system_msg += "Pygame 游戏已启动并连接成功。\n"
        except socket.timeout:
            self.system_msg += "连接超时: 无法连接到游戏端口\n"
        except Exception as e:
            self.system_msg += f"启动游戏失败: {str(e)}\n"

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
# ==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
# ==============================================================================
        
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action": "time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action": "list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += 'If you want to play a game, type "gamestart" to accept start a game between you and your peer\n'
                        self.out_msg += 'Once you see the message of "gamestart" from your peer, type "accept" to accept the game!\n'
                        self.out_msg += 'A1 ~ O15: input your message about move on the board after game starts (e.g., A1, H8, O15)\n '
                        self.out_msg += 'If you want to quit, type "bye" to disconnect\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps(
                        {"action": "search", "target": term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps(
                        {"action": "poem", "target": poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err:
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg

                if peer_msg["action"] == "connect":

                    # ----------your code here------#
                    print(peer_msg)
                    peer = peer_msg["from"]
                    self.out_msg += f"You're connected with {peer}"
                    self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n-----------------------------------\n'
                    self.out_msg += 'If you want to play a game, type "gamestart" to accept start a game between you and your peer\n'
                    self.out_msg += 'Once you see the message of "gamestart" from your peer, type "accept" to accept the game!\n'
                    self.out_msg += 'A1 ~ O15: input your message about move on the board after game starts (e.g., A1, H8, O15)\n '
                    self.out_msg += 'If you want to quit, type "bye" to disconnect\n'
                    self.out_msg += '-----------------------------------\n'
                self.state = S_CHATTING
                    # ----------end of your code----#

# ==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
# ==============================================================================
        elif self.state == S_CHATTING:
            
     
            if isinstance(peer_msg, str):
                peer_msg = peer_msg.strip()
                if peer_msg == '':
                    return self.out_msg  
            
            if len(my_msg) > 0:     # my stuff going out
                mysend(self.s, json.dumps(
                    {"action": "exchange", "from": "[" + self.me + "]", "message": my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in

                # ----------your code here------#
                try:
                    peer_msg = json.loads(peer_msg)  # 尝试解析 JSON
                except json.JSONDecodeError:
                # 如果不是 JSON，可能是普通文本或错误消息
                    self.out_msg += f"[System] Received non-JSON message: {peer_msg}\n"
                    return self.out_msg

                # 确保解析后的内容是字典且包含 "action" 字段
                if not isinstance(peer_msg, dict) or "action" not in peer_msg:
                    self.out_msg += f"[System] Invalid message format: {peer_msg}\n"
                    return self.out_msg

                if peer_msg["action"] == "exchange":
                    self.out_msg += peer_msg["message"]
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                elif peer_msg["action"] == "connect":
                    self.out_msg += peer_msg["from"] + "joined"
                # ----------end of your code----#
            if my_msg.lower() == "gamestart":
                self.system_msg += "Game Start\n"
                if not self.game_started:
                    self.start_game()
                    self.game_started = True
                self.out_msg += 'You are connected with ' + self.peer + '\n'
                self.out_msg += (
                        "The game has started! Enjoy the game :)\n"
                        "- Wait for your opponent to type 'accept' to start the match.\n"
                        "-----------------------------------\n")
                msg = json.dumps({
                    "action": "exchange",
                    "from": "[" + self.me + "]",
                    "message": (
                        "You are invited to play game! Input 'accept' to confirm invitation.\n"
                    )
                })
                mysend(self.s, msg)
                
            elif re.match(r'^[A-Ta-t](1[0-5]|[1-9])$', my_msg.strip()) and self.game_socket:
                try:
                    self.game_socket.sendall(my_msg.encode())
                    self.system_msg += f"You make move：{my_msg}\n"
                except Exception as e:
                    self.system_msg += f"Failure: {str(e)}\n"

            if my_msg == 'accept':
                self.game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.game_socket.settimeout(5)  # 设置连接超时为5秒
                self.game_socket.connect(('127.0.0.1', 50002))
                self.system_msg += "Pygame 游戏已启动并连接成功。\n"
                self.out_msg += 'You are connected with ' + self.peer + '\n'
                self.out_msg += (
                                        "-----------------------------------\n"
                                        "You have confirmed! Enjoy the game :)\n"
                                        "-----------------------------------\n"
                                )
                self.out_msg += (
                                "\n"
                                "-----------------------------------\n"
                                " Game Instructions:\n"
                                "\n"
                                "- Input your move using coordinates like 'A1', 'H8', or 'O15'.\n"
                                "- Valid inputs: A1 ~ O15 (no lowercase required).\n"
                                "- Once you have five in a line, you win\n"
                                "- Only one player needs to type 'gamestart'; the other types 'accept'.\n"
                                "- ⚠️ Make sure the game window is open before making moves.\n"
                                "- If you want to exit the game, type 'bye'.\n"
                                "-----------------------------------\n"
                                )
                msg = json.dumps({
                    "action": "exchange",
                    "from": "[" + self.me + "]",
                    "message": (
                                "\n"
                                "-----------------------------------\n"
                                " Game Instructions:\n"
                                "\n"
                                "- Input your move using coordinates like 'A1', 'H8', or 'O15'.\n"
                                "- Valid inputs: A1 ~ O15 (no lowercase required).\n"
                                "- Once you have five in a line, you win\n"
                                "- Only one player needs to type 'gamestart'; the other types 'accept'.\n"
                                "- ⚠️ Make sure the game window is open before making moves.\n"
                                "- If you want to exit the game, type 'bye'.\n"
                                "-----------------------------------\n"
                                )
                    
                })
                mysend(self.s, msg)

            if isinstance(peer_msg, list):
                for msg in peer_msg:
                    if isinstance(msg, str) and re.match(r'^[A-Ta-t](1[0-5]|[1-9])$', msg.strip()) and self.game_socket:
                        try:
                            self.game_socket.sendall(msg.encode())
                            self.system_msg += f"Your opponent made a move: {msg}\n"
                        except Exception as e:
                            self.system_msg += f"Failed to send opponent move: {str(e)}\n"

   
            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
# ==============================================================================
# invalid state
# ==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg

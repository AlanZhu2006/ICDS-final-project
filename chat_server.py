"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""
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
import numpy as np                # 图像数组处理
from tensorflow import keras 
import numpy as np
from PIL import Image
import io
from flask import Flask, request, jsonify
import contextlib

app = Flask(__name__)
model = keras.models.load_model("cnn_emnist_62class.keras")
emnist_labels = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #//////////
        self.server.bind(SERVER)                                        #//////////
        self.server.listen(5)                                           #//////////
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):  #处理客户端发送过来的登录操作
        # read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    if self.group.is_member(name) != True:
                        # move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        # add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        # load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name] = pkl.load(
                                    open(name + '.idx', 'rb'))
                            except IOError:  # chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "ok"}))
                    else:  # a client under this name has already logged in
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print('wrong code received')
            else:  # client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request this is implemented for you
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name) 
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# ==============================================================================
# handle messeage exchange: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                """
                Finding the list of people to send to and index message
                """
                # IMPLEMENTATION
                # ---- start your code ---- #
                message = msg["message"]
                if from_name in self.indices:
                    self.indices[from_name].add_msg(message)
                group_members = self.group.list_me(from_name)
                for member in group_members:
                    if member != from_name:
                        to_sock = self.logged_name2sock[member]
                        mysend(to_sock, json.dumps({"action": "exchange", "from": from_name, "message":f'{text_proc(message,from_name)}'}))
                # ---- end your code ---- #

# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps(
                        {"action": "disconnect", "msg": "everyone left, you are alone"}))
# ==============================================================================
#                 listing available peers: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "list":

                # IMPLEMENTATION
                # ---- start your code ---- #
                list_result = f"{self.group.list_all()}"
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                     {"action": "list", "results": list_result}))
# ==============================================================================
#             retrieve a sonnet : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "poem":

                # IMPLEMENTATION
                # ---- start your code ---- #
                sonnet_num = msg.get("target")
                try:
                    sonnet_num = int(sonnet_num)
                    poem = self.sonnet.get_poem(sonnet_num)
                except ValueError:
                        poem = "Invalid sonnet number."
                except IndexError:
                    poem = "Sonnet number out of range."
                except AttributeError:
                    poem = "Sonnet functionality not available."
                print('here:\n', poem)
                

                # ---- end of your code --- #

                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search: : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "search":

                # IMPLEMENTATION
                # ---- start your code ---- #
                folder_path = '/Users/xdw/Desktop/chat_system'
                outcome=[]
                for filename in os.listdir(folder_path):
                    if filename.endswith(".idx"):
                        username = filename[:-4]  # 去掉 .idx 后缀
                        filepath = os.path.join(folder_path, filename)
                        with open(filepath, "rb") as f:
                            try:
                                index = pkl.load(f)
                            except Exception as e:
                                print(f"Failed to load {filename}: {e}")
                        if msg["target"] in index.msgs:
                            outcome.append((username,msg["target"]))
                        else:
                            continue
                mysend(from_sock,json.dumps({"action":"time","results":f'{outcome}'}))


# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================

        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================

    @app.route('/predict', methods=['POST'])

    def predict():
    # 接收客户端发送的图像数据
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
    
    # 读取并预处理图像
        img_file = request.files['image']
        img = Image.open(io.BytesIO(img_file.read())).convert('L')
        img = img.resize((28, 28))
        img = img.point(lambda x: 255 - x)  # 反色
    
    # 转换为模型输入格式
        img_array = np.array(img) / 255.0
        img_array = img_array.reshape(1, 28, 28, 1)
    
    # 预测
        predictions = model.predict(img_array)
        predicted_class = np.argmax(predictions)
        result = emnist_labels[predicted_class]
    
        return jsonify({'prediction': result}) 

    def run(self):
        print('starting server...')
        from threading import Thread
        flask_thread = Thread(target=lambda: app.run(host='127.0.0.1', port=50001, debug=False, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)
    



def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()
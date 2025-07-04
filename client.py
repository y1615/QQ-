import socket
import json
import threading
import sys

class SimpleQQClient:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.connected = False
    
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print("已连接到服务器")
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return False
    
    def login(self):
        if self.connected:
            print("已经是登录状态")
            return False
        
        print("欢迎使用简易QQ，请选择用户名:")
        username = input("用户名: ")
        password = input("密码: ")
        
        login_data = {
            'type': 'login',
            'username': username,
            'password': password
        }
        
        try:
            self.client_socket.send(json.dumps(login_data).encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            
            if response_data.get('type') == 'login_success':
                self.username = username
                self.connected = True
                print(response_data.get('message'))
                print("登录成功!")
                return True
            else:
                print(response_data.get('message'))
                return False
        except Exception as e:
            print(f"登录过程中出错: {e}")
            return False
    
    def send_message(self):
        while self.connected:
            try:
                target_user = input("请输入目标用户(username), 或输入'exit'退出: ")
                if target_user.lower() == 'exit':
                    break
                
                message = input("请输入消息内容: ")
                
                if message:
                    message_data = {
                        'type': 'message',
                        'sender': self.username,
                        'recipient': target_user,
                        'content': message
                    }
                    
                    self.client_socket.send(json.dumps(message_data).encode('utf-8'))
            except Exception as e:
                print(f"发送消息时出错: {e}")
                break
    
    def receive_messages(self):
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    print("与服务器的连接已断开")
                    self.connected = False
                    break
                
                print(f"收到原始数据: {data}")  # 打印原始数据以便调试
                
                try:
                    message = json.loads(data)
                    message_type = message.get('type')
                    
                    if message_type == 'message':
                        print(f"\n{message['sender']} ({message.get('timestamp', '未知时间')}): {message['content']}")
                    elif message_type == 'notification':
                        print(f"\n系统通知: {message['message']}")
                    else:
                        print(f"收到未知类型的消息: {message}")
                except json.JSONDecodeError:
                    print("收到不支持格式的消息")
            except Exception as e:
                print(f"接收消息时出错: {e}")
                self.connected = False
                break
    
    def start(self):
        if not self.connect():
            return
        
        if not self.login():
            self.client_socket.close()
            return
        
        # 启动接收消息的线程
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        # 启动发送消息的线程
        send_thread = threading.Thread(target=self.send_message)
        send_thread.daemon = True
        send_thread.start()
        
        # 等待线程结束
        send_thread.join()
        receive_thread.join()
        
        # 关闭连接
        if self.client_socket:
            self.client_socket.close()
            print("已断开连接")

if __name__ == "__main__":
    client = SimpleQQClient()
    client.start()
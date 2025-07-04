import socketserver
import threading
import json
import time

# 用户数据库（实际应用中应该存储在数据库中）
users = {
    'user1': {'password': 'password123', 'online': False, 'connection': None},
    'user2': {'password': 'password456', 'online': False, 'connection': None}
}

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # 用循环持续处理来自客户端的请求
        while True:
            try:
                # 接收客户端数据
                data = self.request.recv(1024).decode('utf-8')
                if not data:
                    break
                
                # 解析JSON数据
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    print("收到的不是有效JSON数据")
                    continue
                
                # 处理不同的消息类型
                if message.get('type') == 'login':
                    self.handle_login(message)
                elif message.get('type') == 'message':
                    self.handle_message(message)
                else:
                    self.request.send(json.dumps({'type': 'error', 'message': '未知的消息类型'}).encode('utf-8'))
            
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"处理请求时出错: {e}")
                break
    
    def handle_login(self, login_data):
        username = login_data.get('username')
        password = login_data.get('password')
        
        # 验证用户
        if username in users and users[username]['password'] == password:
            # 如果该用户已经登录，则强制下线
            if users[username]['online']:
                self.request.send(json.dumps({'type': 'error', 'message': '该用户已登录，请稍后再试'}).encode('utf-8'))
                return
            
            users[username]['online'] = True
            users[username]['connection'] = self.request
            
            # 发送登录成功消息
            self.request.send(json.dumps({
                'type': 'login_success',
                'message': f'欢迎您，{username} ',
                'username': username
            }).encode('utf-8'))
            
            print(f"用户 {username} 登录成功")
            
            # 通知所有在线用户有新用户登录
            self.notify_all_users(f"用户 {username} 加入了聊天")
        else:
            # 发送登录失败消息
            self.request.send(json.dumps({'type': 'login_failure', 'message': '用户名或密码错误'}).encode('utf-8'))
    
    def handle_message(self, message_data):
        sender = message_data.get('sender')
        recipient = message_data.get('recipient')
        content = message_data.get('content')
        
        # 验证发送者是否在线
        if not users.get(sender) or not users[sender]['online']:
            return
        
        print(f"收到消息：{sender} -> {recipient}: {content}")
        
        # 转发消息给接收者
        if recipient in users and users[recipient]['online']:
            users[recipient]['connection'].send(json.dumps({
                'type': 'message',
                'sender': sender,
                'content': content,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }).encode('utf-8'))
        else:
            self.request.send(json.dumps({
                'type': 'error',
                'message': f'用户 {recipient} 不在线或不存在'
            }).encode('utf-8'))
    
    def notify_all_users(self, message):
        for username, user_data in users.items():
            if user_data['online']:
                user_data['connection'].send(json.dumps({
                    'type': 'notification',
                    'message': message
                }).encode('utf-8'))

class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9999
    
    # 创建并启动服务器
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    
    # 启动服务线程
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"服务器启动于 {ip}:{port}")
    print("等待连接...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("关闭服务器...")
        server.shutdown()
        server.server_close()
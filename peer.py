#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""
import time 
import json
import socket
import argparse

import threading 


from daemon.weaprous import WeApRous

messagereceived = [

]
PORT = 5001  # Default port
IP = "192.168.1.2"
server_ip = "127.0.0.1"
server_port = 9000

# susubmit ip : /submit-list 


# 1. Create the body


# add_list 


# /get-list 


app = WeApRous()


def _send_to_peer(target_peer_id, message_obj):
    """Send one chat message object to a specific peer id (ip:port)."""
    peerip, peerport = target_peer_id.split(":")
    peerport = int(peerport)

    body_json = json.dumps({"message": message_obj})
    request_message = (
        f"POST /receive-message HTTP/1.1\r\n"
        f"Host: {peerip}:{peerport}\r\n"
        f"Content-Type: application/json\r\n"
        f"Cookie: auth=true\r\n"
        f"Content-Length: {len(body_json)}\r\n"
        f"\r\n"
        f"{body_json}"
    )

    client_socket = socket.socket()
    try:
        client_socket.connect((peerip, peerport))
        client_socket.send(request_message.encode())
        client_socket.recv(4096)
    finally:
        client_socket.close()

def setPort(pepo):
    global PORT
    PORT = pepo

@app.route("/", methods=["GET"])
def home(headers, body):
    
    try:
      html_content = ""
      
      body_json = "" 

# 2. Calculate length
      content_length = len(body_json)

# 3. Construct the full message
      request_message = (
    f"GET /index.html HTTP/1.1\r\n"
    f"Host: {server_ip}:{server_port}\r\n"
    f"Cookie: auth=true\r\n"
    "\r\n"
      )
      client_socket = socket.socket()
      client_socket.connect((server_ip, server_port))
      client_socket.send(request_message.encode())
      html_content = client_socket.receive_message().decode()
      client_socket.close()
      return 200, html_content
    except Exception as e:
      return 500, str(e)
@app.route("/receive-message", methods=["POST"])
def receive_message(headers, body):
    try:
      # print("new_headers received: ",headers)
      # print("message received: ",json.loads(body)["message"])
      messagereceived.append(json.loads(body)["message"])
      # print("messagereceived: ",messagereceived)
      return 200, "Message received successfullyfasdfa"
    except Exception as e:
      return 500, str(e )
@app.route("/api/get-messages", methods=["GET"])
def get_messages(headers, body):
    try:
      # print("api/get-messages: ")
      # print("body: ",body)
      # print("messagereceived: ",messagereceived)
      grouped = {}
      me = "{}:{}".format(IP, PORT)
      for msg in messagereceived:
          sender = msg.get("sender")
          receiver = msg.get("receiver")
          if not sender:
            continue

          # Group by conversation peer so both sent and received messages
          # appear in the same thread for the current user.
          if sender == me and receiver:
            peer_id = receiver
          else:
            peer_id = sender

          if peer_id not in grouped:
              grouped[peer_id] = []
          grouped[peer_id].append(msg)

      return 200, json.dumps(grouped)
    except Exception as e:
      return 500, str(e)

@app.route("/send-message", methods=["POST"])
def send_message(headers, body):
    try:
      # print("headers: ",headers)
      # print("body: ",body)
      body_json = json.loads(body)
      messageupdate = body_json['message']
      messagereceived.append(messageupdate)
      peer_id = body_json['message']['receiver']
      _send_to_peer(peer_id, messageupdate)
      
      return 200, "Message sent successfully"
    except Exception as e:
      print(f"Error in send_message: {e}")
      return 500, str(e)      


@app.route("/broadcast-peer", methods=["POST"])
@app.route("/broadcast-peer/", methods=["POST"])
def broadcast_peer(headers, body):
    """
    Broadcast one message to every active peer (except myself).
    API example: http://IP:port/broadcast-peer/
    """
    try:
      body_json = json.loads(body) if body else {}
      message = body_json.get("message", {})

      if not isinstance(message, dict):
        return 400, "Invalid message payload"

      sender_id = "{}:{}".format(IP, PORT)
      active_peers_dict = get_listfunc(server_ip, server_port)
      if not active_peers_dict or "peer_list" not in active_peers_dict:
        return 500, "Cannot fetch active peer list from tracker"

      active_peer_ids = list(active_peers_dict["peer_list"].keys())
      targets = [peer_id for peer_id in active_peer_ids if peer_id != sender_id]

      delivered = []
      failed = []

      for peer_id in targets:
        msg_copy = dict(message)
        msg_copy["sender"] = sender_id
        msg_copy["receiver"] = peer_id
        msg_copy["is_broadcast"] = True
        messagereceived.append(msg_copy)
        try:
          _send_to_peer(peer_id, msg_copy)
          delivered.append(peer_id)
        except Exception as err:
          failed.append({"peer": peer_id, "error": str(err)})

      return 200, json.dumps({
        "mode": "broadcast",
        "targets": len(targets),
        "delivered": delivered,
        "failed": failed,
      })
    except Exception as e:
      print(f"Error in broadcast_peer: {e}")
      return 500, str(e)

@app.route("/get-list", methods=["GET"])
def get_list(headers, body):
    # ... (code debug)
    
    active_peers_dict = get_listfunc(server_ip, server_port)
    
    if active_peers_dict is None:
        return 500, "Lỗi khi lấy danh sách Peer." # Lỗi server nội bộ
        
    # 5. Trả về JSON string hợp lệ để frontend parse được ổn định.
    return  200,  json.dumps(active_peers_dict)

@app.route("/userip", methods=["GET"])
def get_user(headers, body):
    
    return 200, "{}:{}".format(IP, PORT)


def print_input(headers, body):
    print("[Peer] HEADERS:")
    print(headers)
    print("[Peer] body:")
    print(body)

def get_listfunc(ip, port):
    client_socket = socket.socket()
    try:
        client_socket.connect((ip, port))
        request_message_getlist = (
            f"GET /get-list HTTP/1.1\r\n"
            f"Host: {ip}:{port}\r\n"
            f"Cookie: auth=true\r\n"
            f"\r\n"
        )
        client_socket.send(request_message_getlist.encode()) 
        
        # 1. Receive and DECODE the bytes to string immediately
        receive_message = client_socket.recv(4096).decode('utf-8')
        
    except Exception as e:
        print(f"[ERROR] Socket connection failed: {e}")
        return None
    finally:
        client_socket.close()
    # print("start: {}\n".format(receive_message))

    # 2. Now receive_message is a string, so we can use string separators
    separator = '\r\n\r\n'
    
    if separator in receive_message:
        # 3. Split header and body
        _, body_content_raw = receive_message.split(separator, 1)
        
        # 4. Parse the body JSON string into a Python Dictionary
        try:
            # strip() removes extra whitespace/newlines around the JSON
            return json.loads(body_content_raw.strip()) 
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON body: {e}")
            return None
            
    print("[ERROR] Header separator not found in response.")
    return None


def handle_peer_connection(client,addr):
  message = client.recv(1024).decode()
  # print(message)
  #to do 


def setIP(ip):
    global IP
    IP = ip

def proc_message(addr, conn):
  message = conn.recv(1024).decode()
  # print(message)
  # to do more 


def connect_server(ip,port,peip,pepo):
  #listenport = 80
  client_socket = socket.socket()
  client_socket.connect((ip,port))
  

  while True :
    addr, conn = client_socket.accept()
    nconn = threading.Thread(target = handle_peer_connection, args = (addr,conn))
    
    nconn.start()

def offline(ip, port, pepo):
    # Note: 'ip' here is the SERVER ip. We need the PEER ip to remove.
    # But looking at your main code, you don't pass peer_ip to offline.
    # You need to use the global IP variable you set via setIP
    global IP 
    
    client_socket = socket.socket()
    client_socket.connect((ip, port))

    body_data = {
        "ip": IP,     # <--- FIX: Use the global Peer IP, not "127.0.0.1"
        "port": pepo
    }
    body_json = json.dumps(body_data)

    content_length = len(body_json)

    request_message = (
        f"POST /remove HTTP/1.1\r\n"
        f"Host: {ip}:{port}\r\n"
        f"Content-Type: application/json\r\n"
        f"Cookie: auth=true\r\n"
        f"Content-Length: {content_length}\r\n"
        f"\r\n"
        f"{body_json}"
    )
    client_socket.send(request_message.encode())
    client_socket.close()
def offline2(ip,port,pepo):
  client_socket = socket.socket()
  client_socket.connect((ip,port))

  body_data = {
    "ip": IP,
    "port": pepo
  }
  body_json = json.dumps(body_data) # Converts to '{"ip": "127.0.0.1", "port": 8000}'

# 2. Calculate length
  content_length = len(body_json)

# 3. Construct the full message
  request_message = (
    "POST /remove HTTP/1.1\r\n"
    "Host: localhost:9000\r\n"
    "Content-Type: application/json\r\n"
    "Cookie: auth=true\r\n"
    f"Content-Length: {content_length}\r\n"
    "\r\n"
    f"{body_json}"
  )
  client_socket.send(request_message.encode())


def submit_info(ip,port,peer_ip,peer_port):
  try:
    print(f"[Peer] Registering with tracker {ip}:{port}...")
    client_socket = socket.socket()
    client_socket.connect((ip,port))
    body_data = {
      "ip": peer_ip,
      "port": peer_port
    }
    body_json = json.dumps(body_data) # Converts to '{"ip": "127.0.0.1", "port": 8000}'

  # 2. Calculate length
    content_length = len(body_json)

  # 3. Construct the full message
    request_message = (
      f"POST /submit-info HTTP/1.1\r\n"
      f"Host: {ip}:{port}\r\n"
      "Content-Type: application/json\r\n"
      "Cookie: auth=true\r\n"
      f"Content-Length: {content_length}\r\n"
      "\r\n"
      f"{body_json}"
    )
    client_socket.send(request_message.encode())
    receive_message =   client_socket.recv(1024).decode()
    print(f"[Peer] Registration successful!")
    print(f"[Peer] Response: {receive_message[:100]}...")
    client_socket.close()
  except Exception as e:
    print(f"[Peer] Registration failed: {e}")

def listen_server(ip,port,peip,pepo): 
  listener = socket.socket()
  listener.bind((peip,pepo))
  listener.listen(10)
  while True: 
    addr,conn = listener.accept()

    nconn = threading.Thread(target= proc_message, args = (addr, conn))
    nconn.start()
def add_list(ip, port, peer_ip,peer_port):
  try:
    print(f"[Peer] Going online to tracker {ip}:{port}...")
    client_socket = socket.socket()
    client_socket.connect((ip,port))
    
    body_data = {"ip": peer_ip, "port": peer_port}
    body_json = json.dumps(body_data)
    
    msg = (
        f"POST /add-list HTTP/1.1\r\n"
        f"Host: {ip}:{port}\r\n"
        "Content-Type: application/json\r\n"
        "Cookie: auth=true\r\n"
        f"Content-Length: {len(body_json)}\r\n"
        "\r\n"
        f"{body_json}"
    )
    
    client_socket.send(msg.encode())  
    receive_message = client_socket.recv(1024).decode()
    print(f"[Peer] Now online!")
    print(f"[Peer] Response: {receive_message[:100]}...")
    client_socket.close()
  except Exception as e:
    print(f"[Peer] Go online failed: {e}")

def get_list(ip,port):
  client_socket = socket.socket()
  client_socket.connect((ip,port))
  client_socket.send(request_message_getlist.encode())  
  receive_message = client_socket.recv(1024).decode()
  # print(receive_message)
  return receive_message
def setServerIP(ip):
    global server_ip
    server_ip = ip
def setServerPort(port):
    global server_port
    server_port = port
if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
    parser.add_argument('--peer-ip')
    parser.add_argument('--peer-port', type = int)
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port
    peip = args.peer_ip
    pepo = args.peer_port
    setIP(peip)
    setPort(pepo)
    setServerIP(ip)
    setServerPort(port)
    # threadlisten = threading.Thread(target= listen_server, args = (ip, port, peip,pepo))
    # threadlisten.daemon = True 
    # threadlisten.start()


    app.prepare_address(peip,pepo)
    peer_thread = threading.Thread(target= app.run)
    peer_thread.daemon = True 
    peer_thread.start()
    
    submit_info(ip,port,peip,pepo)
    time.sleep(1)
    add_list(ip, port,peip,pepo)
    time.sleep(1)
    #get_list(ip,port)

    # Keep the main thread alive so the daemon server thread keeps running
    while True:
      try:
        time.sleep(1)
      except KeyboardInterrupt:
        offline(ip,port,pepo)
        break

    #app.prepare_address(ip, port)
    #app.run()

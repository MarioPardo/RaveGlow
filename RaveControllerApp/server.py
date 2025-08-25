import socket
import threading
import json

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 5000        # pick any free port

clients = []  # keep track of connected clients

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            try:
                msg = json.loads(data.decode())
                print(f"[RECEIVED from {addr}] {msg}")
            except json.JSONDecodeError:
                print(f"[RECEIVED raw from {addr}] {data.decode()}")
    except ConnectionResetError:
        print(f"[DISCONNECTED] {addr}")
    finally:
        clients.remove(conn)
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        
def broadcast_message(msg_dict):
    """Send JSON to all connected clients, each message terminated with newline"""
    data = (json.dumps(msg_dict) + "\n").encode('utf-8')
    for c in clients:
        try:
            c.sendall(data)
        except:
            pass  # ignore disconnected clients


if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    print("[SERVER STARTED]")

    # simple test loop from console
    while True:
        input("Enter message to broadcast: ")
        text={
            "Animation": "FuseWave",
            "r": 255,
            "g": 100,
            "b": 50,
            "BPM": 160
        }
        broadcast_message(text)

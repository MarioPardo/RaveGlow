import socket
import threading
import json

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 5000        # pick any free port

ip_address = None

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

def manually_setup_server():

    # Display current IP address
    hostname = socket.gethostname()
    global ip_address
    ip_address = socket.gethostbyname(hostname)
    print(f"Current IP address: {ip_address}")

    # Prompt for which port to use, default to 5000
    port_input = input("Enter port to use (default 5000): ")
    try:
        global PORT
        PORT = int(port_input) if port_input.strip() else 5000
    except ValueError:
        print("Invalid port. Using default 5000.")
        PORT = 5000
    print(f"Using port: {PORT}")


def start_server():

    hostname = socket.gethostname()
    global ip_address
    ip_address = socket.gethostbyname(hostname)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()


    print(f"[LISTENING] Server is running on {ip_address}:{PORT}")

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


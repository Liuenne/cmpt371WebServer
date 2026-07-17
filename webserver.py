import socket
import os
from datetime import datetime

DOCUMENT_ROOT  = os.path.dirname(os.path.abspath(__file__))

MIME_TYPES = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.txt': 'text/plain',
}

def get_content_type(file_path):
    _, ext = os.path.splitext(file_path)
    return MIME_TYPES.get(ext, 'application/octet-stream')

def build_resp(status_code, status_text, body=b'', content_type='text/html'):
    header = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode('utf-8')
    return header + body

def handle_req(conn, addr):
    request_data = conn.recv(4096).decode('utf-8')
    if not request_data:
        return
    
    request_line = request_data.split('\r\n')[0]
    print (f"{addr} -> {request_line}")

    try:
        method,path, ver = request_line.split()
    except ValueError:
        body = b"<h1>400 Bad Request</h1>"
        conn.sendall(build_resp(400, "Bad Request", body))
        return
    
    path = path.split('?')[0]
    if path == '/':
        path = '/test.html'
    
    requested_data = os.path.normpath(os.path.join(DOCUMENT_ROOT, path.lstrip('/')))
    if not requested_data.startswith(DOCUMENT_ROOT):
        body = b"<h1>403 Forbidden</h1>"
        conn.sendall(build_resp(403, "Forbidden", body))
        return
    if not os.path.exists(requested_data):
        body = b"<h1>404 Not Found</h1>"
        conn.sendall(build_resp(404, "Not Found", body))
        return
    if not os.access(requested_data, os.R_OK):
        body = b"<h1>403 Forbidden</h1>"
        conn.sendall(build_resp(403, "Forbidden", body))
        return
    
    try:
        with open(requested_data, 'rb') as f:
            body = f.read()
        content_type = get_content_type(requested_data)
        conn.sendall(build_resp(200, "OK", body, content_type))
    except Exception as e:
        print(f"Error reading file {requested_data}: {e}")
        body = b"<h1>500 Internal Server Error</h1>"
        conn.sendall(build_resp(500, "Internal Server Error", body))

def start_server(host='', port = 8080):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server started on port {port}")

    while True:
        conn, addr = server_socket.accept()
        try:
            handle_req(conn, addr)
        except Exception as e:
            print(f"Error handling request from {addr}: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    start_server()
import http.server
import socketserver

if __name__ == '__main__':
    PORT = 5050
    HOST = "localhost"

    Handler = http.server.SimpleHTTPRequestHandler

    server = socketserver.TCPServer((HOST, PORT), Handler)
    server.serve_forever()
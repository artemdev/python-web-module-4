
import logging
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
from pathlib import Path
import mimetypes
import urllib
from datetime import datetime

STORAGE_PATH = './storage/data.json'
UDP_IP = '0.0.0.0'
WEB_SERVER_PORT = 3000
SOCKET_PORT = 5000

logging.basicConfig(level=logging.DEBUG)


class MyServer(BaseHTTPRequestHandler):
    def send_html_page(self, page, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(page, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static_file(self, file):
        self.send_response(200)
        mimtype, *_ = mimetypes.guess_type(file)[0]

        if mimtype:
            self.send_header('Content-type', mimtype)
        else:
            self.send_header('Content-type', 'text/plain')

        self.end_headers()

        with open(file, 'rb') as fd:
            self.wfile.write(fd.read())

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        match path:
            case "/":
                self.send_html_page("index.html")
            case "/message.html":
                self.send_html_page("message.html")
            case _:
                file = Path(path[1:])
                if (file.is_file()):
                    self.send_static_file(file)
                else:
                    self.send_html_page("error.html", 404)

    def do_POST(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = UDP_IP, SOCKET_PORT
        byte_data = self.rfile.read(int(self.headers['Content-Length']))
        sock.sendto(byte_data, server)
        logging.info("Response from socket server %s", sock.recv(1024))
        sock.close()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


class MySocket():
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = UDP_IP, SOCKET_PORT
        sock.bind(server)
        try:
            while True:
                data, address = sock.recvfrom(1024)
                print(f'Received data: {data.decode()} from: {address}')

                data_parse = urllib.parse.unquote_plus(data.decode())
                data_dict = {key: value for key, value in [
                    el.split('=') for el in data_parse.split('&')]}

                with open(STORAGE_PATH, 'a', encoding='UTF-8') as fd:
                    fd.write(
                        str({datetime.now().strftime('%Y-%m-%d %H:%M:%S'): data_dict}) + '\n')

                logging.info('Data saved in file %s', data_dict)
                sock.sendto(b'Success', address)
        except KeyboardInterrupt:
            print('Stopping socket...')
        finally:
            sock.close()


if __name__ == "__main__":
    socket_server = MySocket()
    web_server = HTTPServer((UDP_IP, WEB_SERVER_PORT), MyServer)
    socket_thread = Thread(target=socket_server.start, daemon=True)
    web_thread = Thread(target=web_server.serve_forever, daemon=True)
    print('Starting web socket ...')
    socket_thread.start()
    print('Starting web server ...')
    web_thread.start()
    web_thread.join()
    print('Server and socket are closed.')

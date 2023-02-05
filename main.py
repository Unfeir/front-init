from datetime import datetime
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import mimetypes
import pathlib
import socket
from threading import Thread
import urllib.parse


S_IP = '127.0.0.1'
S_PORT = 5000


class HTTPHahdler(BaseHTTPRequestHandler):

    def do_POST(self):
        # print(f'{self.path=}')
        # print(f'{self.headers.__dict__=}')
        body = self.rfile.read(int(self.headers['Content-Length']))
        msg = f'{body.decode()}&dtime={datetime.now()}'
        send_msg(msg.encode())
        self.send_html('message.html')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        # print(self.path)
        # print('--------')
        # print(route)
        match route.path:
            case '/':
                print('main')
                self.send_html('index.html')
            case '/massage':
                print('msg')
                self.send_html('message.html')
            case _:
                file = pathlib.Path() / route.path[1:]

                if file.exists():
                    self.sendstatic(file)
                else:
                    self.send_html('error.html')



    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def sendstatic(self, filename):
        self.send_response(200)
        mim_type, *_ = mimetypes.guess_type(filename)
        # print(mim_type)
        if mim_type:
            self.send_header('Content-Type', mim_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def send_msg(data):
    # print(f'send data: {data}')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (S_IP, S_PORT))
    sock.close()

def save_msg(msg):

    file = pathlib.Path().joinpath('storage/data.json')
    data = {}
    try:
        msg_split = [el.split('=') for el in msg.decode().split('&')]
        reformat_msg = {msg_split[2][1]: {msg_split[0][0]: msg_split[0][1], msg_split[1][0]: msg_split[1][1]}}
        with open(file, 'r', encoding='UTF-8') as fd:
            old_data = json.load(fd)
            data = old_data

        data.update(reformat_msg)
        with open(file, 'w', encoding='UTF-8') as fd:
            json.dump(data, fd, ensure_ascii=False)

    except ValueError as err:
        logging.ERROR(err)
    except OSError as err:
        logging.error(err)


def socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            # print(f'take data {data}')
            save_msg(data)
    except KeyboardInterrupt:
        print('stoped')

    finally:
        sock.close()


def run(server=HTTPServer, handler=HTTPHahdler):
    address = ('127.0.0.1', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s - %(message)s')

    STORAGE_DIR = pathlib.Path().joinpath('storage')
    DATA = STORAGE_DIR / 'data.json'
    if not DATA.exists():
        with open(DATA, 'w', encoding='UTF-8') as fd:
            json.dump({}, fd, ensure_ascii=False)

    thread_server = Thread(target=run)
    thread_server.start()
    thread_socket = Thread(target=socket_server(S_IP, S_PORT))
    thread_socket.start()

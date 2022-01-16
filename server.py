import io
import socket
import struct
import threading
import pickle
import datetime

import numpy
from PIL import Image


class Server:
    def __init__(self):
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 1212
        self.addr = (self.host, self.port)
        self.DISCONNECT_MESSAGE = '!DISCONNECT'
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.addr)
        self.who_is_streaming = None
        self.stream_cooldown = None
        self.users = []
        self.payload_size = struct.calcsize("Q")

    def pack(self, data):
        a = pickle.dumps(data)
        message = struct.pack("Q", len(a)) + a
        return message

    def send_to_all(self, data, new):
        for user in self.users:
            if user != new:
                user.sendall(data)
                print('sent')

    def stream_handler(self, conn, addr, data):
        if not self.stream_cooldown:
            self.who_is_streaming = addr[0]
            self.send_to_all(data, conn)
        else:
            delta_time = datetime.datetime.now() - self.stream_cooldown
            if delta_time.seconds > 5 or self.who_is_streaming == conn:
                self.who_is_streaming = addr[0]
                self.send_to_all(data, conn)
            conn.send(self.pack("error: You can't stream while someone streaming"))

    def client_handle(self, conn, addr):
        print(f'[NEW CONNECTION] {addr} conneted')
        data = b""
        while True:
            while len(data) < self.payload_size:
                data += conn.recv(8192000)
            packed_msg_size = data[:self.payload_size]
            data = data[self.payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += conn.recv(409600)
            message_data = data[:msg_size]
            message_decoded = pickle.loads(message_data)
            if str(type(message_decoded)) == "<class 'PIL.Image.Image'>":
                byte_io = io.BytesIO()

                message_decoded.save(byte_io, 'PNG')
                self.stream_handler(conn, addr, self.pack(byte_io))
            else:
                self.send_to_all(self.pack(message_decoded), conn)
            print(type(message_decoded))
            data = b""

        # while connected:
        #     msg_length = conn.recv(2048).decode(FORMAT)
        #     if msg_length:
        #         msg_length = int(msg_length)
        #         msg = conn.recv(msg_length).decode(FORMAT)
        #         if msg == DISCONNECT_MESSAGE:
        #             connected = False
        #             OTHERS.remove(conn)
        #
        #         print(f'[{addr}] {msg}')
        #         SENDMSG(
        #             f'___________________________________________\n'
        #             f'[NEW MESSAGE]New message from {addr[0]} :\n{msg}\n'
        #             f'___________________________________________\n',conn)

        conn.close()

    def start(self):
        self.server.listen()
        print(f'[LISTENING] Sever is listening on {self.host}:{self.port}')
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.client_handle, args=(conn, addr))
            thread.start()
            self.users.append(conn)
            self.send_to_all(f'___________________________________________\n'
                             f'[NEW CONNECTION]{addr[0]} connected'
                             f'\n___________________________________________\n', conn)
            print(f'\n[ACTIVE CONNECTIONS] {threading.activeCount() - 1}')


if __name__ == '__main__':
    print('[STARTING] server is starting....')
    Server().start()

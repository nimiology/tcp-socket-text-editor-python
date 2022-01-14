import socket
import struct
import threading
import pickle
import datetime


class Server:
    host = socket.gethostbyname('localhost')
    port = 1212
    addr = (host, port)
    DISCONNECT_MESSAGE = '!DISCONNECT'
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    who_is_streaming = None
    stream_cooldown = None
    users = []
    payload_size = struct.calcsize("Q")

    def pack(self, data):
        a = pickle.dumps(data)
        message = struct.pack("Q", len(a)) + a
        return message


    def send_to_all(self, data, new):
        for PERSON in self.users:
            if PERSON != new:
                PERSON.send(self.pack(data))

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
                data += conn.recv(819200)
            packed_msg_size = data[:self.payload_size]
            data = data[self.payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += conn.recv(409600)
            message_data = data[:msg_size]
            data = data[msg_size:]
            if str(type(pickle.loads(message_data))) == "<class 'PIL.Image.Image'>":
                self.stream_handler(conn, addr, message_data)
            print(type(pickle.loads(message_data)))

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
    Server.start()

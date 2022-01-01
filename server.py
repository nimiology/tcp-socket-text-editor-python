import socket
import struct
import threading
import pickle
import cv2

HOST = socket.gethostbyname('localhost')
PORT = 2412
ADDR = (HOST, PORT)
DISCONNECT_MESSAGE = '!DISCONNECT'
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

USERS = []


def SENDMSG(text, new):
    for PERSON in USERS:
        if PERSON != new:
            PERSON.send(pickle.dumps(text))


def client_handle(conn, addr):
    print(f'[NEW CONNECTION] {addr} conneted')
    connected = True
    data = b""
    payload_size = struct.calcsize("Q")
    while True:
        while len(data) < payload_size:
            packet = server.recv(4 * 1024)  # 4K
            if not packet:
                break
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += server.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("RECEIVING VIDEO", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
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


def start():
    server.listen()
    print(f'[LISTENING] Sever is listening on {HOST}:{PORT}')
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=client_handle, args=(conn, addr))
        thread.start()
        USERS.append(conn)
        SENDMSG(f'___________________________________________\n'
                f'[NEW CONNECTION]{addr[0]} connected'
                f'\n___________________________________________\n', conn)
        print(f'\n[ACTIVE CONNECTIONS] {threading.activeCount() - 1}')


if __name__ == '__main__':
    print('[STARTING] server is starting....')
    start()

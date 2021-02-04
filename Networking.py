import socket
from queue import Queue, Empty
from struct import pack
from time import sleep

from Constants import *


class UDP():
    def __init__(self, oth_to_network):
        self.oth_to_network = oth_to_network

        self.sock_tcp_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp_listen.bind(("", 0))
        self.sock_tcp_listen.setblocking(False)
        self.sock_tcp_listen.listen(1)

        self.sock_tcp_data = None
        self.colour = None
        self.authority = False

        self.sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock_udp.setblocking(False)
        self.sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_udp.bind(("", MULTICAST_PORT))

        self.sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        self.sock_udp.sendto(int_to_bytes(self.sock_tcp_listen.getsockname()[1]),
                             (MULTICAST_GROUP, MULTICAST_PORT))  # Use multicast broadcast

        multicast_requirements = pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        self.sock_udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_requirements)

        self.udp_loop()

        self.sock_udp.close()
        self.sock_tcp_listen.close()

        print("Connected!")

    def udp_loop(self):
        while True:
            try:
                data = self.sock_udp.recvfrom(128)
            except BlockingIOError:
                pass
            else:
                self.sock_tcp_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock_tcp_data.bind(("", 0))
                self.sock_tcp_data.settimeout(1)
                try:
                    self.sock_tcp_data.connect((data[1][0], int_from_bytes(data[0])))
                except socket.timeout:
                    print("Failed to connect.")
                    pass
                else:
                    break

            try:
                self.sock_tcp_data, address = self.sock_tcp_listen.accept()
            except BlockingIOError:
                pass
            else:
                self.authority = True
                break

            try:
                get = self.oth_to_network.get(False)
            except Empty:
                pass
            else:
                if get[0] == LOCAL_IO["Net_End"]:
                    exit()

            sleep(0.1)


class TCP():

    def __init__(self, sock_tcp_data, authority, gui_and_network_to_oth: Queue, oth_to_network: Queue):

        self.sock_tcp_data = sock_tcp_data
        self.authority = authority
        self.gui_and_network_to_oth = gui_and_network_to_oth
        self.oth_to_network = oth_to_network

        if self.authority:
            self.colour = "B"
            self.gui_and_network_to_oth.put((LOCAL_IO["Net_Colour"], "B"))
            self.sock_tcp_data.send(TCP_DATA_TYPE["Opponent_Colour"] + b'WW')

        self.tcp_loop()

    def tcp_loop(self):
        while True:
            try:
                data = self.sock_tcp_data.recv(256)
            except socket.timeout:
                pass
            except BlockingIOError:
                pass
            except ConnectionResetError:
                break
            else:
                if data == b'':
                    break

                elif data[0:1] == TCP_DATA_TYPE["Opponent_Colour"]:
                    self.colour = data[1:2].decode('utf-8')
                    self.gui_and_network_to_oth.put((LOCAL_IO["Net_Colour"], self.colour))

                elif data[0:1] == TCP_DATA_TYPE["Move"]:
                    position = (data[1:].decode('utf-8')[0], data[1:].decode('utf-8')[1])
                    self.gui_and_network_to_oth.put((LOCAL_IO["Net_Click"], position))

            try:
                get = self.oth_to_network.get(False)
            except Empty:
                pass
            else:
                if get[0] == LOCAL_IO["Net_Send"]:
                    position = str(get[1][0]).encode('utf-8') + str(get[1][1]).encode('utf-8')
                    print("Sending move")
                    self.sock_tcp_data.send(TCP_DATA_TYPE["Move"] + position)
                elif get[0] == LOCAL_IO["Net_End"]:
                    exit()


            sleep(0.1)

        print("Disconnected!")


# Unsigned only
def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


# Unsigned only
def int_from_bytes(x_bytes):
    return int.from_bytes(x_bytes, 'big')

def main(gui_and_network_to_oth, oth_to_network, network_to_load):
    udp = UDP(oth_to_network)
    network_to_load.put((LOCAL_IO["Net_Loaded"], None))
    TCP(udp.sock_tcp_data, udp.authority, gui_and_network_to_oth, oth_to_network)

    exit()

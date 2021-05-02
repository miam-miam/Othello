"""
This is the main networking file, it runs in a separate thread
from the main GUI. It contains to main parts:
The UDP part which listens to other peers and broadcasts to other peers when starting a LAN game.
The TCP part is used when establishing a connection and communicating with a peer during a game.
"""

import socket
from queue import Queue, Empty
from struct import pack
from os import path
from time import sleep

from Constants import *


class UDP:
    """Class used for UDP connections."""

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

    def udp_loop(self):
        """Run when using UDP connections."""

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
                    self.sock_tcp_data.connect((data[1][0], int.from_bytes(data[0], "big")))
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


class TCP:
    """Used for TCP connections."""

    def __init__(self, sock_tcp_data, authority, gui_and_network_to_oth: Queue, oth_to_network: Queue,
                 network_to_load: Queue,
                 previous_game: str = None):

        self.sock_tcp_data = sock_tcp_data
        self.authority = authority
        self.gui_and_network_to_oth = gui_and_network_to_oth
        self.oth_to_network = oth_to_network
        self.network_to_load = network_to_load
        self.buffer = bytearray()
        self.previous_game = previous_game

        if self.authority:
            self.colour = "B"
            self.gui_and_network_to_oth.put((LOCAL_IO["Net_Colour"], "B"))
            self.send_data(TCP_DATA_TYPE["Opponent_Colour"] + b'W')
            if previous_game is None:
                self.send_data(TCP_DATA_TYPE["Initial_Moves"] + b'\x00')
            else:
                self.send_data(TCP_DATA_TYPE["Initial_Moves"] + b'\x01' + bytes(self.previous_game, encoding="utf-8"))
                self.network_to_load.put((LOCAL_IO["Net_Loaded"], self.previous_game))

        self.tcp_loop()
        print("Finished TCP loop")

    def tcp_loop(self):
        """Run when using TCP connections."""

        while True:
            try:
                datas = self.receive_data(self.sock_tcp_data.recv(256))
            except socket.timeout:
                pass
            except BlockingIOError:
                pass
            except ConnectionResetError:
                break
            else:
                for data in datas:

                    if data == b'':
                        return

                    elif data is None:
                        pass

                    elif data[0:1] == TCP_DATA_TYPE["Opponent_Colour"]:
                        self.colour = data[1:2].decode('utf-8')  # using [1:2] as using [1] would transform into int
                        self.gui_and_network_to_oth.put((LOCAL_IO["Net_Colour"], self.colour))

                    elif data[0:1] == TCP_DATA_TYPE["Move"]:
                        position = data[1], data[2]  # [1] automatically transforms into int
                        self.gui_and_network_to_oth.put((LOCAL_IO["Net_Click"], position))

                    elif data[0:1] == TCP_DATA_TYPE["Initial_Moves"]:
                        if data[1] == 0:  # Authority did not give moves to play
                            if self.authority:
                                self.network_to_load.put((LOCAL_IO["Net_Loaded"], None))
                            elif self.previous_game is not None:
                                self.send_data(
                                    TCP_DATA_TYPE["Initial_Moves"] + b'\x01' + bytes(self.previous_game, encoding="utf-8"))
                                self.network_to_load.put((LOCAL_IO["Net_Loaded"], self.previous_game))
                            else:
                                self.network_to_load.put((LOCAL_IO["Net_Loaded"], None))
                                self.send_data(TCP_DATA_TYPE["Initial_Moves"] + b'\x00')
                        else:  # Load moves
                            self.network_to_load.put((LOCAL_IO["Net_Loaded"], data[2:].decode("utf-8")))

            try:
                get = self.oth_to_network.get(False)
            except Empty:
                pass
            else:
                if get[0] == LOCAL_IO["Net_Send"]:
                    position = get[1][0].to_bytes(1, "big") + get[1][1].to_bytes(1, "big")
                    self.send_data(TCP_DATA_TYPE["Move"] + position)

                elif get[0] == LOCAL_IO["Net_End"]:
                    self.sock_tcp_data.close()
                    exit()

            sleep(0.1)


    def send_data(self, data):
        """Sends data through TCP socket with size bytes"""

        data = (len(data) + 2).to_bytes(2, "big") + bytes(data)
        self.sock_tcp_data.send(data)


    def receive_data(self, data):
        """Receives data through TCP socket ensuring it is the correct size"""

        if data == b"":
            yield data
            return

        while len(data) > 0:
            if len(self.buffer) > 0:
                cutoff = int.from_bytes(self.buffer[0:2], "big") - len(self.buffer)
            else:
                cutoff = int.from_bytes(data[0:2], "big")

            if cutoff > len(data):
                self.buffer = self.buffer + data[cutoff:]
                return None

            else:
                return_val = (self.buffer + data[:cutoff])[2:]  # Remove size bytes
                data = data[cutoff:]
                self.buffer = bytearray()
                yield return_val
        return


def int_to_bytes(x):
    """Changes an unsigned integer into bytes."""

    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def main(gui_and_network_to_oth, oth_to_network, network_to_load, save_name=None, current_line=None):
    """Run by thread to create UDP and TCP connections."""

    udp = UDP(oth_to_network)
    if save_name is not None:
        with open(path.join(SAVE_DIR, save_name), 'r') as file:
            save_name = file.readlines()[0:current_line]
        save_name = "".join(save_name)
    TCP(udp.sock_tcp_data, udp.authority, gui_and_network_to_oth, oth_to_network, network_to_load, save_name)

    exit()

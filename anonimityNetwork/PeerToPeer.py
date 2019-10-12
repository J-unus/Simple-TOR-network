import socket
import threading
import sys
import time
from Config import *


class Server:
    connections = []
    peers = []
    formattedPeers = []

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((INITIAL_ADDRESS, INITIAL_PORT))
        sock.listen(1)
        print("Server running ...")

        while True:
            c, a = sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)
            self.peers.append(a[0])

            print(str(a[0]) + ':' + str(a[1]) + " connected")
            self.formattedPeers.append(str(a[0]) + ':' + str(a[1]))
            self.sendPeers()

    def handler(self, c, a):
        while True:
            try:
                data = c.recv(1024)
                for connection in self.connections:
                    connection.send(bytes(data))
            except:
                print(str(a[0]) + ':' + str(a[1]) + " disconnected")
                self.formattedPeers.remove(str(a[0]) + ':' + str(a[1]))
                self.connections.remove(c)
                self.peers.remove(a[0])
                c.close()
                self.sendPeers()
                break

    def sendPeers(self):
        p = ""
        for peer in self.peers:
            p = p + peer + ","

        for connection in self.connections:
            connection.send(b'\x11' + bytes(p, "utf-8"))
        time.sleep(1)
        self.sendConnections()

    def sendConnections(self):
        for connection in self.connections:
            temp = list(filter(lambda x: x != str(connection.getpeername()[0]) + ":" + str(connection.getpeername()[1]),
                               self.formattedPeers))
            msg = ""
            for x in temp:
                msg += x + ","
            connection.send(b'\x12' + bytes(str(msg), "utf-8"))


class Client:
    clientIP = ""

    def __init__(self, address, file):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((address, INITIAL_PORT))

        self.clientIP = str(sock.getsockname()[0]) + ":" + str(sock.getsockname()[1])
        filename = ROUTING_TABLE_ADDRESS + str(file)
        f = open(filename, "w+")
        f.write(self.clientIP)
        f.close()

        iThread = threading.Thread(target=self.sendMsg, args=(sock,))
        iThread.daemon = True
        iThread.start()
        print("Connected.")

        while True:
            data = sock.recv(1024)
            if not data:
                break
            elif data[0:1] == b'\x11':
                self.updatePeers(data[1:])
            elif data[0:1] == b'\x12':
                self.updateConnections(data[1:])
            else:
                print(str(data, 'utf-8'))

    def updatePeers(self, peerData):
        p2p.peers = str(peerData, "utf-8").split(",")[:-1]


    def updateConnections(self, conData):
        p2p.connections = str(conData, "utf-8").split(",")[:-1]
        time.sleep(1)
        pathToOpen = ROUTING_TABLE_ADDRESS
        filename = pathToOpen + self.clientIP + ".txt"
        filename = filename.replace(":", "_")

        file = open(filename, "w+")
        for peer in p2p.connections:
            file.write(peer + "\n")
        file.close()


    def reqUpdate(self, sock):
        sock.send(b'\x13')

    def sendMsg(self, sock):
        pass


class p2p:
    peers = [INITIAL_ADDRESS]
    connections = []

    def __init__(self, filename):
        if ROUTING_TABLE_ADDRESS in filename:
            filename = str(filename).replace(ROUTING_TABLE_ADDRESS, "")

        while True:
            try:
                print("Trying to connect ...")
                for peer in p2p.peers:
                    try:
                        client = Client(peer, filename)
                    except:
                        pass
                    try:
                        file = open(ROUTING_TABLE_ADDRESS + filename, "w")
                        file.write(INITIAL_ADDRESS + ":" + str(INITIAL_PORT + 1))
                        file.close()
                        server = Server()
                    except:
                        print("Couldn't start the server...")
            except:
                sys.exit(0)


if __name__ == '__main__':
    file = ROUTING_TABLE_ADDRESS + "server.txt"
    p2p(file)

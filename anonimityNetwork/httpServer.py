import base64
from socketserver import ThreadingMixIn
import os
import random
import uuid
from anonimityNetwork import PeerToPeer
import threading
import time
import urllib3
from Config import *
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.parse
import html.parser
import json
import mmap

HOST = "127.0.0.1"
PORT = 4000


def getClient(address, requestId, getUrl):
    http = urllib3.PoolManager()

    url = str(getUrl)
    if "http://" not in url:
        url = "http://" + url

    requestHost = str(HOST) + ":" + str(PORT)

    request = http.request(
        'GET',
        "http://" + str(address),
        headers = {
        'Host': str(requestHost),
        'id': str(requestId),
        'url': str(url)
        })

    http.clear()

def initiateGet(url):
    filename =  REQUEST_TABLES_ADDRESS + str(HOST) + "_" + str(PORT) + "_requests.txt"
    myRequestId = open(filename, "a")

    randomNumb = str(uuid.uuid4())

    myRequestId.write(randomNumb + '\n')
    myRequestId.close()

    ipTable = open(str(ROUTING_TABLE_ADDRESS) + str(HOST)
                                                  + "_" + str(PORT) + ".txt", "r")
    connections = [line.rstrip('\n') for line in ipTable]
    ipTable.close()
    ipToSend = connections[random.randint(0, len(connections) - 1)]
    getClient(ipToSend, randomNumb, url)


def initiatePost(address, responseId, url):
    http = urllib3.PoolManager()

    urlOpened = urllib.request.urlopen(urllib.parse.unquote(url))
    responseCode = urlOpened.status
    contentType = urlOpened.info().get_content_type()
    data = base64.b64encode(urlOpened.read())

    encoded_body = json.dumps({
        'status': str(responseCode),
        'mime-type': str(contentType),
        'content': str(data, "utf8"),
    })

    escapedData = html.escape(encoded_body)

    request = http.request(
        'POST',
        "http://" + str(address),
        headers={
            'id': str(responseId),
        },
        body=escapedData
    )

    http.clear()


def bouncePost(responseIp, responseId, body):
    http = urllib3.PoolManager()

    requestHost = str(HOST) + ":" + str(PORT)

    request = http.request(
        'POST',
        "http://" + str(responseIp),
        headers={
            'id': str(responseId),
        },
        body=body
    )

    http.clear()

class TestHTTPServerRequestHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_response()
        requestIP = self.headers.get('Host')
        postId = self.headers.get('id')
        postUrl = self.headers.get('url')

        myRequests = REQUEST_TABLES_ADDRESS + str(HOST) + "_" + str(PORT) + "_requests.txt"

        if os.path.isfile(myRequests):
            if os.stat(myRequests).st_size != 0:
                with open(myRequests, 'rb', 0) as file, \
                        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                    if s.find(bytes(postId, "utf8")) != -1:
                        print("Sain oma Get-i. Läheb uuele ringile!")
                        time.sleep(3)
                        return initiateGet(postUrl)

        getDownload = self.headers

        if LAZINESS < random.randint(0, 100):
            print("Saatsin teele")
            print(self.headers)
            time.sleep(1)
            initiatePost(requestIP, postId, postUrl)
        else:
            print("Olin laisk")

            print("Toimub vali responsi logimine")
            routingTable = open(RESPONSE_TABLES_ADDRESS + str(HOST) + "_" + str(PORT) + "_responses.txt", "a")
            routingTable.write(str(requestIP) + ' ' + getDownload.get('id') + '\n')
            routingTable.close()

            ipTable = open(str(ROUTING_TABLE_ADDRESS) + str(HOST)
                           + "_" + str(PORT) + ".txt", "r")
            connections = [line.rstrip('\n') for line in ipTable]
            ipTable.close()

            print(requestIP)
            print(connections)

            connections.remove(requestIP)
            if len(connections) != 0:
                ipToSend = connections[random.randint(0, len(connections) - 1)]
                getClient(ipToSend, getDownload.get('id'), getDownload.get('url'))
            else:
                print("Error at bounce. Nowhere to send!")



    def do_POST(self):
        self._set_response()

        print("olen do_post")

        postId = self.headers.get('id')

        myRequests = REQUEST_TABLES_ADDRESS + str(HOST) + "_" + str(PORT) + "_requests.txt"
        if os.path.isfile(myRequests):
            if os.stat(myRequests).st_size != 0:
                with open(myRequests, 'rb', 0) as file, \
                        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                    if s.find(bytes(postId, "utf8")) != -1:
                        content_len = int(self.headers.get('Content-Length'))
                        post_body = json.loads(html.unescape(str(self.rfile.read(content_len), "utf8")))
                        print(base64.b64decode(post_body["content"]).decode("utf-8"))
                        return None
            else:
                print("Error. Mu request fail on tühi.")
        else:
            print("Pehme error. Mu request fail on puudu. Ilmselt pole veel midagi küsinud")


        myResponses = RESPONSE_TABLES_ADDRESS + str(HOST) + "_" + str(PORT) + "_responses.txt"
        if os.path.isfile(myResponses):
            if os.stat(myResponses).st_size != 0:
                with open(myResponses, 'rb', 0) as file, \
                        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                    if s.find(bytes(postId, "utf8")) != -1:
                        print("Andsin posti edasi")

                        responseTable = open(myResponses, "r")
                        responseList = responseTable.readlines()
                        responseTable.close()

                        responseLine = [line for line in responseList if postId in line]
                        splitLine = responseLine[0].split(" ")
                        responseIp = splitLine[0]

                        content_len = int(self.headers.get('Content-Length'))
                        post_body = self.rfile.read(content_len)

                        bouncePost(responseIp, postId, post_body)
            else:
                print("Error. Where did you come from, where did you go, where did you come from Cotton-Eye Joe!")
        else:
            print("Error. Kui olen siia jõudnud, siis post ei teinud midagi. Mis toimub?")

        message = "hello world!"
        self.wfile.write(bytes(message, "utf8"))


def dummyControls():
    while True:
        inc = input("")
        if "DL" in inc:
            parsed = inc.split(" ")
            initiateGet(urllib.parse.quote(parsed[1]))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == "__main__":

    filename = str(random.randint(100000, 999999)) + ".txt"
    f = open(ROUTING_TABLE_ADDRESS + filename, "w+")
    f.close()

    p2p = threading.Thread(target=PeerToPeer.p2p, args=(filename,))
    p2p.start()

    g = open(ROUTING_TABLE_ADDRESS + filename, "r")
    time.sleep(10)
    client = g.read()
    g.close()
    if client is not None:
        data = client.split(":")
        HOST = str(data[0])
        PORT = int(data[1])

    os.remove(ROUTING_TABLE_ADDRESS + filename)


    server = ThreadedHTTPServer((HOST, PORT), TestHTTPServerRequestHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.start()
    print("Server started on port:", PORT)

    routingTable = ROUTING_TABLE_ADDRESS + str(HOST) + "_" + str(PORT) + ".txt"

    dumbControls = threading.Thread(target=dummyControls)
    dumbControls.start()

import binascii
import socket
import json
import time
import logging
import random

if __name__ == "__main__":

    format = "[C1] %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Node Service Starting")
    # Setup socket and such to send DNS Request

    # Setup JSON structure

    jsonDict = {"source": "1.2.3.4", "question": "a.co",
                "loc": {"x": 0, "y": 0}}

    # TODO: Implement MGRS coordinate system
    jsonDict["loc"]["x"] = random.randint(-1000, 1000)
    jsonDict["loc"]["y"] = random.randint(-1000, 1000)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create socket

    port = 10853

    sock.connect(('127.0.0.1', port))  # Connect to server

    # Send the data to the server
    sock.send(bytes(json.dumps(jsonDict), encoding="utf-8"))
    logging.info("Sent request %s to host" % str(jsonDict))

    dnsResponse = sock.recv(1024)
    dnsResponse = dnsResponse.decode("utf-8")

    logging.info("Response: {}".format(dnsResponse))

    sock.close()

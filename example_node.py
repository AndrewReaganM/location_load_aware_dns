"""
Andrew Massey
Operating Systems Theory
Fall 2020
Dr. Christan Grant

Final Project
example_node.py
"""

import binascii
import socket
import json
import time
import logging
import random
import secrets

if __name__ == "__main__":

    format = "[N] %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("Node Service Starting")
    # Setup socket and sucn to send load data to DNS server

    print("Hostname: ", end='')
    hname = str(input())

    print("IP: ", end="")
    ip_addr = str(input())

    key = secrets.token_urlsafe()
    print(key)

    loc_x = random.randint(-1000, 1000)
    loc_y = random.randint(-1000, 1000)

    # Setup JSON structure
    jsonDict = {"hostname": hname, "routable_ip": ip_addr, "load": 5, "loc": {"x": loc_x, "y": loc_y}, "key": key}

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create socket

    port = 12001

    sock.connect(('127.0.0.1', port)) # Connect to server

    while True:
        sock.send(bytes(json.dumps(jsonDict), encoding="utf-8")) # Send the data to the server
        logging.info("Sent load {} to server".format(jsonDict["load"]))
        jsonDict["load"] = random.randint(1,9)
        time.sleep(3)

    sock.close()
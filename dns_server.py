"""
Andrew Massey
Operating Systems Theory
Fall 2020
Dr. Christan Grant

Final Project
dns_server.py
"""

from _thread import *
import logging
import socket
import threading
import json
import math

ANSWER_MAX = 4
DNS_PORT = 9999
PORT = 12001

loadWeight = 0.6 # 0 means no weight on load, 1 means full weight on load

loadInfo = {"test": "data"}


def handleNodeThreads():
    # TODO: Create thread(s) to handle communications between multiple nodes
    # Open socket to facilitate node connections

    sock = socket.socket()

    sock.bind(('', PORT))
    sock.listen(50)
    logging.info("[T1] Binded to port")

    ######################### Parallelize Later ######################
    while True:
        n, addr = sock.accept()
        logging.info("[ThrHndlr] Starting New Thread for {}".format(str(addr)))
        start_new_thread(maintainLoadConn, (n,))

    sock.close()


"""
    This function will be called in its own thread and connect to the individual machines
to retreive load data.
"""


def maintainLoadConn(conn_state):
    # Perform initial receive and decode
    try:
        tempMsg = conn_state.recv(1024)  # Receive data from node
        # Decode data and put in dictionary
        message = json.loads(tempMsg.decode("utf-8"))
    except:
        conn_state.close()
        logging.info(
            "[ntwkr] Unable to receive data from node, exiting thread...")
        return

    # Ensures database is correctly initalized for conn
    initDatabaseForConn(loadInfo, message)

    # If neither of the above conditions is met, we know that the hname and routable_ip were in the database
    # Now we want to verify key and update the database each time
    while True:
        if compareKeys(message, loadInfo):
            # logging.info("[nwkr] " + str(message))
            dbUpdateLoad(loadInfo, message)
            logging.info("[nwkr] {} @ {} ({}) load updated to {}".format(getName(message),
                        getIp(message), getLocation(message), dbGetLoad(loadInfo, message)))

            try:
                tempMsg = conn_state.recv(1024)
                message = json.loads(tempMsg.decode("utf-8"))
            except:
                logging.info("[nwkr] {} @ {} failed to update, outage assumption".format(
                    getName(message), getIp(message)))
                # Set load to 10, indicates outage
                dbNodeOutage(loadInfo, message)
                conn_state.close()
                break
        else:
            logging.info("[nwkr] {} -> {} failed key test".format(getName(message), getIp(message)))
            conn_state.close()
            return


def dbNodeOutage(database, info):
    database[info["hostname"]][info["routable_ip"]]["load"] = 10

def compareKeys(candidateData, database):
    return candidateData["key"] == database[candidateData["hostname"]][candidateData["routable_ip"]]["key"]

def dbGetLoad(database, info):
    return database[info["hostname"]][info["routable_ip"]]["load"]

def getName(info):
    return info["hostname"]

def getLoad(info):
    info["load"]

def getIp(info):
    return info["routable_ip"]

def getKey(info):
    return info["key"]

def getLocation(info):
    return info["loc"]

def dbUpdateLoad(database, info):
    database[info["hostname"]][info["routable_ip"]]["load"] = info["load"]

def euclideanDist(pos0, pos1):
    return math.sqrt( (pos0["x"]+pos1["x"])*(pos0["x"]+pos1["x"]) + (pos0["y"]+pos1["y"])*(pos0["y"]+pos1["y"]) )


def initDatabaseForConn(database, message):
    # Check and see if node hostname in database
    if getName(message) not in database:  # If no hostname
        # Create hname and add first IP entry
        database[message["hostname"]] = {message["routable_ip"]: {
            "load": message["load"], "key": message["key"], "loc": message["loc"]}}
        logging.info("[nwkr] Created new hname entry")

    # If hostname was present, but IP not
    elif getIp(message) not in loadInfo[message["hostname"]]:
        # Getting here implies that the hname WAS present, but routable_ip was NOT associated with the hname.
        # Add new IP to existing hostname
        loadInfo[message["hostname"]][getIp(message)] = {
            "load": getLoad(message), "key": getKey(message), "loc": message["loc"]}
        logging.info("[nwkr] Created new {} entry: {}".format(
            getName(message), getIp(message)))

def dnsSort(validNodes, question):
    # Remove unreachable or down nodes
    for node in list(validNodes.keys()):
        if validNodes[node]["load"] == 10:
            del validNodes[node]

    # Calculate euclidean distance for each node, remove if load=10
    rawDist = []
    rawLoad = []
    i=0
    for node in validNodes:
        if validNodes[node]["load"] == 10:
            del validNodes[node]
        else:
            rawDist.append(euclideanDist(validNodes[node]["loc"], question["loc"]))
            rawLoad.append(validNodes[node]["load"])
            i+=1

    # Optimize list and send to client 
    # Normalize the distance vector
    normalizedDist = [float(x)/max(rawDist) for x in rawDist] # Effectively a score
    normalizedLoad = [float(y)/max(rawLoad) for y in rawLoad]

    # Add the normalized back to the dict
    scoreVec = []
    i=0
    for node in validNodes:
        scoreVec.append((node, ( (1-loadWeight)*normalizedDist[i])+(loadWeight * normalizedLoad[i])) ) # tuple
        i+=1

    # Sort the list
    scoreVec.sort(key=lambda x: x[1], reverse=False)
    
    return scoreVec

def dnsResponder(conn):
    request_tmp = dns_client.recv(1024)
    client_request = json.loads(request_tmp.decode("utf-8"))

    tmpQuestion = client_request["question"] # Convenience variable

    # Set up response ahead of time
    questionResponse = {"status": True,
                            "question": tmpQuestion, "answer": []}

    if client_request["question"] not in loadInfo:
        # Return error
        logging.info("DNS question: {} from {} not in database".format(
            tmpQuestion, str(dns_client_addr)))
        questionResponse["status"] = False
        return
    else:
        logging.info("DNS question: {} from {}".format(
            tmpQuestion, str(dns_client_addr)))

        # Get all nodes for given question (hname)
        validNodes = loadInfo[client_request["question"]]
        
        # Calculate the distance from the client to each of the nodes
        scoredVec = dnsSort(validNodes, client_request)

        # Put UP TO the first ANSWER_MAX elements of validNodes in the response
        i=0
        for node in scoredVec:
            if i >= ANSWER_MAX:
                break
            questionResponse["answer"].append(node[0])
            i+=1
    try:
        dns_client.send(bytes(json.dumps(questionResponse), encoding="utf-8"))
    except:
        logging.info("Failed to send response to {}".format(client_request["source"]))
    
    dns_client.close()


if __name__ == "__main__":
    format = "[S] %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("DNS Server Starting")

    # Open communication for gettting load information for machines
    loadThread = threading.Thread(target=handleNodeThreads)
    loadThread.start()

    # Open port and listen for DNS requests
    dns_sock = socket.socket()
    dns_sock.bind(('', 10853))
    dns_sock.listen(100)

    while True:
        dns_client, dns_client_addr = dns_sock.accept() # Accept the connection
        start_new_thread(dnsResponder, (dns_client,)) # Spawn a thread to handle the connection

    loadThread.join()

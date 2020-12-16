# Load and Location Aware DNS

## Introduction

Traditional mechanisms for load balancing clients across multiple services (round-robin DNS) have a number of drawbacks, though they are very easy to implement. Often those who host services available over the internet would like to be able to dynamically change DNS records based on the status of their services, however the DNS system is not very conducive to such rapid changes.

I propose utilizing existing DNS systems to provide higher quality domain name resolution services using both location and load aware plugins. In the system proposed here, load reported by a node (node being defined as an external IP where a service can be accessed), and a variable accuracy location code sent from DNS clients to the resolver. The combination of these two allows for selecting the optimal node for a user to connect to. This document will discuss the implementation of the software to be ran on a node, the DNS client software and location selection strategy, and the system by which nodes are ranked for a given hostname. Critically, things not discussed are how this would work with the DNS system as defined in the RFCs, and the security of the node-to-DNS server connection.

## Making DNS Load-aware

Existing DNS mechanisms typically use a round-robin approach to handing out node IPs for a given hostname. This approach is simply putting the IP of the node that was most recently send as a response to the end of the list. While this certainly has some usefulness, it would me much more useful to be able to load balance at the DNS layer, allowing at capacity or even downed nodes to recover without having to handle redirecting traffic to another node. Handling this at the DNS layer would add little overhead to current DNS operations while providing higher availability to clients and easier administration for system administrators. Critically, this approach to DNS could allow an somewhat of an end to regional service outages, where service load could be spread out across the globe in the case of these ever-inconvenient incidents.

### How Clients Send Load Parameters

The DNS system proposed here allows for a simple text string to be sent to a domain's authoritative DNS server to notify it of its status. Load is represented as an integer from 0 to 10, where 0 is no load, and 10 indicates an outage, or an overloaded node. It takes the form of the following:

```json
{
    "hostname": hname,
    "routable_ip": ip_addr,
    "load": int, 
    "loc": {
        "x": loc_x,
        "y": loc_y
        },
    "key": key
} 
```

Nodes simply encode their data into this format and send it over TCP to their authoritative DNS server. If the key is correct, then the load data becomes a part of the DNS server's decision making process. Note that this early version uses `x` and `y` coordinates for ease of implementation, but ideally would make use of MGRS for location granularity.

## Making DNS Location-aware

Making DNS location-aware requires some work on the client side of things. The ideal solution to this would be to simply to attach location data onto a normal DNS question using edns(0) [RFC6891]. Due to my lack of knowledge of the intricacies of DNS, I am unaware of whether or not this would be practical. I propose using the NATO MGRS location scheme for encoding location. Its resolution is variable by how long the string is, and would provide privacy options to clients.

## Ranking Nodes based on Load and Location

In developing this system, a ranking system for nodes has been added that I believe is fair, but that is certainly open for analysis as its performance has not been tested. The algorithm used first removes all nodes with a load value of `10` on a scale from 1 to 10, computes the distance from each node to the client, normalizes that distance to fit on a scale from `0.0` to `1.0`. It then normalizes the load from `0.0` to `1.0`. Once those values are computed, they are weighted and added together as seen here:  

$$ r = (1-loadWeight)(normalizedDistance) + (loadWeight)(normalizedLoad) $$  

```python
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
```

It was important to be able to tune this ranking system easily, so in this implementation there is a variable `loadWeight` that defines how much emphasis is put on node load.

The `dnsSort()` function returns a list of nodes, and it is up to the DNS server's configuration to determine how many of these are sent as a DNS response. It is important, however, that they remain in the correct order in the response.

## Client DNS Response

Client DNS responses work very similarly to how DNS currently works, with the exception that the order of the response is relevant. Clients should work their way down the list in the case that the first result is unreachable.

## Testing

It is difficult to test DNS systems in a meaningful way without test networks that mimic the topology you are working with. Testing this system was done locally using multiple "example nodes" and a "dns client" that were meant to emulate the existence of nodes and clients requesting node information.

Results were consistent with the design. In the case that one node was closer or had signifigantly lower load, it was ranked higher. Nodes that reported a 10 load or experienced an outage were removed from the results, as is desirable.

In the future it would be ideal to test this out in a larger network setting, however that would be best to do after implementing it in existing DNS mechanisms.

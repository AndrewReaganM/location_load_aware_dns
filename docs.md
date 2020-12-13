# The edns-client-location EDNS(0) Option and Traffic Steering Framework

## Introduction

Traditional mechanisms for load balancing clients across multiple services (round-robin DNS) have a number of drawbacks, though they are very easy to implement. Often those who host services available over the internet would like to be able to dynamically change DNS records quickly, however the DNS system is not very conducive to such rapid changes.

edns(0) would provide the client's MGRS code (up to a certain length, which can provide anonymity to the user) to the DNS server.

The Traffic Steering Framework would allow DNS servers to be aware of additional node status information needed to make more intelligent decisions about how to respond to queries.

## edns-client-location

This section specifies a potential EDNS(0) [RFC6891] option which allows DNS clients to send their location to DNS servers in a privacy preserving way. This data allows the server to make a more informed decision about which nodes to direct traffic to. 

```txt

                        1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-------------------------------+-------------------------------+
   !         OPTION-CODE           !         OPTION-LENGTH         !
   +-------------------------------+-------------------------------+
   |           TIMEOUT             !
   +-------------------------------+
```

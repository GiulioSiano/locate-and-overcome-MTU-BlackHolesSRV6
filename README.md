
# Locate and overcome MTU Black Holes in SRV6 environment

## Table of content

* [Overview](#overview)
* [How Scamper works](#how-scamper-works)
	- [Inferring the MTU](#inferring-the-mtu)
	- [Hop Limit Finder](#hop-limit-hinder)
	- [Locating the bottleneck](#locating-the-bottleneck)
* [Scamper-like behavior in a SRv6 network with MTU Black Hole](#scamper-like-behavior-in-a-srv6-network-with-mtu-black-hole)
* [Usage](#usage)

## Overview
One of the main differences between the IPv4 and IPv6 protocol is the capability of the intermediate devices to perform the packets fragmentation. In IPv4 the user aiming to send packets to a destination sets as MTU that of the link between itself and the default gateway. From that point on, each intermediate device fragmets the packets according to the MTU of the next link. In IPv6 this feature has been disabled and the fragmentation is on the end-devices and since the MTU along the path changes, it must be known in advance. A technique to know it is the *MTU Path Discovery (PMTUD)*. <br/>
It presents a big issue: is based on ICMPv6 packets that can be blocked by firewalls or suppressed from sending for security reasons. A variant, called *Packetization layer path MTU discovery (PLPMTUD)*, relies on the transport layer to send probes whose size progressively increses and help in inferring the MTU (when no replies are received the value has been found). <br/>
Another solution to the PMTUD issues is *Scamper* which, among other features including the inferring of path MTU, is able to locate the failure as well. <br/>
The goal of this repository is to apply part of the behavior of *Scamper* to the alredy described [MTU Black Holes in SRv6 environment](https://github.com/GiulioSiano/MTUBlackHoleSRv6) problem in order to locate them and to find the *Maximum Segment Size (MSS)* allowed by the Segment Routing architecture.

## How Scamper works
Scamper is a publicly available measurement tool which logic is defined [here](https://users.caida.org/~mjl/pubs/scamper.pdf). According to [Inferring and Debugging Path MTU Discovery Failures](https://www.usenix.org/legacy/events/imc05/tech/full_papers/luckie/luckie.pdf), Scamper can be used to infer the MTU of a path and to locate where the failure occurred. The phases it goes through are the following:
*	Standard traceroute: it can infer the topology by taking into account how the routers behave (if they reply to probes whose TTL field is limited) and if a *ICMP Destination Unreachable* is sent on probe receiving by the destination.
*	PMTUD phase: large probes are sent along the path in order to solicit the *Packet Too Big* messages. It is successfully detected this phase has failed when the size of the probes exceed the currently known Path MTU and no reply protocols-compliant is received. When the PMTUD phase failure is detected, two techniques are implemented in order to:
	-	infer the MTU
	-	infer the location of the failure

### Inferring the MTU
The path MTU finding is accomplished by combining two techinques: first, given a table with predefined values of common MTUs find the largest value for which the probes succeed. It is selected as follows:
*	if the size of the failed probe is larger than 1500 byte, try with a probe whose size is 1500 byte (the usual MTU for Ethernet)
*	if the size of the failed probe is larger than 1454 byte, try with a probe whose size is 1454 byte (the usual MTU for tunnels or IP over Ethernet) 
*	otherwise, select the next smaller MTU value from the table. 

When a *ICMP* feedback is obtained the *lower bound* is found. It can be assumed no *ICMP* feedback has been sent if after the second attempt of the probe (second sent after 5 seconds from the first) no reply arrived. Scamper moves to the next entry of the table containing the well-known MTU values after 10 seconds. <br/>
Every time a probe for the lower bound fails, the *upper bound* value is reduced selecting the next larger value (with the respect to the lower bound).<br/>
Then, the second techinque which consists in some rationales, allows to quickly find the actual MTU:
*	if the lower bound is 1500 bytes or a known value in the table and the upper bound is smaller than the next largest known MTU, then send a probe with size one byte larger than the lower bound. In fact, it is quite probable that the MTU is the lower bound so if no reply is received this is the value sought. 
*	if the next largest MTU in the table is smaller than the current upper bound, send a probe with this size; it is quite probable the value of the MTU is one in the table
*	if both upper and lower bound are from the table, start a binary search.

### Hop Limit Finder
Another feature is inferring the number of hops the packets must traverse in order to reach the destination. This is done by interpreting the behaviour of the destination or intermediate nodes when they reply to probe packets:
	if the received packet is an *ICMP destinationation host unreachable* the hop_limit variable is incremented;
	if the received packet is an ICMPv6 port closed, the value is found;
	if no packet is received there will be another attempt;
	if no packet is received for the second time then return with error.
If no feedbacks are provided by the destination, the only way to infer it is by setting an increasing Hop Limit value while the size of the packets must be set lower than the MTU found. The Hop Limit is the highest value for which the source gets a reply. 

### Locating the bottleneck
This technique is used in an environment where *ICMP PTB, Destination unreachable and Time exceeded* are allowed to be sent by the intermediate devices. The bottleneck is localized by sending a set of probes whose size is the same as the MTU value and with increasing Hop Limit. The following checks are able to return at which hop there is the bottleneck (if any):<br/> 
*	Whenever a *ICMP destination unreachable* is received the job is done and no bottleneck has been detected. This holds also when no feedbacks are received but the current hop set in the header of the packet is the Hop Limit of the path (the destination is not allowed to send any ICMP feedback). <br/>
*	If nothing or a PTB message is received  but the current hop limit in the header of the packet is different than the Hop Limit of the path, then the bottleneck is localized at that hop. 
*	If a *ICMP time_exceeded* is received the hop limit is incremented. 

Locating the bottleneck in the case of a Black Hole means locate it. 

## Scamper-like behavior in a SRv6 network with MTU Black Hole
As already anticipated in the [Overview](#overview), the behavior of Scamper has been applied to the SRv6 network presented [here](https://github.com/GiulioSiano/MTUBlackHoleSRv6) where an MTU Black Hole occurs: the source code is made of the same files used to demonstrate the existence of MTU Black Holes with the addition of the Scamper techniques: the corresponding option will be available and if run the hop limit, the MTU and the bottleneck will be shown. The results are different according to the Recovery Policy status which can be installed/removed using the corresponding options. <br/>
To install the environment, setup the topology and to know how the emulated network works, please refer to the following repository: https://github.com/GiulioSiano/MTUBlackHoleSRv6.
In order to properly run the tool in this network, some policies must be edited. Indeed, the probes have been implemented as UDP packets that, according to the stardard policies installed, are forwared through the second path ([the green one](https://github.com/GiulioSiano/MTUBlackHoleSRv6/blob/main/Readme/SecondMethod.svg)) while the TCP traffic through the first (the red one). The changing consists in swapping the two, so that the first path is used by UDP packets and the second by TCP traffic. In fact, in order to locate the Black Hole and find the MTU, the probes must traverse the path in which it occurs. <br/>
The results are the following:
*	Without the recovery policy (the probes follows the first path traversing the nodes E1-C1-C2-E2):
```
hop_limit: 3
Calculating the MTU...
MTU lower: 1200 Next Largest Value: 1300
MTU = 1252 + 40 (IPv6 header) + 8 (UDP header) = 1300
No bottleneck.
```
*	Using the recovery policy (the probes pass through E1-C1-C3-C4-C2-E2 undergoing the double encapsulation of Segment Routing):
```
hop_limit: 3
Calculating the MTU...
MTU lower: 1100 Next Largest Value: 1200
MTU = 1176 + 40 (IPv6 header) + 8 (UDP header) = 1224
Bottleneck is at hop: 1
```

These results hold with what expected. Once the tool finished, the end-devices can use the actual MTU to properly fragment the packets and the network operator knows where the bottleneck happens (the hop counting starts from the egress node, E1 in this case). It may takes some time before results are returned. <br/>
Also, note how the second encapsulation is completely *hidden*: even if the total path is far longer with the respect to the case where the recovery policy is disabled, the hop limit remains the same.

## Usage
Navigate into the root folder and launch the following command:
```
sudo python3 start.py
```

The following options will be shown:
```
0) Setup topology (running VPP instances, configuring link and SRv6)
1) TCP traffic (Policy 1 (a1::) ).
2) ICMPv6 traffic (Policy 2 (a3::) ).
3) Simultaneous TCP and ICMPv6 traffic.
4) Enable Recovery Policy.
5) Disable Recovery Policy.
8) Start scamper.
9) Exit and kill VPP instances & delete interfaces.
10) Exit without killing VPP instances & deleting interfaces.
Recovery Policy status: FALSE
```

After setting up the network by launching the command *0*, exit from the tool without stopping the network using the command *10*. Thus in the root folder:

```
sudo sh EditSRv6Table.sh
```

Now it is possible to launch again the script *start.py* and run *Scamper* into the network. Since the Black Hole occurs when the recovery policy is active, it is suggested to execute it in this configuration.
To go back to the standard policy (UDP packets traverse the first path and TCP the second), exit from the tool and launch:

```
sudo sh RestoreSRv6Table.sh
```
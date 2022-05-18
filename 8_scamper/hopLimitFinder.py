#!/usr/bin/env python
import packet_generator as pacchetto
from socket import *
import ipaddress

bufferSize  = 1024
hop_limit = 1

def sendPkt_listenReply_tracerouting(s, byte_pkt):
	"""
	
	This method listens for a reply after sending a packet. 
	Since the goal is to find the hop limit, if the received packet is an ICMP destinationation host unreachable the hop_limit variable will be incremented.
	If the received packet is an ICMPv6 port closed, the value was already found.
	
	:param s: socket of host A
	:param byte_pkt: raw packet to be sent (to host B): it is an ICMPv6 packet
	:returns: it returns the reply packet to ICMPv6
	
	| 
	
	"""
	global hop_limit
	
	s.send(byte_pkt)
	try:
		data, server = s.recvfrom(bufferSize)
	except timeout:
		return -1
	
	if(str(data[12])=="134" and str(data[13])=="221"):	#if proto_ethernet is ipv6=86DD, that is in string 134 (86) e 221 (DD)
		if(str(data[20])=="58"):			#if proto is ICMPv6
			if(data[54]==3 and data[55]==0):	#if it's a icmpv6 time_exceeded code=0 (hop-limit exceeded in transit)
				if(str(data[68])=="17" and str(data[102])=="227" and str(data[103])=="57"):	#if icmpv6 contains udp with src_port 58169 
					hop_limit=hop_limit+1 	#destination unreachable -> incrementing hop_limit
					return 0
			if(data[54]==1 and data[55]==4):	#if an ICMPv6 port closed is received (destination reached)
				return 1
		return -1
		
def tracerouting(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, dim_data):
	"""
	The hop limit value is inferred by interpreting the behaviour of the destination or intermediate nodes:
	if the received packet is an ICMP destinationation host unreachable the hop_limit variable will be incremented;
	if the received packet is an ICMPv6 port closed, the value is found;
	if no packet is received there will be another attempt;
	if no packet is received for the second time then return with error.
	
	:param s: socket of host A
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A 
	:param flow_label: traffic flow ID
	:param dst_port: destination port (host B)
	:param src_port: source port (host A)
	:param dim_data: packet size
	
	:returns: error if intermediate hop doesn't reply, hop limit otherwise
	
	|
	
	"""
	resend=0
	
	pkt_new=pacchetto.pkt(dim_data)
	while True:
		byte_pkt=pkt_new.create_packet(dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
		code=sendPkt_listenReply_tracerouting(s, byte_pkt)
		if(code==0):
			byte_pkt=pkt_new.create_packet(dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
			sendPkt_listenReply_tracerouting(s, byte_pkt)
		elif(code==1):
			return hop_limit
		elif(code==-1 and resend==1):
			return -1
		elif(code==-1 and resend==0):
			resend=resend+1

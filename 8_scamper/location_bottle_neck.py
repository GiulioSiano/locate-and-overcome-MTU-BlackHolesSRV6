#!/usr/bin/env python

import packet_generator as packet
from socket import *
from array import *
import ipaddress
import struct 
pkt_new=0
byte_pkt=0
code=0
bufferSize  = 1024

def sending_packet(s, dim_data, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port ):
	"""
	Sending ICMPv6 probe to locate the bottleneck (if it exists).
	
	:param s: host A socket
	:param dim_data: packet size
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A
	:param flow_label: traffic flow ID
	:param hop_limit: hop limit
	:param dst_port: host B port
	:param src_port: host A port
	:resuls: is an integer returned by the "sendPkt_listenReply_mtusearch" function	
	"""
	resend=0
	pkt_new=packet.pkt(dim_data)
	byte_pkt=pkt_new.create_packet(dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
	
	while True:
		code = sendPkt_listenReply_mtusearch(s, byte_pkt)
		if(code==-1 and resend==1):
			return -1
		elif(code==-1 and resend==0):
			resend=1
		elif(code==0):
			return 0
		else:
			return code

def sendPkt_listenReply_mtusearch(s, byte_pkt):
	"""
	If a Packet too big or nothing is received, the hop at which this happens is the bottleneck.
	If an ICMPv6 destination unreachable is received->no bottleneck.
	
	:param s: host A socket
	:param byte_pkt: packet size
	:results:  returns -1 if nothing is received, ->0 if it's ICMPv6 destination unreachable; ->MTU limit given by a PacketTooBig packet received; ->1 if ICMPv6 time_exceeded is received -> -1 otherwise.
	
	|
	
	"""
	s.send(byte_pkt)
	try:
		data, server = s.recvfrom(bufferSize)
		
	except timeout:
		return -1
		
	if(str(data[12])=="134" and str(data[13])=="221"):	#if proto_ethernet is ipv6=86DD, that is in string 134 (86) e 221 (DD)
		if(str(data[20])=="58"):			#if proto is ICMPv6
			if(data[54]==1 and data[55]==4):	#if it's a destination unreachable->job done
				return 0
			elif(data[54]==2 and data[55]==0):	#if icmpv6 ptb code=0 is received
				print(int.from_bytes(data[58:62], byteorder='little'))
				return int.from_bytes(data[58:62], byteorder='little')	
			elif(data[54]==3 and data[55]==0):	#if icmpv6 time_exceeded code=0 is received (hop-limit exceeded in transit)
				return 1
	return -1

def location_bottle_neck (s, dim_data, hop_limit, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, mtu_exit_interface):
	"""
	Interpreting the sendPkt_listenReply_mtusearch method result.
	
	:param s: host A socket
	:param dim_data: packet size
	:param hop_limit: hop limit
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B
	:param src_addr_ipv6: IPv6 address of host A
	:param flow_label: traffic flow ID
	:param dst_port: host B port
	:param src_port: host A port
	:param mtu_exit_interface: host A MTU interface
	:results: returns 0 if there is no bottleneck, else -> integer representing the hop at which there is the first bottleneck
	
	|
	
	"""
	
	j=1
	while(j<=hop_limit):
		code=sending_packet(s, mtu_exit_interface-48, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, j, dst_port, src_port)
		if((code==-1 and j==hop_limit) or code==0):
			return 0
		elif(code==-1 and j!= hop_limit):
			return j
		elif(code==1):
			pass
		else:
			return j
		j=j+1

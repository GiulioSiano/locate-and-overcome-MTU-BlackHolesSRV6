#!/usr/bin/env python

import packet_generator as packet
from socket import *
import ipaddress
import struct

known_mtu_values=[1600, 1500, 1454, 1400, 1300, 1200 , 1100, 1000, 800]
bufferSize  = 1024

def sending_packet(s, dim_data, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port ):
	"""
	UDP probes are created and sent.
	
	:param s: host A socket
	:param dim_data: packet size
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A 
	:param flow_label: traffic flow ID
	:param hop_limit: set at maximum (255)
	:param dst_port: host B port
	:param src_port: host A port
	:returns: is an integer return by the "sendPkt_listenReply_mtusearch" function
	
	|
	
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
	| In the following method the reply to the probes are analyzed: 
	| it return -1 if no reply is received;
	| it return 0 if the destination is reached;
	| it return the value sent by ICMPv6 Packet too big.
	
	:param s: host A socket
	:param byte_pkt: raw packet
	:returns: returns -1 if nothing is received, 0 if it's ICMPv6 port closed; MTU limit given by PacketTooBig packet received; -1 otherwise.
	
	|

	"""
	s.send(byte_pkt)
	try:
		data, server = s.recvfrom(bufferSize)
		
	except timeout:
		return -1
		
	if(str(data[12])=="134" and str(data[13])=="221"):	#if proto_ethernet is ipv6=86DD, that is in string 134 (86) e 221 (DD)
		if(str(data[20])=="58"):			#if proto is ICMPv6
			if(data[54]==1 and data[55]==4):	#if an ICMPv6 port closed is received (destination reached)
				return 0
			elif(data[54]==2 and data[55]==0):	#if icmpv6 ptb code=0 is received
				return (struct.unpack('>I', data[58:62])[0])
	return -1	
	
def upperMTU(s, MTU_lower, MTU_upper, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, hop_limit):
	"""
	The upper bound of the path's MTU is found according to Scamper logic.
	
	:param s: host A socket
	:param MTU_lower: MTU lower bound 
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A 
	:param flow_label: traffic flow ID
	:param dst_port: host B port
	:param src_port: host A port
	:param hop_limit: set at maximum (255)
	
	:returns: MTU upper bound
	
	|
	
	"""
	next_largest_value=-1
	dim_data=-1
	
	for i in range(len(known_mtu_values)):
		if(known_mtu_values[i]> MTU_lower):
			next_largest_value=known_mtu_values[i]
	print("MTU lower: "+ str(MTU_lower)+" Next Largest Value: "+str(next_largest_value))
	
	binary_search=0
	while True:				
		if( MTU_lower==1500 or (MTU_lower in known_mtu_values and MTU_upper <  next_largest_value) ):
			dim_data=MTU_lower+1
			code=sending_packet(s, dim_data, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
			if(code==-1):
				return MTU_lower
		
		if(next_largest_value < MTU_upper):
			dim_data=next_largest_value
			code=sending_packet(s, dim_data, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
			if(code==0):	
				MTU_upper=next_largest_value
		if(MTU_lower in known_mtu_values and MTU_upper in known_mtu_values or binary_search==1):
			binary_search=1
			dim_data=round((MTU_lower + MTU_upper)/2)
			code=sending_packet(s, dim_data, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
			if(code!=0):
				MTU_upper=dim_data
			elif(code==0):
				MTU_lower=dim_data
			if(MTU_upper==MTU_lower or MTU_upper==MTU_lower+1):
				return MTU_lower

def lowerMTU(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, hop_limit, mtu_exit_i, MTU_upper):
	"""
	Starting from the exit interface MTU value, the lower bound of the MTU is found according to the Scamper logic.
	
	:param s: socket of host A
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A 
	:param flow_label: traffic flow ID
	:param dst_port: destination port (host B)
	:param src_port: source port (host A)
	:param hop_limit: set at maximum (255)
	:param mtu_exit_i: MTU interface of host A 
	:param MTU_upper: MTU upper bound 
	:returns: lower bound of the MTU range
	
	|
	
	"""
	MTU_l=mtu_exit_i
	MTU_u=MTU_upper
	
	if(MTU_l>1500):
		code=sending_packet(s, 1500, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
		if(code==0):
			return 1500, MTU_u
		MTU_u=1500
			
	if(MTU_l>1454):
		code=sending_packet(s, 1454, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
		if(code==0):
			return 1454, MTU_u
		MTU_u=1454
	
	for i in range(len(known_mtu_values)):
		if(known_mtu_values[i]< MTU_l):
			MTU_u=MTU_l
			MTU_l=known_mtu_values[i]
			code=sending_packet(s, MTU_l, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, hop_limit, dst_port, src_port)
			if(code==0):
				return MTU_l, MTU_u
				
def nextHop_MTUSearch(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, hop_limit, mtu_exit_i):
	"""
	| There will be the calculation of the lower bound and the upper bound of the MTU.
	| At first, the lower bound is set to the MTU value of the output interface while the upper MTU is set to next largest value in the table of known MTU .
	| The right MTU value will be eventually returned.
	
	:param s: host A socket
	:param dst_addr_eth: next hop ethernet address
	:param src_addr_eth: source ethernet address
	:param dst_addr_ipv6: IPv6 address of host B 
	:param src_addr_ipv6: IPv6 address of host A 
	:param flow_label: traffic flow ID
	:param dst_port: destination port (host B)
	:param src_port: source port (host A)
	:param hop_limit: set at maximum (255)
	:param mtu_exit_i: MTU of the host A's interface
	:results: the mtu of the entire path used by UDP packets is returned
	
	|
	
	"""
	MTU_lower=mtu_exit_i
	MTU_upper=0
	for i in range(len(known_mtu_values)):
				if(known_mtu_values[i]> MTU_lower):
					MTU_upper=known_mtu_values[i]
	
	MTU_lower, MTU_upper= lowerMTU(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, hop_limit, mtu_exit_i, MTU_upper)
	mtu=upperMTU(s, MTU_lower, MTU_upper, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, hop_limit)
	
	return mtu

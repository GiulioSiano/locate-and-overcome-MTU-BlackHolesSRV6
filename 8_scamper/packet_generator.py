#!/usr/bin/env python

from struct import *
import string
import random
import binascii
import ipaddress
import os

class pkt(object):
	"""
	This class define the "Packet": given the data the packet is built.
	"""
	def random_data(self, dim):
		"""
		Random data are generated: this is the payload of the packet.
		
		:param dim: dimension of random data to be generated
		:returns: this function returns the generated random data to insert into the packet
		
		|
		
		"""
		return bytes(random.getrandbits(2) for i in range(dim))
		
	def __init__(self, dim):
		self.dst_addr=""
		self.src_addr=""
		self.ip_dst=""
		self.ip_src=""
		self.flow_label=0
		self.payload_length=dim
		self.hop_limit=0
		self.port_dst=0
		self.port_src=0
		self.payload = self.random_data(self.payload_length)
		
	def eth_header(self, dst_addr, src_addr):
		"""
		This method builds the ethernet header.
		
		:param dst_addr: next hop ethernet address
		:param src_addr: source ethernet address
		:returns: ethernet header
		
		|
		
		"""
		protocol = 0x86DD	#IPv6
		dst_addr = binascii.unhexlify(dst_addr.replace(':', ''))
		src_addr = binascii.unhexlify(src_addr.replace(':', ''))
		
		return pack("!6s6sH", dst_addr, src_addr, protocol)
		
	def ipv6_header(self, ip_dst, ip_src, flow_label, payload_length, hop_limit):
		"""
		This method builds the IPv6 header.
		
		:param ip_dst: destionation IP address
		:param ip_dst: source IP address
		:param flow_label: traffic flow ID
		:param payload_lenght: current packet size
		:param hop_limit: set at maximum (255)
		:returns: ipv6 header
		
		|
		
		"""
		version_tc=600
		flow_label=hex(flow_label)
		flow_label=flow_label[2:]
		version_tc_tf=str(version_tc) + str(flow_label)
		version_tc_tf= bytearray.fromhex(version_tc_tf)
		
		payload_length=str(hex(payload_length))
		payload_length=payload_length[2:]
		
		if(len(payload_length)==2):
			payload_length=("{}"+payload_length).format("00")
		elif(len(payload_length)==3):
			payload_length=("{}"+payload_length).format("0")
		elif(len(payload_length)==4):
			payload_length=(+payload_length)
		payload_length= bytearray.fromhex(payload_length)
		
		next_header=0x11					#UDP in hex=11
		
		ip_dst=binascii.unhexlify(ip_dst.replace(':', ''))
		
		ip_src=binascii.unhexlify(ip_src.replace(':', ''))
		
		return pack("!4s2sBB16s16s", version_tc_tf, payload_length, next_header, hop_limit, ip_src, ip_dst)

	def checksum_func(self, data):
		"""
		This method calculates the checksum.
		
		:param data: data of which calculate checksum
		:returns: data checksum
		
		|
		
		"""
		checksum = 0
		data_len = len(data)
		if (data_len % 2):
			data_len += 1
			data += pack('!B', 0)
	    
		for i in range(0, data_len, 2):
			w = (data[i] << 8) + (data[i + 1])
			checksum += w

		checksum = (checksum >> 16) + (checksum & 0xFFFF)
		checksum = ~checksum & 0xFFFF
		return checksum

	def udp_pseudoheader(self, ip_src, ip_dst, length):
		"""
		This method builds the UDP pseudo-header, useful to the method 'checksum_func'.
		
		:param ip_src: IPv6 address of host A 
		:param ip_dst: IPv6 address of host B 
		:param lenght: pseudo-header length
		:returns: udp pseudo-header
		
		|
		
		"""
		ip_dst=binascii.unhexlify(ip_dst.replace(':', ''))
		
		ip_src=binascii.unhexlify(ip_src.replace(':', ''))
		
		zero=0x00
		proto=0x11
		
		return pack("!16s16sBBH", ip_src, ip_dst, zero, proto, length )
		
	def udp_header(self, port_src, port_dst, length, checksum):
		"""
		This method builds the UDP header.
		
		:param port_src: source port
		:param port_dst: destination port
		:param length: udp header size
		:param checksum: checksum calculated by the udp_pseudoheader function
		:returns: udp header
		
		|
		
		"""
		return pack ("!4H", port_src, port_dst, length, checksum)
		
	def create_packet(self, eth_dst, eth_src, ip_dst, ip_src, flow_label, hop, port_dst, port_src):
		"""
		All the informations calculated by the other methods is collected to compose the packet.
		
		:param eth_dst: next hop ethernet address
		:param eth_src: source ethernet address
		:param ip_dst: IPv6 address of host B 
		:param ip_src: IPv6 address of host A
		:param flow_label: traffic flow ID
		:param hop: hop limit
		:param port_dst: destination port (host B)
		:param port_src: source port (host A)
		:returns: resulting packet
		
		|
		
		"""
		self.dst_addr=eth_dst
		self.src_addr=eth_src
		self.ip_dst=ip_dst
		self.ip_src=ip_src
		self.flow_label=flow_label
		self.hop_limit=hop
		self.port_dst=port_dst
		self.port_src=port_src
		
		eth_hdr = self.eth_header(self.dst_addr, self.src_addr)
		
		ipv6_hdr = self.ipv6_header(self.ip_dst, self.ip_src, self.flow_label, self.payload_length+8, self.hop_limit) 
		
		cs=0	#checksum
		udp_pseudo=self.udp_pseudoheader(self.ip_src, self.ip_dst, self.payload_length+8)
		udp_hdr = self.udp_header(self.port_dst, self.port_src, self.payload_length+8, cs)
		
		cs = self.checksum_func(udp_pseudo + udp_hdr + self.payload)
		udp_hdr = self.udp_header(self.port_src, self.port_dst, self.payload_length+8, cs)
		
		return eth_hdr + ipv6_hdr + udp_hdr + self.payload

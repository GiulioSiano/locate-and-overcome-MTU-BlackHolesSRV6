#!/usr/bin/env python

from hopLimitFinder import *
from nextHopMTU import *
from socket import *
from location_bottle_neck import *
import ipaddress

#eth fields
dst_addr_eth = '66:55:44:33:77:71'
src_addr_eth = '12:22:33:44:55:66'

#ipv6 fields
dst_addr_ipv6='fc00::2:2'
src_addr_ipv6='fc00::1:2'

dst_addr_ipv6=ipaddress.ip_address( dst_addr_ipv6 )
dst_addr_ipv6=dst_addr_ipv6.exploded

src_addr_ipv6=ipaddress.ip_address( src_addr_ipv6 )
src_addr_ipv6=src_addr_ipv6.exploded
		
flow_label=0
flow_label_maxValue=1048575
dim_data=1000
hop_limit=0
	
#udp fields
src_port=58169
dst_port=33434	

mtu_exit_interface=1300

s = 0

def main():
	"""
	| This script replicates the scamper behaviour calling the following files:
	| To find the hop_limit value: *8_scamper/tracerouting.py*
	| To find the MTU path value: *8_scamper/nextHopMTU.py*
	| To locate the possible bottleneck: *8_scamper/location_bottle_neck.py*
	"""
	ETH_P_ALL = 3
	s = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))
	s.bind(("vethns1", 0))
	s.settimeout(5)
	
	hop_limit=tracerouting(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, dim_data)
	print("hop_limit: " + str(hop_limit))
	
	print("Calculating the MTU...")
	result_mtu =nextHop_MTUSearch(s, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, 255, mtu_exit_interface) #hop_limit=255
	mtu=result_mtu
	print("MTU = " + str(mtu) +" + 40 (IPv6 header) + 8 (UDP header) = " + str(mtu+48))
	
	hop=location_bottle_neck(s, mtu, hop_limit, dst_addr_eth, src_addr_eth, dst_addr_ipv6, src_addr_ipv6, flow_label, dst_port, src_port, mtu_exit_interface)
	if(hop==0):
		print("No bottleneck.")	
	elif(hop!=0):
		print("Bottleneck is at hop: " + str(hop))

if __name__=="__main__" :
	main()

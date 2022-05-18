#!/usr/bin/sudo bash

#Enabling the top-policy for UDP probes
sudo vppctl -s /run/vpp/cli-vppE1.sock classify table del table 0
sudo vppctl -s /run/vpp/cli-vppE2.sock classify table del table 0

sudo vppctl -s /run/vpp/cli-vppE1.sock classify table mask l3 ip6 src dst proto	#proto=next header, 58=ICMPv6, 6=TCP, 17=UDP
sudo vppctl -s /run/vpp/cli-vppE1.sock classify session acl-hit-next 1 table-index 0 match l3 ip6 src fc00::1:2 dst fc00::2:2 proto 17 action set-sr-policy-index 0
sudo vppctl -s /run/vpp/cli-vppE1.sock set interface input acl intfc host-pc1 ip6-table 0

sudo vppctl -s /run/vpp/cli-vppE2.sock classify table mask l3 ip6 src dst proto
sudo vppctl -s /run/vpp/cli-vppE2.sock classify session acl-hit-next 1 table-index 0 match l3 ip6 src fc00::2:2 dst fc00::1:2 proto 17 action set-sr-policy-index 0
sudo vppctl -s /run/vpp/cli-vppE2.sock set interface input acl intfc host-pc2 ip6-table 0

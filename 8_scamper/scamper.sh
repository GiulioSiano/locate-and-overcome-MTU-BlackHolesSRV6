#!/usr/bin/sudo bash
sudo ip netns exec ns1 ethtool -K vethns1 tx off
sudo ip netns exec ns1 python3 8_scamper/scamper.py

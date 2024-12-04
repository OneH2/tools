#!/usr/bin/env bash
if [ "$EUID" -eq 0 ] ;then
	echo "########################################################"
	echo "#######                                         ########"
	echo "####### OneH2 Raspberry Pi 5 Communicator Setup ########"
	echo "#######                                         ########"
	echo "########################################################"
	cd /home/pi/
	rm -r Bookshelf/  Desktop/  Documents/  Downloads/  Music/  Pictures/  Public/  Templates/  Videos/
	cd
	apt update -y && apt upgrade -y
	wait
	if lsusb | grep -q 'Quectel Wireless Solutions';then
		if ls /sys/class/net | grep -q 'usb0';then
			echo 'Quectel Modem already setup'
		else
			/bin/echo -n -e 'AT\r\n' > /dev/ttyUSB2
			sleep 0.5
			/bin/echo -n -e 'AT+QCFG="usbnet",1\r\n' > /dev/ttyUSB2
			sleep 0.5
			/bin/echo -n -e 'AT+CGDCONT=1,"IP","hologram"\r\n' > /dev/ttyUSB2
			sleep 0.5
			/bin/echo -n -e 'AT+CFUN=1,1\r\n' > /dev/ttyUSB2
			sleep 0.5
			echo "Restarting Modem. Please wait..."
			sleep 5
			systemctl daemon-reload
			wait
			sleep 5
		fi
	else
		echo "Quectel Modem not detected, ensure USB is properly seated"
		exit 1
	fi
	printf "dtparam=i2c_arm=on\ndtparam=i2s=on\ndtparam=spi=on\ndtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000\nhdmi_group=2\nhdmi_mode=87\nhdmi_pixel_freq_limit=356000000\nhdmi_timings=1080 0 68 32 100 1080 0 12 4 16 0 0 0 60 0 85500000 0\n" >> /boot/firmware/config.txt
	metric=$(ip route | grep usb0 | sed -n -e '0,/metric/{s/^.*metric \(.*$\)/\1/p}')
	metric=$((metric+1))
	if ! nmcli | grep -q 'connected to wifi_connection';then
		nmcli con modify "preconfigured" con-name "wifi_connection"
		nmcli con mod 'wifi_connection' ipv4.route-metric $metric
		nmcli connection up 'wifi_connection'
		wait
	else
		echo "Wifi connection already configured"
	fi
	metric=$((metric+1))
	if ! nmcli | grep -q 'connected to ethernet_connection';then
		nmcli con modify "Wired connection 1" con-name "ethernet_connection"
		nmcli c mod "ethernet_connection" ipv4.addresses 192.168.2.99/24 ipv4.method manual
		nmcli con mod "ethernet_connection" ipv4.gateway 192.168.2.1
		nmcli con mod "ethernet_connection" ipv4.dns "8.8.8.8,8.8.4.4,192.168.2.1"
		nmcli con mod 'ethernet_connection' ipv4.route-metric $metric
		nmcli c down "ethernet_connection"
		wait
		nmcli c up "ethernet_connection"
		wait
	else
		echo "Ethernet connection already configured"
	fi
	sudo -H -u pi bash -c 'pip3 install minimalmodbus pyModbusTCP --break-system-packages'
	wait

	echo "########################################################"
	echo "#######                                         ########"
	echo "#######            Setup Finished               ########"
	echo "#######            Please Restart               ########"
	echo "########################################################"
else
	echo "Invalid User! User MUST be root, current user is $USER."
	echo "To change user execute: 'sudo su root'"
fi
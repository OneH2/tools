from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import test_bit,set_bit,reset_bit
import sys, time, ctypes,subprocess
import serial, minimalmodbus, optparse, re, json
from collections import OrderedDict

from simple_term_menu import TerminalMenu

def isfloat(num):
	try:
		float(num)
		return True
	except ValueError:
		return False

with open('assets.json') as infile:
	assets = json.load(infile)

parser = optparse.OptionParser()

parser.add_option('-r','--rtu',action="store",type="string",dest='rtu',help ='Specify RTU settings as "<device path>,<baud>,<slave ID>"')
parser.add_option('-t','--tcp',action="store",type="string",dest='tcp',help ='Specify TCP settings as "<ip address>,<port>,<device ID>"')
parser.add_option('-o','--timeout',action="store",type="string",dest='timeout',help ='Specify communication timeout in seconds (Default: 5 sec)',default='5')
parser.add_option('-a','--asset',action="store",type="string",dest='asset',help ='Specify the name of the asset to control. Available: '+str(list(assets.keys())))

(options, args) = parser.parse_args()
if not options.rtu and not options.tcp:
	parser.error('Please select a communication method (-r or -t option is required to begin)')

if options.rtu and options.tcp:
	parser.error('Please select only one communication method at a time')

rtuSettings = []
tcpSettings = []
if not options.asset:
	parser.error("Please specify an asset out of the following list: "+str(list(assets.keys())))
if options.rtu:
	rtuSettings = options.rtu.split(",")
	mbRTU = minimalmodbus.Instrument(rtuSettings[0], int(rtuSettings[2]))
	mbRTU.serial.baudrate = int(rtuSettings[1])         # Baud
	mbRTU.serial.bytesize = 8
	mbRTU.serial.parity   = serial.PARITY_NONE
	mbRTU.serial.stopbits = 1
	mbRTU.serial.timeout  = int(options.timeout)

elif options.tcp:
	tcpSettings = options.tcp.split(",")
	try:
		mbTCP = ModbusClient(host=tcpSettings[0], port=int(tcpSettings[1]), unit_id=int(tcpSettings[2]), timeout=int(options.timeout),auto_open=True)
	except:
		print("Unable to connect to specified modbus TCP server")
		sys.exit()

devices = OrderedDict() 
devices = assets[options.asset]

def main():
	outp = []
	if options.rtu:
		outp = mbRTU.read_registers(0,40,4)
	elif options.tcp:
		outp = mbTCP.read_holding_registers(0,40)

	main_menu_title = "  E200 Simulator\n  Main Menu.\n  Press Q or Esc to quit. \n"
	main_menu_items = []
	main_menu_items.extend(devices.keys())
	main_menu_items.append("Quit")
	main_menu_cursor = "> "
	main_menu_cursor_style = ("fg_red", "bold")
	main_menu_style = ("bg_red", "fg_yellow")
	main_menu_exit = False

	main_menu = TerminalMenu(
		menu_entries=main_menu_items,
		title=main_menu_title,
		menu_cursor=main_menu_cursor,
		menu_cursor_style=main_menu_cursor_style,
		menu_highlight_style=main_menu_style,
		cycle_cursor=True,
		clear_screen=True,
	)
	deviceMenus = []

	for device in devices:
		for dev in devices[device]:
			if device == "DI":
				devices[device][dev][2] = test_bit(outp[devices[device][dev][0]],devices[device][dev][1])
			else:
				if devices[device][dev][1] == 1:
					devices[device][dev][2] = outp[devices[device][dev][0]]
				elif devices[device][dev][1] == 2:
					devices[device][dev][2] = ctypes.c_uint32(0).value 
					devices[device][dev][2] = outp[devices[device][dev][0]+1] << 16
					devices[device][dev][2] |= outp[devices[device][dev][0]]
			
		menu = []
		menu.append(TerminalMenu(
			devices[device].keys(),
			title="  "+device+" Menu.\n  Press Q or Esc to back to main menu. \n",
			menu_cursor=main_menu_cursor,
			menu_cursor_style=main_menu_cursor_style,
			menu_highlight_style=main_menu_style,
			cycle_cursor=True,
			clear_screen=True,
		))
		menu.append(False)
		menu.append(device)
		menu.append(list(devices[device].keys()))
		deviceMenus.append(menu)
	while not main_menu_exit:
			main_sel = main_menu.show()
			if main_sel == len(main_menu_items)-1 or main_sel == None:
				main_menu_exit = True
				print("Quit Selected")
			elif main_sel != None:
				while not deviceMenus[main_sel][1]:
					dev_sel = deviceMenus[main_sel][0].show()
					if dev_sel != None:
						while(1):
							devName = deviceMenus[main_sel][-1][dev_sel]
							devType = deviceMenus[main_sel][-2]
							validate = input("Currently set to "+str(devices[devType][devName][2])+"\nPlease enter new value: ")
							if validate == 'q' or validate == None or validate == "":
								break
							elif devType == "DI" and validate != "0" and validate != "1":
								print("invalid entry, Digital Inputs only take 0 or 1")
							elif isfloat(validate):
								validate = float(validate)
								if options.rtu:
									if devType == "DI":
										if validate:
											di = set_bit(validate,devices[devType][devName][1])
										else:
											di = reset_bit(validate,devices[devType][devName][1])
										mbRTU.write_register(devices[devType][devName][0],di,0,16,True)
									else:
										if devices[devType][devName][1] == 2:
											y = ctypes.c_uint32(validate).value
											tmp = [0,0]
											tmp[0] = int(y & 0x0000FFFF)
											tmp[1] = int((y & 0xFFFF0000) >> 16)
											mbRTU.write_registers(devices[devType][devName][0],tmp)
										else:
											mbRTU.write_register(devices[devType][devName][0],int(validate))
								elif options.tcp:
									if devType == "DI":
										if validate:
											di = set_bit(validate,devices[devType][devName][1])
										else:
											di = reset_bit(validate,devices[devType][devName][1])
										mbTCP.write_single_register(devices[devType][devName][0],di)
									else:
										if devices[devType][devName][1] == 2:
											y = ctypes.c_uint32(validate).value
											tmp = [0,0]
											tmp[0] = int(y & 0x0000FFFF)
											tmp[1] = int((y & 0xFFFF0000) >> 16)
											mbTCP.write_multiple_registers(devices[devType][devName][0],tmp)
										else:
											mbTCP.write_single_register(devices[devType][devName][0],int(validate))
								if devices[devType][devName][1] == 2:
									devices[devType][devName][2] = float(validate)
								else:
									devices[devType][devName][2] = int(validate)
								
								time.sleep(0.25)
								break
							else:
								print("invalid entry")
					else:
						deviceMenus[main_sel][1] = True
				deviceMenus[main_sel][1] = False
				
					


if __name__ == "__main__":
	main()

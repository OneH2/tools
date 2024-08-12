from pyModbusTCP.client import ModbusClient
import time, serial, minimalmodbus, optparse, re,sys, os.path


def valid_IP_Address(sample_str):
	try:
		''' Returns True if given string is a
				valid IP Address, else returns False'''
		result = True
		match_obj = re.search( r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", sample_str)
		if  match_obj is None:
			result = False
		else:
			for value in match_obj.groups():
				if int(value) > 255:
					result = False
					break
	except:
		result = False
	return result
#  0      1       2      3       4     5
#ID/IP,dev/port,baud,dataType,offset,numRegs
def checkList(rawList):
	strList = rawList.split(",")

	#slave id or ip address
	if any(c.isalpha() for c in strList[0]):
		print("letters do not belong in IP/ID Address")
		sys.exit()
	elif "." in strList[0]:
		if not valid_IP_Address(strList[0]):
			print("invalid IP Address")
			sys.exit()
	elif 0 < int(strList[0]) and int(strList[0]) < 247:
		strList[0] = int(strList[0])
	else:
		print("invalid Slave ID")
		sys.exit()
	
	#device path or port number
	if any(c.isalpha() for c in strList[1]):
		if not os.path.exists(strList[1]):
			print("Device path does not exist")
			sys.exit()
	else:
		strList[1] = int(strList[1])

	# baud rate
	if any(c.isalpha() for c in strList[2]):
		print("Invalid Baudrate")
		sys.exit()
	else:
		strList[2] = int(strList[2])
	

	#data type
	strList[3] = int(strList[3])
	if not strList[3] == 1 and not strList[3] == 2 and not strList[3] == 3 and not strList[3] == 4:
		print("Invalid datatype. allowed: [1,2,3,4]")
		sys.exit()
	elif strList[3] == 3:
		strList[3] = 4
	elif strList[3] == 4:
		strList[3] = 3
	
	#offset
	if any(c.isalpha() for c in strList[4]):
		print("Invalid offset")
		sys.exit()
	else:
		strList[4] = int(strList[4])

	return strList


usage = "%prog \n Read format: \"ID/IP,dev/port,baud,dataType,offset,numRegs\"\n Write format: \"ID/IP,dev/port,baud,dataType,offset,data1,data2,...\"\n \
Data Types: 1=Coils, 2=Discrete Registers, 3=Input Registers, 4=Holding Registers\n NOTE: When using TCP, baudrate still needs to be inputted, but will not be used\
	\n EXAMPLE: Reads 10 values from TCP modbus server at offset 30 and pipes it to write those values to an RTU device starting at offset 0\n \
	  python3 modbusPi.py -r \"58.105.200.89,502,0,4,30,10\" -w \"1,/dev/ttyAMA0,9600,4,0\" -p"
parser = optparse.OptionParser(usage=usage)

parser.add_option('-r','--read',action="store",type="string",dest='read',help ='Specify settings of device to read from.')
parser.add_option('-w','--write',action="store",type="string",dest='write',help ='Specify settings of device to write to.')
parser.add_option('-p','--pipe',action="store_true",dest ='pipe',help='Pipe output from read to input for write. Write no longer takes data, just offset')
parser.add_option('-f','--file',action="store",type="string",dest ='fileOp',help='Take read data and write it to given file')
(options, args) = parser.parse_args()
if options.pipe:
	if not options.read or not options.write:
		parser.error('Pipe (-p) option requires BOTH read and write options to be inputted')
if options.fileOp:
	if options.read and options.write:
		parser.error('Please only use file option to read to file OR write from file')
	if not options.read and not options.write:
		parser.error('file option requires either a read or write command to accompany it')

readList = []
writeList = []
trys = 0
while(1):
	try:
		if options.read:
			readList = checkList(options.read)
			#if int(readList[5]) > 124:

			if len(readList) > 6:
				del readList[6:len(readList)]
			readList[5] = int(readList[5])
    
			if(valid_IP_Address(readList[0])):
				readTCP = ModbusClient(host=readList[0], port=readList[1], unit_id=1, auto_open=True)
				if readList[3] == 1:
					outp = readTCP.read_coils(readList[4],readList[5])
				elif readList[3] == 2:
					outp = readTCP.read_discrete_inputs(readList[4],readList[5])
				elif readList[3] == 4:
					outp = readTCP.read_input_registers(readList[4],readList[5])
				elif readList[3] == 3:
					outp = readTCP.read_holding_registers(readList[4],readList[5])
			else:
				readDev = minimalmodbus.Instrument(readList[1], readList[0])  # port name, slave address (in decimal)
				readDev.serial.baudrate = readList[2]         # Baud
				readDev.serial.bytesize = 8
				readDev.serial.parity   = serial.PARITY_NONE
				readDev.serial.stopbits = 1
				readDev.serial.timeout  = 1          # seconds
		
				if readList[3] < 3:
					outp = readDev.read_bits(readList[4],readList[5],readList[3])
				else:
					outp = readDev.read_registers(readList[4],readList[5],readList[3])
		print("Read: ",outp)
		if not options.write and not options.fileOp:
			sys.exit()
    
		if options.fileOp:
			if options.read:
				with open(options.fileOp, 'w+') as fp:
					for item in outp:
						fp.write("%s\n" % item)
				sys.exit()  
			elif options.write:
				with open(options.fileOp) as file:
					for line in file:
						outp.append(line.rstrip())
		
		
			if options.write:
				writeList = checkList(options.write)
			
				if not options.pipe:
					if len(writeList) > 6:
						dataList = []
						for x in range(5,len(writeList)):
							if any(c.isalpha() for c in writeList[x]):
								print("Please convert all string or char data to decimal")
								sys.exit()
							else:
								dataList.append(int(writeList[x]))
								
						writeList[5] = dataList
						del writeList[6:len(writeList)]
					else:
						writeList[5] = int(writeList[5])
				else:
					del writeList[6:len(writeList)]
			
				if(valid_IP_Address(writeList[0])):
					writeTCP = ModbusClient(host=writeList[0], port=writeList[1], unit_id=2, auto_open=True)
					if writeList[3] == 1:
						writeTCP.write_multiple_coils(writeList[4],writeList[5])
					elif writeList[3] == 3:
						writeTCP.write_multiple_registers(writeList[4],writeList[5])
				else:
					writeDev = minimalmodbus.Instrument(writeList[1], writeList[0])  # port name, slave address (in decimal)
					writeDev.serial.baudrate = writeList[2]         # Baud
					writeDev.serial.bytesize = 8
					writeDev.serial.parity   = serial.PARITY_NONE
					writeDev.serial.stopbits = 1
					writeDev.serial.timeout  = 1          # seconds
			
					if writeList[3] == 1:
						if options.pipe or options.fileOp:
							writeDev.write_bits(writeList[4],outp,15)
						else:
							writeDev.write_bits(writeList[4],writeList[5],15)
			
					elif writeList[3] == 3:
						if options.pipe or options.fileOp:
							writeDev.write_registers(writeList[4],outp)
						else:
							writeDev.write_registers(writeList[4],writeList[5])
					else:
						print("unable to write to read only data types")
				sys.exit()
	except minimalmodbus.NoResponseError:
		print("No connection found...")
		if trys > 10:
			print("exiting")
			sys.exit()
		else:
			print("retrying")
			time.sleep(1)
			trys = trys+1
	except minimalmodbus.InvalidResponseError:
		print("incomplete data recieved...")
		if trys > 10:
			print("exiting")
			sys.exit()
		else:
			print("retrying")
			time.sleep(1)
			trys = trys+1
	except KeyboardInterrupt:
		print("manual stop")
		sys.exit()
  

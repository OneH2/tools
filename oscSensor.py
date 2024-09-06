from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import test_bit
import time,numpy,optparse,ctypes

def map_range(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

parser = optparse.OptionParser()

parser.add_option('-I','--ip',action="store",type="string",dest='ip',help ='Set device IP (Default: "58.105.200.89")',default='58.105.200.89')
parser.add_option('-p','--port',action="store",type="string",dest='port',help ='Set device port (Default: 5020)',default='5020')
parser.add_option('-d','--id',action="store",type="string",dest='id',help ='Set device ID (Default: 1)',default='1')
parser.add_option('-r','--register',action="store",type="string",dest='reg',help ='Data register to write to')
parser.add_option('-A','--amplitude',action="store",type="string",dest='amp',help ='Adjust peak amplitude of waveform in Volts (Default:2)',default='2')
parser.add_option('-f','--frequency',action="store",type="string",dest='freq',help ='Adjust frequency of the waveform in cycles/second (Default:0.1)',default='0.1')
parser.add_option('-o','--offset',action="store",type="string",dest='offset',help ='Adjust offset from 0V (Default: 2)',default='2')
parser.add_option('-x','--maximum',action="store",type="string",dest='maximum',help ='Set maximum allowed voltage (Default: 4.5)',default='4.5')
parser.add_option('-n','--minimum',action="store",type="string",dest='minimum',help ='Set minimum allowed voltage (Default: 0)',default='0')
parser.add_option('-L','--interval',action="store",type="string",dest='inter',help ='Interval in seconds of sending data (Default: 0.5)',default='0.5')
parser.add_option('-F','--float',action="store_true",dest='flt',help ='Send data as float (32bits over 2 registers)')
parser.add_option('-v','--verbose',action="store_true",dest='verb',help ='Print out all sent values')
#parser.add_option('-P','--plot',action="store",type="store_true",dest='plotout',help ='Export plot of data being sent every 10 seconds')
(options, args) = parser.parse_args()
if not options.reg:
	parser.error("Please specify the register to write to using the -r option")
xs = []
ys = []
mb = ModbusClient(host=options.ip, port=int(options.port), unit_id=int(options.id), timeout=5,auto_open=True)

timer = time.perf_counter()
try:
	while(1):
		y = float(options.amp)*100*numpy.sin(2 * numpy.pi * float(options.freq) * (time.perf_counter() - timer))+(float(options.offset)*100)
		if y < float(options.maximum)*100 and y > float(options.minimum)*100:
			if options.verb:
				print("{:.2f}".format(y/100)+"V")
			if options.flt:
					y = ctypes.c_uint32(y).value
					tmp = [0,0]
					tmp[0] = int(y & 0x0000FFFF)
					tmp[1] = int((y & 0xFFFF0000) >> 16)
					mb.write_multiple_registers(int(options.reg),tmp)
			else:
				mb.write_single_register(0,int(y))
		time.sleep(float(options.inter))
except KeyboardInterrupt:
	pass

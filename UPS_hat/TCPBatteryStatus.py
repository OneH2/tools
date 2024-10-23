import smbus2
import time, struct,sys
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee
# Config Register (R/W)
_REG_CONFIG								 = 0x00
# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE					 = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE						 = 0x02

# POWER REGISTER (R)
_REG_POWER									= 0x03

# CURRENT REGISTER (R)
_REG_CURRENT								= 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION						= 0x05

RELOAD_ADD = 0x00
RELOAD_KEY = 0xCA

WRITE_INTERVAL_ADD = 0x01
READ_INTERVAL_ADD = 0x03

WRITE_INITIAL_INTERVAL_ADD = 0x05
READ_INITIAL_INTERVAL_ADD = 0x07

RESETS_COUNT_ADD = 0x09
CLEAR_RESET_COUNT_ADD = 0x0b
V_IN_ADD = 0x0c

POWER_OFF_INTERVAL_SET_ADD = 14
POWER_OFF_INTERVAL_GET_ADD = 18
V_BAT_ADD = 22
V_OUT_ADD = 24
TEMP_ADD = 26
CHARGE_STAT_ADD = 27
POWER_OFF_ON_BATTERY_ADD = 28
POWER_SW_USAGE_ADD = 29
POWER_SW_STATUS_ADD = 30



WDT_MAX_POWER_OFF_INTERVAL = 31 * 24 * 3600
class BusVoltageRange:
	"""Constants for ``bus_voltage_range``"""
	RANGE_16V							 = 0x00			# set bus voltage range to 16V
	RANGE_32V							 = 0x01			# set bus voltage range to 32V (default)

class Gain:
	"""Constants for ``gain``"""
	DIV_1_40MV							= 0x00			# shunt prog. gain set to	1, 40 mV range
	DIV_2_80MV							= 0x01			# shunt prog. gain set to /2, 80 mV range
	DIV_4_160MV						 = 0x02			# shunt prog. gain set to /4, 160 mV range
	DIV_8_320MV						 = 0x03			# shunt prog. gain set to /8, 320 mV range

class ADCResolution:
	"""Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
	ADCRES_9BIT_1S					= 0x00			#	9bit,	 1 sample,		 84us
	ADCRES_10BIT_1S				 = 0x01			# 10bit,	 1 sample,		148us
	ADCRES_11BIT_1S				 = 0x02			# 11 bit,	1 sample,		276us
	ADCRES_12BIT_1S				 = 0x03			# 12 bit,	1 sample,		532us
	ADCRES_12BIT_2S				 = 0x09			# 12 bit,	2 samples,	1.06ms
	ADCRES_12BIT_4S				 = 0x0A			# 12 bit,	4 samples,	2.13ms
	ADCRES_12BIT_8S				 = 0x0B			# 12bit,	 8 samples,	4.26ms
	ADCRES_12BIT_16S				= 0x0C			# 12bit,	16 samples,	8.51ms
	ADCRES_12BIT_32S				= 0x0D			# 12bit,	32 samples, 17.02ms
	ADCRES_12BIT_64S				= 0x0E			# 12bit,	64 samples, 34.05ms
	ADCRES_12BIT_128S			 = 0x0F			# 12bit, 128 samples, 68.10ms

class Mode:
	"""Constants for ``mode``"""
	POWERDOW								= 0x00			# power down
	SVOLT_TRIGGERED				 = 0x01			# shunt voltage triggered
	BVOLT_TRIGGERED				 = 0x02			# bus voltage triggered
	SANDBVOLT_TRIGGERED		 = 0x03			# shunt and bus voltage triggered
	ADCOFF									= 0x04			# ADC off
	SVOLT_CONTINUOUS				= 0x05			# shunt voltage continuous
	BVOLT_CONTINUOUS				= 0x06			# bus voltage continuous
	SANDBVOLT_CONTINUOUS		= 0x07			# shunt and bus voltage continuous


class INA219:
	def __init__(self, i2c_bus=1, addr=0x40):
		self.bus = smbus2.SMBus(i2c_bus);
		self.addr = addr

		# Set chip to known config values to start
		self._cal_value = 0
		self._current_lsb = 0
		self._power_lsb = 0
		self.set_calibration_32V_2A()

	def getName(self):
		return 1

	def read(self,address):
		data = self.bus.read_i2c_block_data(self.addr, address, 2)
		return ((data[0] * 256 ) + data[1])

	def write(self,address,data):
		temp = [0,0]
		temp[1] = data & 0xFF
		temp[0] =(data & 0xFF00) >> 8
		self.bus.write_i2c_block_data(self.addr,address,temp)

	def set_calibration_32V_2A(self):
		self._current_lsb = .1	# Current LSB = 100uA per bit
		self._cal_value = 4096
		self._power_lsb = .002	# Power LSB = 2mW per bit

		# Set Calibration register to 'Cal' calculated above
		self.write(_REG_CALIBRATION,self._cal_value)

		# Set Config register to take into account the settings above
		self.bus_voltage_range = BusVoltageRange.RANGE_32V
		self.gain = Gain.DIV_8_320MV
		self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
		self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
		self.mode = Mode.SANDBVOLT_CONTINUOUS
		self.config = self.bus_voltage_range << 13 | \
									self.gain << 11 | \
									self.bus_adc_resolution << 7 | \
									self.shunt_adc_resolution << 3 | \
									self.mode
		self.write(_REG_CONFIG,self.config)

	# def getShuntVoltage_mV(self):
	# 	self.write(_REG_CALIBRATION,self._cal_value)
	# 	value = self.read(_REG_SHUNTVOLTAGE)
	# 	if value > 32767:
	# 			value -= 65535
	# 	return value * 0.01

	def readVoltage(self):
		self.write(_REG_CALIBRATION,self._cal_value)
		self.read(_REG_BUSVOLTAGE)
		return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

	def readCurrent(self):
		value = self.read(_REG_CURRENT)
		if value > 32767:
				value -= 65535
		return (value * self._current_lsb)/1000

	def readPower(self):
		self.write(_REG_CALIBRATION,self._cal_value)
		value = self.read(_REG_POWER)
		if value > 32767:
				value -= 65535
		return value * self._power_lsb

	def readPercentage(self):
		self.write(_REG_CALIBRATION,self._cal_value)
		bus_voltage = (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004
		p = (bus_voltage - 6)/2.4*100
		if(p > 100):p = 100
		if(p < 0):p = 0
		return p

class X729:
	def __init__(self, i2c_bus=1, addr=0x36):
		self.bus = smbus2.SMBus(i2c_bus);
		self.addr = addr
	
	def getName(self):
		return 2

	def readVoltage(self):
		read = self.bus.read_word_data(self.addr, 2)
		swapped = struct.unpack("<H", struct.pack(">H", read))[0]
		voltage = swapped * 1.25 /1000/16
		return voltage

	def readPercentage(self):
		read = self.bus.read_word_data(self.addr, 4)
		swapped = struct.unpack("<H", struct.pack(">H", read))[0]
		capacity = swapped/256
		return capacity

	def readCurrent(self):
		return float(0)
	
	def readPower(self):
		return float(0)

class sequent7:
	def __init__(self,i2c_bus=1,addr=0x30):
		self.bus = smbus2.SMBus(i2c_bus)
		self.addr = addr

	def getName(self):
		return 3

	def readVoltage(self):
		try:
			val = self.bus.read_word_data(self.addr, V_BAT_ADD) / 1000.0
		except Exception as e:
			val = 0
		#self.bus.close()
		return val

	def readCurrent(self):
		return float(0)
	
	def readPower(self):
		return float(0)
	
	def readPercentage(self):
		bus_voltage = (self.bus.read_word_data(self.addr, V_BAT_ADD) / 1000.0)
		p = 123 - (123/pow((1+ pow((bus_voltage/3.7),80)),0.165))
		if(p > 100):p = 100
		if(p < 0):p = 0
		return p
if __name__=='__main__':
	
	def split32(val):
		high = (val >> 16) & 0xFFFF  # extract high 16 bits
		low = val & 0xFFFF  # extract low 16 bits
		return high, low
	try:
		mbTCP = ModbusClient(host="127.0.0.1", port=502, unit_id=200, auto_open=True)
		bus = smbus2.SMBus(1)
		try:
			val = bus.read_byte_data(0x42, 0)
			device = INA219(addr=0x42) #waveshare
		except OSError:
			pass
		try:
			val = bus.read_byte_data(0x36, 0)
			device = X729() #geekworm
		except OSError:
			pass
		try:
			val = bus.read_byte_data(0x30, 0)
			device = sequent7()
		except OSError:
			pass
		bus.close()
		if not device:
			sys.exit(1)
		
		while True:
			voltage = device.readVoltage()					
			current = device.readCurrent()								
			power = device.readPower()
			percentage = device.readPercentage()									
			
			data = []
			data.extend([3,0])
			data.extend(split32(encode_ieee(voltage)))

			data.extend(split32(encode_ieee(current)))

			data.extend(split32(encode_ieee(power)))

			data.extend(split32(encode_ieee(percentage)))

			print(data)
			mbTCP.write_multiple_registers(0,data)
			print("Load Voltage:  {:6.3f} V".format(voltage))
			print("Current:       {:9.6f} A".format(current))
			print("Power:         {:6.3f} W".format(power))
			print("Percent:        {:3.1f}%".format(percentage))
			print("")

			time.sleep(2)
	except Exception as e:
		print(e)
		device.bus.close()

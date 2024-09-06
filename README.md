modbusPi.py -- A tool for reading/writing/piping data from/to/into modbus devices

simulatorControl/simulatorControl.py -- Tool for viewing and modifying simulated sensor values

simulatorControl/assets.json -- json file containing structer for different assets, their devices, and said device's data register names,registers,data types
  NOTE: for analog values: "deviceName":[registerAddress,numberOfRegisters,0]    (ignore last value)
  NOTE: for digital values: "deviceBitName":[<registerAddress>,<bitOffset>,0]    (ignore last value)

oscSensor.py -- A tool for modifying a single simulated sensor (via tcp) into a continuous sine wave


NOTE: ALL tools have an arguments help message, simply run python toolName.py -h

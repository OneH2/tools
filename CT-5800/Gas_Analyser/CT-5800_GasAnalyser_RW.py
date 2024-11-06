from pyModbusTCP.client import ModbusClient
import struct
import time

# Modbus connection settings
GAS_ANALYSER_IP = '10.0.0.10'   # Gas Analyzer IP address
MODBUS_GATEWAY_IP = '127.0.0.1' # Modbus gateway IP address
MODBUS_PORT = 502               # Modbus port
MODBUS_GATEWAY_SLAVE_ID = 202   # Modbus gateway slave ID
MODBUS_START_WRITE_REGISTER = 49# Starting register on the gateway for analog values
NAMUR_WRITE_REG = 89            # Starting Register for storing NAMUR coil states in lower 4 bits
DO_WRITE_REG = 1                # Starting Register for storing all the digital outputs
MODULES_1_WRITE_REG = 93        # Starting Register for storing all the coils under modules
MODULES_2_WRITE_REG = 2000      # Starting Register for storing all the 16 bit Modules registers on the MB Gateway
AO_WRITE_REG = 81               # Starting Register for storing all the 16 bit Analog Output registers on the MB Gateway
DI_WRITE_REG = 2                # Starting Register for storing all the digital inputs on the MB Gateway

# Gas Analyzer register offsets
GAS_ANALYSER_REGISTERS = {
    'CH4 raw': 31203,
    'CH4 compensated': 31205,
    'CH4': 31207,
    'H2O raw': 31209,
    'H2O compensated': 31211,
    'H2O': 31213,
    'CO2 raw': 31215,
    'CO2 compensated': 31217,
    'CO2': 31219,
    'CO raw': 31221,
    'CO raw compensated': 31223,
    'CO': 31225,
    'Gas Temperature': 31103,
    'Cell Temperature': 31105,
    'Internal Temperature': 31107,
    'Pressure': 31109
}

# NAMUR RELAY coil addresses
NAMUR_COILS = {
    'Function check': 16101,       # Bit 0
    'Maintenance required': 16102, # Bit 1
    'Out of specification': 16103, # Bit 2
    'Failed': 16104                # Bit 3
}

# Digital Output coil addresses
DIGITAL_OUTPUTS = {
    'CH_0_DO 0': 7001,
    'CH_1_DO 1': 7002,
    'CH_2_DO 2': 7003,
    'CH_3_DO 3': 7004,
    'CH_4_DO 4': 7005,
    'CH_5_DO 5': 7006
}

#Modules Coil Addresses
MODULES_1 = {
    'Config':19002,
    'Sensor':19003,
    'Laser 1':19004,
    'Laser 2':19005,
    'Laser 3':19006,
    'Laser 4':19007,
    'Path 1':19008,
    'Fit 1/Path 1':19010,
    'Fit 2/Path 1':19011,
    'Fit 3/Path 1':19012,
    'Fit 4/Path 1':19013,
    'DataBase':19018,
    'Modbus TCP':19021,
    'Acromag 4-20mA':19023,
    'Acromag Digital':19024,
    'USB Data Dump':19028,
    'Cell heater':19029,
    'XStream':19032,
    'Moxa Digital 1':19054,
    'Moxa Analog Out 1':19058
}

MODULES_2 = {
    'Config':32102,
    'Sensor':32103,
    'Laser 1':32104,
    'Laser 2':32105,
    'Laser 3':32106,
    'Laser 4':32107,
    'Path 1':32108,
    'Fit 1/Path 1':32110,
    'Fit 2/Path 1':32111,
    'Fit 3/Path 1':32112,
    'Fit 4/Path 1':32113,
    'DataBase':32118,
    'Modbus TCP':32121,
    'Acromag 4-20mA':32123,
    'Acromag Digital':32124,
    'USB Data Dump':32128,
    'Cell heater':32129,
    'XStream':32132,
    'Moxa Digital 1':32154,
    'Moxa Analog Out 1':32158
}

MOXA_ANALOG_OUTPUTS = {
    'AO_1_(4-20mA)':47201,
    'AO_2_(4-20mA)':47202,
    'AO_3_(4-20mA)':47203,
    'AO_4_(4-20mA)':47204,
}

MOXA_DIGITAL_INPUTS = {
    'CH_0_DI_0': 17101,
    'CH_1_DI_1': 17102,
    'CH_2_DI_2': 17103,
    'CH_3_DI_3': 17104,
    'CH_4_DI_4': 17105,
    'CH_5_DI_5': 17106
}

# Initialize Modbus clients for gas analyzer and gateway
gas_analyser_client = ModbusClient(host=GAS_ANALYSER_IP, port=MODBUS_PORT, auto_open=True)
gateway_client = ModbusClient(host=MODBUS_GATEWAY_IP, port=MODBUS_PORT, unit_id=MODBUS_GATEWAY_SLAVE_ID, auto_open=True)

# Function to read from the Modbus device
def read_modbus(register, count=2):
    try:
        response = gas_analyser_client.read_input_registers(register - 30001, count)
        if response and len(response) == count:
            return response
        else:
            print(f"Failed to read register {register}")
            return [0xFFFF, 0xFFFF]  # Default value for failed read
    except Exception as e:
        print(f"Error reading Modbus register {register}: {e}")
        return [0xFFFF, 0xFFFF]

# Function to write to the Modbus device
def write_modbus(register_offset, msb, lsb):
    try:
        # Write both MSB and LSB in one call
        success = gateway_client.write_multiple_registers(register_offset, [msb, lsb])
        if success:
            print(f"Written values: [{msb}, {lsb}] to registers {register_offset} and {register_offset + 1}")
        else:
            print(f"Failed to write to registers {register_offset} and {register_offset + 1}")
    except Exception as e:
        print(f"Error writing Modbus registers {register_offset} and {register_offset + 1}: {e}")

# Function to read from coil registers
def read_coil_register(coil_address):
    try:
        response = gas_analyser_client.read_coils(coil_address - 1, 1)  # Coil addresses are zero-based
        return response[0] if response else 0  # Return 0 if the read fails
    except Exception as e:
        print(f"Error reading coil {coil_address}: {e}")
        return 0

# Function to write to a single 16-bit Modbus register - RAW 89
def write_single_register(register, value):
    try:
        success = gateway_client.write_single_register(register, value)
        if success:
            print(f"Written value: {value} to register {register}")
        else:
            print(f"Failed to write to register {register}")
    except Exception as e:
        print(f"Error writing to register {register}: {e}")

# Function to read from digital output coil registers
def read_digital_outputs(do_address):
    try:
        response = gas_analyser_client.read_coils(do_address - 1, 1)  # Coil addresses are zero-based
        return response[0] if response else 0  # Return 0 if the read fails
    except Exception as e:
        print(f"Error reading coil {do_address}: {e}")
        return 0

# Function to write to a single 16-bit Modbus register - RAW 1
def write_digital_outputs(do_register, value):
    try:
        success = gateway_client.write_single_register(do_register, value)
        if success:
            print(f"Written value: {value} to register {do_register}")
        else:
            print(f"Failed to write to register {do_register}")
    except Exception as e:
        print(f"Error writing to register {do_register}: {e}")

# Function to read from digital output coil registers
def read_modules_1(module_address):
    try:
        response = gas_analyser_client.read_coils(module_address - 1, 1)  # Coil addresses are zero-based
        return response[0] if response else 0  # Return 0 if the read fails
    except Exception as e:
        print(f"Error reading coil {module_address}: {e}")
        return 0

# Function to write to a single 16-bit Modbus register - RAW 1
def write_modules_1(module_register, value):
    try:
        success = gateway_client.write_single_register(module_register, value)
        if success:
            print(f"Written value: {value} to register {module_register}")
        else:
            print(f"Failed to write to register {module_register}")
    except Exception as e:
        print(f"Error writing to register {module_register}: {e}")

# Function to read and write from the 16 bit registers of Gas Analyser Modules to the Modbus gateway
def read_and_write_modules_2_registers():
    module_2_register_offset = MODULES_2_WRITE_REG  # Start writing to this register on the gateway

    for label, register in MODULES_2.items():
        try:
            # Read the 16-bit register from the gas analyzer
            response = gas_analyser_client.read_input_registers(register - 30001, 1)
            if response:
                value = response[0]
                print(f"Read Successful! {label}'s {value} read from gas analyzer's register {register}")

                # Write the value to the gateway's holding register
                success = gateway_client.write_single_register(module_2_register_offset, value)
                if success:
                    print(f"Write Successful! Written value {value} to Modbus gateway register {module_2_register_offset}")
                else:
                    print(f"Failed to write value {value} to Modbus gateway register {module_2_register_offset}")
            else:
                print(f"Failed to read register {register} ({label}) from gas analyzer")

        except Exception as e:
            print(f"Error processing register {register} ({label}): {e}")

        module_2_register_offset += 1

#--------------------------------------------------------------------------------------------------------------------------------

# Function to read and write from the 16 bit registers of Gas Analyser Analog Outputs (4-20mA) to the Modbus gateway
def read_and_write_moxa_analog_outputs():
    ao_register_offset = AO_WRITE_REG  # Start writing to this register on the gateway

    for AO, ao_register in MOXA_ANALOG_OUTPUTS.items():
        try:
            # Read the 16-bit ao_register from the gas analyzer
            response = gas_analyser_client.read_holding_registers(ao_register - 40001, 1)
            if response:
                value = response[0]
                print(f"Read Successful! {AO}'s {value} read from gas analyzer's register {ao_register}")

                # Write the value to the gateway's holding register
                success = gateway_client.write_single_register(ao_register_offset, value)
                if success:
                    print(f"Write Successful! Written value {value} to Modbus gateway register {ao_register_offset}")
                else:
                    print(f"Failed to write value {value} to Modbus gateway register {ao_register_offset}")
            else:
                print(f"Failed to read register {ao_register} ({AO}) from gas analyzer")

        except Exception as e:
            print(f"Error processing register {ao_register} ({AO}): {e}")

        ao_register_offset += 1
#--------------------------------------------------------------------------------------------------------------------------------

# Function to read from digital input coil registers from Gas Analyser
def read_digital_inputs(di_address):
    try:
        response = gas_analyser_client.read_coils(di_address - 1, 1)  # Coil addresses are zero-based
        return response[0] if response else 0  # Return 0 if the read fails
    except Exception as e:
        print(f"Error reading coil {di_address}: {e}")
        return 0

# Function to write digital inputs to a single 16-bit Modbus register - RAW 2
def write_digital_inputs(di_register, value):
    try:
        success = gateway_client.write_single_register(di_register, value)
        if success:
            print(f"Written value: {value} to register {di_register}")
        else:
            print(f"Failed to write to register {di_register}")
    except Exception as e:
        print(f"Error writing to register {di_register}: {e}")

# Function to read, pack, unpack, write, and verify gas data
def read_write_and_verify_gas_data():
    register_offset = MODBUS_START_WRITE_REGISTER
    for gas, register in GAS_ANALYSER_REGISTERS.items():
        # Read 2 consecutive 16-bit registers from gas analyzer
        response = read_modbus(register)

        # Pack and unpack as a float
        if response != [0xFFFF, 0xFFFF]:
            packed_float = struct.pack('>HH', response[0], response[1])
            float_value = struct.unpack('>f', packed_float)[0]
            # Unpack back into two 16-bit integers for writing
            lsb, msb = struct.unpack('>HH', struct.pack('>f', float_value))
        else:
            lsb, msb = 0xFFFF, 0xFFFF  # Default values for failed read

        # Write MSB to register_offset and LSB to register_offset + 1
        write_modbus(register_offset, msb, lsb)

        # Verification read
        verify_response = gateway_client.read_holding_registers(register_offset, 2)
        if verify_response == [msb, lsb]:
            print(f"Verification successful for {gas}: {verify_response}")
        else:
            print(f"Verification failed for {gas}: Expected [{msb}, {lsb}], got {verify_response}")

        # Increment offset for the next value
        register_offset += 2
        print("\n")
#------------------------------------------------------------------------------------------------
# Read and store NAMUR coil states in the lower 4 bits of a 16-bit integer
    coil_states = 0
    for i, (status, coil_address) in enumerate(NAMUR_COILS.items()):
        coil_state = read_coil_register(coil_address)
        print(f"{status}: {coil_state}")
        if coil_state:
            coil_states |= (1 << i)  # Set the corresponding bit if the coil is active

    # Ensure only lower 4 bits are used
    coil_states &= 0x000F  # Mask to retain only the lower 4 bits

    # Write the coil states to a single 16-bit register (register 89)
    write_single_register(NAMUR_WRITE_REG, coil_states)

    # Verification step for NAMUR coil states
    verify_coil_states = gateway_client.read_holding_registers(NAMUR_WRITE_REG, 1)
    if verify_coil_states and verify_coil_states[0] == coil_states:
        print(f"Verification successful for NAMUR coil states : {bin(verify_coil_states[0])}")
    else:
        print(f"Verification failed for NAMUR coil states: Expected {bin(coil_states)}, got {bin(verify_coil_states[0]) if verify_coil_states else 'None'}")
    print("\n")
#------------------------------------------------------------------------------------------------
# Read and store Digital Output coil states in the lower 4 bits of a 16-bit integer
    do_states = 0
    for i, (do_status, do_address) in enumerate(DIGITAL_OUTPUTS.items()):
        do_state = read_digital_outputs(do_address)
        print(f"{do_status}: {do_state}")
        if do_state:
            do_states |= (1 << i)  # Set the corresponding bit if the coil is active

    # Ensure only lower 4 bits are used
    #do_states &= 0x000F

    # Write the coil states to a single 16-bit register (register 89)
    write_digital_outputs(DO_WRITE_REG, do_states)

    # Verification step for NAMUR coil states
    verify_do_states = gateway_client.read_holding_registers(DO_WRITE_REG, 1)
    if verify_do_states and verify_do_states[0] == do_states:
        print(f"Verification successful for Digital Outputs coil states: {bin(verify_do_states[0])}")
    else:
        print(f"Verification failed for Digital Outputs coil states: Expected {bin(do_states)}, got {bin(verify_do_states[0]) if verify_do_states else 'None'}")
    print("\n")
#------------------------------------------------------------------------------------------------
# Read and store modules
    module_states = 0
    for i, (module_status, module_address) in enumerate(MODULES_1.items()):
        module_state = read_modules_1(module_address)
        print(f"{module_status}: {module_state}")
        if module_state:
            module_states |= (1 << i)  # Set the corresponding bit if the coil is active

    # Ensure only lower 4 bits are used
    module_states &= 0xFFFF

    # Write the coil states to a single 16-bit register (register 89)
    write_modules_1(MODULES_1_WRITE_REG, module_states)

    # Verification step
    verify_module_states = gateway_client.read_holding_registers(MODULES_1_WRITE_REG, 1)
    if verify_module_states and verify_module_states[0] == module_states:
        print(f"Verification successful for Diagnostic Modules coil states: {bin(verify_module_states[0])}")
    else:
        print(f"Verification failed for Diagnostic Modules coil states: Expected {bin(module_states)}, got {bin(verify_module_states[0]) if verify_module_states else 'None'}")
    print("\n")
#------------------------------------------------------------------------------------------------
    #Function to read and write 16-bit integer values from Gas Analyser Modules to the Modbus Gateway.
    read_and_write_modules_2_registers()
    print("\n")
#------------------------------------------------------------------------------------------------
    #Function to read and write 16-bit integer values from Gas Analyser Analog Outputs to the Modbus Gateway.
    read_and_write_moxa_analog_outputs()
    print("\n")
#------------------------------------------------------------------------------------------------
# Read and store NAMUR coil states in the lower 4 bits of a 16-bit integer
    di_states = 0
    for i, (di_status, di_address) in enumerate(MOXA_DIGITAL_INPUTS.items()):
        di_state = read_digital_inputs(di_address)
        print(f"{di_status}: {di_state}")
        if di_state:
            di_states |= (1 << i)  # Set the corresponding bit if the coil is active

    # Ensure only lower 4 bits are used
    #di_states &= 0x000F  # Mask to retain only the lower 4 bits

    # Write the coil states to a single 16-bit register (register 89)
    write_single_register(DI_WRITE_REG, di_states)

    # Verification step for NAMUR coil states
    verify_di_states = gateway_client.read_holding_registers(DI_WRITE_REG, 1)
    if verify_di_states and verify_di_states[0] == di_states:
        print(f"Verification successful for Moxa Digital Inputs coil states : {bin(verify_di_states[0])}")
    else:
        print(f"Verification failed for Moxa Digital Inputs coil states: Expected {bin(di_states)}, got {bin(verify_di_states[0]) if verify_di_states else 'None'}")
    print("\n")

#------------------------------------------------------------------------------------------------

# Run the function in a continuous loop with delays
while True:
    read_write_and_verify_gas_data()
    time.sleep(5)  # Delay between each read/write cycle

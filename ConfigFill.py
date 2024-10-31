import re
#NOTE: CONFIG_PARAM_ERROR_ALL is created automatically as a writable bitfield where any write to resets it
#NOTE: CONFIG_PARAM_OP_STATE_ALL, CONFIG_PARAM_RELAYS, and CONFIG_PARAM_INPUTS are automatically created
#NOTE: CONFIG_PARAM_SLAVE_ID, CONFIG_PARAM_PCB_VERSION, CONFIG_PARAM_FIRMWARE_VERSION, CONFIG_PARAM_SERIAL_NUM are automatically created

#variable name:[writable?, errorable?, eeprom?, 0=bitfield / 1=integer / 2=16bit float / 3=32bit float]
asset = "E100"
configVar={ 
"EVO_GAS_PX":[0,1,0,1],
"PSA_PRESS_1_PX":[0,1,0,1],
"PSA_PRESS_2_PX":[0,1,0,1],
"FINAL_GAS_DISCHARGE_PX":[0,1,0,1],
"ACT_1_PX":[0,1,0,1],
"ACT_2_PX":[0,1,0,1],
"PSA_1_PX":[0,1,0,1],
"GAS_SUCTION_PX":[0,1,0,1],
"TC105":[0,1,0,1],
"TC205":[0,1,0,1],
"TC313":[0,1,0,1],
"TC444":[0,1,0,1],
"TC447":[0,1,0,1],
"TC_RPSA1":[0,1,0,1],
"TC_RPSA2":[0,1,0,1],
"TC_SPARE":[0,1,0,1],
"AO_PSA1":[1,0,0,3],
"AO_PSA2":[1,0,0,3],
"AO_FAN":[1,0,0,3],
"AO_EVO":[1,0,0,3],
"EVO_PID_SETPOINT":[1,0,1,3],
"EVO_PID_P":[1,0,1,3],
"EVO_PID_I":[1,0,1,3],
"EVO_PID_D":[1,0,1,3]
}
control_cpp = open("control_"+asset+".cpp","w+")
control_cpp.write('\
void '+asset+'_parameter_check(){\n\
  if ((millis() - paramter_check_timer) > 1000){\n\
')
for var in configVar:
  if configVar[var][1]:
    control_cpp.write('\
    error_check(CONFIG_PARAM_'+var+',CONFIG_PARAM_'+var+'_LOW_LIMIT,CONFIG_PARAM_'+var+'_HIGH_LIMIT,\n\
    CONFIG_PARAM_'+var+'_TIMER,CONFIG_PARAM_'+var+'_TIMEOUT_LOW,CONFIG_PARAM_'+var+'_TIMEOUT_HIGH,\n\
    CONFIG_PARAM_'+var+'_ACTION_CONFIG,CONFIG_PARAM_ERROR_ALL,ERROR_'+var+');\n\
    \n\
')
control_cpp.write('''
    paramter_check_timer = millis();    // Reset the 1s timer
  }
}
''')
control_cpp.close()


config_h = open("config_"+asset+".h", "w+")
config_h.write('\
#if !defined(_CONFIG_'+asset+'_H)\n\
  #define  _CONFIG_'+asset+'_H\n\
  \n\
  #include <stdint.h>\n\
')

config_h.write('''
  typedef union
  {
    float number;
    uint16_t words[2];
    uint8_t bytes[4];
    uint32_t uint_value;
  } FLOATUNION_t;
  #define MSB         16
  #define LSB         0
  #define AS_INT      32\n\n
''')


config_h.write('\t#define CONFIG_PARAM_RELAYS    1\n\n\n\t#define CONFIG_PARAM_INPUTS    3\n\n\n\t#define CONFIG_PARAM_ERROR_ALL     89\n')
errCnt = 0
for var in configVar:
    if configVar[var][1]:
        config_h.write(re.sub(r'(^.*$)',r'\t#define ERROR_\1     '+str(errCnt)+r'\n',var))
        errCnt += 1

config_h.write('\n\n\t#define CONFIG_PARAM_OP_STATE_ALL    91\n\n\n')
setCnt = 2600
ttCnt = 29
ptCnt = 9
aoCnt = 75
otherCnt = 2001
for var in configVar:
    if "TC" in var or "TT" in var:
        valCnt = ttCnt
        ttCnt += 1
    elif "PT" in var or "PX" in var:
        valCnt = ptCnt
        ptCnt += 1
    elif "AO" in var:
        valCnt = aoCnt
        aoCnt += 2
    else:
        valCnt = otherCnt
        otherCnt += 2

    config_h.write(re.sub(r'(^.*$)',r'\t#define  CONFIG_PARAM_\1    '+str(valCnt)+r'\n',var))

config_h.write("\n\n\t#define  CONFIG_PARAM_SLAVE_ID    2051\n\t#define  CONFIG_PARAM_PCB_VERSION    2053\n\t#define  CONFIG_PARAM_FIRMWARE_VERSION    2055\n\t#define  CONFIG_PARAM_SERIAL_NUM    2057\n\n\n")

for var in configVar:
    if configVar[var][1]:
        config_h.write('\t#define CONFIG_PARAM_'+var+'_TIMEOUT_LOW	'+str(setCnt)+'\n')
        config_h.write('\t#define CONFIG_PARAM_'+var+'_TIMEOUT_HIGH	'+str(setCnt+1)+'\n')
        config_h.write('\t#define CONFIG_PARAM_'+var+'_TIMER	'+str(setCnt+2)+'\n')
        config_h.write('\t#define CONFIG_PARAM_'+var+'_LOW_LIMIT	'+str(setCnt+4)+'\n')
        config_h.write('\t#define CONFIG_PARAM_'+var+'_HIGH_LIMIT	'+str(setCnt+6)+'\n')
        config_h.write('\t#define CONFIG_PARAM_'+var+'_ACTION_CONFIG	'+str(setCnt+8)+'\n\n')
        setCnt += 10
config_h.write('''
  void init_config(void);
  float get_config_parameter(int);
  bool test_config_parameter(int, int);
  uint16_t get_config_parameter(int, int);
  void set_config_parameter(int, float);
  void set_config_parameter(int, uint16_t, int);
  void set_config_bit(int, uint16_t, int);
#endif
''')

config_h.close()

config_cpp = open("config_"+asset+".cpp", "w+")

config_cpp.write('\
#include <stdint.h>\n\
#include <Wire.h>\n\
#include "config_'+asset+'.h"\n\
#include "eeprom_'+asset+'.h"\n\
')
config_cpp.write('static FLOATUNION_t slave_id,serial_number,firmware_version,pcb_version,relays,inputs,error_states,operational_states;')
for var in configVar:
    
    config_cpp.write('static FLOATUNION_t ')
    if configVar[var][1]:
        config_cpp.write(re.sub(r'(^.*$)',r'\1,\1_timeout_low, \1_timeout_high, \1_timer, \1_low_limit, \1_high_limit, \1_action_config;\n',var).lower())
    else:
        config_cpp.write(re.sub(r'(^.*$)',r'\1;\n',var).lower())

config_cpp.write('''

void init_config(){
  slave_id.number = 1;    // Default Modbus slave ID number
  serial_number.number = 1;
  firmware_version.number = 0;
  pcb_version.number = 0;
  relays.number = 0;      // Set parameter initial values.
  inputs.number = 0;      // Digital inputs
  error_states.number = 0;
  operational_states.number = 0;
''')
for var in configVar:
    if configVar[var][1]:
        config_cpp.write(re.sub(r'(^.*$)',r'\1.number = -1; \1_timeout_low.number = 0; \1_timeout_high.number = 0; \1_timer.number = 0; \1_low_limit.number = 0; \1_high_limit.number = 0; \1_action_config.number = 0;\n\t',var).lower())
    else:
        config_cpp.write(re.sub(r'(^.*$)',r'\1.number = 0;\n\t',var).lower())

config_cpp.write('\n}\n\nfloat get_config_parameter(int param){\n\tswitch(param){\n')
config_cpp.write('''
    case CONFIG_PARAM_RELAYS:
      return((isnan(relays.number) || relays.number == (float)0xFFFFFFFF)?0:relays.number);
    case CONFIG_PARAM_INPUTS:
      return((isnan(inputs.number) || inputs.number == (float)0xFFFFFFFF)?0:inputs.number);
    case CONFIG_PARAM_ERROR_ALL:
      return((isnan(error_states.number) || error_states.number == (float)0xFFFFFFFF)?0:error_states.number);
    case CONFIG_PARAM_OP_STATE_ALL:
      return((isnan(operational_states.number) || operational_states.number == (float)0xFFFFFFFF)?0:operational_states.number);
''')
for var in configVar:
    lwr = var.lower()
    config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1:\n\t\t\treturn((isnan('+lwr+r'.number) || '+lwr+r'.number == (float)0xFFFFFFFF)?0:'+lwr+r'.number);\n',var))
config_cpp.write('\t\tdefault:\n\t\t\treturn(-1);\n\t}\n}\n\n')

config_cpp.write('''
bool test_config_parameter(int param, int mask){
  switch(param){
    case CONFIG_PARAM_RELAYS:
      return(relays.uint_value & (1 << mask));
    case CONFIG_PARAM_INPUTS:
      return(inputs.uint_value & (1 << mask));
    case CONFIG_PARAM_ERROR_ALL:
      return(error_states.uint_value & (1 << mask));
    case CONFIG_PARAM_OP_STATE_ALL:
      return(operational_states.uint_value & (1 << mask));
''')
for var in configVar:
    if configVar[var][0] and not configVar[var][3]:
        lwr = var.lower()
        config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1:\n\t\t\treturn('+lwr+r'.uint_value & (1 << mask));\n',var))
    elif configVar[var][1]:
        lwr = var.lower()
        config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1_ACTION_CONFIG:\n\t\t\treturn('+lwr+r'_action_config'+r'.uint_value & (1 << mask));\n',var))
config_cpp.write('\t\tdefault:\n\t\t\treturn(0);\n\t}\n}\n\n')

config_cpp.write('''
uint16_t get_config_parameter(int param, int byte_n){
  uint16_t return_param = 0;
  FLOATUNION_t return_float;
  return_float.number = get_config_parameter(param);

  if (byte_n == MSB){
    return_param = return_float.words[0];
  }else if (byte_n == LSB){
    return_param = return_float.words[1];
  }else if (byte_n == AS_INT){    // As int
  return_param =  int(return_float.number);
}
  return(return_param);
}
''')

config_cpp.write('''
void set_config_parameter(int param, float param_value){
  switch(param){
    case CONFIG_PARAM_RELAYS:
      relays.number = param_value;
      break;
    case CONFIG_PARAM_INPUTS:
      inputs.number = param_value;
      break;
    case CONFIG_PARAM_ERROR_ALL:
      error_states.number = 0;  // A write of any sort clears all errors. 
      break;
    case CONFIG_PARAM_OP_STATE_ALL:
      operational_states.number = param_value;
      break;
    case CONFIG_PARAM_SLAVE_ID:
      // Only slave ID numbers between 1 and 254 are valid. All others are to be ignored
      if ((param_value > 0) && (param_value < 255)){
        slave_id.number = param_value;
        // Any change to the SLAVE ID must trigger an EEPROM write, otherwise we may lose track
        eeprom_save();
      }
      break;
    case CONFIG_PARAM_SERIAL_NUM:
      serial_number.number = param_value;
''')
for var in configVar:
    lwr = var.lower()
    config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1:\n\t\t\t'+lwr+r'.number = param_value;\n',var))
    if configVar[var][2]:
        config_cpp.write('\t\t\teeprom_save();\n')
    config_cpp.write('\t\t\tbreak;\n')
    if configVar[var][1]:
                config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1_TIMEOUT_LOW:\n\t\t\t'+lwr+r'_timeout_low.number = param_value;\n\t\t\teeprom_save();\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_TIMEOUT_HIGH:\n\t\t\t'+lwr+r'_timeout_high.number = param_value;\n\t\t\teeprom_save();\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_TIMER:\n\t\t\t'+lwr+r'_timer.number = param_value;\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_LOW_LIMIT:\n\t\t\t'+lwr+r'_low_limit.number = param_value;\n\t\t\teeprom_save();\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_HIGH_LIMIT:\n\t\t\t'+lwr+r'_high_limit.number = param_value;\n\t\t\teeprom_save();\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_ACTION_CONFIG:\n\t\t\t'+lwr+r'_action_config.number = param_value;\n\t\t\teeprom_save();\n\t\t\tbreak;\n',var))
config_cpp.write('\t\tdefault:\n\t\t\tbreak;\n\t}\n}\n\n')

config_cpp.write('''
void set_config_bit(int param, uint16_t param_value, int bit_n){
  switch(param){
    case CONFIG_PARAM_RELAYS:
      if (param_value){
        relays.uint_value |= 1 << bit_n;
      }else{
        relays.uint_value &= ~(1 << bit_n);
      }
      break;
    case CONFIG_PARAM_INPUTS:
      if (param_value){
        inputs.uint_value |= 1 << bit_n;
      }else{
        inputs.uint_value &= ~(1 << bit_n);
      }
      break;
    case CONFIG_PARAM_OP_STATE_ALL:
      if (param_value){
        operational_states.uint_value |= 1 << bit_n;
      }else{
        operational_states.uint_value &= ~(1 << bit_n);
      }
      break;
    case CONFIG_PARAM_ERROR_ALL:
      if (param_value){
        error_states.uint_value |= 1 << bit_n;
      }else{
        error_states.uint_value &= ~(1 << bit_n);
      }
      break;
''')
for var in configVar:
    if configVar[var][1]:
        lwr = var.lower()
        config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1_ACTION_CONFIG:\n\t\t\tif (param_value){\n\t\t\t\t'+lwr+r'_action_config.uint_value |= 1 << bit_n;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_action_config.uint_value &= ~(1 << bit_n);\n\t\t\t}\n\t\t\tbreak;\n',var))
config_cpp.write('\t\tdefault:\n\t\t\tbreak;\n\t}\n}\n\n')

config_cpp.write('''
void set_config_parameter(int param, uint16_t param_value, int byte_n){
  switch(param){
    case CONFIG_PARAM_RELAYS:
      if (byte_n == MSB){
        relays.words[0] = param_value;
      }else{
        relays.words[1] = param_value;
      }
      break;
    case CONFIG_PARAM_INPUTS:
      if (byte_n == MSB){
        inputs.words[0] = param_value;
      }else{
        inputs.words[1] = param_value;
      }
      break;
    case CONFIG_PARAM_OP_STATE_ALL:
      if (byte_n == MSB){
        operational_states.words[0] = param_value;
      }else{
        operational_states.words[1] = param_value;
      }
      break;
    case CONFIG_PARAM_SLAVE_ID:
      if (byte_n == MSB){
        serial_number.words[0] = param_value;
      }else{
        serial_number.words[1] = param_value;
      }
      break;
    case CONFIG_PARAM_SERIAL_NUM:
      if (byte_n == MSB){
        serial_number.words[0] = param_value;
      }else{
        serial_number.words[1] = param_value;
      }
      break;
''')
for var in configVar:
    if configVar[var][0]:
        lwr = var.lower()
        config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n',var))
    if configVar[var][1]:
        lwr = var.lower()
        config_cpp.write(re.sub(r'(^.*$)',r'\t\tcase CONFIG_PARAM_\1_TIMEOUT_LOW:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_timeout_low.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_timeout_low.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_TIMEOUT_HIGH:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_timeout_high.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_timeout_high.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_TIMER:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_timer.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_timer.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_LOW_LIMIT:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_low_limit.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_low_limit.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_HIGH_LIMIT:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_high_limit.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_high_limit.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n\t\tcase CONFIG_PARAM_\1_ACTION_CONFIG:\n\t\t\tif (byte_n == MSB){\n\t\t\t\t'+lwr+r'_action_config.words[0] = param_value;\n\t\t\t}else{\n\t\t\t\t'+lwr+r'_action_config.words[1] = param_value;\n\t\t\t}\n\t\t\tbreak;\n',var))
config_cpp.write('\t\tdefault:\n\t\t\tbreak;\n\t}\n}\n\n')
config_cpp.close()

modbus_h = open("modbus_"+asset+".h", "w+")

modbus_h.write('\
#if !defined(_MODBUS_'+asset+'_H)\n\
  #define  _MODBUS_'+asset+'_H\n\
')
modbus_h.write('''
  #define     TCP_BUFFER                    1 
  #define     RS_485_BUFFER                 2
  #define     BLE_BUFFER                    3
''')
modbus_h.write('''
  #define MODBUS_REG_BUTTONS_RGA                    0
  #define MODBUS_REG_RELAYS                         1
  #define MODBUS_REG_INPUTS                         3 // Digital inputs
  #define MODBUS_REG_ERROR_ALL                      89
  #define MODBUS_REG_OP_STATE_ALL                   91
''')
setCnt = 26
ttCnt = 29
ptCnt = 9
aoCnt = 75
otherCnt = 2001
for var in configVar:
    if "TC" in var or "TT" in var:
        valCnt = ttCnt
        ttCnt += 1
    elif "PT" in var or "PX" in var:
        valCnt = ptCnt
        ptCnt += 1
    elif "AO" in var:
        valCnt = aoCnt
        aoCnt += 2
    else:
        valCnt = otherCnt
        otherCnt += 2

    modbus_h.write(re.sub(r'(^.*$)',r'\t#define  MODBUS_REG_\1    '+str(valCnt)+r'\n',var))

modbus_h.write('''
  #define  MODBUS_REG_SLAVE_ID    2051
  #define  MODBUS_REG_PCB_VERSION    2053
  #define  MODBUS_REG_FIRMWARE_VERSION    2055
  #define  MODBUS_REG_SERIAL_NUM    2057
               

''')
setCnt = 2600
for var in configVar:
    if configVar[var][1]:
        modbus_h.write('\t#define MODBUS_REG_'+var+'_TIMEOUT_LOW	'+str(setCnt)+'\n')
        modbus_h.write('\t#define MODBUS_REG_'+var+'_TIMEOUT_HIGH	'+str(setCnt+1)+'\n')
        modbus_h.write('\t#define MODBUS_REG_'+var+'_TIMER	'+str(setCnt+2)+'\n')
        modbus_h.write('\t#define MODBUS_REG_'+var+'_LOW_LIMIT	'+str(setCnt+4)+'\n')
        modbus_h.write('\t#define MODBUS_REG_'+var+'_HIGH_LIMIT	'+str(setCnt+6)+'\n')
        modbus_h.write('\t#define MODBUS_REG_'+var+'_ACTION_CONFIG	'+str(setCnt+8)+'\n\n')
        setCnt += 10

modbus_h.write('''
  #if defined(HARDWARE_GIGA)
    void modbuxRxData(uint8_t, int);
    int modbus_loop(int);
    int get_tx_bytes(int);
    uint8_t * get_tx_buffer(int);
  #endif
#endif
''')
modbus_h.close()

modbus_cpp = open("modbus_"+asset+".cpp", "w+")

modbus_cpp.write('\
#include <WiFi.h>\n\
#include "modbus_'+asset+'.h"\n\
#include "config_'+asset+'.h"\n\
')
modbus_cpp.write('''
#define TCP_SERIAL_BUFFER_LIMIT       256
#define PACKET_CHECK_ONLY             1
#define PACKET_CRC_INSERT             0
uint8_t TCPSerialBufferRx[TCP_SERIAL_BUFFER_LIMIT];
uint8_t TCPSerialBufferTx[TCP_SERIAL_BUFFER_LIMIT];
uint8_t RSSerialBufferRx[TCP_SERIAL_BUFFER_LIMIT];
uint8_t RSSerialBufferTx[TCP_SERIAL_BUFFER_LIMIT];
uint8_t BLESerialBufferRx[TCP_SERIAL_BUFFER_LIMIT];
uint8_t BLESerialBufferTx[TCP_SERIAL_BUFFER_LIMIT];
int TCPSerialBufferPt = 0; 
int RSSerialBufferPt = 0; 
int BLESerialBufferPt = 0; 
int tcp_tx_bytes = 0;
int rs_tx_bytes = 0;
int ble_tx_bytes = 0;

bool CRC16(uint8_t * packet, int dataLength, char checkElseInsert) //CRC 16 for modbus checksum
{
    unsigned int CheckSum;
    unsigned int j;
    unsigned char lowCRC, highCRC;
    unsigned short i;

    CheckSum = 0xFFFF;
    for (j = 0; j < dataLength; j++)
    {
        CheckSum = CheckSum ^ (unsigned int)packet[j];
        for(i = 8; i > 0; i--)
            if((CheckSum) & 0x0001)
                CheckSum = (CheckSum >> 1) ^ 0xa001;
            else
                CheckSum >>= 1;
    }
    highCRC = (CheckSum >> 8) & 0xFF;
    lowCRC = (CheckSum & 0xFF);

    if (checkElseInsert == 1){
        if ((packet[dataLength+1] == highCRC) & (packet[dataLength] == lowCRC ))
            return 1;
        else
            return 0;
    }else{
        packet[dataLength] = lowCRC;
        packet[dataLength+1] = highCRC;
        return 1;
    }  
}

uint16_t readRegResponse(int i){
  uint16_t reg_response_val = 0;

  switch(i){
    case MODBUS_REG_RELAYS:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_RELAYS, MSB);
      break;
    case MODBUS_REG_RELAYS+1:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_RELAYS, LSB);
      break;
    case MODBUS_REG_INPUTS:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_INPUTS, MSB);
      break;
    case MODBUS_REG_INPUTS+1:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_INPUTS, LSB);
      break;
    case MODBUS_REG_ERROR_ALL:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_ERROR_ALL, MSB);
      break;
    case MODBUS_REG_ERROR_ALL+1:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_ERROR_ALL, LSB);
      break;
    case MODBUS_REG_OP_STATE_ALL:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_OP_STATE_ALL, MSB);
      break;
    case MODBUS_REG_OP_STATE_ALL+1:
      reg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_OP_STATE_ALL, LSB);
      break;
''')
for var in configVar:
    if not configVar[var][3]:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1, MSB);\n\t\t\tbreak;\n\t\tcase MODBUS_REG_\1+1:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1, LSB);\n\t\t\tbreak;\n',var))
    elif configVar[var][3] == 3:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1, LSB);\n\t\t\tbreak;\n\t\tcase MODBUS_REG_\1+1:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1, MSB);\n\t\t\tbreak;\n',var))
    elif configVar[var][3] == 2:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1);\n\t\t\tbreak;\n',var))
    else:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1, AS_INT);\n\t\t\tbreak;\n',var))
    
    if configVar[var][1]:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_TIMEOUT_LOW:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1_TIMEOUT_LOW);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_TIMEOUT_HIGH:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1_TIMEOUT_HIGH);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_TIMER:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1_TIMER);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_LOW_LIMIT:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1_LOW_LIMIT, AS_INT);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_HIGH_LIMIT:\n\t\t\treg_response_val = get_config_parameter(CONFIG_PARAM_\1_HIGH_LIMIT, AS_INT);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_ACTION_CONFIG:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1_ACTION_CONFIG, MSB);\n\t\t\tbreak;\n\t\tcase MODBUS_REG_\1_ACTION_CONFIG+1:\n\t\t\treg_response_val = (uint16_t)get_config_parameter(CONFIG_PARAM_\1_ACTION_CONFIG, LSB);\n\t\t\tbreak;\n',var))  

modbus_cpp.write('''
    case MODBUS_REG_SLAVE_ID:
      reg_response_val = get_config_parameter(CONFIG_PARAM_SLAVE_ID, AS_INT);
      break; 
    case MODBUS_REG_SERIAL_NUM:             // **** 32-bit float
      reg_response_val = get_config_parameter(CONFIG_PARAM_SERIAL_NUM, LSB);
      break;
    case MODBUS_REG_SERIAL_NUM+1:  
      reg_response_val = get_config_parameter(CONFIG_PARAM_SERIAL_NUM, MSB);
      break;
    case MODBUS_REG_PCB_VERSION:
      reg_response_val = 0;
      break;
    case MODBUS_REG_FIRMWARE_VERSION:
      reg_response_val = 0;
      break;

    default:
      break;
  }
  return(reg_response_val);
}

int writeRegResponse(int register_n, int16_t value){
  #if defined(DEBUG_MODE)
    Serial.print(F("Write register: "));
    Serial.print(String(register_n));
    Serial.print(F(", value: "));
    Serial.println(String(value));
  #endif

  switch(register_n){
    // case MODBUS_REG_BUTTONS_RGA:
    //   set_config_parameter(CONFIG_PARAM_OP_STATE_ALL, ((value >> OP_STATE_GREEN_BUTTON) & 0x1), OP_STATE_GREEN_BUTTON); 
    //   set_config_parameter(CONFIG_PARAM_OP_STATE_ALL, ((value >> OP_STATE_AMBER_BUTTON) & 0x1), OP_STATE_AMBER_BUTTON);   // according to Arduino?!??!
    //   set_config_parameter(CONFIG_PARAM_OP_STATE_ALL, ((value >> OP_STATE_RED_BUTTON) & 0x1), OP_STATE_RED_BUTTON);
    //   break;
    case MODBUS_REG_OP_STATE_ALL:
      set_config_parameter(CONFIG_PARAM_OP_STATE_ALL, value, MSB);
      break;
    case MODBUS_REG_OP_STATE_ALL+1:
      set_config_parameter(CONFIG_PARAM_OP_STATE_ALL, value, LSB);
      break;
    case MODBUS_REG_RELAYS:
      set_config_parameter(CONFIG_PARAM_RELAYS, value, MSB);
      break;
    case MODBUS_REG_RELAYS+1:
      set_config_parameter(CONFIG_PARAM_RELAYS, value, LSB);
      break;
    case MODBUS_REG_PCB_VERSION:
      break;
    case MODBUS_REG_FIRMWARE_VERSION:
      break;
    case MODBUS_REG_SLAVE_ID:
      set_config_parameter(CONFIG_PARAM_SLAVE_ID, (float)value);
      break;
    case MODBUS_REG_SERIAL_NUM:
      set_config_parameter(CONFIG_PARAM_SERIAL_NUM, value, LSB);
      break;
    case MODBUS_REG_SERIAL_NUM+1:  
      set_config_parameter(CONFIG_PARAM_SERIAL_NUM, value, MSB);
      break;
    case MODBUS_REG_ERROR_ALL: // A write of any value will clear all errors
      set_config_parameter(CONFIG_PARAM_ERROR_ALL, 0);
      break;
    case MODBUS_REG_ERROR_ALL+1: // A write of any value will clear all errors
      set_config_parameter(CONFIG_PARAM_ERROR_ALL, 0);
      break;
''')

for var in configVar:
    if configVar[var][0]:
        if not configVar[var][0]:
            modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1,value,MSB);\n\t\t\tbreak;\n\t\tcase MODBUS_REG_\1+1:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1,value,LSB);\n\t\t\tbreak;\n',var))
        else:
            modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1,(float)value);\n\t\t\tbreak;\n',var))
    if configVar[var][1]:
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_TIMEOUT_LOW:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_TIMEOUT_LOW,(float)value);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_TIMEOUT_HIGH:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_TIMEOUT_HIGH,(float)value);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_LOW_LIMIT:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_LOW_LIMIT,(float)value);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_HIGH_LIMIT:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_HIGH_LIMIT,(float)value);\n\t\t\tbreak;\n',var))
        modbus_cpp.write(re.sub(r'(^.*$)',r'\t\tcase MODBUS_REG_\1_ACTION_CONFIG:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_ACTION_CONFIG,value,MSB);\n\t\t\tbreak;\n\t\tcase MODBUS_REG_\1_ACTION_CONFIG+1:\n\t\t\tset_config_parameter(CONFIG_PARAM_\1_ACTION_CONFIG,value,LSB);\n\t\t\tbreak;\n',var))

modbus_cpp.write('''
    default:
      break;
  }
}
void modbuxRxData(uint8_t new_byte, int buffer)
{
  int * bufferPtr;

  if (buffer == TCP_BUFFER){
    TCPSerialBufferRx[TCPSerialBufferPt] = new_byte;
    bufferPtr = &TCPSerialBufferPt;
  }else if (buffer == RS_485_BUFFER){
    RSSerialBufferRx[RSSerialBufferPt] = new_byte;
    bufferPtr = &RSSerialBufferPt;
  }else if (buffer == BLE_BUFFER){
    BLESerialBufferRx[BLESerialBufferPt] = new_byte;
    bufferPtr = &BLESerialBufferPt;
  }else{
    #if defined(DEBUG_MODE)
      Serial.print(F("Unknown buffer in modbuxRxData modbus_c200.cpp"));
    #endif
    return;
  }
  // Increment whichever pointer goes with this buffer
  if (*bufferPtr < (TCP_SERIAL_BUFFER_LIMIT - 1)){
    *bufferPtr = *bufferPtr + 1;    // The normal *buggerPtr++ will not work here. For some reason this needs to be explicit!
  }else{
    *bufferPtr = 0;
  }
  return;
}

int get_tx_bytes(int buffer)
{
  int temp_tx_bytes = 0;
  if (buffer == TCP_BUFFER){
    temp_tx_bytes = tcp_tx_bytes;
    tcp_tx_bytes = 0; 
  }else if (buffer == RS_485_BUFFER){
    temp_tx_bytes = rs_tx_bytes;
    rs_tx_bytes = 0; 
  }else if (buffer == BLE_BUFFER){
    temp_tx_bytes = ble_tx_bytes;
    ble_tx_bytes = 0; 
  }else{
    #if defined(DEBUG_MODE)
      Serial.print(F("Unknown buffer in modbus_loop modbus_r050.cpp"));
    #endif
    return(0);
  }

  #if defined(DEBUG_MODE)
    Serial.print(F("Responding with n bytes: "));
    Serial.println(String(temp_tx_bytes));
  #endif
  return(temp_tx_bytes);
}

uint8_t * get_tx_buffer(int buffer)
{
  if (buffer == TCP_BUFFER){
    return(TCPSerialBufferTx);
  }else if (buffer == RS_485_BUFFER){
    return(RSSerialBufferTx);
  }else if (buffer == BLE_BUFFER){
    return(BLESerialBufferTx);
  }else{
    #if defined(DEBUG_MODE)
      Serial.print(F("Unknown buffer in modbus_loop modbus_r050.cpp"));
    #endif
    return(0);
  }
}

// Investigate the buffer for valid MODBUS data and return a response
int modbus_loop(int buffer) {
  int dataLength = 8;   // All register reads are 8 bytes in length. ID, Fn, 2x REGISTER, 2x length req, 2x CRC = 8
  int * bufferPtr;
  uint8_t * processingBufferRx;
  uint8_t * processingBufferTx;
  int * tx_bytes;

  if (buffer == TCP_BUFFER){
    processingBufferRx = &TCPSerialBufferRx[0];
    processingBufferTx = &TCPSerialBufferTx[0];
    bufferPtr = &TCPSerialBufferPt;
    tx_bytes = &tcp_tx_bytes;
  }else if (buffer == RS_485_BUFFER){
    processingBufferRx = &RSSerialBufferRx[0];
    processingBufferTx = &RSSerialBufferTx[0];
    bufferPtr = &RSSerialBufferPt;
    tx_bytes = &rs_tx_bytes;
  }else if (buffer == BLE_BUFFER){
    processingBufferRx = &BLESerialBufferRx[0];
    processingBufferTx = &BLESerialBufferTx[0];
    bufferPtr = &BLESerialBufferPt;
    tx_bytes = &ble_tx_bytes;
  }else{
    #if defined(DEBUG_MODE)
      Serial.print(F("Unknown buffer in modbus_loop modbus_c200.cpp"));
    #endif
    return(0);
  }
  
  for(int i = 0; i < (TCP_SERIAL_BUFFER_LIMIT - dataLength); i++){  // Look through the entire buffer
    // EXCEPTION! On BLE the connection can only be 1:1 and therefore just work whatever the slave ID is!
    if (buffer != BLE_BUFFER){
      // For faster processing, don't bother doing anything unless the first byte under investigation is at least
      // the MOSBUS slave ID
      if (processingBufferRx[i] != get_config_parameter(CONFIG_PARAM_SLAVE_ID, AS_INT)){
        continue; 
      }
    }

    int requestID = processingBufferRx[i]; // The ID in the packet from the master
    int functionCode = processingBufferRx[i+1]; // The function code. 
    int nRegisters = (processingBufferRx[i+4] << 8) | processingBufferRx[i+5];   // How many registers to read?
    int functionRegister = (processingBufferRx[i+2] << 8) | processingBufferRx[i+3];   // MB Register

    // The data length will depend on the function code we are operating with at this time
    if ((functionCode == 3) || (functionCode == 6)){
      dataLength = 6;   // All register reads are 8 bytes in length. ID, Fn, 2x REGISTER, 2x length req, 2x CRC = 8
    }else if (functionCode == 16){
      dataLength = 7 + (2*nRegisters);  // Total length 9 + 2*nR, however we do not include the CRC in the data length
    }
''')
modbus_cpp.write('''

    if (i <= (TCP_SERIAL_BUFFER_LIMIT - dataLength)){         // If we have the entire packet
      if(CRC16(&processingBufferRx[i], dataLength, PACKET_CHECK_ONLY)){        // CRC Checking    
        // The tx buffer can only handle 255 bytes. So limit the number of registers we are allowed to read to a MAX 100
        if (nRegisters > 100){
            // Now that this packet has been processed - and is not valid for this device! We can destroy it so that it will not be processed again
            processingBufferRx[i] = 0;    // Wipe the RTU ID 
            processingBufferRx[i+1] = 0;  // Wipte the function code
            TCPSerialBufferPt = 0;   // We can return the pointer to the beginning of the buffer since a valid packet has been detected
            #if defined(DEBUG_MODE)
              Serial.println(F("Unable to return more than 100 registers at once"));
            #endif
        }else{ //  if (requestID == SLAVE_ID){ We already know this is true from above 
          if (functionCode == 3){
            int index = 0;    // Index the number of registers returned
            
            processingBufferTx[0] = requestID;    // Slave ID
            processingBufferTx[1] = 3;    // Function code
            processingBufferTx[2] = 2 * nRegisters;    // Number of bytes being returned
            
            for (int j = nRegisters; j > 0; j--){
              uint16_t modbus_response_val = readRegResponse(functionRegister++);
              processingBufferTx[3+index] = (uint8_t)((modbus_response_val >> 8) & 0xFF);    // MSB data being returned
              processingBufferTx[4+index] = (uint8_t)(modbus_response_val & 0xFF);    // LSB data being returned, byte only 
              index = index + 2;  // Increment to the next point in the buffer where the register response will be stored for sending
            }
            // The data length is 3 (ID, FN, Length) + 2 bytes for every register!
            CRC16(processingBufferTx, (3 + (2*nRegisters)), PACKET_CRC_INSERT); // Insert the CRC
            
            // Finally, send the data
            //SerialBT.write(TCPSerialBufferTx, 7);  // Respond to the MODBUS request by sending data out of the BT Serial port
            *tx_bytes = 5 + (2 * nRegisters);
          }else if(functionCode == 16){
            int16_t value_n = (processingBufferRx[i+7] << 8) | processingBufferRx[i+8];   // MB Register
            Serial.print(F("Function code 16 CRC Pass for nRegisters = "));
            Serial.println(nRegisters);            
            
            processingBufferTx[0] = requestID;    // Slave ID
            processingBufferTx[1] = 16;    // Function code
            processingBufferTx[2] = processingBufferRx[i+2];    // MB register MSB
            processingBufferTx[3] = processingBufferRx[i+3];   // MB Register LSB
            processingBufferTx[4] = processingBufferRx[i+4];    // n registers MSB
            processingBufferTx[5] = processingBufferRx[i+5];    // n registers LSB
            CRC16(processingBufferTx, 6, PACKET_CRC_INSERT); // Insert the CRC

            while(nRegisters > 0){
              writeRegResponse(functionRegister, value_n);    // Write the value
              nRegisters--;   // Remove one from the number of registers we need to process
              functionRegister++;   // Move to the next function register to be written
              i = i + 2;    // Move our buffer indexing to the next word (below) that will be written
              value_n = (processingBufferRx[i+7] << 8) | processingBufferRx[i+8];   // Next value to be written
            }

            // Finally, send the data
            //SerialBT.write(TCPSerialBufferTx, 7);  // Respond to the MODBUS request by sending data out of the BT Serial port
            *tx_bytes = 8;
          }else{   // End if read holding registers
            // Unsupported function code
            Serial.print(F("Unsupported function code: "));
            Serial.println(String(functionCode));
          }// End if test function code
          // Wipe the data bytes just processed in the buffer to avoid double processing
          memset(processingBufferRx, '\0', TCP_SERIAL_BUFFER_LIMIT);    // We know that dataLength is safe because it was tested above
          *bufferPtr = 0; // Reset the buffer data pointer to the beginning of the buffer
        } // End if slave ID matches our own
      } // end CRC checking
    }
  } // End buffer itteration
  return(*tx_bytes);
}

''')

eeprom_h = open("eeprom_"+asset+".h", "w+")

eeprom_h.write('''
/*
   Author: Christopher Glanville
   EEPROM_XX00.h configuration header file. To acompany usb_XX00.cpp
   Date: 9/6/24
   updated : 9/6/24
*/
''')
eeprom_h.write('\
#if !defined(_EEPROM_'+asset+'_H)\n\
  #define _EEPROM_'+asset+'_H\n\
\n\
  void eeprom_setup(void);\n\
  void eeprom_save(void);\n\
\n\
#endif\n\
')
eeprom_h.close()

eeprom_cpp = open("eeprom_"+asset+".cpp", "w+")

eeprom_cpp.write('\
#include <SPI.h>\n\
#include <Adafruit_SPIFlash.h>\n\
#include "config_'+asset+'.h"\n\
#include "eeprom_'+asset+'.h"\n\
')
eeprom_cpp.write('''



// Addresses up from 0-999 saved for future use of more generic data 
#define PAGE_SIZE 256

// Define the chip select pin
#define CS_PIN 10

// Create an Adafruit_SPIFlash object with SPI1
Adafruit_FlashTransport_SPI flashTransport(CS_PIN, SPI1);
Adafruit_SPIFlash flash(&flashTransport);

bool eeprom_online = false;

void printUniqueID();
void eeprom_setup();
void read_eeprom(uint32_t address);
void read_parameters(uint8_t* dataRead);
void eeprom_save();
void write_eeprom(uint32_t address, uint8_t* dataToWrite, int length);


void printUniqueID() {
  uint8_t uniqueID[8];

  digitalWrite(CS_PIN, LOW);
  SPI1.transfer(0x4B); // Unique ID read command
  for (int i = 0; i < 4; i++) {
    SPI1.transfer(0x00); // Send dummy bytes
  }
  for (int i = 0; i < 8; i++) {
    uniqueID[i] = SPI1.transfer(0x00); // Read Unique ID
  }
  digitalWrite(CS_PIN, HIGH);

  for (int i = 0; i < 8; i++) {
    if (uniqueID[i] < 0x10) Serial.print("0"); // Leading zero for single hex digits
    Serial.print(uniqueID[i], HEX);
    if (i < 7) {
      Serial.print(":");
    }
  }
  Serial.println();
}

void eeprom_setup(void) {
  // Initialize SPI1
  SPI1.begin();

  if (flash.begin()) {
    const uint32_t startAddress = 0x000000;  // Starting address in EEPROM
    Serial.println("SPIFlash library initialized.");

    // Print JEDEC ID
    uint32_t jedecID = flash.getJEDECID();
    Serial.print("JEDEC ID: 0x");
    Serial.println(jedecID, HEX);

    // Print Unique ID using raw SPI commands
    Serial.print("Unique ID: ");
    printUniqueID();

    // Dummy data to write if 0xFF is found
    uint8_t dataRead[PAGE_SIZE * 5];
    bool foundDummy = true;

    // Read data from EEPROM
    read_eeprom(startAddress);
  
    
    // Unblock future writes to the EEPROM
    eeprom_online = true;
  } else {
    Serial.println("Failed to initialize SPIFlash library.");
  }
}

void read_eeprom(uint32_t address) {
  uint8_t dataRead[PAGE_SIZE * 5];
  if (flash.readBuffer(address, dataRead, sizeof(dataRead))) {
    Serial.print("Read Data: ");
    for (int i = 0; i < sizeof(dataRead); i++) {
      Serial.print(dataRead[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    // Read individual parameters
    read_parameters(dataRead);
  } else {
    Serial.println("Failed to read data.");
  }
}

void read_parameters(uint8_t* dataRead) {
  FLOATUNION_t read_config_var;
  int offset = 0;


  //****Safety and Error setpoints*****//
''')
for var in configVar:
    if configVar[var][2]:
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+',read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n\n')
    if configVar[var][1]:
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+'_TIMEOUT_LOW,read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+'_TIMEOUT_HIGH,read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+'_LOW_LIMIT,read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+'_HIGH_LIMIT,read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tmemcpy(read_config_var.bytes, &dataRead[offset], 4);\n')
        eeprom_cpp.write('\tset_config_parameter(CONFIG_PARAM_'+var+'_ACTION_CONFIG,read_config_var.number);\n')
        eeprom_cpp.write('\toffset += 4;\n\n')

eeprom_cpp.write('''

  //PCB VERSION
  memcpy(read_config_var.bytes, &dataRead[offset], 4);
  set_config_parameter(CONFIG_PARAM_PCB_VERSION,read_config_var.number);
  offset += 4;
  
  //FRIMWARE VERSION
  memcpy(read_config_var.bytes, &dataRead[offset], 4);
  set_config_parameter(CONFIG_PARAM_FIRMWARE_VERSION,read_config_var.number);
  offset += 4;
  
  //SERIAL NUMBER
  memcpy(read_config_var.bytes, &dataRead[offset], 4);
  set_config_parameter(CONFIG_PARAM_SERIAL_NUM,read_config_var.number);
  offset += 4;

  //SLAVE_ID
  memcpy(read_config_var.bytes, &dataRead[offset], 4);
  // Only slave ID numbers between 1 and 254 are valid. All others are to be ignored
  if ((read_config_var.number > 0) && (read_config_var.number < 255)){
  set_config_parameter(CONFIG_PARAM_SLAVE_ID, read_config_var.number);
  }else{
  Serial.println("Invalid Modbus ID read from EEPROM. Disregarding.");  
  Serial.println(read_config_var.number);  
  }

  Serial.println("EEPROM read_parameters completed");
  
}




void eeprom_save(void) {
  const uint32_t startAddress = 0x000000;  // Starting address in EEPROM
  uint8_t dataToWrite[PAGE_SIZE * 5];  // Assuming you might need up to six pages

  
  int offset = 0;
  FLOATUNION_t save_config_var;


  //****Safety and Error setpoints*****//
''')

for var in configVar:
    if configVar[var][2]:
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+');\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n\n')
    if configVar[var][1]:
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+'_TIMEOUT_LOW);\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+'_TIMEOUT_HIGH);\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+'_LOW_LIMIT);\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+'_HIGH_LIMIT);\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n')
        eeprom_cpp.write('\tsave_config_var.number = get_config_parameter(CONFIG_PARAM_'+var+'_ACTION_CONFIG);\n')
        eeprom_cpp.write('\tmemcpy(&dataToWrite[offset], save_config_var.bytes, 4);\n')
        eeprom_cpp.write('\toffset += 4;\n\n')

eeprom_cpp.write('''

  //PCB VERSION
  save_config_var.number = get_config_parameter(CONFIG_PARAM_PCB_VERSION);
  memcpy(&dataToWrite[offset], save_config_var.bytes, 4);
  offset += 4;

  //FRIMWARE VERSION
  save_config_var.number = get_config_parameter(CONFIG_PARAM_FIRMWARE_VERSION);
  memcpy(&dataToWrite[offset], save_config_var.bytes, 4);
  offset += 4;

  //SERIAL NUMBER
  save_config_var.number = get_config_parameter(CONFIG_PARAM_SERIAL_NUM);
  memcpy(&dataToWrite[offset], save_config_var.bytes, 4);
  offset += 4;

  //SLAVE_ID
  save_config_var.number = get_config_parameter(CONFIG_PARAM_SLAVE_ID);
  memcpy(&dataToWrite[offset], save_config_var.bytes, 4);



  // Erase and write data to EEPROM
  write_eeprom(startAddress, dataToWrite, offset);
}


void write_eeprom(uint32_t address, uint8_t* dataToWrite, int length) {
  int remainingBytes = length;
  int currentAddress = address;
  int bytesToWrite = min(PAGE_SIZE - (currentAddress % PAGE_SIZE), remainingBytes);

  if (flash.eraseSector(currentAddress)) {
    
    // Write data to EEPROM
    if (flash.writeBuffer(currentAddress, dataToWrite, bytesToWrite)) {

      // Read data from EEPROM to verify
      uint8_t dataRead[PAGE_SIZE * 5];
      if (flash.readBuffer(currentAddress, dataRead, bytesToWrite)) {
        for (int i = 0; i < bytesToWrite; i++) {
        }
       
      } else {
        Serial.println("Failed to read data.");
      }
    } else {
      Serial.println("Failed to write data.");
    }
  } else {
    Serial.println("Failed to erase sector.");
  }

  currentAddress += bytesToWrite;    // Increment the current address by the number of bytes written
  remainingBytes -= bytesToWrite;    // Decrement the remaining bytes to write

  if (remainingBytes > 0) {
    write_eeprom(currentAddress, dataToWrite + bytesToWrite, remainingBytes);
  }
}
''')

eeprom_cpp.close()

wifi_cpp = open("wifi_"+asset+".cpp", "w+")
wifi_cpp.write('''
/*
   Author: Christopher Glanville
   C200 Compressor function
   Date: 14/2/24
   updated : 14/2/24
   Updates to be added (Front end app to send all data) and setting set points
*/
''')
wifi_cpp.write('\
#include <SPI.h>\n\
#include <WiFi.h>\n\
#include <ADS7828.h>\n\
#include "'+asset+'.h"\n\
#include "modbus_'+asset+'.h"\n\
')
wifi_cpp.write('''
#define   MAX_WIFI_CONNECT_RETRIES      5

#if defined(HARDWARE_GIGA)
// WiFi SSID and Password
char ssid[] = "One H 2";              // your network SSID (name)
char pass[] = "HGmLBJvC3QKCcb7j";     // your network password (use for WPA, or use as key for WEP)
int status = WL_IDLE_STATUS;          // the WiFi radio's status

WiFiServer server(502);               // MODBUS Server port
boolean alreadyConnected = false;     // whether or not the client was connected previously

unsigned long wiFiSocketDataTiming = 0;

/*
    Name:         printMacAddress
    Arguments:    uint8_t*    A byte poiner to the 4 mac address bytes 
    Returns:      void        
    Description:  For simple diagnostics it is sometimes useful to know the MAC address of the radio module as it can be used in some network routers 
                  for NAT and DHCP configurations. 
*/
void printMacAddress(byte mac[]) {
  for (int i = 5; i >= 0; i--) {
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
    if (i > 0) {
      Serial.print(":");
    }
  }
  Serial.println();
}

/*
    Name:         printCurrentNet
    Arguments:    void
    Returns:      nil        
    Description:  Print the details of the current WiFi network we are attached to. 
*/
void printCurrentNet() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print the MAC address of the router you're attached to:
  byte bssid[6];
  WiFi.BSSID(bssid);
  Serial.print("BSSID: ");
  printMacAddress(bssid);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.println(rssi);

  // print the encryption type:
  byte encryption = WiFi.encryptionType();
  Serial.print("Encryption Type:");
  Serial.println(encryption, HEX);
  Serial.println();
}

/*
    Name:         printEncryptionType
    Arguments:    void
    Returns:      nil        
    Description:  Print the encryption details of the current WiFi network we are attached to. 
*/
void printEncryptionType(int thisType) {
  // read the encryption type and print out the name:
  switch (thisType) {
    case ENC_TYPE_WEP:
      Serial.println("WEP");
      break;
    case ENC_TYPE_TKIP:
      Serial.println("WPA");
      break;
    case ENC_TYPE_CCMP:
      Serial.println("WPA2");
      break;
    case ENC_TYPE_NONE:
      Serial.println("None");
      break;
    case ENC_TYPE_AUTO:
      Serial.println("Auto");
      break;
    case ENC_TYPE_UNKNOWN:
    default:
      Serial.println("Unknown");
      break;
  }
}

/*
    Name:         listNetworks
    Arguments:    void
    Returns:      nil        
    Description:  Print the details of the networks that have been discovered
*/
void listNetworks() {
  // scan for nearby networks:
  Serial.println("** Scan Networks **");
  int numSsid = WiFi.scanNetworks();
  if (numSsid == -1) {
    Serial.println("Couldn't get a WiFi connection");
    return;
  }

  // print the list of networks seen:
  Serial.print("number of available networks:");
  Serial.println(numSsid);

  // print the network number and name for each network found:
  for (int thisNet = 0; thisNet < numSsid; thisNet++) {
    Serial.print(thisNet);
    Serial.print(") ");
    Serial.print(WiFi.SSID(thisNet));
    Serial.print("\tSignal: ");
    Serial.print(WiFi.RSSI(thisNet));
    Serial.print(" dBm");
    Serial.print("\tEncryption: ");
    printEncryptionType(WiFi.encryptionType(thisNet));
  }
}

/*
    Name:         printWifiData
    Arguments:    void
    Returns:      nil        
    Description:  For simple diagnostics print the IP address that was assigned during DHCP
*/
void printWifiData() {
  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  Serial.println(ip);

  // print your MAC address:
  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC address: ");
  printMacAddress(mac);
}

/*
    Name:         wifi_init
    Arguments:    void
    Returns:      nil
    Description:  Initialize the radio module for WiFi and look for a known SSID that we might be able to connect with
*/
void wifi_init() {
  int attempt = 0;

  #if defined(DEBUG_MODE)
    Serial.println("Scanning available networks...");
    listNetworks();
  #endif

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    return;
  }

  // attempt to connect to WiFi network:
  while ((status != WL_CONNECTED) && (attempt < MAX_WIFI_CONNECT_RETRIES)) {
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network:
    status = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(10000);
    attempt++;    // Increment the attempt number so that we don't block here if no WiFi is available. 
  }

  if (attempt >= MAX_WIFI_CONNECT_RETRIES){
    Serial.println("Failed to connect to the WiFi network");
  }else{
    // you're connected now, so print out the data:
    Serial.print("You're connected to the network");
    printCurrentNet();
    printWifiData();

    // start the server:
    server.begin();
  }
  return;
}

void wifi_loop()
{
  WiFiClient client = server.available();   // This connection status will presist, even when the returned client object goes out of scope
  
  // Check to see if the client is valid
  while (client) {
    if (!alreadyConnected) {
      // clear out the input buffer:
      client.flush();
      Serial.println("We have a new client");
      alreadyConnected = true;
      wiFiSocketDataTiming = millis();    // Reset the timer on connection, otherwise it will be immediatly disconnected if t>15s
    }

    while(client.available() > 0){
      wiFiSocketDataTiming = millis();    // Reset the timeout timer every time new data is received on the socket
      // read the bytes incoming from the client, and add them to the MODBUS processing buffer
      char thisChar = client.read();
      modbuxRxData(thisChar, TCP_BUFFER);
      
      #if defined(DEBUG_MODE)
        // echo the bytes to the server as well:
        Serial.write(thisChar);
      #endif
    }
    // Process the buffer for any new incoming packets

    if (modbus_loop(TCP_BUFFER)){ 
      int tx_bytes = get_tx_bytes(TCP_BUFFER);
      client.write(get_tx_buffer(TCP_BUFFER), tx_bytes);

      #if defined(DEBUG_MODE)
        Serial.write(get_tx_buffer(TCP_BUFFER), tx_bytes);
      #endif
    }

    // if the server's disconnected, stop the client:
    if (!client.connected()) {
      Serial.println();
      Serial.println("TCP Client disconnected");
      client.stop();
      alreadyConnected = false;   // Reset ready for the next connection
    // If there is more than 15 seconds since the last data byte was received on the socket, DISCONNECT
    // This is required because Arduino does not handle the socket disconnection well and it can hang for a 
    // very long time which prevents any new connections. By putting this here we can allow a recovery mechanism
    }else if ((millis() - wiFiSocketDataTiming) >= 15000){
      Serial.println();
      Serial.println("TCP Client TIMEOUT disconnected");
      client.stop();
      alreadyConnected = false;   // Reset ready for the next connection
    }
    loop_two();     // FUCKING Arduino!
  }// End while connection loop
  return;   // Return from the WiFi loop - essential to allow for other processing
}

#endif    // if defined HARDWARE_GIGA
''')
wifi_cpp.close()
wifi_h = open("wifi_"+asset+".h", "w+")

wifi_h.write('''
#if defined(HARDWARE_GIGA)

  void wifi_init(void);
  void wifi_loop(void);

#endif
''')
wifi_h.close()
ble_cpp = open("ble_"+asset+".cpp","w+")

ble_cpp.write('\
// Bluetooth headers\n\
#include <ArduinoBLE.h>\n\
\n\
#include "'+asset+'.h"   // Required for loop_two()\n\
#include "modbus_'+asset+'.h"\n\
')
ble_cpp.write('''
// JDY-33
//#define SERVICE_UUID              "0000ffe0-0000-1000-8000-00805f9b3fb"
//#define CHARACTERISTIC_UUID_RX    "0000ffe1-0000-1000-8000-00805f9b34fb"
//#define CHARACTERISTIC_UUID_TX    "0000ffe2-0000-1000-8000-00805f9b34fb"

#define SERVICE_UUID                "49535343-FE7D-4AE5-8FA9-9FAFD205E455"
#define CHARACTERISTIC_UUID_TX      "49535343-1E4D-4BD9-BA61-23C647249616"
#define CHARACTERISTIC_UUID_RX      "49535343-8841-43F4-A8D4-ECBE34729BB3"

BLEService modbusService(SERVICE_UUID); // Bluetooth® Low Energy LED Service

// Bluetooth® Low Energy LED Switch Characteristic - custom 128-bit UUID, read and writable by central
BLECharacteristic modbusCharacteristicRx(CHARACTERISTIC_UUID_RX, BLERead | BLEWrite, 16);
BLEByteCharacteristic modbusCharacteristicTx(CHARACTERISTIC_UUID_TX, BLERead | BLENotify);

unsigned long bleSocketDataTiming = 0;

void ble_init()
{
  // set advertised local name and service UUID:
  BLE.begin();
''')
ble_cpp.write('\
  BLE.setLocalName("'+asset+'");\n\
')
ble_cpp.write('''
  BLE.setAdvertisedService(modbusService);

  // add the characteristic to the service
  modbusService.addCharacteristic(modbusCharacteristicRx);
  modbusService.addCharacteristic(modbusCharacteristicTx);

  // add service
  BLE.addService(modbusService);

  // start advertising
  BLE.advertise();
}

void ble_loop()
{
  // listen for Bluetooth® Low Energy peripherals to connect:
  BLEDevice central = BLE.central();

  // if device is conneced to our peripheral...
  if (central) {
    Serial.print("Connected to central: ");
    // Start the disconnection timeout.
    bleSocketDataTiming = millis();    
    // print the central's MAC address:
    Serial.println(central.address());

     // while the central is still connected to peripheral:
    while (central.connected()) {
      if (modbusCharacteristicRx.written()){     
        uint8_t small_buffer[16]; 
        uint8_t ble_rx_d = modbusCharacteristicRx.readValue(small_buffer, 16);
        Serial.print("BLE Byte RX bytes ");
        Serial.println(ble_rx_d);
        for(int i = 0; i < ble_rx_d; i++){
          modbuxRxData(small_buffer[i], BLE_BUFFER);
        }
      }

      if (modbus_loop(BLE_BUFFER)){
        int tx_bytes = get_tx_bytes(BLE_BUFFER);
        uint8_t * temp_ble_buffer_ptr = get_tx_buffer(BLE_BUFFER);
        Serial.print("BLE Byte TX bytes ");
        Serial.println(tx_bytes);
        for(int i = 0; i < tx_bytes; i++){
          modbusCharacteristicTx.writeValue(temp_ble_buffer_ptr[i]);
        }
        bleSocketDataTiming = millis();    // Reset the timer on connection, otherwise it will be immediatly disconnected if t>15s
      }else if ((millis() - bleSocketDataTiming) >= 15000){
        Serial.println();
        Serial.println("BLE Client TIMEOUT disconnected");
        central.disconnect();
      }
      loop_two();     // FUCKING Arduino!
    }
    Serial.println("Connected BLE disconnected");
  } // end if (central)
}
''')

ble_cpp.close()
ble_h = open("ble_"+asset+".h","w+")

ble_h.write('\
#if !defined(_BLE_'+asset+'_H)\n\
  #define  _BLE_'+asset+'_H\n\
\n\
  void ble_init(void);\n\
  void ble_loop(void);\n\
\n\
#endif\n\
')
ble_h.close()
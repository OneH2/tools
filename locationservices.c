#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <modbus.h>

#define MODBUS_SLAVE_ADDESS 203
#define MODBUS_TCP_PORT_ID 502
#define MODBUS_BUFFER_SIZE 20
#define MODBUS_REGISTER_OFFSET 0

// Function to convert NMEA absolute position to decimal degrees 
float GpsToDecimalDegrees(const char* nmeaPos, const char* quadrant) {
  float v = 0;
  
  if(strlen(nmeaPos) > 5) {
    char integerPart[3+1];
    int digitCount = (nmeaPos[4] == '.' ? 2 : 3);
    memcpy(integerPart, nmeaPos, digitCount);
    integerPart[digitCount] = 0;
    nmeaPos += digitCount;
    v = atoi(integerPart) + atof(nmeaPos) / 60.0;
    if(quadrant[0] == 'W' || quadrant[0] == 'S') {
      v = -v;
    }
  }
  return v;
}

// Function to convert 32-bit float into 16-bit unsigned int MSB & LSB
void floatToTwoUInt16(float floatData, u_int16_t *msb, u_int16_t *lsb) {
  u_int32_t temp;
  memcpy(&temp, &floatData, sizeof(float));
  *msb = (u_int16_t)((temp >> 16) & 0xFFFF);
  *lsb = (u_int16_t)(temp & 0xFFFF);
}

// Function to convert 16-bit unsigned int MSB & LSB to 32-bit float
float twoUInt16ToFloat(u_int16_t msb, u_int16_t lsb) {
  float result;
  u_int32_t temp = ((u_int32_t)msb << 16) | (u_int32_t)lsb;
  memcpy(&result, &temp, sizeof(float));
  return result;
}

int main(void) {
  modbus_t *mb0;
  uint16_t modbusBuffer[MODBUS_BUFFER_SIZE] = {0};
  mb0 = modbus_new_tcp("127.0.0.1", MODBUS_TCP_PORT_ID);
  modbus_set_slave(mb0, MODBUS_SLAVE_ADDESS);
  
  FILE *gpsDevice;
  
  char *token;
  char buffer[100];
  
  char time[15];           // UTC time: hhmmss.sss
  char latitude[15];       // Latitude: ddmm.mmmmm
  char latDirection[15];   // Latitude direction: N=north, S=south
  char longitude[15];      // Longitude: dddmm.mmmmm
  char longDirection[15];  // Longitude direction:  E=east, W=west
  
  char fixQuality[15];     // Fix Quality: 0=invalid, 1=GPS fix, 2=DGPS fix
  char numStatellites[15]; // Number of satellites are in view
  char gpsPrecision[15];   // Relative accuracy of horizontal position
  char elevation[15];      // Meters above mean sea level
  char geoidHeight[15];    // Height of geoid above WGS84 ellipsoid
  
  char trackMadeGoodTrue[15];  // Resultant direction from the point of departure to point of arrival at any given time
  char trackMadeGoodMagnetic[15];
  char speedInKnot[15];    // Speed over ground in knots
  char speedInKmHr[15];    // Speed over ground in kilometers/hour
  
  float latitudeDecimalDegree = 0.0;
  float longitudeDecimalDegree = 0.0;
  float latitudeDecimalDegreeConverted = 0.0;
  float longitudeDecimalDegreeConverted = 0.0;
  
  u_int16_t latitudeMSB = 0;
  u_int16_t latitudeLSB = 0;
  u_int16_t longitudeMSB = 0;
  u_int16_t longitudeLSB = 0;
  u_int16_t precisionMSB = 0;
  u_int16_t precisionLSB = 0;
  u_int16_t elevationMSB = 0;
  u_int16_t elevationLSB = 0;
  u_int16_t trackMadeGoodTrueMSB = 0;
  u_int16_t trackMadeGoodTrueLSB = 0;
  u_int16_t trackMadeGoodMagneticMSB = 0;
  u_int16_t trackMadeGoodMagneticLSB = 0;
  u_int16_t speedInKnotMSB = 0;
  u_int16_t speedInKnotLSB = 0;
  u_int16_t speedInKmHrMSB = 0;
  u_int16_t speedInKmHrLSB = 0;
  
  gpsDevice = fopen("/dev/ttyUSB1", "r");
  
  if(gpsDevice == NULL) {
    perror("Error opening gps device");
    return 1;
  }

  while (fgets(buffer, 100, gpsDevice)) {
    if (buffer[0] != '\0') {
      if (strstr(buffer, "$GPGGA") != NULL) {
      // Split string and store in corresponding variables
      token = strtok(buffer, ",");
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(time, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(latitude, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(latDirection, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(longitude, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(longDirection, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(fixQuality, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(numStatellites, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(gpsPrecision, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(elevation, token);
      
      token = strtok(NULL, ",");
      if (token != NULL) strcpy(geoidHeight, token);
      
      // Convert nmea position and direction to decimal degrees
      latitudeDecimalDegree = GpsToDecimalDegrees(latitude, latDirection);
      longitudeDecimalDegree = GpsToDecimalDegrees(longitude, longDirection);
      
      // Convert decimal degrees float into 16-bit unsigned int MSB and LSB
      floatToTwoUInt16(latitudeDecimalDegree, &latitudeMSB, &latitudeLSB);
      floatToTwoUInt16(longitudeDecimalDegree, &longitudeMSB, &longitudeLSB);
      floatToTwoUInt16(atof(gpsPrecision), &precisionMSB, &precisionLSB);
      floatToTwoUInt16(atof(elevation), &elevationMSB, &elevationLSB);
      
      // Store data in modbus buffer
      modbusBuffer[0] = latitudeMSB;
      modbusBuffer[1] = latitudeLSB;
      modbusBuffer[2] = longitudeMSB;
      modbusBuffer[3] = longitudeLSB;
      modbusBuffer[4] = atoi(fixQuality);
      modbusBuffer[5] = atoi(numStatellites);
      modbusBuffer[6] = precisionMSB;
      modbusBuffer[7] = precisionLSB;
      modbusBuffer[8] = elevationMSB;
      modbusBuffer[9] = elevationLSB;
    }
    else if (strstr(buffer, "$GPVTG") != NULL) {
      token = strtok(buffer, ",");
      
      token = strtok(NULL, ",");
      if(token != NULL) strcpy(trackMadeGoodTrue, token);
      
      token = strtok(NULL, ",");
      
      token = strtok(NULL, ",");
      if(token != NULL) strcpy(trackMadeGoodMagnetic, token);
      
      token = strtok(NULL, ",");
      
      token = strtok(NULL, ",");
      if(token != NULL) strcpy(speedInKnot, token);
      
      token = strtok(NULL, ",");
      
      token = strtok(NULL, ",");
      if(token != NULL) strcpy(speedInKmHr, token);
      
      floatToTwoUInt16(atof(trackMadeGoodTrue), &trackMadeGoodTrueMSB, &trackMadeGoodTrueLSB);
      floatToTwoUInt16(atof(trackMadeGoodMagnetic), &trackMadeGoodMagneticMSB, &trackMadeGoodMagneticLSB);
      floatToTwoUInt16(atof(speedInKnot), &speedInKnotMSB, &speedInKnotLSB);
      floatToTwoUInt16(atof(speedInKmHr), &speedInKmHrMSB, &speedInKmHrLSB);
      
      modbusBuffer[10] = trackMadeGoodTrueMSB;
      modbusBuffer[11] = trackMadeGoodTrueLSB;
      modbusBuffer[12] = trackMadeGoodMagneticMSB;
      modbusBuffer[13] = trackMadeGoodMagneticLSB;
      modbusBuffer[14] = speedInKnotMSB;
      modbusBuffer[15] = speedInKnotLSB;
      modbusBuffer[16] = speedInKmHrMSB;
      modbusBuffer[17] = speedInKmHrLSB;
      }
    }
    
    if (modbus_connect(mb0) == -1) {
      printf("\n100 connection failed: %s", modbus_strerror(errno));
      modbus_free(mb0);
    }
    
    // Write modbus buffer to slave device
    modbus_write_registers(mb0, MODBUS_REGISTER_OFFSET, MODBUS_BUFFER_SIZE, modbusBuffer);
    modbus_close(mb0);
    sleep(1);
  }
  
  fclose(gpsDevice);
  modbus_free(mb0);
  return 0;
}

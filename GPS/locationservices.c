#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <modbus.h>

#define MODBUS_SLAVE_ID 203
#define MODBUS_TCP_PORT 502
#define MODBUS_BUFFER_SIZE 20
#define MODBUS_REGISTER_OFFSET 0

// Changed to true for debug print out
#define DEBUG_PRINT false

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

// Function to convert 32-bit float into 16-bit unsigned int MSB & LSB
void int32ToTwoUInt16(int intData, u_int16_t *msb, u_int16_t *lsb) {
  u_int32_t temp;
  memcpy(&temp, &intData, sizeof(int));
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

int main(int argc, char *argv[]) {
  modbus_t *mb0;
  uint16_t modbusBuffer[MODBUS_BUFFER_SIZE] = {0};
  mb0 = modbus_new_tcp("127.0.0.1", MODBUS_TCP_PORT);
  modbus_set_slave(mb0, MODBUS_SLAVE_ID);
  
  FILE *gpsDevice;
  
  bool gpggaDataUpdated = false;
  bool gpvtgDataUpdated = false;
  
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
  
  u_int16_t timeMSB = 0;
  u_int16_t timeLSB = 0;
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
  
  if (argc > 1){
    printf("Using alternative GPS device: %s\n", argv[1]);
    gpsDevice = fopen(argv[1], "r");
  }else{
    gpsDevice = fopen("/dev/ttyACM1", "r");
  }
  
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
        
        int32ToTwoUInt16(atoi(time), &timeMSB, &timeLSB);
        
        // Store data in modbus buffer
        modbusBuffer[ 0] = latitudeMSB;
        modbusBuffer[ 1] = latitudeLSB;
        modbusBuffer[ 2] = longitudeMSB;
        modbusBuffer[ 3] = longitudeLSB;
        modbusBuffer[ 4] = timeMSB;
        modbusBuffer[ 5] = timeLSB;
        modbusBuffer[ 6] = atoi(fixQuality);
        modbusBuffer[ 7] = atoi(numStatellites);
        modbusBuffer[ 8] = precisionMSB;
        modbusBuffer[ 9] = precisionLSB;
        modbusBuffer[10] = elevationMSB;
        modbusBuffer[11] = elevationLSB;
        
        // Set data update flag to keep track of each loop
        gpggaDataUpdated = true;
      
        if(DEBUG_PRINT) {
          printf("\n***** Degrees and decimal minutes *****\n");
          printf("Latitude: %s (direction: %s)\n", latitude, latDirection);
          printf("Longitude: %s (direction: %s)\n", longitude, longDirection);
          printf("\n***** Decimal degree *****\n");
          printf("Latitude: %f\n", latitudeDecimalDegree);
          printf("Longitude: %f\n", longitudeDecimalDegree);
          printf("\n***** Convert float to MSB and LSB *****\n");
          printf("Latitude MSB: %u\n", latitudeMSB);
          printf("Latitude LSB: %u\n", latitudeLSB);
          printf("Longitude MSB: %u\n", longitudeMSB);
          printf("Longitude LSB: %u\n", longitudeLSB);
          printf("\n***** Other data *****\n");
          printf("Time: %s\n", time);
          printf("Fix quality: %s\n", fixQuality);
          printf("Number of statellites: %s\n", numStatellites);
          printf("GPS precision: %s\n", gpsPrecision);
          printf("Elevation: %s m\n", elevation);
        }
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
        
        modbusBuffer[12] = trackMadeGoodTrueMSB;
        modbusBuffer[13] = trackMadeGoodTrueLSB;
        modbusBuffer[14] = trackMadeGoodMagneticMSB;
        modbusBuffer[15] = trackMadeGoodMagneticLSB;
        modbusBuffer[16] = speedInKnotMSB;
        modbusBuffer[17] = speedInKnotLSB;
        modbusBuffer[18] = speedInKmHrMSB;
        modbusBuffer[19] = speedInKmHrLSB;
        
        gpvtgDataUpdated = true;
        
        if(DEBUG_PRINT) {
          printf("\n***** Direction and speed *****\n");
          printf("Track made good true: %s\n", trackMadeGoodTrue);
          printf("Track made good magnetic: %s\n", trackMadeGoodMagnetic);
          printf("Speed in knots: %s\n", speedInKnot);
          printf("Speed in km/h: %s\n", speedInKmHr);
        }
      }
    
      if (gpggaDataUpdated && gpvtgDataUpdated) {
        // Break loop if modbus connection is bad
        if(modbus_connect(mb0) == -1) {
          printf("\nModbus connection failed: %s", modbus_strerror(errno));
          modbus_free(mb0);
          break;
        }
        else {
          // Write modbus buffer to slave device
          modbus_write_registers(mb0, MODBUS_REGISTER_OFFSET, MODBUS_BUFFER_SIZE, modbusBuffer);
          modbus_close(mb0);
        }
        
        // Reset data update flags
        gpggaDataUpdated = false;
        gpvtgDataUpdated = false;
      }
    }
  }
  
  fclose(gpsDevice);
  modbus_free(mb0);
  return 0;
}

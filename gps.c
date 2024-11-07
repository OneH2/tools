#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

int main() {
  FILE *gpsDevice;
  
  char *token;
  char buffer[100];
  char rawData[100];
  
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
  
  float latitudeDecimalDegree = 0.0;
  float longitudeDecimalDegree = 0.0;
  float latitudeDecimalDegreeConverted = 0.0;
  float longitudeDecimalDegreeConverted = 0.0;
  
  u_int16_t latitudeMSB = 0;
  u_int16_t latitudeLSB = 0;
  u_int16_t longitudeMSB = 0;
  u_int16_t longitudeLSB = 0;
  
  gpsDevice = fopen("/dev/ttyUSB1", "r");
  
  if(gpsDevice == NULL) {
    perror("Error opening gps device");
    return 1;
  }
  
  while(fgets(buffer, 100, gpsDevice)) {
    if(buffer[0] != '\0') {
      if(strstr(buffer, "$GPGGA") != NULL) {
        // Store a copy of original string
        strcpy(rawData, buffer);
        token = strtok(buffer, ",");
        
        // Split string and store in corresponding variables
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(time, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(latitude, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(latDirection, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(longitude, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(longDirection, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(fixQuality, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(numStatellites, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(gpsPrecision, token);

        token = strtok(NULL, ",");
        if(token != NULL) strcpy(elevation, token);
        
        token = strtok(NULL, ",");
        if(token != NULL) strcpy(geoidHeight, token);
        
        // Convert nmea position and direction to decimal degrees
        latitudeDecimalDegree = GpsToDecimalDegrees(latitude, latDirection);
        longitudeDecimalDegree = GpsToDecimalDegrees(longitude, longDirection);
        
        // Convert decimal degrees float into 16-bit unsigned int MSB and LSB
        floatToTwoUInt16(latitudeDecimalDegree, &latitudeMSB, &latitudeLSB);
        floatToTwoUInt16(longitudeDecimalDegree, &longitudeMSB, &longitudeLSB);
        
        // Convert 16-bit unsigned int MSB and LSB back to decimal degrees float
        latitudeDecimalDegreeConverted = twoUInt16ToFloat(latitudeMSB, latitudeLSB);
        longitudeDecimalDegreeConverted = twoUInt16ToFloat(longitudeMSB, longitudeLSB);
        
        printf("\n***** Raw data *****\n");
        printf(rawData);
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
        printf("\n***** Convert MSB & LSB back to float *****\n");
        printf("Latitude converted: %f\n", latitudeDecimalDegreeConverted);
        printf("Longitude converted: %f\n", longitudeDecimalDegreeConverted);
        printf("\n***** Other data *****\n");
        printf("Fix quality: %s\n", fixQuality);
        printf("Number of statellites: %s\n", numStatellites);
        printf("GPS precision: %s\n", gpsPrecision);
        printf("Elevation: %s m\n", elevation);
        printf("\n");
      }
    } 
    else {
      fprintf(stderr, "Empty buffer\n");
    }
  }
  
  fclose(gpsDevice);
  return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <modbus.h>
#include <sys/select.h>

#define SLAVE_ID 203
#define TCP_PORT 502
#define NUM_REGISTERS 20

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
  // Initialize GPS
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
  
  // Initialize Modbus Slave
  modbus_t *ctx;
  modbus_mapping_t *mb_mapping;
  int server_socket;
  int rc;
  uint8_t request[MODBUS_TCP_MAX_ADU_LENGTH];  // Buffer for modbus_receive
  
  // Create Modbus TCP context and mappings
  ctx = modbus_new_tcp("127.0.0.1", TCP_PORT);
  if (ctx == NULL) {
    fprintf(stderr, "Unable to allocate libmodbus context\n");
    return -1;
  }
  modbus_set_slave(ctx, SLAVE_ID);
  mb_mapping = modbus_mapping_new(0, 0, NUM_REGISTERS, 0);
  if (mb_mapping == NULL) {
    fprintf(stderr, "Failed to allocate mapping: %s\n", modbus_strerror(errno));
    modbus_free(ctx);
    return -1;
  }
  
  // Initialize holding registers
  for (int i = 0; i < NUM_REGISTERS; i++) {
    mb_mapping->tab_registers[i] = 0;
  }
  
  // Start listening for incoming connections
  server_socket = modbus_tcp_listen(ctx, 1);
  if (server_socket == -1) {
    fprintf(stderr, "Failed to create server socket\n");
    modbus_mapping_free(mb_mapping);
    modbus_free(ctx);
    return -1;
  }

  // Set up select to monitor the server socket for incoming connections
  fd_set read_fds;
  struct timeval timeout;

  // Check for GPS data
  while (fgets(buffer, 100, gpsDevice)) {
    FD_ZERO(&read_fds);
    FD_SET(server_socket, &read_fds);
    
    // Set timeout value
    timeout.tv_sec = 0;
    timeout.tv_usec = 100000;

    // Use select to wait for a connection or timeout
    int ready = select(server_socket + 1, &read_fds, NULL, NULL, &timeout);
    if (ready > 0) {
      // If the server socket is ready, accept the connection
      if (FD_ISSET(server_socket, &read_fds)) {
        modbus_tcp_accept(ctx, &server_socket);
        
        // Handle a single Modbus request
        rc = modbus_receive(ctx, request);
        
        if (rc > 0) {
          if (request[6] == SLAVE_ID) {
            modbus_reply(ctx, request, rc, mb_mapping);
          } 
        } 
        else if (rc == -1) {
          fprintf(stderr, "Connection closed or error: %s\n", modbus_strerror(errno));
          break;
        }
      }
    } 
    else if (ready == 0) {
      // Timeout occurred, no activity, continue with GPS polling
      if (buffer[0] != '\0') {
        if (strstr(buffer, "$GPGGA") != NULL) {
          // Store a copy of original string
          strcpy(rawData, buffer);
          token = strtok(buffer, ",");
    
          // Split string and store in corresponding variables
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
    
          mb_mapping->tab_registers[0] = latitudeMSB;
          mb_mapping->tab_registers[1] = latitudeLSB;
          mb_mapping->tab_registers[2] = longitudeMSB;
          mb_mapping->tab_registers[3] = longitudeLSB;
          mb_mapping->tab_registers[4] = atoi(fixQuality);
          mb_mapping->tab_registers[5] = atoi(numStatellites);
          mb_mapping->tab_registers[6] = precisionMSB;
          mb_mapping->tab_registers[7] = precisionLSB;
          mb_mapping->tab_registers[8] = elevationMSB;
          mb_mapping->tab_registers[9] = elevationLSB;
        }
        else if (strstr(buffer, "$GPVTG") != NULL) {
          strcpy(rawData, buffer);
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
          
          mb_mapping->tab_registers[10] = trackMadeGoodTrueMSB;
          mb_mapping->tab_registers[11] = trackMadeGoodTrueLSB;
          mb_mapping->tab_registers[12] = trackMadeGoodMagneticMSB;
          mb_mapping->tab_registers[13] = trackMadeGoodMagneticLSB;
          mb_mapping->tab_registers[14] = speedInKnotMSB;
          mb_mapping->tab_registers[15] = speedInKnotLSB;
          mb_mapping->tab_registers[16] = speedInKmHrMSB;
          mb_mapping->tab_registers[17] = speedInKmHrLSB;
        }
      }
    } 
    else {
      perror("Error in select");
      break;
    }
  }

  fclose(gpsDevice);
  close(server_socket);
  modbus_mapping_free(mb_mapping);
  modbus_free(ctx);
  return 0;
}

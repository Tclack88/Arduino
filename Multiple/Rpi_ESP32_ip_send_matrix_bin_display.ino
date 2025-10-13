#include <Wire.h>
#include <LedController.hpp> // Noa Sakurajin

#define DIN_PIN 23  // DIN (Data In)
#define CS_PIN  5   // CS/LOAD (Chip Select)
#define CLK_PIN 18  // CLK (Clock)

const uint8_t NUM_MATRICES = 1;
sakurajin::LedController<NUM_MATRICES, NUM_MATRICES> lc;

// char buff[4] = {0,0,0,0}; // Buffer for one octet (max 3 digits + null terminator)
uint8_t ip[4];


// void displayMessage(int size){
//   Serial.println("<incoming message>:");
//   while (Wire.available()){
//     char c = Wire.read();
//     Serial.print(c); 
//   }
//   Serial.println("\t<fin>");
// }


void printArr(uint8_t arr[], int size){
  for(int i=0; i<size; i++){
    Serial.printf("%d ",arr[i]);
  }
  Serial.println();
}

void printBuf(char arr[], int size){
  for(int i=0; i<size; i++){
    Serial.printf("%c ",arr[i]);
  }
  Serial.println();
}

void displayMatrix(uint8_t ip[4]){
  lc.clearMatrix();
  lc.setRow(0,0,ip[0]);
  lc.setRow(0,2,ip[1]);
  lc.setRow(0,4,ip[2]);
  lc.setRow(0,6,ip[3]);
}

void displayMessage(int size) {
  Serial.printf("<incoming message>:\n");

  char buff[4] = {0,0,0,0}; // Buffer for one octet (max 3 digits + null terminator)
  int i = 0;

  int ip_idx = 0;

  while (Wire.available()){
    for (int j=0; j<size;j++){
      char c = Wire.read();
      if (c == '.') { // End of octet or message. Null-terminate. Convert to an integer
          buff[i] = '\0';
          printBuf(buff, i);
          int val = (uint8_t) atoi(buff); // char array to int
          Serial.printf("%d\n",val);
          ip[ip_idx] = val;
          ip_idx++;
          i = 0; // Reset buffer for next octet
      }
      else if (isspace(c) or c=='\0') // was getting leading nullbyte or space that was affecting displayed ip addr.
        continue;
      else { // Add the digit character to the buffer
        if (i < 3) { // prevent seg fault
          buff[i] = c;
          i++;
        }
      }

      if(i>0 && ip_idx<4){ // populate last index (no '.')
        buff[i] = '\0';
        ip[ip_idx] = (uint8_t) atoi(buff);
        
      }
    }
    printArr(ip,4);
  }
}

void setup() {
  Serial.begin(9600);
  Wire.begin(0x77); // arbitrarily chosen from 0x8 to 0x77
  Wire.onReceive(displayMessage);

  // Configure the LedController object for software SPI
  sakurajin::controller_configuration<NUM_MATRICES, NUM_MATRICES> config;
  config.useHardwareSpi = false; // Use software SPI
  config.SPI_MOSI = DIN_PIN;
  config.SPI_CS = CS_PIN;
  config.SPI_CLK = CLK_PIN;

  lc.init(config);
  lc.activateAllSegments();
  lc.setIntensity(1); // 0-15
  lc.clearMatrix();
}

void loop() {
  // implement matrix stuff here when other logic handled
  // uint8_t ip[4] = {192, 168, 1, 74}; // test
  displayMatrix(ip);
}

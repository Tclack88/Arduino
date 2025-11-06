// UDP connection with ESP32 as server interacting with Rpi. Used in conjunction with Rpi_ESP32_UDP_transmit_client.py
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"
// #include "secrets_phone.h" // used when hotspotting
/* format of secrets.h
#define WIFI_SSID "network_name"
#define WIFI_PW "wifi_password"
*/

const char ID = 1;

const char* ssid = WIFI_SSID;
const char* pw = WIFI_PW;
int rpi_port = 12005;
int swarm_port = 3000; // internal communicatin for ESPs
#define iLED 2 // internal LED
bool IS_MASTER = false;

bool iLED_status = false;
int sensor = 34;
int val = 0;
int sending = 0; // toggle 1 or 0. Keep track if sending to UDP or not
float voltage = 0.0;
IPAddress myIP;
char myIP_string[16];
char brother1IP[16];
char brother2IP[16];
char* brothers[] = {brother1IP,brother2IP};
int swarm_size = 1;

char packet_received[255]; // Buffer to hold any incoming packets
WiFiUDP PI_UDP;
WiFiUDP ESP_UDP;

int I = 0;
float data[5] = {0.0,0.0,0.0,0.0,0.0};

float avg_photoresistor(){
  float sum = 0.0;
  for (int i=0; i<5; i++)
    sum += data[i];
  return sum / 5;
}

int check_request(){
  int packetSize = PI_UDP.parsePacket();
  return packetSize; // 0 if no packet (button press), else positive
}

void collect(){
  val = analogRead(sensor);
  voltage = ( (float)val /4095 )*3.3;
  data[I] = voltage;
  I = (I+1)%5;
}

void send(){
  PI_UDP.beginPacket(PI_UDP.remoteIP(),PI_UDP.remotePort());
  char message_out[255];
  sprintf(message_out, "%d %d", ID, avg_photoresistor());
  PI_UDP.print(message_out);
  PI_UDP.endPacket();
}

void toggle_iLED(){
  iLED_status = !iLED_status;
  digitalWrite(iLED,iLED_status);
}

void parse_packet(char packet_received[]){
  // Changes the "brothers" list (who is available)
  printf("packet received: %s\n",packet_received);
  char cmd;
  int size;
  int num_chars = 0;
  char ip_addr[16]; // 255.255.255.255 15 char max + nullbyte                                                                                                                             sscanf(packet_received, "%c %d %n", &cmd, &size, &num_chars); // maybe change to fgets (255 buffer size) for "safety"
  printf("cmd: %c, size: %d\n", cmd, size);
  swarm_size = size; // update locally known count
  if (cmd == 'C'){
    int brother = 0;
    for (int i=0; i<size; i++){
      packet_received += num_chars; // advance pointer
      sscanf(packet_received, "%s %n", ip_addr, &num_chars);
      if (strcmp(ip_addr,myIP.toString().c_str()) != 0){
        sscanf(ip_addr,"%s",brothers[brother]);
        brother++;
      }
    }
  }
  else { // 'E' or end
    printf("END\n");
  }
}

bool determine_master(char* brothers[]){
  // delay(10*ID); // delay 10,20 or 30 ms to give time for sending/receiving (necessary? Trying to ensure simultaneously sent/received messages are not lost)
  char local_packet_received[255]; // Buffer to hold any incoming packets
  float myVal = avg_photoresistor();
  float largest = myVal;
  int packetSize = 0;
  for (int i=0; i<swarm_size-1; i++){
    IPAddress brotherIP;
    brotherIP.fromString(brothers[i]);
    ESP_UDP.beginPacket(brotherIP,swarm_port); // TODO: double check ip address format
    ESP_UDP.print(myVal);
    ESP_UDP.endPacket();
    ESP_UDP.begin(swarm_port); // re-Begin UDP listener
    int esp_packetSize = ESP_UDP.parsePacket();
    if (esp_packetSize){
      int len = ESP_UDP.read(local_packet_received,sizeof(local_packet_received)-1);
      local_packet_received[len] = 0; // Null terminate
      Serial.printf("local packet message: %s\n", local_packet_received);
      float val = atoi(local_packet_received); 
      largest = max(largest, val);
    }
  }
  if (myVal == largest)
    return true; // IS_MASTER set to true
  return false; // IS_MASTER set to false
}

void setup() {
  pinMode(iLED,OUTPUT);
  // pinMode(sensor,INPUT); // apparently this is not needed
  Serial.begin(9600);
  // connect to network. Display IP
  WiFi.begin(ssid,pw);
  Serial.println(WiFi.macAddress());
  Serial.print("Connecting to Wifi ");
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.printf(" Wifi connected\n IP address: ");
  myIP = WiFi.localIP();
  Serial.println(myIP);
  PI_UDP.begin(rpi_port); // Begin UDP listener
  ESP_UDP.begin(swarm_port); // Begin UDP listener for internal (swarm) netwwork
}

void loop() {
  int packetSize = PI_UDP.parsePacket();
  if (packetSize){  // add "or" condition check for cancellation
    int len = PI_UDP.read(packet_received,sizeof(packet_received)-1);
    packet_received[len] = 0; // Null terminate
    Serial.print("UDP request received from ");
    Serial.print(PI_UDP.remoteIP());
    Serial.printf(". Packetsize: %d, Message: %s.\n",packetSize, packet_received);
    parse_packet(packet_received); // establishes brothers, receives cmd ('C' or 'E')
    IS_MASTER = determine_master(brothers);
    if (IS_MASTER){
      sending = 1;
      unsigned long now = millis();
      unsigned long blink_timer = now; // timer for blink. Ever 0.5 seconds toggle
      unsigned long send_timer = now; // timer to send. ever 2 seconds send
      unsigned long collect_timer = now; // timer for every 1 second
      while (sending){
        // Sending stopped if IS_MASTER returns false or a button press is received while sneding as the master
        IS_MASTER = determine_master(brothers);
        sending = IS_MASTER;
        unsigned long now = millis();
        if (int r = check_request()){ // button pressed again, cancel
          Serial.printf("\tRequest received: %d",r);
          sending = 0; 
          PI_UDP.beginPacket(PI_UDP.remoteIP(),PI_UDP.remotePort());
          PI_UDP.print("-1");
          Serial.println("cancelled, no more sending information");
          PI_UDP.endPacket();
          PI_UDP.begin(rpi_port); // re-Begin UDP listener
        }
        if ( (now - send_timer) >= 2000 ){
          send();
          send_timer = now; // reset
          Serial.printf("(data sent)(val=%d)\n",val);
        }
        if ( (now - collect_timer) >= 1000){
          collect();
          collect_timer = now;
        }
        if ( (now - blink_timer) >= 500){
          toggle_iLED();
          blink_timer = now;
        }
        delay(50); // short enough to catch button press, but still save energy
      }
    }
  }
  digitalWrite(iLED,false); // not receiving/sending, turn off
  delay(300);
}

// Lessons learned: If using Wifi (as in this project), GIOP pin #25 cannot be used. As I tried to do for data collection.

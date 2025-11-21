// UDP connection with ESP32 as server interacting with Rpi. Used in conjunction with Rpi_ESP32_UDP_transmit_client.py
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"
// #include "secrets_phone.h" // used when hotspotting
/* format of secrets.h
#define WIFI_SSID "network_name"
#define WIFI_PW "wifi_password"
*/

const char ID = 2;

const int STORAGE_CAPACITY = 1; // set array size for collecting last N voltages
const char* ssid = WIFI_SSID;
const char* pw = WIFI_PW;
int rpi_port = 12005; // external communication to Rpi
int swarm_port = 3000; // internal communicatin for ESPs
#define iLED 2 // internal LED pin for ESP32 is always pin 2
bool IS_MASTER = false;

bool iLED_status = false;
int sensor = 34; // pin to read photoresistor
const int ext_led = 27; // external LED

int sending = 0; // toggle 1 or 0. Keep track if sending to UDP or not
int highest_voltage = 0; // global. Used to determine blink rate

IPAddress myIP;
char brother1IP[16];
char brother2IP[16];
char* brothers[] = {brother1IP,brother2IP}; // hold up to 2 other ESP32 "brothers"
int swarm_size = 1;

char packet_received[255]; // Buffer to hold any incoming packets
WiFiUDP PI_UDP;
WiFiUDP ESP_UDP;

int I = 0; // global I (index pointer for data array)
float data[STORAGE_CAPACITY] = {0.0};

float avg_photoresistor(){
  float sum = 0.0;
  for (int i=0; i<STORAGE_CAPACITY; i++)
    sum += data[i];
  return sum / STORAGE_CAPACITY;
}

void collect(){ // update voltage reading and light up external LED
  int val = analogRead(sensor);
  float voltage = 3.3-( (float)val /4095 )*3.3;
  if (voltage > highest_voltage)
    highest_voltage = voltage; // update global highest_voltage
  data[I] = voltage;
  long int vv = 255 - 255*val/4095; // cast to 0-255 for analogWrite()
  analogWrite(ext_led, vv); // light up external LED
  I = (I+1)%STORAGE_CAPACITY;
}

void send(){ // send ID and Voltage to Raspberry Pi
  PI_UDP.beginPacket(PI_UDP.remoteIP(),PI_UDP.remotePort());
  char message_out[255];
  sprintf(message_out, "%d %f", ID, avg_photoresistor());
  Serial.printf("\n\nsending message: %s\n\n",message_out);
  PI_UDP.print(message_out);
  PI_UDP.endPacket();
}

void toggle_iLED(){
  iLED_status = !iLED_status;
  digitalWrite(iLED,iLED_status);
}

char parse_packet(char packet_received[]){
  // update the "brothers" list (who is on network)
  char cmd; // 'C' (continue/commence) or 'E' (end)
  int size; // number of total ESPs on network
  int num_chars = 0; // message size, needed for parsing array for other ESPs
  char ip_addr[16]; // 255.255.255.255 15 char max + nullbyte                                                                                                                             
  sscanf(packet_received, "%c %d %n", &cmd, &size, &num_chars); // maybe change to fgets (255 buffer size) for "safety"
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
  return cmd;
}

bool determine_master(char* brothers[]){
  char local_packet_received[255]; // Buffer to hold any incoming packets
  float myVal = avg_photoresistor();
  float largest = myVal;
  int packetSize = 0;
  for (int i=0; i<swarm_size-1; i++){
    IPAddress brotherIP;
    brotherIP.fromString(brothers[i]);
    ESP_UDP.beginPacket(brotherIP,swarm_port);
    ESP_UDP.print(myVal);
    ESP_UDP.endPacket();
    int esp_packetSize = ESP_UDP.parsePacket();
    if (esp_packetSize){
      Serial.print("receeiving...");
      int len = ESP_UDP.read(local_packet_received,sizeof(local_packet_received)-1);
      local_packet_received[len] = 0; // Null terminate
      Serial.println(" ...read");
      float val = atof(local_packet_received); 
      largest = max(largest, val);
      Serial.print("\n\t brother:");Serial.print(brotherIP); Serial.print("  ");Serial.println(val);
      Serial.print("\t me     :");Serial.print(myIP); Serial.print("  ");Serial.println(myVal);
    }
  }
  if (myVal == largest)
    return true; // IS_MASTER = true
  return false; // IS_MASTER = false
}

char check_request(int packetSize){
  // update contents of packet_received (last Rpi message)
  // Calls parse_packet to "update brother's"
  int len = PI_UDP.read(packet_received,sizeof(packet_received)-1);
  packet_received[len] = 0; // Null terminate
  char cmd = parse_packet(packet_received); // establishes brothers, receives cmd ('C' or 'E')
  return cmd;
}

void setup() {
  pinMode(iLED,OUTPUT);
  // pinMode(sensor,INPUT); // apparently this is not needed
  pinMode(ext_led, OUTPUT);
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
  PI_UDP.begin(rpi_port); // Begin external UDP listener (to Raspberry Pi) 
  ESP_UDP.begin(swarm_port); // Begin internal UDP listener (to swarm netwwork)
}

void loop() {
  collect(); // Collection still happens even when not "IS_MASTER"
  int packetSize = PI_UDP.parsePacket();
  if (packetSize){
    char cmd = check_request(packetSize); 
    IS_MASTER = determine_master(brothers);
    if (IS_MASTER){
      sending = 1;
      unsigned long now = millis();
      unsigned long blink_timer = now; // timer for blink. Toggle based on voltage read
      unsigned long send_timer = now; // timer to send. every 1s, send
      unsigned long collect_timer = now; // timer for reading photoresistor. every 300ms
      while (sending){
        packetSize = PI_UDP.parsePacket(); // check for update from Rpi
        if (packetSize){ // if non-empty (message received)
          cmd = check_request(packetSize); // cmd = 'C' or 'E'
          IS_MASTER = determine_master(brothers);
          sending = (IS_MASTER && cmd == 'C'); // both'C' received AND IS_MASTER => send
          if (cmd == 'E'){ // cancel 
            PI_UDP.beginPacket(PI_UDP.remoteIP(),PI_UDP.remotePort());
            PI_UDP.print("-1 -1"); // return -1 ID and -1 voltage (no LED or voltage/blink rate set)
            PI_UDP.endPacket();
          }
        }
        now = millis();
        if ( (now - send_timer) >= 1000 ){
          send();
          send_timer = now; // reset
        }
        if ( (now - collect_timer) >= 300){
          collect();
          collect_timer = now;
        }
        if ( (now - blink_timer) >= 1000*(highest_voltage - avg_photoresistor()) ){ // variable blink rate
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

// UDP connection with ESP32 as server interacting with Rpi. Used in conjunction with Rpi_ESP32_UDP_transmit_client.py
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"
// #include "secrets_phone.h" // used when hotspotting
/* format of secrets.h
#define WIFI_SSID "network_name"
#define WIFI_PW "wifi_password"
*/

const char* ssid = WIFI_SSID;
const char* pw = WIFI_PW;
int port = 12005;
#define iLED 2 // internal LED

int sensor = 34;
int val = 0;
int sending = 0; // toggle 1 or 0. Keep track if sending to UDP or not
float voltage = 0.0;

char packet_received[255]; // Buffer to hold any incoming packets
WiFiUDP UDP;

int I = 0;
float data[5] = {0.0,0.0,0.0,0.0,0.0};

// float R1 = 1000; // TODO: measure for more precision

float avg_photoresistor(){
  float sum = 0.0;
  for (int i=0; i<5; i++)
    sum += data[i];
  return sum / 5;
}

int check_request(){
  int packetSize = UDP.parsePacket();
  // Serial.printf("checking for packet... size: %d",packetSize);
  return packetSize; // 0 if no packet (button press), else positive
}

void collect(){
  val = analogRead(sensor);
  voltage = ( (float)val /4095 )*3.3;
  data[I] = voltage;
  I = (I+1)%4;
}

void send(){
  UDP.beginPacket(UDP.remoteIP(),UDP.remotePort());
  UDP.print(avg_photoresistor());
  UDP.endPacket();
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
  Serial.println(WiFi.localIP());
  UDP.begin(port); // Begin UDP listener
}

void loop() {
  int packetSize = UDP.parsePacket();
  if (packetSize){
    int len = UDP.read(packet_received,sizeof(packet_received)-1);
    packet_received[len] = 0; // Null terminate
    Serial.print("UDP request received from ");
    Serial.print(UDP.remoteIP());
    Serial.printf(". Packetsize: %d, Message: %s.\n",packetSize, packet_received);
    // sending = (sending + 1)%2;
    sending = 1;
    for (int i=0; i<5; i++){ // collect initial 5 packets
      collect();
      delay(1000);
    }
    send(); // send first sample of 5
    unsigned long now = millis();
    unsigned long blink_timer = now; // timer for blink. Ever 0.5 seconds toggle
    unsigned long send_timer = now; // timer to send. ever 2 seconds send
    unsigned long collect_timer = now; // timer for every 1 second
    while (sending){
      unsigned long now = millis();
      if (int r = check_request()){ // button pressed again, cancel
        Serial.printf("\tRequest received: %d",r);
        sending = 0; 
        UDP.beginPacket(UDP.remoteIP(),UDP.remotePort());
        UDP.print("-1");
        Serial.println("cancelled, no more sending information");
        UDP.endPacket();
        UDP.begin(port); // re-Begin UDP listener
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
      // TODO: blink_tiemr
      delay(50); // short enough to catch button press, but still save energy

    }

  // TODO: work on logic for average value,  for now, just return current reading
  //   data[I] = val;
  //   I++;
  //   int begin = millis();
  //   while (millis() - begin < 1000){
  //     // add some interrupt to read data upon request from UDP
  //     check_request();
  //     continue;
  //   }
  }
  delay(300);
}

// Lessons learned: If using Wifi (as in this project), GIOP pin #25 cannot be used. As I tried to do for data collection.

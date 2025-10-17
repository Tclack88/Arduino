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

int sensor = 34;
int val = 0;
float voltage = 0.0;

char packet_received[255]; // Buffer to hold any incoming packets
WiFiUDP UDP;

int I = 0;
int data[5] = {0,0,0,0,0};

// float R1 = 1000; // TODO: measure for more precision

float read_photoresistor(){
  int avg = 0;
  for (int i=0; i<5; i++)
    avg += data[i];
  return ((float) avg) / 5;
}

void check_request(){
  // look if UDP request made over wifi.
  // if so, call read_photoresistor()
}

void setup() {
  // pinMode(sensor,INPUT);
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
    val = analogRead(sensor);
    voltage = ( (float)val )*3.3/4095;
    Serial.print("UDP request received from ");
    Serial.print(UDP.remoteIP());
    Serial.printf(". Packetsize: %d, Message: %s.\n",packetSize, packet_received);

    UDP.beginPacket(UDP.remoteIP(),UDP.remotePort());
    UDP.print(voltage);
    UDP.endPacket();

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

// reference: https://www.makerguides.com/tcs34725-rgb-color-sensor-with-arduino/
#include "Adafruit_TCS34725.h"

Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);
float R, G, B;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  tcs.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  tcs.setInterrupt(false);
  delay(60);
  tcs.getRGB(&R, &G, &B);
  tcs.setInterrupt(true);
  Serial.print("R: "); Serial.print(R);
  Serial.print(" G: "); Serial.print(G);
  Serial.print(" B: "); Serial.println(B);
  delay(1000);
}
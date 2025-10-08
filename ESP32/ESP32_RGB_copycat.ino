// references: https://www.makerguides.com/tcs34725-rgb-color-sensor-with-arduino/
//             https://learn.adafruit.com/adafruit-color-sensors/assembly-and-wiring
//             https://www.luisllamas.es/en/use-gamma-correction-light-sources-arduino/
#include "Adafruit_TCS34725.h"
#include "GammaCorrectionLib.h"
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

// Full disclosure, this part with the gammatable was provided with AI assistance
#include <math.h>
#define GAMMA 2.2
uint8_t gammatable[256];

void generateGammaTable() {
  for (int i = 0; i < 256; i++) {
    gammatable[i] = pow((float)i / 255.0, GAMMA) * 255.0 + 0.5;
  }
}
// end AI assistance

float R, G, B, RGB_sum;

int red = 32;
int green = 25;
int blue = 27;

int freq = 5000;
int res = 8;

void setup() {
  Serial.begin(9600);
  tcs.begin();

  generateGammaTable();

  ledcAttach(red, freq, res);
  ledcAttach(green, freq, res);
  ledcAttach(blue, freq, res);
  tcs.setInterrupt(true);
}

void loop() {
  delay(60);
  tcs.getRGB(&R, &G, &B);
  RGB_sum = R+G+B;

  Serial.print("R: "); Serial.print(R);
  Serial.print(" G: "); Serial.print(G);
  Serial.print(" B: "); Serial.println(B);
  Serial.printf("\tR+G+B: %f\n",RGB_sum);
  Serial.println("____________________");

  ledcWrite(red, gammatable[(int) R]);
  ledcWrite(green, gammatable[(int) G]);
  ledcWrite(blue, gammatable[(int) B]);
  delay(200);
}
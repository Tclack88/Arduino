// LCD MORSE

#include <LiquidCrystal.h>
int rs=7;
int en=8;
int d4=9;
int d5=10;
int d6=11;
int d7=12;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// TODO: 
//    [x] dictionary pulses to letters
//    [] print to LCD
//    [] overflow LCD 1st line to next
//    [] automatically clear 1st line if 2nd is filled?
//    [] implement reset button
//    [] buzzer? (optional)
//    [] circuit diagram



int in = A0;
int reset = 2;
String chr = "";

struct Map {
  String key;
  String value;
};

Map morse[] = {
  {".-", "a"},
  {"-...", "b"},
  {"-.-.", "c"},
  {"-..", "d"},
  {".", "e"},
  {"..-.", "f"},
  {"--.", "g"},
  {"....", "h"},
  {"..", "i"},
  {".---", "j"},
  {"-.-", "k"},
  {".-..", "l"},
  {"--", "m"},
  {"-.", "n"},
  {"---", "o"},
  {".--.", "p"},
  {"--.-", "q"},
  {".-.", "r"},
  {"...", "s"},
  {"-", "t"},
  {"..-", "u"},
  {"...-", "v"},
  {".--", "w"},
  {"-..-", "x"},
  {"-.--", "y"},
  {"--..", "z"},
};

String getValue(String key) {
  for (int i = 0; i < sizeof(morse) / sizeof(Map); i++) {
    if (morse[i].key == key) {
      return morse[i].value;
    }
  }
  return ""; // Not found
}




void parsePulse(int start, int duration,int pulse){
  while (pulse){
    duration = millis() - start;
    pulse = analogRead(in);
  }
  if(duration < 200)
    // Serial.print(".");
    chr += ".";
  else
    // Serial.print("-");
    chr += "-";
  Serial.print(duration);
}

void checkReset(){
  // Serial.print(digitalRead(reset));
  if(digitalRead(reset)>0){
    Serial.print(" Reset! ");
    resetLCD();
  }
}

void resetLCD(){
  lcd.clear();
  lcd.setCursor(0,0);
  //   lcd.print(i);
}



void setup() {
  // put your setup code here, to run once:
  lcd.begin(16,2);
  Serial.begin(9600);
  pinMode(A0,INPUT);
  pinMode(reset,INPUT);
  Serial.println(" "); // newline for fresh test
}

void loop() {
  // put your main code here, to run repeatedly:
  
  int pulse = analogRead(in);
  int spaceStart = millis();
  while (!pulse){
    pulse = analogRead(in);
    checkReset();
    delay(5);
  }
  int space = millis() - spaceStart;
  if (space > 1300){
    Serial.print(" "); // print a space if a "long enough" delay has occured
    lcd.print(" ");
  }

  int start = millis();
  int duration = 0;
  
  parsePulse(start, duration, pulse);

  int timeoutStart = millis();
  int timeout = 0;
  pulse = 0;

  while (!pulse && timeout < 500){
    delay(10); // mitigate bounce effects
    checkReset();
    pulse = analogRead(in);
    timeout = millis() - timeoutStart;
    if (pulse){
      parsePulse(millis(),0,pulse);
      timeoutStart = millis();
      timeout = 0;
      pulse = 0;
    }
  }
 
  Serial.print(getValue(chr)); // space for new char
  lcd.print(getValue(chr));


    // Serial.print(" "); // space for new char

  chr = "";

}

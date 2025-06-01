// LCD MORSE

// #include <LiquidCrystal.h>
// int rs=7;
// int en=8;
// int d4=9;
// int d5=10;
// int d6=11;
// int d7=12;
// LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// TODO: 
//    [] dictionary pulses to letters
//    [] print to LCD
//    [] buzzer? (optional)
//    [] circuit diagram



int in = A0;




void parsePulse(int start, int duration,int pulse){
  while (pulse){
    duration = millis() - start;
    pulse = analogRead(in);
  }
  if(duration < 200)
    Serial.print(".");
  else
    Serial.print("-");
}

void setup() {
  // put your setup code here, to run once:
  // lcd.begin(16,2);
  Serial.begin(9600);
  pinMode(A0,INPUT);
  // pinMode(in,INPUT);
  Serial.println(" "); // newline for fresh test
}

void loop() {
  // put your main code here, to run repeatedly:
  // lcd.setCursor(0,0);
  // lcd.print("Counting");
  // delay(1000);
  // lcd.setCursor(0,1);
  // for (int i=0; i<50; i++){
  //   lcd.setCursor(0,1);
  //   lcd.print(i);
  //   delay(500);
  // }
  // lcd.clear();
  int pulse = analogRead(in);
  while (!pulse){
    pulse = analogRead(in);
    delay(5);
  }
  int start = millis();
  int duration = 0;
  
  parsePulse(start, duration, pulse);

  int timeoutStart = millis();
  int timeout = 0;
  pulse = 0;

  while (!pulse && timeout < 500){
    delay(10); // mitigate bounce effects
    pulse = analogRead(in);
    timeout = millis() - timeoutStart;
    if (pulse){
      parsePulse(millis(),0,pulse);
      timeoutStart = millis();
      timeout = 0;
      pulse = 0;
    }
  }
  Serial.print(" "); // space for new char

}

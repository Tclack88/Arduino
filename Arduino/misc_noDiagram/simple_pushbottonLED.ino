int ledOUT = 2;
int ledIN = 7;
int lit = 0;

void setup() {
  pinMode(ledOUT, OUTPUT);
  pinMode(ledIN, INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (digitalRead(ledIN)){
      if (lit){
        digitalWrite(ledOUT,LOW);
        lit = 0;
      }
      else{
        digitalWrite(ledOUT,HIGH);
        lit = 1;
      }
   }delay(80);
}

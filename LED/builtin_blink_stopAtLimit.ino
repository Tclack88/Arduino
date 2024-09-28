// See if I can break out of the loop after x blinks
int COUNTER = 0;

void setup(){
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop(){
  if (COUNTER < 10){
    digitalWrite(LED_BUILTIN,HIGH);
    delay(300);
    digitalWrite(LED_BUILTIN,LOW);
    delay(300);
    COUNTER++;
  }
  else{
    delay(100);
  }
}

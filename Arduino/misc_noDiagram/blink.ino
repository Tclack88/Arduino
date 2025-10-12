// Just makes an LED blink (led variable) for as many times specified by num
int led = 7;
int num = 10;

void setup() {
  pinMode(led,OUTPUT);
}

void loop() {
  Blink(num);
}

void Blink(int num){
  for (int i=0; i<num; i++){
    digitalWrite(led,HIGH);
    delay(200);
    digitalWrite(led,LOW);
    delay(200);
  }
}

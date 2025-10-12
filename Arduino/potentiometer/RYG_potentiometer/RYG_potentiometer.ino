// red, yellow, green, potentiometer
// this code just progressively lights up different LED based on voltage
// (voltage set by potentiometer)
int red = 2;
int yellow = 3;
int green = 4;

void setup() {
  pinMode(A0,INPUT);
  pinMode(red,OUTPUT);
  pinMode(yellow,OUTPUT);
  pinMode(green,OUTPUT);
}

void loop() {
  int detect = analogRead(A0);
  if (detect < 340)
    digitalWrite(green,HIGH);
  else
    digitalWrite(green,LOW);

  if (detect < 682 && detect > 340)
    digitalWrite(yellow,HIGH);
  else
    digitalWrite(yellow,LOW);

  if (detect > 682)
    digitalWrite(red,HIGH);
  else
    digitalWrite(red,LOW);
  
}

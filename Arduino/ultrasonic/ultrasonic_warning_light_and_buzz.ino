// Ultrasonic sensor. Effect:
// If distance > 50cm, a green light is on
// if something moves closer (25-50cm range) a red light comes on to warn
// If something is closer than 25 cm, the buzzer alarms

int distance;
int time;
int green = 4;
int red = 2;
int buzz = 13;

void setup() {
  pinMode(7,OUTPUT);
  pinMode(8,INPUT);
  pinMode(13,OUTPUT);
  Serial.begin(9600);
}

void loop() {
  digitalWrite(7,LOW);
  delayMicroseconds(2);
  digitalWrite(7,HIGH);
  delayMicroseconds(100);
  digitalWrite(7,LOW);

  time = pulseIn(8,HIGH); // returns timein microseconds
  Serial.print("time: ");
  Serial.println(time);
  distance = 34300*time/(2*1000000); // speed of sound: 34300 cm/s. divide by 2 to get actual distance, divide by 1000000 to convert microseconds to seconds
  Serial.print("Distance: ");
  Serial.println(distance);

  if (distance < 25){
    digitalWrite(buzz,LOW);
    digitalWrite(red,LOW);
    digitalWrite(green,LOW);
    digitalWrite(buzz,HIGH);
    delay(10);
  }
  else if (distance < 50){
    digitalWrite(buzz,LOW);
    digitalWrite(red,LOW);
    digitalWrite(green,LOW);
    digitalWrite(red,HIGH);
  }
  else{
    digitalWrite(buzz,LOW);
    digitalWrite(red,LOW);
    digitalWrite(green,LOW);
    digitalWrite(green,HIGH);
  }
}

/* Just a simple buzzer. Buzzes when light is above a certain level */

int DETECT;
void setup() {
  pinMode(5,OUTPUT);
  pinMode(A5,INPUT);
  // Serial.begin(9600); // used to determine above ambient values. Not necessary for functionality
}

void loop() {
  DETECT = analogRead(A5);
  // Serial.println(DETECT); // used to determine above ambient values. Not necessary for functionality
  if (DETECT>750){
    digitalWrite(5,HIGH);
  }
  else {
    digitalWrite(5,LOW);
  }

}

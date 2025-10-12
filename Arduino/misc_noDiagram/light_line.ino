// a row of 10 LEDs ligned up will on a timer all light up then turn off
byte ledPin[] = {4,5,6,7,8,9,10,11,12,13};
int dir = 1;
int currentLED = 0;


void setup() {
  for (int i=0;i<=9;i++){

  pinMode(ledPin[i],OUTPUT);
  Serial.begin(9600);
  }
}

void loop() {
  if (dir > 0){
    if (currentLED == 10){
      dir = -1;
    }
    else{
    digitalWrite(ledPin[currentLED],HIGH);
    currentLED += 1;
    }
  }
  else if (dir < 0){
    if (currentLED < 0){
      dir = 1;
      }
    else {
      digitalWrite(ledPin[currentLED],LOW);
      currentLED -= 1;
    }
    }
  delay(200);
}

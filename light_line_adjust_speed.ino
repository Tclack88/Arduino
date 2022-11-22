// 10 LEDs ligned up, on a timer they light up sequentially then reverses
// A potentiometer adjusts the speed (analog voltage determines the delay time)
byte ledPin[] = {4,5,6,7,8,9,10,11,12,13};
int dir = 1;
int currentLED = 0;
int analogPin = 0;
int val = 0;

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
  delay(checkDelay());
}

int checkDelay(){
  val = analogRead(analogPin);
  Serial.println(val);
  return val;
}

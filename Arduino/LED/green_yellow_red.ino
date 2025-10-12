// Cycles through 3 LEDs whenever a voltage is provided to a detected pin (12 here).
// Kind of like a smooth button without having to deal with the debouncing

int detect = 12;
int counter = 0;
int mode = 0;
int detected;
boolean isON;

void setup() {
  Serial.begin(9600);
  // pinMode(green,OUTPUT);
  // pinMode(yellow,OUTPUT);
  // pinMode(red,OUTPUT);  
  pinMode(7,OUTPUT);
  pinMode(8,OUTPUT);
  pinMode(9,OUTPUT);
  pinMode(detect,INPUT);
  isON = 0;
}

void loop() {
  // digitalWrite(7,HIGH);
  detected = digitalRead(detect);

  if (detected && isON){
    delay(10);
  }
  else if (detected && !isON){
    mode = counter%3+7;
    counter++;
    digitalWrite(7,LOW);
    digitalWrite(8,LOW);
    digitalWrite(9,LOW);
    digitalWrite(mode,HIGH);
    isON = 1;
    delay(10);
  }
  else{
    isON = 0;
    delay(10);
  }
}

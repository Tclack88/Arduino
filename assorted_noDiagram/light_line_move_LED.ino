// 10 led's lined up in a row. a potentiometer is attached and as its 
// value is adjusted, only one LED will be active

byte ledPin[] = {4,5,6,7,8,9,10,11,12,13};
int dir = 1;
int currentLED = 0;
int analogPin = 0;
int val = 0;
int originalVal = 0;

void setup() {
  for (int i=0;i<=9;i++){

  pinMode(ledPin[i],OUTPUT);
  Serial.begin(9600);
  }
}

void loop() {
  for (int i=0; i<10; i++) {
  digitalWrite(ledPin[i],LOW);
  }
  currentLED = checkPin();
  digitalWrite(ledPin[currentLED],HIGH);
  delay(20); // small delay, prevent it from fluttering and staying OFF for longer than the human eye can perceive
}

int checkPin(){
  originalVal = analogRead(analogPin)/102;
  Serial.print(val);
  Serial.print(" -- ");
  val = originalVal%10; //potentiometer reads between 0 and 1023, mod this to get a val 0-9
  Serial.println(val);
  if (originalVal > 500 && val<=1){
    return 9;
  }else{
    return val;
  }
}

// blinks SOS, beginning a morse code sort of thing
int led = 7;
String s = "... --- ...";
void setup() {
  pinMode(led,OUTPUT);
}

void loop() {
  for (int i=0; i<s.length(); i++){
    if (s[i] == '.'){
      shortBlink();
    }
    else if (s[i] == '-'){
      longBlink();
    }
    else if (s[i]==' '){
      delay(1000);
    }
    }
  delay(2500);
}


void shortBlink(){
  digitalWrite(led,HIGH);
  delay(200);
  digitalWrite(led,LOW);
  delay(200);
}

void longBlink(){
  digitalWrite(led,HIGH);
  delay(500);
  digitalWrite(led,LOW);
  delay(500);
}

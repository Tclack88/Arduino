
int led = 7;
int num = 10;
String s = "... --- ...";
void setup() {
  // put your setup code here, to run once:
  pinMode(led,OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  //Blink(num);
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

void Blink(int num){
  for (int i=0; i<num; i++){
    digitalWrite(led,HIGH);
    delay(200);
    digitalWrite(led,LOW);
    delay(200);
  }
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

int DETECT;
int green = 10;
int yellow = 9;
int red = 8;
int energy;
long total_energy;
int loss = 300;
int VL = 500;
int L = 2000;
int H = 8000;
int VH = 10000;

void setup(){
  pinMode(red,OUTPUT);
  pinMode(yellow,OUTPUT);
  pinMode(green,OUTPUT);
  pinMode(A5,INPUT);
  total_energy = 0;
  Serial.begin(9600);
}

void loop(){
  energy = analogRead(A5);
  total_energy += energy;
  total_energy -= loss;
  Serial.println(total_energy);
  if (total_energy<=0){
    total_energy = 0;
  }

  if (total_energy <= VL){
    digitalWrite(green,LOW);
    digitalWrite(yellow,LOW);
    digitalWrite(red,LOW);
    digitalWrite(red,HIGH);
    delay(100);
  }
  else if (total_energy <= L){
    digitalWrite(green,LOW);
    digitalWrite(yellow,LOW);
    digitalWrite(red,LOW);
    digitalWrite(red,HIGH);
    delay(100); 
    digitalWrite(red,LOW);
    delay(100); 
  }
  else if ( (total_energy >= H)&& (total_energy <VH) ){
    digitalWrite(green,LOW);
    digitalWrite(yellow,LOW);
    digitalWrite(red,LOW);
    digitalWrite(green,HIGH);
    delay(100); 
    digitalWrite(green,LOW);
    delay(100); 
  }
    else if (total_energy >= H){
    digitalWrite(green,LOW);
    digitalWrite(yellow,LOW);
    digitalWrite(red,LOW);
    digitalWrite(green,HIGH);
    delay(100); 
  }
  else{
    digitalWrite(green,LOW);
    digitalWrite(yellow,LOW);
    digitalWrite(red,LOW);
    digitalWrite(yellow,HIGH);
    delay(100);
  }

}
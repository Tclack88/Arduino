// RGB rainbow ith potentiometer

/* previous INCORRECT assumption: 
red starts at a max. Then,
red drops while green rises simultaneously (like a seesaw)
Then green hits a max
Then green steadily drops while blue rises (like a seesaw)
Then blue is at a max
Then blue sreadily drops while red simultaneously rises (like a seesaw)

The strategy: divide 1024 into 3 parts (~340). Then in each third section,
take care of the two colors while maintaining the third at zero.
The (incorrect) code for that strategy:

  if (detect < 340){ //red -> green
    greenval = detect*255/340; // green increase
    redval = (340-detect)*255/340; //red decrease
    blueval = 0;
  }
  else if (detect >= 340 && detect <= 680){ //green -> blue
    greenval = (680-detect)*255/340;// green decrease
    blueval = (detect-340)*255/340;// blue increase;
    redval = 0;
  }
  else if (detect > 680 ){ // blue -> red
    blueval = (1023 - detect)*255/342; // blue decrease
    redval= (detect - 680)*255/342; // red increase
    greenval = 0;
  }

Based on seeing the values using a hex colorcode picker here:
https://htmlcolorcodes.com/color-picker/
I can see that what actually happens is
Red starts at a max
Green steadily rises to a max (while red is maintained constant)
Then Green is maintained constant while red is steadily dropped
Now green is at a max
Blue steadily rises while green remains constant
Blue hits a max (with green)
Green is steadily dropped
Blue is at a max
Red steadily rises wile Blue is maintained constant
Red and Blue are both at a max
Blue steadily decreases while red is maintained constant
Red is at a max

EDIT: int on arduino is just 16 bits 
and it defaults to signed, so the max value is 32,767
But some of my intermediate calculations will take values 
up to around 37,000 (eg. 876-730)*255 /146 as intermediate
multiplication is 146*255 = 37,230). This can be corrected
by using an unsigned int
*/
int red = 9;
int green = 5;
int blue = 3;

void setup() {
  pinMode(red,OUTPUT);
  pinMode(green,OUTPUT);
  pinMode(blue,OUTPUT);
  pinMode(A0,INPUT);
}

void loop() {
  unsigned int detect = analogRead(A0);
  unsigned int redval;
  unsigned int greenval;
  unsigned int blueval;
  if (detect <= 146){ // off -> red (+red)
    redval = (detect*255)/146; // +red
    greenval = 0;
    blueval = 0;
  }
  else if (detect > 146 && detect <= 292){ //red -> yellow (+green)
    redval = 255;
    greenval = (detect - 146)*255/146; // +green
    blueval = 0;
  }
  else if (detect > 292 && detect <= 438 ){ // yellow -> green (-red)
    redval= (438 - detect)*255/146; // -red
    greenval = 255;
    blueval = 0; // blue decrease
  }
  else if (detect > 438 && detect <= 584 ){ // green -> cyan (+blue)
    redval = 0;
    greenval = 255;
    blueval = (detect-438)*255/146; // +blue
  }
  else if (detect > 584 && detect <= 730 ){ // cyan -> blue (-green)
    redval = 0;
    greenval = (730-detect)*255/146; // -green
    blueval = 255;
  }
  else if (detect > 730 && detect <= 876 ){ // blue -> magenta (+red)
    redval = (detect-730)*255/146; // +red
    greenval = 0;
    blueval = 255;
  }
  else{ // 877-1023magenta -> fade out (-red and blue)
    redval = (1023-detect)*255/146; // (-red)
    greenval = 0;
    blueval = (1023-detect)*255/146; // (-blue)
  }
  
  analogWrite(red,redval);
  analogWrite(green,greenval);
  analogWrite(blue,blueval);


}                                       

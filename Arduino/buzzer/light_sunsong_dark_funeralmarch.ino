/* Passive Buzzer song. Reacts to light. When light is present it plays the
 Morning song. When the light is removed it plays the funeral march 

 NOTE: circuit diagram: same as bright_buzz.png
 
 Code partially stolen from https://docs.arduino.cc/built-in-examples/digital/toneMelody/
 */

#include "pitches.h"

// notes in the melody:
int DETECT;
int song_length;
int sun_melody[] = {
  NOTE_G5, NOTE_E5, NOTE_D5, NOTE_C5, NOTE_D5, NOTE_E5, NOTE_G5, NOTE_E5, NOTE_D5, NOTE_C5, NOTE_D5, NOTE_E5, NOTE_D5, NOTE_E5, NOTE_G5, NOTE_E5, NOTE_G5, NOTE_A5, NOTE_E5, NOTE_A5, NOTE_G5, NOTE_E5, NOTE_D5, NOTE_C5, NOTE_D5, NOTE_E5
};
// note durations: 4 = quarter note, 8 = eighth note, etc.:
int sun_noteDurations[] = {
  4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 4, 4 , 4, 4, 4, 4, 4, 4, 4
};

int sun_song_length = sizeof(sun_melody)/sizeof(sun_melody[0]);
int die_melody[] = {
  NOTE_C4, NOTE_C4, NOTE_C4, NOTE_C4, NOTE_DS4, NOTE_D4, NOTE_D4, NOTE_C4, NOTE_C4, NOTE_B3, NOTE_C4
};
// note durations: 4 = quarter note, 8 = eighth note, etc.:
int die_noteDurations[] = {
  4, 4, 8, 4, 4, 8, 4, 8, 4, 8 , 4
};

int die_song_length = sizeof(die_melody)/sizeof(die_melody[0]);


void play_melody(int melody[], int noteDurations[], int song_length) {
  
  for (int thisNote = 0; thisNote < song_length; thisNote++) {
    // to calculate the note duration, take one second divided by the note type.
    //e.g. quarter note = 1000 / 4, eighth note = 1000/8, etc.
    int noteDuration = 1000 / noteDurations[thisNote];
    tone(5, melody[thisNote], noteDuration);
    // to distinguish the notes, set a minimum time between them.
    // the note's duration + 30% seems to work well:
    int pauseBetweenNotes = noteDuration * 1.30;
    delay(pauseBetweenNotes);
    noTone(5);
  }
}

void no_song() {
  noTone(5);
}


void setup() {
  pinMode(5,OUTPUT);
  pinMode(A5,INPUT);
}

void loop() {
  DETECT = analogRead(A5);
  if (DETECT > 750){
    play_melody(sun_melody, sun_noteDurations, sun_song_length);
    while (DETECT > 750){
      delay(10);
      DETECT = analogRead(A5);
    }
    play_melody(die_melody, die_noteDurations, die_song_length);
  }
  else{
    no_song();
    delay(1000);
  }
}
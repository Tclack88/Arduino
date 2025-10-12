// Driver program for small stepper motor
// MCEN30021 Group 37
#include <Stepper.h>

// Define constants
const int stepsPerRevolution = 2038;
const int rpm = 10;
const int note_delay = 1000; // ms
const int left = 50;
const int right = -left;

const int IN1 = 8;
const int IN2 = 10;
const int IN3 = 9;
const int IN4 = 11;

// Define global variables
int direction_flag = 1;
int in;

// Define functions
int play_notes(int num);
int step_incr(int dir);

// Initialise stepper motor
Stepper myStepper = Stepper(stepsPerRevolution, IN1, IN2, IN3, IN4);

void setup() {
  // Begin serial
  Serial.begin(9600);

  // Set stepper speed (max 19 rpm)
  myStepper.setSpeed(rpm);

  // Print instructions
  Serial.println("Input number of notes to play...\n");
}

void loop() {
  if (Serial.available()) {
    in = int(Serial.read());

    if ((in==int('l')) || (in==int('r')) || (in==int('$'))) { // step motor incrementally
      if (step_incr(in) == -1){
        Serial.println("ERROR: step_once() returned error status");
      }
    } else if (play_notes(in-48) == -1) { // play notes; convert in from ascii to int
      Serial.println("ERROR: play_notes() returned error status");
    }
  }
}

// FUNCTIONS
// Play a certain number of notes given by the input
int play_notes(int num) {
  // Error check
  if ((num < 1) || (num > 5)) {
    Serial.print("ERROR: num = ");
    Serial.print(num);
    Serial.println(", expecting 1 <= num <= 5");
    return -1;
  } else {
    Serial.print("Playing ");
    Serial.print(num);
    Serial.println(" notes:");
    Serial.print("Current: ");
  }

  // Play note specified number of times
  for (int i=1; i<=num; i++) {
    // User feedback
    Serial.print(i);

    // Run motor
    myStepper.step(direction_flag*stepsPerRevolution/4);

    // Change direction flag
    direction_flag *= -1;

    // Delay if not the last note play
    if (i != num) {
      Serial.print(", ");
      delay(note_delay);
    }
  }

  // End function
  Serial.println("\n");
  return 1;
}

// Increment the stepper motor manually using the format:
// 3 increments CW: 'lll$'
// 5 increments CCW: 'rrrrr$'
// That is, l for clockwise, r for anticlockwise, $ to finalise
int step_incr(int dir) {
  // Determine direction
  if (dir == int('l')) {
    Serial.print("Stepping left...\n");
    myStepper.step(left);
  } else if (dir == int('r')) {
    Serial.print("Stepping right...\n");
    myStepper.step(right);
  } else if (dir == int('$')) {
    myStepper.step(stepsPerRevolution/4);
    delay(100);
    myStepper.step(-stepsPerRevolution/4);
    Serial.println("Finalised...\n");
  } else {
    return -1;
  }
  return 1;
}
       

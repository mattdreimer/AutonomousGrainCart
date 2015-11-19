// This has not been fully tested in the tractor
// but works well on the bench

const int blueIn =    2;
const int whiteIn =   3;
const int greenIn =   4;
const int brownIn =   5;

const int blueOut =   6;
const int whiteOut =  7;
const int greenOut =  8;
const int brownOut =  9;

int blueState = 0;
int whiteState= 1;
int greenState= 1;
int brownState= 0;

const int signalPin = 10;
int signalState = 1000;

const int safetyPin = 11;
int safetyState =1;

//function to pass signals through
void passThru(){
    blueState= digitalRead(blueIn);
    whiteState= digitalRead(whiteIn);
    greenState= digitalRead(greenIn);
    brownState= digitalRead(brownIn);
  
    digitalWrite(blueOut, blueState);
    digitalWrite(whiteOut, whiteState);
    digitalWrite(greenOut, greenState);
    digitalWrite(brownOut, brownState);  
}

//function to put tractor in gear
void inGear(){
    digitalWrite(blueOut, HIGH);
    digitalWrite(whiteOut, LOW);
    digitalWrite(greenOut, LOW);
    digitalWrite(brownOut, HIGH);  
}

void setup() {
  // put your setup code here, to run once:
  pinMode(blueIn, INPUT);
  pinMode(whiteIn, INPUT);
  pinMode(greenIn, INPUT);
  pinMode(brownIn, INPUT);
  
  pinMode(blueOut, OUTPUT);
  pinMode(whiteOut, OUTPUT);
  pinMode(greenOut, OUTPUT);
  pinMode(brownOut, OUTPUT);
  
  pinMode(signalPin, INPUT);
  pinMode(safetyPin, INPUT_PULLUP);
//  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  signalState= pulseIn(signalPin, HIGH, 30000);
  safetyState= digitalRead(safetyPin);
//  Serial.println(signalState);
  if (2100 > signalState && signalState > 1900 && safetyState == 0)  { 
    inGear();
  }else {
    passThru();
  }
}


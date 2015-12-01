/**************************************************************************/
/*! 

    Adafruit invests time and resources providing this open source code, 
    please support Adafruit and open-source hardware by purchasing 
    products from Adafruit!
*/
/**************************************************************************/
#include <Wire.h>
#include <Adafruit_MCP4725.h>

Adafruit_MCP4725 dacLow;
Adafruit_MCP4725 dacHigh;

//function to pass signals through
void passThru(){
  int sensorValueLow = analogRead(A0);
//  Serial.println(sensorValueLow); 
  int sensorValueHigh = analogRead(A1);
//  Serial.println(sensorValueHigh); 
  dacLow.setVoltage(sensorValueLow*4, false);
  dacHigh.setVoltage(sensorValueHigh*4, false);
}

//function to set speed to low
void lowSpeed(){
  dacLow.setVoltage(312, false);
  dacHigh.setVoltage(624, false);
}
const int signalPin = 10;
int signalState = 900;

const int safetyPin = 11;
int safetyState =1;

//function to change speed
void controlSpeed(){
  while(true){
    signalState= pulseIn(signalPin, HIGH, 40000);
    safetyState= digitalRead(safetyPin);
    int sensorValueLow = analogRead(A0);
    
    if (safetyState == 0 && 1000 > signalState && sensorValueLow<82) {
      while (safetyState == 0){
        //This should be code that reacts to pixhawk
        safetyState = digitalRead(safetyPin);
        signalState= pulseIn(signalPin, HIGH, 40000);
//        Serial.println("Normal pixhawk operation");
//        Serial.println(signalState);
        int dacHighVolt = (float(signalState-1000)/1000.0*(2176.0-624.0))+624;
//        Serial.println("dacHighVolt is ");
//        Serial.println(dacHighVolt);
        if (dacHighVolt<624){
          dacHighVolt=624;
        }
        
        else if (dacHighVolt>2176){
          dacHighVolt=2176;
        }
//        Serial.println("after if statements dacHighVolt is ");
//        Serial.println(dacHighVolt);
        int dacLowVolt = dacHighVolt/2;
//        Serial.println("after if statements dacLowVolt is ");
//        Serial.println(dacLowVolt);
        dacLow.setVoltage(dacLowVolt, false);
        dacHigh.setVoltage(dacHighVolt, false);
      }

    }
    else if (safetyState == 1 && sensorValueLow<82) {
      while(safetyState==1){
        passThru();
        safetyState= digitalRead(safetyPin);
//        Serial.println("Pass through after safety released");
      }
      
    }
    else{
      //If any other situation exists set speed to slow
      lowSpeed();
//      Serial.println(signalState);
//      Serial.println("Emergency Situation");
    }
  }
}
void setup(void) {
//  Serial.begin(9600);

  // For Adafruit MCP4725A1 the address is 0x62 (default) or 0x63 (ADDR pin tied to VCC)
  // For MCP4725A0 the address is 0x60 or 0x61
  // For MCP4725A2 the address is 0x64 or 0x65
  pinMode(7, OUTPUT);
  digitalWrite(7,LOW);
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  pinMode(9, OUTPUT);
  digitalWrite(9, HIGH);
  
  dacLow.begin(0x62);
  dacHigh.begin(0x63);
  
  pinMode(signalPin, INPUT);
  pinMode(safetyPin, INPUT_PULLUP);
}

void loop(void) {
  safetyState= digitalRead(safetyPin);
//  Serial.println(signalState);
  if (safetyState == 0) { 
    controlSpeed();
  }else {
    passThru();
//    Serial.println("Pass through");
  }

}

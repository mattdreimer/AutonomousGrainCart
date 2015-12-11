#include <elapsedMillis.h>
#include <mcp_can.h>
#include <SPI.h>
#include <SoftwareSerial.h>

const int SPI_CS_PIN = 10;
MCP_CAN CAN(SPI_CS_PIN); // Set CS pin

unsigned char flagRecv = 0;
unsigned char len = 0;
unsigned char buf[8];
char str[20];

SoftwareSerial toPixhawk(3, 6); // RX, TX

uint8_t rpm_D4 = 0;
uint8_t rpm_D5 = 0;
uint8_t coolant_temp_D1 = 0;
uint8_t oil_pres_D4 = 0;
uint8_t fuel_level_D2 = 0;
char tractor_health[] = "12345";

elapsedMillis timer0;
#define interval 90

void setup() {
  // put your setup code here, to run once:
//  Serial.begin(115200);
  toPixhawk.begin(57600);

START_INIT:

  if (CAN_OK == CAN.begin(CAN_250KBPS)) // init can bus : baudrate = 500k
  {
//    Serial.println("CAN BUS Shield init ok!");
  }
  else
  {
//    Serial.println("CAN BUS Shield init fail");
//    Serial.println("Init CAN BUS Shield again");
    delay(100);
    goto START_INIT;
  }

  timer0=0;
}

void loop() {
  // put your main code here, to run repeatedly:

  unsigned char len = 0;
  unsigned char buf[8];

  if (CAN_MSGAVAIL == CAN.checkReceive()) // check if data coming
  {
    CAN.readMsgBuf(&len, buf); // read data, len: data length, buf: data buf
    unsigned long canId = CAN.getCanId();
    if (canId == 0xCF00400) {
      rpm_D4 = buf[3];
      rpm_D5 = buf[4];
      tractor_health[0]=rpm_D4;
      tractor_health[1]=rpm_D5;
//      int rpm = (rpm_D4+(256*rpm_D5))/8;
//      Serial.println(rpm);
    }
    else if (canId == 0x18FEEE00) {
      coolant_temp_D1 = buf[0];
      tractor_health[2]=coolant_temp_D1;
    }
    else if (canId == 0x18FEEF00) {
      oil_pres_D4 = buf[3];
      tractor_health[3]=oil_pres_D4;
    }    
    else if (canId == 0x18FEFC47) {
      fuel_level_D2 = buf[1];
      tractor_health[4]=fuel_level_D2;
    }
  }

  if (timer0> interval){
    timer0 -= interval;
    toPixhawk.write(tractor_health);
//    Serial.print("tttttttttttttttttttttttttttttttttt");
  }

//  Serial.print(rpm_D4);
//  Serial.print(" ");
//  Serial.print(rpm_D5);
//  Serial.print(" ");
//  Serial.print(coolant_temp_D1);
//  Serial.print(" ");
//  Serial.print(oil_pres_D4);
//  Serial.print(" ");
//  Serial.println(fuel_level_D2);
}

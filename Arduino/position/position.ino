#include <DFRobot_MGC3130.h>

uint8_t DPin= 2;
uint8_t MCLRPin= 4;

DFRobot_MGC3130 myGesture(DPin,MCLRPin);

void setup()
{
  Serial.begin(115200);
  while(!myGesture.begin()){
    Serial.println("begin error! Please check whether the connection is correct");
    delay(100);
  };
}
void loop()
{
  myGesture.sensorDataRecv();

  if(myGesture.havePositionInfo()){
    Serial.print("X: ");
    Serial.print(myGesture.getPositionX());
    Serial.print("   Y: ");
    Serial.print(myGesture.getPositionY());
    Serial.print("   Z: ");
    Serial.println(myGesture.getPositionZ());
  }
  delay(20);
}
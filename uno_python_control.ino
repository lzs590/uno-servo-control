#include <Servo.h>

Servo myServo;
int servoPin = 9;
int angle = 90;       // 当前角度

void setup() {
  myServo.attach(servoPin);
  Serial.begin(9600);
  myServo.write(angle);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("d")) { // 动态模式
      int minAngle, maxAngle, speedDelay;
      sscanf(input.c_str(), "d %d %d %d", &minAngle, &maxAngle, &speedDelay);
      dynamicMode(minAngle, maxAngle, speedDelay);
    } else { // 直接设置角度
      int newAngle = input.toInt();
      if (newAngle >= 0 && newAngle <= 180) {
        angle = newAngle;
        myServo.write(angle);
      }
    }
  }
}

void dynamicMode(int minAngle, int maxAngle, int speedDelay) {
  int step = 1;
  for (int pos = minAngle; pos <= maxAngle; pos += step) {
    myServo.write(pos);
    delay(speedDelay);
  }
  for (int pos = maxAngle; pos >= minAngle; pos -= step) {
    myServo.write(pos);
    delay(speedDelay);
  }
}

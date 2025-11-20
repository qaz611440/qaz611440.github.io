/////////////////////////////////////////////
///LabVIEW with arduino IDE 程式設計
char command;
String string;
/////////////////////////////////////////////
///指紋辨識
int getFingerprintIDez();
#include <Adafruit_Fingerprint.h>
SoftwareSerial mySerial(A1, A0);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);
// 腳位 A1 對應指紋辨識的綠線
// 腳位 A0  對應指紋辨識的黃線
/////////////////////////////////////////////
//DHT11 溫度濕度感測
#include <SimpleDHT.h>
int pinDHT11 = A2;
SimpleDHT11 dht11(pinDHT11);
//DAT: A2                          //溫書度感測資料線街腳為A2             
/////////////////////////////////////////////
///倒車雷達
int spk=A3;                        //定義蜂鳴器為數位接腳A6
int trigPinRL =5;                  //定義(左後 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳5
int echoPinRL =4;                  //定義(左後 HC-SR04)Echo Pin(超音波模組接收腳) -接腳4
int trigPinRR =3;                  //定義(右後 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳3
int echoPinRR =2;                  //定義(右後 HC-SR04)Echo Pin(超音波模組接收腳) -接腳2
long durationRL;                   //宣告durationRL
long durationRR;                   //宣告durationRR
float distanceRL;                  //宣告distanceRL
float distanceRR;                  //宣告distanceRR
int s=100;                         //基準時間
void lndash();                     //宣告長劃訊號
void dash();                       //宣告劃訊號
void dot();                        //宣告點訊號
void sdot();                       //宣告短點訊號
/////////////////////////////////////////////
///防撞
int trigPinFL =12;                 //定義(左前 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳12
int echoPinFL =13;                 //定義(左前 HC-SR04)Echo Pin(超音波模組接收腳) -接腳13
int trigPinFR =10;                 //定義(右前 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳10
int echoPinFR =11;                 //定義(右前 HC-SR04)Echo Pin(超音波模組接收腳) -接腳11
int trigPinL =9;                   //定義(左 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳9
int echoPinL =8;                   //定義(左 HC-SR04)Echo Pin(超音波模組接收腳) -接腳8
int trigPinR =6;                   //定義(右 HC-SR04)Trig Pin(超音波模組觸發腳) -接腳6
int echoPinR =7;                  //定義(右 HC-SR04)Echo Pin(超音波模組接收腳) -接腳7
long durationFL;                  //宣告durationFL
long durationFR;                  //宣告durationFR
float distanceFL;                 //宣告distanceFL
float distanceFR;                 //宣告distanceFR
long durationL;                   //宣告durationL
long durationR;                   //宣告durationR
float distanceL;                  //宣告distanceL
float distanceR;                  //宣告distanceR
void setup() {
  Serial.begin(9600);
  while (!Serial); 
  finger.begin(57600);
  finger.getTemplateCount();
  pinMode(A3, OUTPUT);
  pinMode(trigPinRL, OUTPUT);      //trigPinRL，OUTPUT
  pinMode(echoPinRL, INPUT);       //echoPinRL，INPUT
  pinMode(trigPinRR, OUTPUT);      //trigPinRR，OUTPUT
  pinMode(echoPinRR, INPUT);       //echoPinRR，INPUT
  pinMode(spk, OUTPUT);            //spk，OUTPUT
  pinMode(trigPinFL, OUTPUT);      //trigPinFL，OUTPUT
  pinMode(echoPinFL, INPUT);       //echoPinFL，INPUT
  pinMode(trigPinFR, OUTPUT);      //trigPinFR，OUTPUT
  pinMode(echoPinFR, INPUT);       //echoPinFR，INPUT
  pinMode(trigPinL, OUTPUT);       //trigPinL，OUTPUT
  pinMode(echoPinL, INPUT);        //echoPinL，INPUT
  pinMode(trigPinR, OUTPUT);       //trigPinR，OUTPUT
  pinMode(echoPinR, INPUT);        //echoPinR，INPUT
}
void loop(){
  string=""; 
for(int i=0;i<=1;i++){
      command = ((byte)Serial.read());
      string += command;
}
   if(string == "01")
    { 
     TemperatureHumidity();  
    }   
  else   if(string == "02")
    {
     BackDoDoDo();
    }
  else   if(string == "03"){
     Finger();
    }
  else   if(string == "04"){
     AvoidCollision();
    }
  else{     
    }
    delay(50);
}
///////////////////////////////////
///////////////////////////////////溫度濕度
void TemperatureHumidity(){
  byte temperature  ;
  byte humidity  ;
  int err = SimpleDHTErrSuccess;
  if ((err = dht11.read(&temperature, &humidity, NULL)) != SimpleDHTErrSuccess) {
    Serial.print("Read DHT11 failed, err="); 
    Serial.println(err);
    return;
  }
  Serial.print('a');                            //方便LabVIEW分割數據
  Serial.print((int)temperature);
  Serial.print('i');                            //方便LabVIEW分割數據
  Serial.print((int)humidity);
}
//////////////////////////////////////
//////////////////////////////////////倒車雷達
void BackDoDoDo(){
 ////////////////////////////////////////////////////////////////////
 /////左後超音波感測  
  int twoa,twob;
  digitalWrite(trigPinRL, LOW);              //給 Trig 低電位
  delayMicroseconds(2);                     //持續2微秒
  digitalWrite(trigPinRL, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續10微秒
  digitalWrite(trigPinRL, LOW);             //給 Trig 低電位
  pinMode(echoPinRL, INPUT);                //讀取 echo 的電位
  durationRL = pulseIn(echoPinRL, HIGH);    //收到高電位時的時間
  distanceRL =durationRL*0.034/2;           //將時間換算成距離 cm  //cm = (duration/2) / 29.1   
  if(distanceRL>1000){
    distanceRL=1;
    }
  twoa=distanceRL;                                                
  Serial.print('b');                        //方便LabVIEW分割數據
  Serial.print(twoa);                       //Serial.print(實測距離)
/////////////////////////////////////////////////////////////////////
////////右後超音波感測
  digitalWrite(trigPinRR, LOW);             //給 Trig 低電位
  delayMicroseconds(2);                     //持續 2微秒
  digitalWrite(trigPinRR, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續 10微秒
  digitalWrite(trigPinRR, LOW);             //給 Trig 低電位
  pinMode(echoPinRR, INPUT);                //讀取 echo 的電位
  durationRR = pulseIn(echoPinRR, HIGH);    //收到高電位時的時間
  distanceRR =durationRR*0.034/2;           //將時間換算成距離 cm //cm = (duration/2) / 29.1 
    if(distanceRR>1000){
    distanceRR=1;
    }
  twob=distanceRR;              
  Serial.print('c');                        //方便LabVIEW分割數據                                   
  Serial.print(twob);                       //Serial.print(實測距離)

/////////////////////////////////////////////////////////////////////////
/////////雷達部分

if(distanceRL>distanceRR){
 distanceRL = distanceRR ;
  }
else if(distanceRL<distanceRR){
 distanceRR = distanceRL ;
  }
  if( distanceRL >= 80 && distanceRL <=100 || distanceRR >= 80 && distanceRR <=100){      //假設距離介於80~100之間
    lndash();                                                                             //spk聲音為長劃訊號
}
  else if (distanceRL >=60  && distanceRL <80 || distanceRR >=60  && distanceRR <80){     //假設距離介於60~79之間
    dash();                                                                               //spk聲音為劃訊號
}
  else if (distanceRL >= 40 && distanceRL <60 || distanceRR >= 40 && distanceRR <60){     //假設距離介於40~59之間
    dot();                                                                                //spk聲音為點訊號
}
  else if (distanceRL >= 30 && distanceRL <40 || distanceRR >= 30 && distanceRR <40){     //假設距離介於30~39之間
    sdot(); sdot();                                                                       //spk聲音為兩個短點訊號
}
  else if (distanceRL >= 20 && distanceRL <30 || distanceRR >= 20 && distanceRR <30){     //假設距離介於20~29之間
    sdot(); sdot(); sdot(); sdot();                                                       //spk聲音為四個短點訊號
}
  else if (distanceRL <20 || distanceRR <20){                                             //假設距離小於19cm
    digitalWrite(spk, HIGH);                                                              //spk持續發出聲響
    delay(10);
}
  else
    digitalWrite(spk, LOW);                                                               //超過100cm以上spk不發出聲響
}

void lndash(){             //設定長劃訊號
  digitalWrite(spk,HIGH);  //spk響4秒
  delay(s*4);
  digitalWrite(spk,LOW);
}
void dash(){               //設定劃訊號
  digitalWrite(spk,HIGH);  //spk響2.5秒
  delay(s*2.5);
  digitalWrite(spk,LOW);
 }
void dot(){                //設定點訊號
  digitalWrite(spk,HIGH);  //spk響1.5秒
  delay(s*1.5);
  digitalWrite(spk,LOW);
}
void sdot(){               //設定短點訊號
  digitalWrite(spk,HIGH);  //spk響1秒，停頓0.3秒
  delay(s);
  digitalWrite(spk,LOW);
  delay(s*0.3);
}
///////////////////////////////////////////////////////
/////////////////////////////指紋辨識部分
int Finger(){
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK)  return -1;
  p = finger.image2Tz();
  if (p != FINGERPRINT_OK)  return -1;
  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK)  return -1;
  Serial.print('d');                      //方便LabVIEW分割數據
  Serial.print(finger.confidence);        //輸出手指信任度數值
  return finger.fingerID; 
}
/////////////////////////////////////////////////////////
/////////////////////////////防撞四腳
void AvoidCollision(){
/////////////////////////////////////////////////////////////////////左前
  Serial.print('e');                        //方便LabVIEW分割數據
  int foura,fourb,fourc,fourd;      //使輸出數值能整數且更新
  digitalWrite(trigPinFL, LOW);             //給 Trig 低電位
  delayMicroseconds(2);                     //持續2微秒
  digitalWrite(trigPinFL, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續10微秒
  digitalWrite(trigPinFL, LOW);             //給 Trig 低電位
  pinMode(echoPinFL, INPUT);                //讀取 echo 的電位
  durationFL = pulseIn(echoPinFL, HIGH);    //收到高電位時的時間
  distanceFL =durationFL*0.034/2;           //將時間換算成距離 cm //cm = (duration/2) / 29.1
      if(distanceFL>1000){
    distanceFL=1;
    } 
  foura = distanceFL;                             
  Serial.print(foura);                      //Serial.print(實測距離)
  /////////////////////////////////////////////////////////////////////右前
  Serial.print('f');                        //方便LabVIEW分割數據
  digitalWrite(trigPinFR, LOW);             //給 Trig 低電位
  delayMicroseconds(2);                     //持續 2微秒
  digitalWrite(trigPinFR, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續 10微秒
  digitalWrite(trigPinFR, LOW);             //給 Trig 低電位
  pinMode(echoPinFR, INPUT);                //讀取 echo 的電位
  durationFR = pulseIn(echoPinFR, HIGH);    //收到高電位時的時間
  distanceFR =durationFR*0.034/2;           //將時間換算成距離 cm //cm = (duration/2) / 29.1 
  if(distanceFR>1000){
    distanceFR=1;
    } 
  fourb = distanceFR;                       
  Serial.print(fourb);                      //Serial.print(實測距離)
////////////////////////////////////////////////////////////////////////左
  Serial.print('g');                        //方便LabVIEW分割數據
  digitalWrite(trigPinL, LOW);             //給 Trig 低電位
  delayMicroseconds(2);                     //持續2微秒
  digitalWrite(trigPinL, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續10微秒
  digitalWrite(trigPinL, LOW);             //給 Trig 低電位
  pinMode(echoPinL, INPUT);                 //讀取 echo 的電位
  durationL = pulseIn(echoPinL, HIGH);      //收到高電位時的時間
  distanceL =durationL*0.034/2;             //將時間換算成距離 cm   //cm = (duration/2) / 29.1    
  if(distanceL>1000){
    distanceL=1;
    } 
  fourc = distanceL ;                         
  Serial.print(fourc);                     //Serial.print(實測距離)
///////////////////////////////////////////////////////////////////////右
  Serial.print('h');                        //方便LabVIEW分割數據
  digitalWrite(trigPinR, LOW);             //給 Trig 低電位
  delayMicroseconds(2);                     //持續 2微秒
  digitalWrite(trigPinR, HIGH);            //給 Trig 高電位
  delayMicroseconds(10);                    //持續 10微秒
  digitalWrite(trigPinR, LOW);             //給 Trig 低電位
  pinMode(echoPinR, INPUT);                //讀取 echo 的電位
  durationR = pulseIn(echoPinR, HIGH);    //收到高電位時的時間
  distanceR =durationR*0.034/2;           //將時間換算成距離 cm  //cm = (duration/2) / 29.1 
  if(distanceR>1000){
    distanceR=1;
    } 
  fourd = distanceR ;                    
  Serial.print(fourd);                 //Serial.print(實測距離)
  }

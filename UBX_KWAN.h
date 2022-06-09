//
// Created by jeppesen on 5/23/22.
//

#ifndef PARSE_UBLOX_UBX_KWAN_H
#define PARSE_UBLOX_UBX_KWAN_H

#include "UBloxPacket.h"

class UBX_KWAN_IMU:public UBloxPacket {
public:
  uint32_t t,dt;
  int16_t ax,ay,az;
  int16_t gx,gy,gz;
  int16_t T;
  static uint32_t lastT;
  UBX_KWAN_IMU(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(t,buf+6,pos);
    readField(ax,buf+6,pos);
    readField(ay,buf+6,pos);
    readField(az,buf+6,pos);
    readField(gx,buf+6,pos);
    readField(gy,buf+6,pos);
    readField(gz,buf+6,pos);
    readField(T,buf+6,pos);
    if(t<last_t) {
      minutes++;
      dt=3'600'000'000-last_t+t;
    } else {
      dt=t-last_t;
    }
    last_t=t;
  }
  void print() {
    UBloxPacket::print();
    printf("\nt  =%12u %02d:%011.9f\n",t,minutes,double(t)/60'000'000.0);
    printf("dt =%12u    %011.9f %f Hz\n",dt,double(dt)/60'000'000.0,60'000'000.0/double(dt));
    printf("ax =%6d\n",ax);
    printf("ay =%6d\n",ay);
    printf("az =%6d\n",az);
    printf("gx =%6d\n",gx);
    printf("gy =%6d\n",gy);
    printf("gz =%6d\n",gz);
    printf("T  =%6d\n",T);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_IMU>(buf);}
};

class UBX_KWAN_MAG:public UBloxPacket {
public:
  uint32_t t,dt;
  uint8_t st1,st2;
  int16_t bx,by,bz;
  static uint32_t last_t;
  UBX_KWAN_MAG(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(t,buf+6,pos);
    readField(st1,buf+6,pos);
    readField(bx,buf+6,pos);
    readField(by,buf+6,pos);
    readField(bz,buf+6,pos);
    readField(st2,buf+6,pos);
    if(t<last_t) {
      dt=3'600'000'000-UBX_KWAN_MAG::last_t+t;
    } else {
      dt=t-UBX_KWAN_MAG::last_t;
    }
    UBX_KWAN_MAG::last_t=t;
  }
  void print() {
    UBloxPacket::print();
    printf("\nt  =%12u %011.9f\n",t,double(t)/60'000'000.0);
    printf("dt =%12u 00:%011.9f %f Hz\n",dt,double(dt)/60'000'000.0,60'000'000.0/double(dt));
    printf("st1=0x%02x\n",st1);
    printf("bx =%6d\n",bx);
    printf("by =%6d\n",by);
    printf("bz =%6d\n",bz);
    printf("st2=0x%02x\n",st2);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_MAG>(buf);}
};

class UBX_KWAN_TP:public UBloxPacket {
public:
  static const uint8_t clsconst='K';
  static const uint8_t idconst=0x04;
  uint32_t pulseCount;
  uint32_t tc;
  uint32_t dtc;

  UBX_KWAN_TP(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(pulseCount,buf+6,pos);
    readField(tc,buf+6,pos);
    readField(dtc,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
    printf("\npulseCount=%12u\n",pulseCount);
    printf("tc        =%12.9f\n",double(tc)/60'000'000.0);
    printf("dtc       =%12.9f\n",double(dtc)/60'000'000.0);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_TP>(buf);}
};

class UBX_KWAN_PCAL:public UBloxPacket {
public:
  uint16_t par_t1;
  int16_t par_t2;
  int8_t par_t3;
  //  pressure coefficients
  uint16_t par_p1;
  int16_t par_p2;
  int8_t par_p3;
  int16_t par_p4;
  int16_t par_p5;
  int8_t par_p6;
  int8_t par_p7;
  int16_t par_p8;
  int16_t par_p9;
  uint8_t par_p10;
  //  humidity coefficients
  uint16_t par_h1;
  uint16_t par_h2;
  int8_t par_h3;
  int8_t par_h4;
  int8_t par_h5;
  uint8_t par_h6;
  int8_t par_h7;
  UBX_KWAN_PCAL(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(par_t1 ,buf+6,pos);
    readField(par_t2 ,buf+6,pos);
    readField(par_t3 ,buf+6,pos);

    readField(par_p1 ,buf+6,pos);
    readField(par_p2 ,buf+6,pos);
    readField(par_p3 ,buf+6,pos);
    readField(par_p4 ,buf+6,pos);
    readField(par_p5 ,buf+6,pos);
    readField(par_p6 ,buf+6,pos);
    readField(par_p7 ,buf+6,pos);
    readField(par_p8 ,buf+6,pos);
    readField(par_p9 ,buf+6,pos);
    readField(par_p10,buf+6,pos);

    readField(par_h1 ,buf+6,pos);
    readField(par_h2 ,buf+6,pos);
    readField(par_h3 ,buf+6,pos);
    readField(par_h4 ,buf+6,pos);
    readField(par_h5 ,buf+6,pos);
    readField(par_h6 ,buf+6,pos);
    readField(par_h7 ,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
    printf("\nt1: %6u\n",par_t1);
    printf("t2: %6d\n",par_t2);
    printf("t3:   %4d\n",par_t3);

    printf("p1:  %6u\n",par_p1);
    printf("p2:  %6d\n",par_p2);
    printf("p3:    %4d\n",par_p3);
    printf("p4:  %6d\n",par_p4);
    printf("p5:  %6d\n",par_p5);
    printf("p6:    %4d\n",par_p6);
    printf("p7:    %4d\n",par_p7);
    printf("p8:  %6d\n",par_p8);
    printf("p9:  %6d\n",par_p9);
    printf("p10: %6u\n",par_p10);

    printf("h1:  %6u\n",par_h1);
    printf("h2:  %6u\n",par_h2);
    printf("h3:    %4d\n",par_h3);
    printf("h4:    %4d\n",par_h4);
    printf("h5:    %4d\n",par_h5);
    printf("h6:    %4u\n",par_h6);
    printf("h7:    %4d\n",par_h7);
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_PCAL>(buf);}
};

class UBX_KWAN_PRES:public UBloxPacket {
public:
  uint32_t tp0,tp1;
  uint8_t pst;
  uint32_t rP,rT;
  uint16_t rh;
  float P,T,h;
  UBX_KWAN_PRES(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(tp0,buf+6,pos);
    readField(tp1,buf+6,pos);
    readField(pst,buf+6,pos);
    readField(rP,buf+6,pos);
    readField(rT,buf+6,pos);
    readField(rh,buf+6,pos);
    readField(P,buf+6,pos);
    readField(T,buf+6,pos);
    readField(h,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_PRES>(buf);}
};

class UBX_KWAN_LOOP:public UBloxPacket {
public:
  static const uint8_t clsconst='K';
  static const uint8_t idconst=0x09;
  uint32_t t;
  uint64_t clickCount;
  UBX_KWAN_LOOP(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    readField(t,buf+6,pos);
    readField(clickCount,buf+6,pos);
  }
  void print() {
    UBloxPacket::print();
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_KWAN_LOOP>(buf);}
};

extern const char* KWANid[];
extern const packetFactory KWAN[];

#endif //PARSE_UBLOX_UBX_KWAN_H

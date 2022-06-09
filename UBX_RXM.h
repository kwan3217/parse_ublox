//
// Created by jeppesen on 5/23/22.
//

#ifndef PARSE_UBLOX_UBX_RXM_H
#define PARSE_UBLOX_UBX_RXM_H

#include "UBloxPacket.h"

class UBX_RXM_RAWX:public UBloxPacket {
public:
  double rcvTow;
  uint16_t week;
  int8_t leapS;
  uint8_t numMeas;
  struct recStat_t {
    bool leapSec: 1;
    bool clkReset: 1;
  };
  recStat_t recStat;
  uint8_t version;
  uint16_t reserved0;
  std::vector<double> prMes;
  std::vector<double> cpMes;
  std::vector<float> doMes;
  std::vector<uint8_t> gnssId;
  std::vector<uint8_t> svId;
  std::vector<uint8_t> sigId;
  std::vector<uint8_t> freqId;
  std::vector<uint16_t> lockTime;
  std::vector<uint8_t> cno;
  std::vector<uint8_t> prStdev;
  std::vector<uint8_t> cpStdev;
  std::vector<uint8_t> doStdev;
  std::vector<uint8_t> trkStat;
  std::vector<uint8_t> reserved1;
  static const char *gnssIdStr[];
  static const char *gpsSigIdStr[];
  static const char *sbasSigIdStr[];
  static const char *galSigIdStr[];
  static const char *bdsSigIdStr[];
  static const char *qzssSigIdStr[];
  static const char *gloSigIdStr[];
  static const char *navicSigIdStr[];
  UBX_RXM_RAWX(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    buf+=6;
    readField(rcvTow,buf,pos);
    readField(week,buf,pos);
    readField(leapS,buf,pos);
    readField(numMeas,buf,pos);
    readField(recStat,buf,pos,1);
    readField(version,buf,pos);
    readField(reserved0,buf,pos);
    for(uint8_t iMeas=0;iMeas<numMeas;iMeas++) {
      prMes.push_back(readField<double>("prMes",buf,pos));
      cpMes.push_back(readField<double>("cpMes",buf,pos));
      doMes.push_back(readField<float>("doMes",buf,pos));
      gnssId.push_back(readField<uint8_t>("gnssId",buf,pos));
      svId.push_back(readField<uint8_t>("svId",buf,pos));
      sigId.push_back(readField<uint8_t>("sigId",buf,pos));
      freqId.push_back(readField<uint8_t>("freqId",buf,pos));
      lockTime.push_back(readField<uint16_t>("lockTime",buf,pos));
      cno.push_back(readField<uint8_t>("cno",buf,pos));
      prStdev.push_back(readField<uint8_t>("prStdev",buf,pos));
      cpStdev.push_back(readField<uint8_t>("cpStdev",buf,pos));
      doStdev.push_back(readField<uint8_t>("doStdev",buf,pos));
      trkStat.push_back(readField<uint8_t>("trkStat",buf,pos));
      reserved1.push_back(readField<uint8_t>("reserved1",buf,pos));
    }
  }
  void print() {
    UBloxPacket::print();
    printf("rcvTow: %24.18f week: %4d\n",rcvTow,week);
    printf("  id  gnss svId    sig              prMes              cpMes\n");
    printf("---- ----- ---- ------ ------------------ ------------------\n");
    for(auto i=0;i<numMeas;i++) {
      printf("%4d %5s %4d %6s %18.9f %18.6f\n",i,gnssIdStr[gnssId[i]],svId[i],gpsSigIdStr[sigId[i]],prMes[i],cpMes[i]);
    }
  }
  static std::unique_ptr<Packet> read(uint8_t *buf) {return std::make_unique<UBX_RXM_RAWX>(buf);}
};

class UBX_RXM_SFRBX:public UBloxPacket {
public:
  gnss_t gnssId;
  uint8_t svId;
  sig_t sigId;
  uint8_t freqId;
  uint8_t numWords;
  uint8_t chn;
  uint8_t version;
  uint8_t reserved0;
  std::vector<uint32_t> dwrd;
  std::unique_ptr<NavMessage> navMessage;
  UBX_RXM_SFRBX(uint8_t* buf):UBloxPacket(buf) {
    size_t pos;
    pos=0;
    buf+=6;
    gnssId= static_cast<gnss_t>(0);readField(gnssId, buf, pos, 1);
    readField(svId,buf,pos);
    sigId.gps_sig= static_cast<gps_sig_t>(0);readField(sigId, buf, pos, 1);
    readField(freqId,buf,pos);
    readField(numWords,buf,pos);
    readField(chn,buf,pos);
    readField(version,buf,pos);
    readField(reserved0,buf,pos);
    for(uint8_t iMeas=0;iMeas<numWords;iMeas++) {
      dwrd.push_back(readField<uint32_t>("dwrd",buf,pos));
    }
    if(gnssId==GPS && sigId.gps_sig==g_L1CA) {
      navMessage=std::unique_ptr<NavMessage>(L1CA::read(&dwrd));
    } else {
      navMessage=nullptr;
    }
  }
  void print() {
    UBloxPacket::print();
    printf("\tgnssId: %d  svId: %d  sigId: %d  freqId: %d  numWords: %d  chn: %d",gnssId,svId,sigId,freqId,numWords,chn);
    if(navMessage) navMessage->print();
  }
  static std::unique_ptr<Packet> read(uint8_t* buf) {return std::make_unique<UBX_RXM_SFRBX>(buf);}
};

extern const char* RXMid[];
extern const packetFactory RXM[];

#endif //PARSE_UBLOX_UBX_RXM_H

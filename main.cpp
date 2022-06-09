#include <iostream>
#include <cstring>

#include "Packet.h"
#include "UBloxPacket.h"
#include "UBX_NAV.h"
#include "UBX_KWAN.h"
#include "UBX_TIM.h"
#include "L1CA.h"
#include <vector>

int main() {
  const char* basename="LOG00092.TXT";
  char infn[256];
  snprintf(infn,256,"/mnt/big/home/chrisj/Desktop/Fluttershy Survey/fluttershy_base_station_220608_210000.ubx");
  FILE* inf=fopen(infn,"rb");
  /*
  char nmeafn[256];
  snprintf(nmeafn,256,"/home/jeppesen/workspace/rollercoasterometer/data/OverTheHill/%s.nmea",basename);
  FILE* nmeaf=fopen(nmeafn,"wt");
  char ppsfn[256];
  snprintf(ppsfn,256,"/home/jeppesen/workspace/rollercoasterometer/data/OverTheHill/%s.pps.csv",basename);
  FILE* ppsf=fopen(ppsfn,"wt");
  fprintf(ppsf,"gpt_tick,utc_sec,utc_ssec\n");

  char icm2fn[256];
  snprintf(icm2fn,256,"/home/jeppesen/workspace/rollercoasterometer/data/OverTheHill/%s.icm2.csv",basename);
  FILE* icm2f=fopen(icm2fn,"wt");
  fprintf(ppsf,"gpt_tick,\n");
  */
  uint64_t pkt_count=0;
  uint8_t packet[65535+8];

  hp_time_t tim_tp{-1,-1};
  uint64_t kwan_tp;
  while(!feof(inf)) {
    size_t pkt_start=ftell(inf);
    packet_result pkttype=read_packet(packet,inf);
    if(pkttype.type==UBlox) {
      printf("0x%08lx  pktCount %10ld:",pkt_start,pkt_count);
      std::unique_ptr<Packet> pkt=UBloxPacket::read(packet);
      UBloxPacket* ubx_pkt=static_cast<UBloxPacket*>(pkt.get());
      ubx_pkt->print();
      if(ubx_pkt->cls==UBX_NAV_PVT::clsconst && ubx_pkt->id==UBX_NAV_PVT::idconst) {
        // Note that the timestamp of this message is the time at which the position fix is valid. This
        // means that the position fix has already been calculated, and therefore the time is in the past (as
        // far as would be concerned in real-time).
      //  ((UBX_NAV_PVT*)(ubx_pkt))->RMC(nmeaf);
      //  ((UBX_NAV_PVT*)(ubx_pkt))->GGA(nmeaf);
      } else if(ubx_pkt->cls==UBX_KWAN_TP::clsconst && ubx_pkt->id==UBX_KWAN_TP::idconst) {
        // This is the measured time on the Teensy GPT of the time pulse, in 60MHz subseconds
        printf("kwan_tp!");
        if(tim_tp.sec>0) {
          kwan_tp=ubx_pkt->minutes*3'600'000'000+((UBX_KWAN_TP*)(ubx_pkt))->tc;
          // We have a valid predicted time of this pulse, from a previous TIM_TP message
        //  fprintf(ppsf,"%ld,%ld,%.15lf\n",kwan_tp,tim_tp.sec,tim_tp.ssec);
        }
      } else if(ubx_pkt->cls==UBX_TIM_TP::clsconst && ubx_pkt->id==UBX_TIM_TP::idconst) {
        // This is the predicted time of the *next* time pulse
        printf("tim_tp!");
        tim_tp=((UBX_TIM_TP*)(ubx_pkt))->get();
      }
      printf("\n");
    } else {
      printf("0x%08lx  pktCount %10ld: packet type %d\n",pkt_start,pkt_count,pkttype.type);
      if(pkt_count==1000) {
        printf("stop!");
      }
    }
    pkt_count++;
  }
  UBloxPacket::printStats();
}

#include "source/audio-connection.hpp"
#include <cassert>
#include <iostream>
using namespace sd_audio_connection;
int main() {
  assert(port_device("output-wired_headphone",false)==8);
  assert(port_device("output-wired_headset",false)==4);
  assert(port_device("input-wired_headset",true)==0x80000010u);
  assert(port_device("output-sco_headset",false)==0x10);
  assert(port_device("output-a2dp_headphones",false)==0x80);
  assert(port_device("analog-output-headphones",false)==8);
  assert(port_device("output-parking",false)==0);
  assert(port_device("null",false)==0);
  assert(!present(1,true)&&!present(1,false));
  assert(present(2,false)&&present(0,true)&&!present(0,false));
  assert(endpoint_device("bluez5","a2dp_sink","",false)==0x80);
  assert(endpoint_device("bluez","sco","",false)==0x10);
  assert(endpoint_device("bluez5","","handsfree-head-unit",true)==0x80000008u);
  assert(endpoint_device("alsa","sco","",false)==0);
  assert(device_matches(0x100,0x80)&&!device_matches(8,4));
  assert(address_matches("AA:BB:CC:DD:EE:FF","aa_bb_cc_dd_ee_ff"));
  assert(!address_matches("AA:BB:CC:DD:EE:FF","aa_bb_cc_dd_ee_00"));
  assert(!address_matches("foreign",""));
  std::cout<<"AUDIO_CONNECTION_PORTS=passed\n";
}

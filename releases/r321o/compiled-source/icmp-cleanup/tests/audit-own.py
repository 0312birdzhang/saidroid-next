from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[3];b=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();module=json.loads((b/'icmp-cleanup286-module-boundary-v1.json').read_text());encoded=json.loads((b/'icmp-cleanup286-encoded-v1-boundary.json').read_text());prototype=json.loads((b/'icmp-cleanup286-prototype-v1.json').read_text());own=json.loads((b/'icmp-cleanup286-own-v1.json').read_text());assert all(v['passed']for v in [module,encoded,prototype,own]);assert module['changed_classes']==['java/net/Inet6AddressImpl.class']and module['unmodified_classfiles_byte_identical']and module['all_other_classes_byte_identical']and not module['added_members'];assert encoded['changed_jars']==['java/dex/art/core-oj.jar']and not encoded['new_flags']and not encoded['canonical_member_flag_changes']and encoded['all_existing_effective_flags_preserved'];assert encoded['core_module_manifest_sha256']==module['module_manifest_sha256']==own['module_manifest_sha256'];assert prototype['files']==1953 and prototype['symlinks']==5 and prototype['all_other_bytes_identical'];assert own['private_data_removed']and own['source_sha256']==sha(r/'scripts/api29/tests/network/Network286ReachabilityContract.java');assert own['prototype_proof_sha256']==sha(b/'icmp-cleanup286-prototype-v1.json');assert len(own['results'])==4
metrics=[]
for row in own['results']:
 assert row['code']==0 and not row['server_errors'];v=row['actual'];assert v['uid']==65534 and v['images']==9 and v['fd_after']==v['fd_before']==26;assert len(v['results'])==4;assert len(row['tcp_accepted'])==(32 if row['which']=='after'and not row['allowed']else 0);calls=0;errors=0
 for index,z in enumerate(v['results']):
  assert bool(z.get('raw_socket_opened'))==row['allowed']
  if not row['allowed']:assert z['raw_socket_errno']==13
  assert len(z['calls'])==(16 if index<2 else 1)
  for call in z['calls']:
   calls+=1
   if row['which']=='before'and not row['allowed']:assert call['error']=='java.lang.NullPointerException'and'isSocket$'in call['message'];errors+=1
   else:assert'error'not in call and call['reachable']is(index<2)
 assert calls==34;metrics.append(dict(label=row['label'],calls=calls,actual_null_fd_crashes=errors,tcp_connections=len(row['tcp_accepted']),fd_before=v['fd_before'],fd_after=v['fd_after']))
source=r/'scripts/api29/core/icmp-cleanup-compat';meta=json.loads((source/'sources.json').read_text());entry=meta['files']['java/net/Inet6AddressImpl.java'];assert sha(source/'java/net/Inet6AddressImpl.java')==entry['sha256']and sha(r/entry['baseline_source'])==entry['baseline_sha256']and sha(r/entry['reference'])==entry['reference_sha256'];old=(r/entry['baseline_source']).read_text();new=(source/'java/net/Inet6AddressImpl.java').read_text();old_block='''        } finally {
            try {
                Libcore.os.close(fd);
            } catch (ErrnoException e) { }
        }

        return false;
''';new_block='''        } finally {
            if (fd != null) {
                try {
                    Libcore.os.close(fd);
                } catch (ErrnoException e) { }
            }
        }

        return false;
''';assert old.count(old_block)==1 and old.replace(old_block,new_block)==new and new_block.strip()in(r/entry['reference']).read_text()
raw=json.loads((b/'network285-icmp-v3-vm.json').read_text());assert raw['passed']and raw['private_data_removed'];assert all(z['actual']['results'][0]['raw_reply_matches']for z in raw['results'])and all(z['raw_reply_matches']for z in raw['system_socket']['actual']['results']);v1=json.loads((b/'network285-icmp-v1-vm.json').read_text());v2=json.loads((b/'network285-icmp-v2-vm.json').read_text());assert not v1['passed']and not v2['passed']and v1['private_data_removed']and v2['private_data_removed'];assert all('java.lang.NoSuchMethodError'==z['actual']['results'][0]['java_icmp_error']['class']for z in v1['results'][:2]);assert all(z['actual']['results'][0]['java_reachable_error']['class']=='java.lang.NullPointerException'for z in v2['results'][:2]);assert v2['ping_group_range'].split()==['1','0']
record=dict(passed=True,scope='Canonical Android10 nullable ICMP FD cleanup only. Four actual ordinary-UID VM rows/136 calls, two real address families, real ICMP allowed and denied, 32 independent TCP accepts after denial, 34 baseline nullFD crashes, no FD leak and unreachable targets false. V1 hiddenAPI refusal/V2 discovered crash retained, raw genuine IPv4/IPv6 replies independently match system sockets. This does not fix or prove phone external Google ICMP, original CTS, hostname, TLS, trust or network configuration.',changed_classes=module['changed_classes'],metrics=metrics,existing_members_flags_native_preserved=True,current_module_boundary_sha256=sha(b/'icmp-cleanup286-module-boundary-v1.json'),encoded_boundary_sha256=sha(b/'icmp-cleanup286-encoded-v1-boundary.json'),prototype_boundary_sha256=sha(b/'icmp-cleanup286-prototype-v1.json'),raw_own_sha256=sha(b/'icmp-cleanup286-own-v1.json'),source_sha256=entry['sha256'],canonical_source_sha256=entry['reference_sha256'],phone_executed=False,full_module_passed=False);out=b/'icmp-cleanup286-own-v1-audit.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

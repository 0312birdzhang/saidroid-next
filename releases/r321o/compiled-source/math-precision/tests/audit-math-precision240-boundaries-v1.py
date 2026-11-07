from pathlib import Path
import collections,hashlib,json
b=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();raw=b/'original-math-precision240-selected-v1.json';d=json.loads(raw.read_text());paths=json.loads((b/'math-precision240-own-paths-v1.json').read_text());oracle=json.loads((b/'math-precision240-mpfr-sample-contract-v1.json').read_text());agg={};ordered={};failures={}
for label in ['before237','companion240','full240']:
 rows=[r for r in d['results']if r['runtime']==label];assert len(rows)==8;counts=collections.Counter();events=[];failed=[]
 for r in rows:
  counts.update({k:r[k]for k in ['tests','failures','assumptions','real_passed']});events+=r['events'];failed += [e[1]for e in r['events']if e[0]=='failure']
 assert counts==dict(tests=216,failures=3 if label=='before237'else 0,assumptions=0,real_passed=213 if label=='before237'else 216)
 agg[label]=dict(counts);ordered[label]=[e for e in events if e[0]in['start','finish']];failures[label]=failed
assert ordered['before237']==ordered['companion240']==ordered['full240']
assert len([e for e in ordered['full240']if e[0]=='start'])==len({e[1]for e in ordered['full240']if e[0]=='start'})==216
assert not failures['full240']and not failures['companion240']and len(failures['before237'])==3
assert paths['passed']and len(paths['results'])==3 and all(any('MathPrecision240Contract.call' in t for t in row['jit_evidence'])for row in paths['results'])
assert paths['results'][-1]['marker']=='MATH_PRECISION240_CONTRACT=PASS|boundary=full240|checks=43'
assert oracle['passed']and oracle['samples']==20575 and all(v<=1 for v in oracle['max_error_ulps'].values())and not oracle['failures']
record=dict(scope='Eight whole original mathematical classes including CSV and StrictMath; same216unique ordered original methods213PASS3FAIL before to216PASS0FAIL after. Independent native MPFR20575 and actualreflection/cold/warmedJITfivefunctions43checks. Whole selected CSV passed, not fullmodule/phone/formalCTSacceptance.',passed=True,counts=agg,same_ordered_callbacks=True,unique_original_tests=216,fixed_original_tests=failures['before237'],whole_csv_passed=True,whole_module_passed=False,formal_module_acceptance=False,phone_staged=False,raw_sha256=sha(raw),paths_sha256=sha(b/'math-precision240-own-paths-v1.json'),oracle_sha256=sha(b/'math-precision240-mpfr-sample-contract-v1.json'))
p=b/'math-precision240-boundaries-v1-audit.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

#!/usr/bin/env python3
"""Verify cache rejection, full-directory exchange and restoration without a phone."""
from pathlib import Path
import tempfile,importlib.util,json,hashlib,os
spec=importlib.util.spec_from_file_location('cache',Path(__file__).with_name('app-aot-cache.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='saidroid-cache-transaction-')as directory:
 b=Path(directory);home=b/'apps';app=home/'org.example.cache';version=app/'versions'/'v1';version.mkdir(parents=True);apk=version/'base.apk';apk.write_bytes(b'original-apk');root=b/'runtime';root.mkdir();(root/'runtime.jar').write_bytes(b'exact-runtime');source=b/'source';source.mkdir()
 record=dict(package='org.example.cache',apk=str(apk),signers=['test-signer'],apkSha256=m.digest(apk));(app/'record.json').write_text(json.dumps(record));identity=dict(apk_sha256=m.digest(apk));manifest=dict(schema='saidroid-app-aot-cache-v2',identity=identity,cache_key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest(),install_preconditions=dict(package=record['package'],apk=str(apk),signers=record['signers'],apk_sha256=record['apkSha256'],runtime_inputs={'runtime.jar':m.digest(root/'runtime.jar')}),files={})
 for name in ['base.odex','base.vdex']:
  p=source/name;p.write_bytes(('new-'+name).encode());manifest['files'][name]=dict(bytes=p.stat().st_size,sha256=m.digest(p))
 (source/'saidroid-cache-manifest.json').write_text(json.dumps(manifest));old=version/'oat/arm64';old.mkdir(parents=True);(old/'baseline-only').write_bytes(b'preserve')
 (source/'base.vdex').write_bytes(b'corrupted')
 try:m.install(source,record['package'],root,'bad',home)
 except RuntimeError as e:assert 'payload mismatch'in str(e)
 else:raise AssertionError('Corrupt cache accepted')
 assert (old/'baseline-only').read_bytes()==b'preserve'and not (old.parent/'arm64.saved-bad').exists()
 (source/'base.vdex').write_bytes(b'new-base.vdex');m.install(source,record['package'],root,'baseline',home);assert not (old/'baseline-only').exists()and (old/'base.odex').read_bytes()==b'new-base.odex'
 m.switch(record['package'],'baseline','optimized',home);assert (old/'baseline-only').read_bytes()==b'preserve'and not (old/'base.odex').exists()
 m.switch(record['package'],'optimized','baseline-again',home);assert (old/'base.odex').read_bytes()==b'new-base.odex';assert apk.read_bytes()==b'original-apk'and (root/'runtime.jar').read_bytes()==b'exact-runtime'
 (root/'runtime.jar').write_bytes(b'changed')
 try:m.install(source,record['package'],root,'runtime-mismatch',home)
 except RuntimeError as e:assert 'Runtime input mismatch'in str(e)
 else:raise AssertionError('Wrong runtime accepted')
 print('APP_CACHE_TRANSACTION=PASS|corrupt-rejected|old-directory-preserved|atomic-install|baseline-restore|optimized-restore|runtime-mismatch-rejected|apk-untouched')

# Adoption must preserve payload inodes, reject unsafe upload trees and restore
# the previous cache when publication fails. These checks use real renames.
import shutil
from unittest.mock import patch
with tempfile.TemporaryDirectory(prefix='saidroid-cache-adoption-')as directory:
 b=Path(directory);home=b/'apps';app=home/'org.example.cache';version=app/'versions/v1';version.mkdir(parents=True);apk=version/'base.apk';apk.write_bytes(b'original-apk');root=b/'runtime';root.mkdir();(root/'runtime.jar').write_bytes(b'exact-runtime')
 record=dict(package='org.example.cache',apk=str(apk),signers=['test-signer'],apkSha256=m.digest(apk));(app/'record.json').write_text(json.dumps(record));identity=dict(apk_sha256=m.digest(apk));manifest=dict(schema='saidroid-app-aot-cache-v2',identity=identity,cache_key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest(),install_preconditions=dict(package=record['package'],apk=str(apk),signers=record['signers'],apk_sha256=record['apkSha256'],runtime_inputs={'runtime.jar':m.digest(root/'runtime.jar')}),files={})
 seed=b/'seed';seed.mkdir(mode=0o700)
 for name in ['base.odex','base.vdex']:
  p=seed/name;p.write_bytes(('valid-'+name).encode());manifest['files'][name]=dict(bytes=p.stat().st_size,sha256=m.digest(p))
 (seed/'saidroid-cache-manifest.json').write_text(json.dumps(manifest));old=version/'oat/arm64';old.mkdir(parents=True);(old/'baseline').write_bytes(b'rollback-cache')
 snapshot=lambda folder:{p.name:(p.read_bytes(),p.stat().st_ino)for p in folder.iterdir()};before=snapshot(old)
 for case in ['extra-entry','writable-directory','hardlinked-payload','symlinked-payload','corrupt-payload']:
  source=b/case;shutil.copytree(seed,source)
  if case=='extra-entry':(source/'unexpected').write_bytes(b'no')
  elif case=='writable-directory':source.chmod(0o777)
  elif case=='hardlinked-payload':(source/'base.odex').unlink();os.link(seed/'base.odex',source/'base.odex')
  elif case=='symlinked-payload':(source/'base.odex').unlink();(source/'base.odex').symlink_to(seed/'base.odex')
  else:(source/'base.odex').write_bytes(b'corrupt')
  try:m.install(source,record['package'],root,case,home,adopt_source=True)
  except RuntimeError:pass
  else:raise AssertionError('Unsafe adopted cache accepted: '+case)
  assert snapshot(old)==before and source.is_dir()and not(old.parent/('arm64.saved-'+case)).exists()
  shutil.rmtree(source)
 source=b/'publish-failure';shutil.copytree(seed,source);original_rename=os.rename
 def fail_publication(src,dst):
  if Path(src).name=='arm64.pending-publication-failure'and Path(dst)==old:raise OSError('injected cache publication failure')
  return original_rename(src,dst)
 with patch.object(m.os,'rename',side_effect=fail_publication):
  try:m.install(source,record['package'],root,'publication-failure',home,adopt_source=True)
  except OSError as failure:assert 'injected'in str(failure)
  else:raise AssertionError('Publication failure not propagated')
 assert snapshot(old)==before and(old.parent/'arm64.pending-publication-failure/base.odex').read_bytes()==b'valid-base.odex'
 source=b/'adopt-good';shutil.copytree(seed,source);inodes={n:(source/n).stat().st_ino for n in manifest['files']};result=m.install(source,record['package'],root,'adopt-good',home,adopt_source=True)
 assert result['source_adopted']and not source.exists()and {n:(old/n).stat().st_ino for n in manifest['files']}==inodes
 assert snapshot(old.parent/'arm64.saved-adopt-good')==before
 assert apk.read_bytes()==b'original-apk'and(root/'runtime.jar').read_bytes()==b'exact-runtime'
 print('APP_CACHE_ADOPTION=PASS|inodes-preserved|unsafe-trees-rejected|publication-rollback|old-cache-preserved|apk-runtime-unchanged')

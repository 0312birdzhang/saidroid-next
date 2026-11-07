"""Honor original runner policy options without granting writable APK requests authority."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET

def hidden_api_checks(runner):
    values=[o['value']for o in runner.get('options',[])if o.get('name')=='hidden-api-checks']
    if not values:return True
    if len(values)!=1 or values[0]not in['true','false']:
        raise ValueError('Original hidden-api-checks option is ambiguous or invalid')
    return values[0]=='true'

def original_disabled_runners(xml,package):
    matches=[]
    # LibcoreTest is the original CTS subclass of AndroidJUnitTest. ICU uses
    # two annotation shards for the same APK; both original runners must
    # explicitly request the same false policy before accepting that package.
    allowed={'com.android.tradefed.testtype.AndroidJUnitTest','com.android.compatibility.testtype.LibcoreTest'}
    for test in ET.fromstring(xml).findall('test'):
        if test.get('class')not in allowed:continue
        options=[dict(o.attrib)for o in test.findall('option')]
        if any(o.get('name')=='package'and o.get('value')==package for o in options):
            matches.append(dict(options=options))
    if not matches or any(hidden_api_checks(runner)for runner in matches):
        raise ValueError('Original runner does not unambiguously disable hidden API checks')
    return len(matches)

def verify_original_hidden_api_override(config,out):
    if config.get('hidden_api_checks',True)is True:return None
    if config.get('hidden_api_checks')is not False:raise ValueError('Invalid hidden API runner policy')
    evidence=next((p for p in out.parents if(p/'module-plan.json').is_file()and(p/'official-index.json').is_file()),None)
    if evidence is None:raise ValueError('Original official configuration is required')
    plan=json.loads((evidence/'module-plan.json').read_text())
    module=next(m for m in plan['modules']if m['module']==config['module'])
    if module['config_sha256']!=config.get('official_config_sha256'):
        raise ValueError('Official configuration identity differs')
    from official_archive import Archive
    source=out/('original-hidden-api-policy-'+Path(module['config_source']).name)
    metadata=Archive(evidence/'official-index.json').extract(module['config_source'],source)
    if metadata['sha256']!=module['config_sha256']or hashlib.sha256(source.read_bytes()).hexdigest()!=module['config_sha256']:
        raise ValueError('Official configuration bytes differ')
    count=original_disabled_runners(source.read_bytes(),config['test_package'])
    return dict(config_sha256=module['config_sha256'],config_source=module['config_source'],hidden_api_checks=False,matching_original_runners=count)

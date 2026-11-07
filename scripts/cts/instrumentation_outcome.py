"""Retain runner-level failures that need not emit an individual test status."""
import re

def inspect_finish(finish, counts):
    finish=finish or {};results=finish.get('results')or {};stream=str(results.get('stream')or'')
    failures=list(re.finditer(r'Tests run:\s*(\d+),\s*Failures:\s*(\d+)(?:,\s*Errors:\s*(\d+))?',stream))
    success=list(re.finditer(r'OK\s*\(\s*(\d+)\s+tests?\s*\)',stream))
    reported_tests=reported_failures=reported_errors=None
    if failures:
        match=failures[-1];reported_tests=int(match[1]);reported_failures=int(match[2]);reported_errors=int(match[3]or 0)
    elif success:
        reported_tests=int(success[-1][1]);reported_failures=reported_errors=0
    marker='FAILURES!!!'in stream or bool(re.search(r'There (?:was|were)\s+\d+\s+(?:failure|error)',stream))
    unexpected_code=bool(finish)and finish.get('code')!=-1
    message=results.get('shortMsg')or results.get('longMsg')
    has_failures=marker or unexpected_code or bool(message)or bool((reported_failures or 0)+(reported_errors or 0))
    individual=counts.get('failed',0)+counts.get('error',0)
    total=(reported_failures or 0)+(reported_errors or 0)
    return dict(callback_present=bool(finish),finish_code=finish.get('code'),reported_tests=reported_tests,
                reported_failures=reported_failures,reported_errors=reported_errors,
                failure_summary_marker=marker,has_failures=has_failures,
                unattributed_failures=max(0,total-individual),message=message)

# Verified from the original 10_r16 tradefed.jar InstrumentationTest constructor.
# The ordinary AndroidJUnitTest inherits this value and passes timeout_msec.
TRADEFED_DEFAULT_TEST_TIMEOUT_MSEC=300000

def test_timeout_msec(runner):
    values=runner.get('options',[])
    declared=next((o['value']for o in values if o.get('name')=='instrumentation-arg'and o.get('key')=='timeout_msec'),None)
    value=declared if declared is not None else next((o['value']for o in values if o.get('name')=='test-timeout'),str(TRADEFED_DEFAULT_TEST_TIMEOUT_MSEC))
    if not re.fullmatch(r'[0-9]+',str(value)):raise ValueError('Unsupported original per-test timeout '+str(value))
    return int(value)

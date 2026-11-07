# Hardware identity startup evidence

The baseline is the exact SdRuntime source matching the deployed R317b runtime
(the R292 receiver-guard source). The source pair adds only a public Build-field
startup log after SDK29 validation. It has no application-specific branch.

The isolated R318b build scripts and byte/hidden-API audits are retained in
`build/evidence/device-model318-20261104/fix-v2/`. This module avoids incorporating
unrelated pre-existing drift from the canonical `scripts/device/SdRuntime.java`.
Hardware values are provisioned through `hardware_identity.py` and build.prop;
the startup log observes them and does not override them.

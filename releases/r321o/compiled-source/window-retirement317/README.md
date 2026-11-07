# Retired child surface lifetime candidate

Retain a removed layer and its compositor role outside the parent until the
Wayland connection ends. The existing implementation retained producer queues
but detached their buffers and destroyed roles after one parent frame callback;
that callback does not prove the compositor GPU has finished with the texture.

This is an isolated candidate for the real QQ long-press then keyboard-reopen
compositor failure. Causality and a long-term stability fix remain unproven.
Retired IDs remain hidden after late swaps/layout calls; no role is recreated.
Existing process-lifetime queue allocations are still retained; compositor
references now share that lifetime. Repeated popups can retain more resources
until the application exits. No vibration support or rendering fallback added.

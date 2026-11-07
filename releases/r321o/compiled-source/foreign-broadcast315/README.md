# Package-scoped broadcasts with no local receiver

The local ActivityManager implementation returns without delivery when an
implicit broadcast names another package. It must not invoke matching local
receivers, and sendBroadcast must not throw simply because no local target
exists. Same-package local/remote delivery and existing permission/user guards
remain in force. Cross-application receiver delivery is still unavailable.

The baseline source must reproduce the accepted r314c ActivityManager class
files exactly before the overlay is compiled. SDK 29/34 fixture coverage:
foreign/absent package sends return without local delivery, local package and
unscoped sends reach the registered receiver, and the process remains alive.

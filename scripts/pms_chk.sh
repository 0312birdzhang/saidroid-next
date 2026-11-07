F=/tmp/ap/SdPackageManagerService.java
grep -n "getPersistentApplications" $F | head -3
sed -n "$(grep -n 'getPersistentApplications' $F | head -1 | cut -d: -f1),+3p" $F
echo "=== queryIntentActivities 附近 ==="
sed -n "$(grep -n 'queryIntentActivities' $F | head -1 | cut -d: -f1),+3p" $F

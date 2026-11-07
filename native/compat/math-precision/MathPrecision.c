/* Actual Androidfdlibm entrypoints; ordinary libc symbols unchanged. */
extern double ieee_sin(double);
__attribute__((visibility("default"))) double Math_sin(double x) { return ieee_sin(x); }
extern double ieee_cos(double);
__attribute__((visibility("default"))) double Math_cos(double x) { return ieee_cos(x); }
extern double ieee_tan(double);
__attribute__((visibility("default"))) double Math_tan(double x) { return ieee_tan(x); }
extern double ieee_cbrt(double);
__attribute__((visibility("default"))) double Math_cbrt(double x) { return ieee_cbrt(x); }
extern double ieee_pow(double,double);
__attribute__((visibility("default"))) double Math_pow(double x, double y) { return ieee_pow(x,y); }

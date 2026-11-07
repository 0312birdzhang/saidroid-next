/* Component-private Android trigonometry; ordinary libc symbols untouched. */
extern double ieee_sin(double);
__attribute__((visibility("default"))) double Math_sin(double value) { return ieee_sin(value); }
extern double ieee_cos(double);
__attribute__((visibility("default"))) double Math_cos(double value) { return ieee_cos(value); }
extern double ieee_tan(double);
__attribute__((visibility("default"))) double Math_tan(double value) { return ieee_tan(value); }

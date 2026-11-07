/* Component-private Android Math.tan backend. Ordinary libc tan stays intact. */
extern double ieee_tan(double);

/* The API29 native entry's binary64 argument and return value use d0 on ARM64.
 * The captured older JNI implementation also passes its binary64 value in d0;
 * its unused JNI environment/class integer registers are intentionally ignored.
 */
__attribute__((visibility("default"))) double Math_tan(double value) {
    return ieee_tan(value);
}

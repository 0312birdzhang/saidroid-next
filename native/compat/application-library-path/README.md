# Application JNI directory boundary

The host's `java.library.path` contains framework/host roots. The application's
`ApplicationInfo.nativeLibraryDir` remains exclusively in the application
class loader's native directory list. Putting it in the property as well makes
Android `DexPathList.systemNativeLibraryDirectories` misclassify application
libraries as system libraries. App loaders that distinguish these lists can
then skip the real ART load and its JNI initialization.

The baseline snapshot reproduces the accepted R308 host executable byte for
byte. The candidate removes only the duplicated application directory from
that property. It does not alter APKs or add package-specific paths.

A signed ordinary-app fixture checks that its directory is absent from system
paths, remains present in the app class loader, and loads a real JNI ELF by
name then absolute path. Its native state progresses 81 to 82 with exactly one
JNI_OnLoad. R320g fails the boundary assertion; R320h passes on SDK29 and SDK34.

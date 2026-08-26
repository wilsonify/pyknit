# pyKnit Android

This is a native Android shell around the existing pyKnit Python domain code.

## Architecture

- **Python remains the source of truth.** `pyknit/chaquopy/mobile_api.py` calls the existing
  modules in `pyknit/pyscript/_demos`; it does not reimplement their formulas.
- **Chaquopy embeds CPython** in the APK. The app packages the repository's
  `pyknit` package and its pinned runtime dependencies, so calculations work
  offline after installation.
- **Kotlin owns only Android concerns:** lifecycle, navigation, form controls,
  and the stepper UI. It does not parse knitting instructions or calculate
  garment dimensions.
- **Planner → Simulator:** planner calls return the canonical `sim_plan`.
  Opening the simulator copies its exact `instructions` into the editable
  field. If the field is changed, the plan metadata is discarded and the
  simulator runs the edited instructions as a manual pattern.

The six preserved tools are available from the native navigation: Raglan
Sweater Planner, Hat Crown Planner, Sleeve Decreases, Sock Calculator, Knit
Simulator, and Yarn & Time Estimator.

## Build

From this directory, with Android SDK platform 34 and JDK 17 installed:

```console
./gradlew assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

Chaquopy downloads the pinned Python dependencies on the first build. The
resulting APK contains them and does not require a network connection at run
time. The build also needs the Android SDK location configured through
`ANDROID_HOME` or `android/local.properties`.

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.diffplug.spotless")
}

spotless {
    kotlin {
        target("src/**/*.kt")
        ktlint("1.1.1")
    }
}

android {
    namespace = "org.pyknit.android"
    compileSdk = 34

    defaultConfig {
        applicationId = "org.pyknit.android"
        minSdk = 24
        targetSdk = 34
        versionCode = ((project.findProperty("versionCode") as String?)?.toIntOrNull()) ?: 1
        versionName = (project.findProperty("versionName") as String?) ?: "0.1.0"
    }

    // The offline web runtime lives in underscore-prefixed asset dirs
    // (_assets/, _shared/, _wheel/), which AAPT ignores by default
    // (<dir>_*). Keep every other default ignore rule, drop only that one.
    aaptOptions {
        ignoreAssetsPattern = "!.svn:!.git:!.ds_store:!*.scc:.*:!CVS:!thumbs.db:!picasa.ini:!*~"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // Local-asset WebView hosting (WebViewAssetLoader) + back-press dispatcher.
    implementation("androidx.webkit:webkit:1.10.0")
    implementation("androidx.activity:activity:1.9.3")
}

// Stage the demos/ web app + offline PyScript/Pyodide runtime into
// src/main/assets/dist before merging assets, so every APK build is
// reproducible and fully offline. Override the interpreter with
// -PwebPython=... or $ANDROID_WEB_PYTHON (default: python3, or python
// on Windows where the python3 alias usually does not exist).
val defaultWebPython = if (System.getProperty("os.name").startsWith("Windows")) "python" else "python3"
val webPython: String = (project.findProperty("webPython") as String?)
    ?: System.getenv("ANDROID_WEB_PYTHON")
    ?: defaultWebPython

tasks.register<Exec>("stageWebAssets") {
    description = "Stage offline web assets for the WebView APK."
    group = "build"
    inputs.dir(rootDir.resolve("../demos"))
    inputs.dir(rootDir.resolve("../scripts"))
    inputs.dir(rootDir.resolve("../build/pyodide"))
    inputs.dir(rootDir.resolve("../build/pyscript"))
    inputs.dir(rootDir.resolve("../build/wheels"))
    inputs.dir(rootDir.resolve("../build/wheel"))
    outputs.dir(layout.projectDirectory.dir("src/main/assets/dist"))
    commandLine(
        webPython,
        rootDir.resolve("../scripts/package_android_assets.py").absolutePath,
        "--root",
        rootDir.resolve("..").absolutePath,
    )
}

tasks.register<Exec>("auditWebAssets") {
    description = "Audit staged web assets for completeness/offline use."
    group = "verification"
    dependsOn("stageWebAssets")
    commandLine(
        webPython,
        rootDir.resolve("../scripts/audit_android_assets.py").absolutePath,
        "--root",
        rootDir.resolve("..").absolutePath,
    )
}

tasks.named("preBuild") {
    dependsOn("stageWebAssets")
}

// merge*Assets must not race stageWebAssets: preBuild alone does not order
// them (this bit us with org.gradle.parallel=true — the APK shipped a
// half-staged dist/). Depend on staging explicitly for every variant.
tasks.matching { it.name.matches(Regex("merge.*Assets")) }.configureEach {
    dependsOn("stageWebAssets")
}

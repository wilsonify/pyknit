plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
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
        versionCode = 1
        versionName = "0.1.0"
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
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
    implementation("com.google.android.material:material:1.11.0")
}

chaquopy {
    sourceSets {
        getByName("main") {
            // Use the canonical repository package; algorithms are not copied.
            // This source root contains pyknit/chaquopy/mobile_api.py as the adapter.
            srcDir("../../")
            include("pyknit/**/*.py")
        }
    }
    defaultConfig {
        version = "3.11"
        // Machine-specific build Python must not be hard-coded (it broke CI).
        // Default to Chaquopy's PATH discovery (python3.11/python3/python), and
        // allow an explicit override via -Pchaquopy.python=... or
        // $CHAQUOPY_PYTHON for local builds.
        val buildPy: String? = project.findProperty("chaquopy.python") as String?
            ?: System.getenv("CHAQUOPY_PYTHON")
        if (buildPy != null) {
            buildPython(buildPy)
        }
        pip {
            install("-r", "../requirements-android.txt")
        }
    }
}

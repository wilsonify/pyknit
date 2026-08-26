plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
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
        buildPython("C:/Users/toman/AppData/Roaming/uv/python/cpython-3.11.15-windows-x86_64-none/python.exe")
        pip {
            install("-r", "../requirements-android.txt")
        }
    }
}

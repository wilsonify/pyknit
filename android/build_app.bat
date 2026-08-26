@echo off
set ANDROID_PREFS_ROOT=
set ANDROID_SDK_HOME=
set ANDROID_USER_HOME=C:\Users\toman\.android
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot
call .\gradlew.bat assembleDebug

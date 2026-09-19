#!/bin/bash
set -e

echo "===================================================="
echo "  🌸 Building Jenna AI Companion Native Android APK  "
echo "===================================================="

SDK="/data/data/com.termux/files/home/android-sdk"
ANDROID_JAR="$SDK/platforms/android-34/android.jar"
BUILD_TOOLS="$SDK/build-tools/34.0.0"
D8="bash $BUILD_TOOLS/d8"
APKSIGNER="bash $BUILD_TOOLS/apksigner"

PROJECT_ROOT="/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna"
ANDROID_ROOT="$PROJECT_ROOT/apps/android"
BUILD_DIR="$ANDROID_ROOT/build"
OUTPUT_APK="$ANDROID_ROOT/jenna-app.apk"
KEYSTORE="$ANDROID_ROOT/debug.keystore"

echo "[1/7] Cleaning previous build artifacts..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/gen" "$BUILD_DIR/classes" "$BUILD_DIR/dex"

echo "[2/7] Compiling resources with aapt2..."
aapt2 compile --dir "$ANDROID_ROOT/app/src/main/res" -o "$BUILD_DIR/compiled_res.zip"

echo "[3/7] Linking resources & generating R.java..."
aapt2 link \
    -I "$ANDROID_JAR" \
    --min-sdk-version 26 \
    --target-sdk-version 34 \
    --manifest "$ANDROID_ROOT/app/src/main/AndroidManifest.xml" \
    --java "$BUILD_DIR/gen" \
    -o "$BUILD_DIR/base.apk" \
    "$BUILD_DIR/compiled_res.zip" \
    --auto-add-overlay

echo "[4/7] Compiling Java source files with javac..."
find "$ANDROID_ROOT/app/src/main/java" "$BUILD_DIR/gen" -name "*.java" > "$BUILD_DIR/sources.txt"
javac -source 8 -target 8 -d "$BUILD_DIR/classes" -cp "$ANDROID_JAR" @"$BUILD_DIR/sources.txt"

echo "[5/7] Converting bytecode to DEX with d8..."
find "$BUILD_DIR/classes" -name "*.class" > "$BUILD_DIR/classes.txt"
$D8 --output "$BUILD_DIR/dex" --min-api 26 --lib "$ANDROID_JAR" @"$BUILD_DIR/classes.txt"

echo "[6/7] Packaging DEX and Assets into APK..."
cp "$BUILD_DIR/base.apk" "$BUILD_DIR/jenna-unsigned.apk"
cd "$BUILD_DIR/dex"
jar -uf "$BUILD_DIR/jenna-unsigned.apk" classes.dex
cd "$PROJECT_ROOT"

if [ -d "$ANDROID_ROOT/app/src/main/assets" ]; then
    echo "  -> Packaging Antigravity, Cyberpunk & Knowledge Assets (1.25 GB) into APK..."
    cd "$ANDROID_ROOT/app/src/main"
    jar -0uf "$BUILD_DIR/jenna-unsigned.apk" assets
    cd "$PROJECT_ROOT"
fi

echo "[7/8] Aligning APK (4-byte boundary)..."
python3 "$ANDROID_ROOT/zipalign.py" -p 4 "$BUILD_DIR/jenna-unsigned.apk" "$BUILD_DIR/jenna-aligned.apk"

echo "[8/8] Signing APK with apksigner..."
if [ ! -f "$KEYSTORE" ]; then
    echo "  -> Generating debug keystore..."
    keytool -genkeypair -v \
        -keystore "$KEYSTORE" \
        -alias jennadebug \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass jennapass \
        -keypass jennapass \
        -dname "CN=Jenna, OU=AI, O=Antigravity, L=Neo, ST=Cyber, C=IN"
fi

$APKSIGNER sign \
    --ks "$KEYSTORE" \
    --ks-key-alias jennadebug \
    --ks-pass pass:jennapass \
    --key-pass pass:jennapass \
    --out "$OUTPUT_APK" \
    "$BUILD_DIR/jenna-aligned.apk"

echo "===================================================="
echo "  🎉 APK BUILT SUCCESSFULLY: $OUTPUT_APK"
$APKSIGNER verify -v "$OUTPUT_APK"
ls -lh "$OUTPUT_APK"
echo "===================================================="

# Implementation Plan - Create Mobile APK

This plan outlines the steps to build a functional Android APK from the Flutter source code in the `mobile` directory, configured to use the Render backend.

## User Review Required

> [!IMPORTANT]
> The app will now be configured to connect to: `https://propmptwars-hackathon-main.onrender.com/api/`.

## Proposed Changes

### [mobile] (Flutter Project)

#### [MODIFY] [api_service.dart](file:///E:/Projects/PromptWars/recover/mobile/lib/services/api_service.dart)
- Update `baseUrl` to `https://propmptwars-hackathon-main.onrender.com/api/`.

#### [MODIFY] [AndroidManifest.xml](file:///E:/Projects/PromptWars/recover/mobile/android/app/src/main/AndroidManifest.xml)
- Add the following permissions:
    - `android.permission.INTERNET`
    - `android.permission.ACCESS_FINE_LOCATION`
    - `android.permission.ACCESS_COARSE_LOCATION`
    - `android.permission.CALL_PHONE`
    - `android.permission.SEND_SMS`
    - `android.permission.RECEIVE_SMS`

## Execution Steps

1. **Configure Backend URL**: Update `api_service.dart`.
2. **Configure Permissions**: Update `AndroidManifest.xml`.
3. **Build the APK**: Run `flutter build apk --release`.
4. **Locate and Provide APK**: Find and share the path to `app-release.apk`.

## Execution Steps

1. **Set Up Flutter Environment**:
   - Locate Flutter SDK (found at `E:\flutter\bin\flutter.bat`).
   - Initialize the project with `flutter create .` (Completed).
2. **Accept Android Licenses**:
   - Run `flutter doctor --android-licenses` to ensure the build toolchain is ready.
3. **Configure Permissions**:
   - Update `AndroidManifest.xml` with necessary permissions.
4. **Build the APK**:
   - Run `flutter build apk --release` to generate the final APK.
5. **Locate and Provide APK**:
   - Find the generated APK file in `build/app/outputs/flutter-apk/app-release.apk`.

## Verification Plan

### Automated Tests
- N/A (Focusing on build success).

### Manual Verification
- Verify that the APK file exists at the expected path.
- Provide the user with the absolute path to the generated APK.

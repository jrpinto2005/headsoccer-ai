# Android Emulator gRPC API

`emulator_controller.proto` is copied verbatim from the Android Emulator **37.1.11** (build 15917651), found at `$ANDROID_HOME/emulator/lib/emulator_controller.proto`. It is licensed under Apache-2.0 by The Android Open Source Project; the license header is kept in the file.

The Python bindings in `src/hsai/emulator/_proto/` are generated from it by `scripts/gen_protos.sh`. Re-copy the proto and regenerate the bindings whenever the emulator is upgraded.

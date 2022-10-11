@echo off
start cmd /k firebase --project="test" emulators:start --import=./emulator_data --export-on-exit
@echo off
echo Building C++ audio core module...

if exist build rmdir /s /q build
mkdir build
cd build

cmake .. -Dpybind11_DIR=%VIRTUAL_ENV%\Lib\site-packages\pybind11\share\cmake\pybind11
cmake --build . --config Release

cd ..

echo Copying module...
copy build\Release\audio_core_cpp*.pyd .
copy build\Release\audio_core_cpp*.pyd .venv\Lib\site-packages\

echo Done! Module ready to use.
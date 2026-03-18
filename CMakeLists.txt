cmake_minimum_required(VERSION 3.16)
project(audio_core_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)

find_package(pybind11 REQUIRED)

pybind11_add_module(audio_core_cpp
    cpp/src/audio_core.cpp
)
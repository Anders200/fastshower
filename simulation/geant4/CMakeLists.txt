cmake_minimum_required(VERSION 3.16)
project(fastshower_g4)

find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})

find_package(nlohmann_json QUIET)
if(NOT nlohmann_json_FOUND)
    message(STATUS "nlohmann_json not found system-wide, using vendored copy (third_party/nlohmann/json.hpp)")
    include_directories(${CMAKE_SOURCE_DIR}/third_party)
endif()

include_directories(${CMAKE_SOURCE_DIR}/include)

file(GLOB sources ${CMAKE_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${CMAKE_SOURCE_DIR}/include/*.hh)

add_executable(fastshower_g4 fastshower_g4.cc ${sources} ${headers})

if(nlohmann_json_FOUND)
    target_link_libraries(fastshower_g4 ${Geant4_LIBRARIES} nlohmann_json::nlohmann_json)
else()
    target_link_libraries(fastshower_g4 ${Geant4_LIBRARIES})
endif()

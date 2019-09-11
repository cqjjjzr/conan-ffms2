cmake_minimum_required(VERSION 3.14)
project(ffms2)

if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
  include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
else()
  include(conanbuildinfo.cmake)
endif()
conan_basic_setup()

add_compile_definitions(FFMS_EXPORTS _CRT_SECURE_NO_WARNINGS __STDC_CONSTANT_MACROS _WINDOWS _USRDLL FFMS2_EXPORTS)
if ("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
  add_compile_definitions(_DEBUG)
else()
  add_compile_definitions(NDEBUG)
endif()

set(FFMS2_SOURCES src/core/audiosource.cpp
                  src/core/ffms.cpp
                  src/core/filehandle.cpp
                  src/core/indexing.cpp
                  src/core/track.cpp
                  src/core/utils.cpp
                  src/core/videosource.cpp
                  src/core/videoutils.cpp
                  src/core/zipfile.cpp)

add_library(ffms2 SHARED ${FFMS2_SOURCES})
target_link_libraries(ffms2 ${CONAN_LIBS})
include_directories(include)

set_target_properties(ffms2 PROPERTIES PUBLIC_HEADER "include/ffms.h;include/ffmscompat.h")
install(TARGETS ffms2
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        PUBLIC_HEADER DESTINATION include
)

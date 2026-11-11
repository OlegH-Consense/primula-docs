# CMake toolchain file: Windows x86_64 on Linux with MinGW-w64 (stage 23.2).
#
# Used by studio/windows/build-win.sh.  The compilers come from the environment
# (MINGW_CC / MINGW_CXX / MINGW_RC) so that the same file works with the openSUSE
# packages (mingw64-cross-gcc-c++) and with the Debian ones (g++-mingw-w64-x86-64-posix).
# Libraries and packages are looked up only in the Windows Qt (CMAKE_PREFIX_PATH)
# and in the MinGW sysroot; programs (moc, rcc, lrelease ...) come from the host Qt
# through QT_HOST_PATH.  The approach is described in csRESP-windows-cross-build.md.
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

foreach(_var IN ITEMS CC CXX RC)
    set(_value "$ENV{MINGW_${_var}}")
    if(NOT _value)
        if(_var STREQUAL "CC")
            set(_value x86_64-w64-mingw32-gcc)
        elseif(_var STREQUAL "CXX")
            set(_value x86_64-w64-mingw32-g++)
        else()
            set(_value x86_64-w64-mingw32-windres)
        endif()
    endif()
    set(_MINGW_${_var} "${_value}")
endforeach()
set(CMAKE_C_COMPILER   "${_MINGW_CC}")
set(CMAKE_CXX_COMPILER "${_MINGW_CXX}")
set(CMAKE_RC_COMPILER  "${_MINGW_RC}")

# CMAKE_FIND_ROOT_PATH (Windows Qt and the MinGW sysroot) is given by build-win.sh: without it
# "ONLY" restricts nothing and host headers such as /usr/include/GL leak into the compilation.
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

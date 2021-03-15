# Modified from https://gist.github.com/mariospr/a93b211da627d9277b3b01ab04fe249b
set(ROOTFS "/media/patrick/40A1A59F65953017/Docker/rootfs")
set(MULTIARCH "arm-linux-gnueabihf")

set(CMAKE_SYSTEM_NAME "Linux")
set(CMAKE_SYSTEM_PROCESSOR "armv7l")

# Has only been tested with GCC 7+
SET(CMAKE_C_COMPILER "${MULTIARCH}-gcc")
SET(CMAKE_CXX_COMPILER "${MULTIARCH}-g++")
set(CMAKE_CROSSCOMPILING ON)

# Ensure that FIND_PACKAGE() functions and friends look in the rootfs
# only for libraries and header files, but not for programs (e.g perl)
SET(CMAKE_FIND_ROOT_PATH "${ROOTFS}")
SET(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
SET(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
SET(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)


# Need to export this variables for pkg-config to pick them up, so that it
# sets the right search path and prefixes the result paths with the rootfs.
SET(ENV{PKG_CONFIG_PATH} "${ROOTFS}/usr/share/pkgconfig")
SET(ENV{PKG_CONFIG_LIBDIR} "${ROOTFS}/usr/lib/${MULTIARCH}/pkgconfig:${ROOTFS}/usr/lib/pkgconfig")
SET(ENV{PKG_CONFIG_SYSROOT_DIR} "${ROOTFS}")

set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")

# These variables make sure that pkg-config does never discard standard
# include and library paths from the compile and linking flags.
SET(ENV{PKG_CONFIG_ALLOW_SYSTEM_CFLAGS} 1)
SET(ENV{PKG_CONFIG_ALLOW_SYSTEM_LIBS} 1)
SET(PKG_CONFIG_USE_CMAKE_PREFIX_PATH TRUE)

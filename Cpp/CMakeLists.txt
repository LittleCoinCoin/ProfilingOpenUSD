cmake_minimum_required(VERSION 3.12)
set(CMAKE_CXX_STANDARD 20)

set(TargetName "WriteBenchmark")
project (${TargetName})

# Because the USD plugin file directory resolution expects the dlls to be in a "/bin" folder
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/bin" CACHE STRING "" )

### build CppProfiler as a shared library ###
set(BUILD_PROFILER_TESTS OFF)
set(RUNTIME_PROFILER_TESTS OFF)
set(ENABLE_PROFILER ON)
add_subdirectory("ext/CppProfiler") # its name is Profile

### add OpenUSD ###
# copied and adapted from the successful setup in https://github.com/LittleCoinCoin/OpenUSD-setup-vcpkg-template
if(WIN32)
	message("Building for Windows: disabling min/max macros from minwin.h which collide with OpenUSD max member function in robin_growth_policy.h")
	add_compile_definitions(NOMINMAX)
endif()

find_package(TBB CONFIG REQUIRED)
find_package(pxr CONFIG REQUIRED)

### build WriteBenchmark as an executable ###
add_executable(${TargetName} "main.cpp")

# Link WriteBenchmark to OpenUSD, TBB, and Profile
target_link_libraries(${TargetName} PRIVATE 

ar
arch
gf
js
kind
ndr
pcp
plug
sdf
sdr
tf
trace
usd
usdGeom
usdHydra
usdLux
usdMedia
usdPhysics
usdRender
usdShade
usdSkel
usdUI
usdUtils
usdVol
vt
work

TBB::tbb

Profile

)

### Post build commands to copy the runtime plugin dependencies of OpenUSD to a directory where the application can find them ###
add_custom_command(TARGET ${TargetName}
	POST_BUILD

	#### Copy the required plugins to the lib directory. ####
	#### Mandatory for the application to run. ####
	COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/"

	#base plugin file
	COMMAND ${CMAKE_COMMAND} -E copy_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/plugInfo.json" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/"
	
	#for the default asset resolver plugin
	#required even for the very basic action of creating a new stage
	COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/ar"
	COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/ar" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/ar"
	
	#for the scene description format plugin
	#required even for the very basic action of creating a new stage
	COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/sdf"
	COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/sdf" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/sdf"
	
	#for many things (judging by the number of plugin information given in the plugin file)
	#required even for the very basic action of creating a new stage
	COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usd"
	COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/usd" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usd"
	
	#required for any of the built-in prims (sphere, mesh, etc.)
	COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usdGeom"
	COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/usdGeom" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usdGeom"
	
	#required for materials, introduced in the tutorial on simple shading (TestFunction_PixarTutorial_SimpleShading)
	#COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usdShade"
	#COMMAND ${CMAKE_COMMAND} -E copy_directory_if_different "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/lib/usd/usdShade" "${CMAKE_BINARY_DIR}/${TargetName}/$<CONFIG>/lib/usd/usdShade"
)

cmake_minimum_required(VERSION 3.8)
project(panai_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

set(msg_files
  "msg/FrameMeta.msg"
  "msg/DepthProfile.msg"
  "msg/AcousticSpectrum.msg"
  "msg/EnvironmentSample.msg"
  "msg/HeightEstimate.msg"
  "msg/SessionState.msg"
)

set(srv_files
  "srv/TriggerStrike.srv"
  "srv/StartSession.srv"
  "srv/StopSession.srv"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()

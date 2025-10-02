include(GoogleTest)

add_executable(statesurf_hsm_test
  hsm_machine_test.cpp
)

target_include_directories(statesurf_hsm_test PRIVATE
  ${PROJECT_SOURCE_DIR}/cpp/generated
)

target_link_libraries(statesurf_hsm_test PRIVATE
  GTest::gtest_main
)

gtest_discover_tests(statesurf_hsm_test)

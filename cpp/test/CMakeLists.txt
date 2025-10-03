include(GoogleTest)

add_executable(statesurf_hsm_test
  hsm_machine_test.cpp
)

target_compile_features(statesurf_hsm_test PRIVATE cxx_std_11)

if (MSVC)
  target_compile_options(statesurf_hsm_test PRIVATE
    /permissive-
    /W4
    /WX
    /w14242 # conversion warnings
    /w14254 # possible loss of data
    /w14263 # member function does not override any base
    /w14265 # class has virtual functions, but non-virtual destructor
    /w14287 # unsigned/operation mismatch
    /w14296 # pointer truncation warnings
    /w14311 # pointer truncation from bool
    /w14545 /w14546 /w14547 /w14549 # narrow string or cast warnings
    /w14555 # expression with side effects discarded
    /w14619 # dangerous wchar_t to char conversion
    /w14905 /w14906 # wide/narrow string mix
    /w14928 # illegal copy-initialization
  )
else()
  target_compile_options(statesurf_hsm_test PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wsign-conversion
    -Wshadow
    -Wdouble-promotion
    -Wold-style-cast
    -Wnon-virtual-dtor
    -Woverloaded-virtual
    -Werror
  )
endif()

target_include_directories(statesurf_hsm_test PRIVATE
  ${PROJECT_SOURCE_DIR}/cpp/generated
)

target_link_libraries(statesurf_hsm_test PRIVATE
  GTest::gtest_main
)

gtest_discover_tests(statesurf_hsm_test)

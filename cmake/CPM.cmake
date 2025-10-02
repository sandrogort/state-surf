# Minimal CPM shim tailored for this project.

include(FetchContent)

function(CPMAddPackage)
  set(options)
  set(oneValueArgs NAME VERSION GITHUB_REPOSITORY GIT_TAG URL)
  set(multiValueArgs)
  cmake_parse_arguments(CPM "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  if(NOT CPM_NAME)
    message(FATAL_ERROR "CPMAddPackage requires NAME")
  endif()

  if(TARGET ${CPM_NAME})
    return()
  endif()

  if(CPM_URL)
    set(_package_url "${CPM_URL}")
  elseif(CPM_GITHUB_REPOSITORY)
    if(NOT CPM_GIT_TAG)
      message(FATAL_ERROR "CPMAddPackage(${CPM_NAME}) missing GIT_TAG")
    endif()
    set(_package_url "https://github.com/${CPM_GITHUB_REPOSITORY}/archive/refs/tags/${CPM_GIT_TAG}.tar.gz")
  else()
    message(FATAL_ERROR "CPMAddPackage(${CPM_NAME}) needs GITHUB_REPOSITORY or URL")
  endif()

  set(_dest_dir "${CMAKE_BINARY_DIR}/_deps/${CPM_NAME}-src")

  FetchContent_Declare(
    ${CPM_NAME}
    URL ${_package_url}
    SOURCE_DIR ${_dest_dir}
  )

  set(FETCHCONTENT_UPDATES_DISCONNECTED_${CPM_NAME} ON)
  FetchContent_MakeAvailable(${CPM_NAME})
endfunction()

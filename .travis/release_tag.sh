#!/bin/bash -ex

# Local testing options
LOCAL_TEST_MODE="false"
TESTING_GITHUB_TOKEN="make-yourself-one-in-github"


function ensure_running_in_travis_master_branch {
  if [ "$TRAVIS" != "true" ]; then
      echo "Not running this script outside of Travis."
      exit 1
  fi

  if [ "$TRAVIS_BRANCH" != "master" ]; then
      echo "Not pushing a release tag, not on Travis master."
      exit 2
  fi
}

function ensure_only_tagging_on_production_python_version {
  if [ "${TRAVIS_PYTHON_VERSION}" != "2.7" ]; then
    echo "Not release tagging for Python version ${TRAVIS_PYTHON_VERSION}"
    exit 3
  fi
}

function make_temp_repo_directory {
  TMP_REPO_DIR=$(mktemp --directory --suffix _travis_${TRAVIS_BUILD_NUMBER})
}

function clone_repo {
  turn_off_bash_echo
  git clone https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG} ${TMP_REPO_DIR}
  turn_on_bash_echo
}

function turn_off_bash_echo {
  set +x
}

function turn_on_bash_echo {
  set -x
}

function make_release_tag_from_travis_build_number {
  pushd ${TMP_REPO_DIR}

  git checkout ${TRAVIS_COMMIT}
  git tag "${RELEASE_BRANCH_NAME}_${TRAVIS_BUILD_NUMBER}"
  git push origin --tags --quiet

  git tag --force "${RELEASE_BRANCH_NAME}"
  git push --force origin --tags --quiet

  popd
}

function setup_fake_travis_environment {
  echo "Setting up fake Travis environment"
  TRAVIS="true"
  TRAVIS_REPO_SLUG="alphagov/performanceplatform-admin"
  TRAVIS_BRANCH="master"
  TRAVIS_COMMIT="bb7d6b2a29d876d244ccf54381221c1e22b43bc1"
  TRAVIS_BUILD_NUMBER="123456789"
  TRAVIS_PYTHON_VERSION="2.7"
  GH_TOKEN="${TESTING_GITHUB_TOKEN}"
}

if [ "${LOCAL_TEST_MODE}" == "true" ]; then
    setup_fake_travis_environment
    RELEASE_BRANCH_NAME="release_testing"
else
    RELEASE_BRANCH_NAME="release"
fi

ensure_running_in_travis_master_branch
ensure_only_tagging_on_production_python_version
make_temp_repo_directory
clone_repo
make_release_tag_from_travis_build_number

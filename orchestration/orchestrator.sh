#!/bin/bash

# import utilities
source "$fbrd/fb_cli/utils.sh"
source "$fbrd/orchestration/lockfile_utils.sh"

valid_commands="bootstrap destroy"
valid_platforms="aws_lambda azure_functions aws_ec2 azure_linuxvm openfaas_client_vm"
# get valid experiment names
experiments=$(ls -I "*.md" "$fbrd/experiments")

# parse inputs
experiment_name=$1
cmd=$2
platform=$3

# validate inputs
if ! listContainsElement "$experiments" "$experiment_name"  ; then errmsg "Invalid experiment" ; exit 1 ; fi
if ! listContainsElement "$valid_commands" "$cmd"           ; then errmsg "Invalid command" ; exit 1 ; fi
if ! listContainsElement "$valid_platforms" "$platform"     ; then errmsg "Invalid platform" ; exit 1 ; fi

# source the correct platform orchestrator
source "$fbrd/orchestration/${platform}_orchestrator.sh"

case "$cmd" in
    bootstrap)
        create_lock "$experiment_name" "$platform" "build" || exit \
            && bootstrap "$experiment_name" || exit \
            && create_lock "$experiment_name" "$platform" "infra"
        ;;

    destroy)
        create_lock "$experiment_name" "$platform" "destroy" || exit \
            && destroy "$experiment_name" || exit \
            && release_lock "$experiment_name" "$platform" "destroy"
        ;;
esac

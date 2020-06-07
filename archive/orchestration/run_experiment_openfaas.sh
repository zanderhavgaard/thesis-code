#!/bin/bash

source "$fbrd/fb_cli/utils.sh"

# provision infrastructure, run experiment code and then destroy infrastructure

# the experiment name to test
experiment_name=$1
# unique experiment idenfifier for the experiments started in parallel for the different cloud providers
experiment_meta_identifier=$2
# the context of the experiment
experiment_context="$fbrd/experiments/$experiment_name"
# the experiemnt logic file
experiment_python_file="$fbrd/experiments/$experiment_name/$experiment_name.py"
# which client vm
experiment_client_provider="openfaas_client_vm"
# which cloud function provider
experiment_cloud_function_provider="openfaas"
# env vars for the client vm
experiment_client_env="$experiment_context/$experiment_name-openfaas_client_vm.env"

# remote faas-benchmarker directory location
remote_fbrd="/home/ubuntu/faas-benchmarker"

# the interval to check progress on client in seconds
check_progress_interval=600

# ===== create client vm

cd "$experiment_context/openfaas_client_vm"

pmsg "Initializing terraform ..."
bash init.sh "$experiment_name"

pmsg "Creating client vm ..."
terraform apply \
    -auto-approve

pmsg "Outputting variables to $experiment_name-openfaas_client.env ..."
terraform output > "$experiment_client_env"

smsg "Done creating client vm."

# ===== run experiment code

pmsg "Executing experiment code on remote client vm ..."

cd "$experiment_context"

# we should use a unique name for the cluster each time we run the experiment, as if
# we run the experiment back-to-back we can get a race-condition where eksctl will report
# that the cluster name is already taken, as the cluster is still being deleted, so we append
# a random sha to the experiment name
openfaas_eks_cluster_name="$experiment_name-$(date +%s | sha256sum | base64 | head -c 10 ; echo)"

client_user="ubuntu"
client_ip=$(grep -oP "\d+\.\d+\.\d+\.\d+" $experiment_client_env)
key_path="$fbrd/secrets/ssh_keys/experiment_servers"
timestamp=$(date -u +\"%d-%m-%Y_%H-%M-%S\")
logfile="/home/ubuntu/$timestamp-$experiment_meta_identifier-$experiment_cloud_function_provider-$experiment_name.log"
docker_experiment_code_path="/home/docker/faas-benchmarker/experiments/$experiment_name/$experiment_name.py"
docker_env_file_path="openfaas-does-not-need-an-env-file"
dev_mode="False"
verbose="False"
ssh_command="
    nohup bash -c ' \
        bash \$fbrd/eks_openfaas_orchestration/bootstrap_openfaas_eks_fargate.sh $openfaas_eks_cluster_name >> $logfile 2>&1
        ; docker run \
            --rm \
            --mount type=bind,source=\"/home/ubuntu\",target=\"/home/docker/shared\" \
            --mount type=bind,source=\"/home/ubuntu/.ssh\",target=\"/home/docker/key\" \
            -e \"DB_HOSTNAME=\$DB_HOSTNAME\" \
            --network host \
            faasbenchmarker/client:latest \
            python \
            $docker_experiment_code_path \
            $experiment_name \
            $experiment_meta_identifier \
            $experiment_cloud_function_provider \
            $experiment_client_provider \
            $docker_env_file_path \
            $dev_mode \
            $verbose
        >> $logfile 2>&1
        ; bash \$fbrd/eks_openfaas_orchestration/teardown_openfaas_eks_fargate.sh $openfaas_eks_cluster_name >> $logfile 2>&1
        ; scp -o StrictHostKeyChecking=no $logfile ubuntu@\$DB_HOSTNAME:/home/ubuntu/logs/experiments/
        ; [ -f \"/home/ubuntu/ErrorLogFile.log\" ] && scp -o StrictHostKeyChecking=no /home/ubuntu/ErrorLogFile.log \
            ubuntu@\$DB_HOSTNAME:/home/ubuntu/logs/error_logs/$timestamp-$experiment_meta_identifier-$experiment_client_provider-$experiment_name-ErrorLogFile.log
        ; touch /home/ubuntu/done
    ' > /dev/null & "

# start the experiment process on the remote worker server
ssh -o StrictHostKeyChecking=no -i $key_path $client_user@$client_ip $ssh_command

# check every interval if the experiment code has finished running and the infrastructure can be destroyed
until ssh -o "StrictHostKeyChecking=no" -i "$key_path" "$client_user@$client_ip" "[ -f '/home/ubuntu/done' ]" ; do
    echo "$(date) Waiting for experiment to finish ..."
    sleep $check_progress_interval
done

smsg "Done executing experiment code."

# ===== destroy client vm

cd "$experiment_context/$experiment_client_provider"

pmsg "Destroying client vm ..."

terraform destroy \
    -auto-approve

smsg "Done destroying client vm."

# ===== remove experiment env files

pmsg "Removing experiment environment files ..."

rm "$experiment_client_env"

pmsg "Done removing environment files."

# ===== remove experiment pid file

pmsg "Removing experiment pidfile"

rm -f "/tmp/$experiment_name-openfaas.pid"

smsg "Done running experiment orchestration."
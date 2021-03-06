
import sys
import json
import time
from datetime import datetime
import traceback
from benchmarker import Benchmarker
from mysql_interface import SQL_Interface as database
import function_lib as lib

# =====================================================================================
# Read cli arguments from calling script

# name of the terraform experiment
experiment_name = sys.argv[1]

# unique identifier string tying this experiment together with the
# experiments conducted for the other cloud providers in this round
experiment_meta_identifier = sys.argv[2]

# name of cloud function provider for this experiment
provider = sys.argv[3]

# name of the client provider
client_provider = sys.argv[4]

# relative path to experiment.env file
env_file_path = sys.argv[5]

# dev_mode
dev_mode = eval(sys.argv[6]) if len(sys.argv) > 6 else False


# verbose for more prints
verbose = eval(sys.argv[7]) if len(sys.argv) > 7 else False

# =====================================================================================

# describe experiment, should be verbose enough to figure
# out what the experiment does and what it attempts to test
description = f"""
{experiment_name}: This experiment is a scenario test of how the platform behaves when
sudden spikes of traffic occures. This experiment is conducted by giving the platform 
a baseline traffic in between concurretn invocations (spikes) that keeps growing by a number
of 16 until it reaches 128 to then decline at the same rate.
"""

# =====================================================================================
# create the benchmarker
benchmarker = Benchmarker(experiment_name=experiment_name,
                          experiment_meta_identifier=experiment_meta_identifier,
                          provider=provider,
                          client_provider=client_provider,
                          experiment_description=description,
                          env_file_path=env_file_path,
                          dev_mode=dev_mode,
                          verbose=verbose)
# =====================================================================================
# database interface for logging results if needed
db = database(dev_mode)
# name of table to insert data into - HAVE TO BE SET!!
table = None
# =====================================================================================
# set meta data for experiment
# UUID from experiment
experiment_uuid = benchmarker.experiment.uuid

# what function to test on (1-3), or 'monolith' 
function = 'function1'

# =====================================================================================
# meassured time for a function to be cold in a sequantial environment
# default value set to 15 minutes if the experiment has not been run
coldtime = db.get_delay_between_experiment(provider,threaded=False) 
# =====================================================================================



# sift away errors at runtime and report them later
errors = []
# ======================================================================================

# ***************************************************
# * comment below function out and other invoke     *
# * function in if experiment is concurrent invoked *
# ***************************************************
def invoke(args:dict= None):
    response = benchmarker.invoke_function(function_name=function, function_args=args)
    return response if 'error' not in response else errors.append(response)

def invoke_concurrently( args:tuple= None ):
    err_count = len(errors)
    # sift away potential error responses and transform responseformat to list of dicts from list of dict of dicts
    invocations = list(filter(None, [x if 'error' not in x else errors.append(x) for x in map(lambda x: lib.get_dict(x), 
        benchmarker.invoke_function_conccurrently(function_name=function, numb_threads=args[0], function_args=args[1]))]))
    return None if invocations == [] else invocations


# =====================================================================================

try:
    # how many times to run the whole experiment
    iterations = 2
    
    # setup arguments for baseline invocations
    baseline_functions = [lambda x: invoke(x)]
    baseline_args = [{'throughput_time': 0.1}]
    #  baseline_seconds = 30
    baseline_seconds = 30

    # setup arguments for concurent spikes
    spike_start=8
    spike_increment=8
    number_of_spikes=32
    increasing_spikes = lib.increment_list(start=spike_start, increment=spike_increment, n=number_of_spikes)
    decreasing_spikes = lib.increment_list(start=spike_start, increment=spike_increment, n=number_of_spikes, reverse=True) 
    spikes = increasing_spikes + decreasing_spikes \
        #  if not dev_mode else lib.increment_list(2,2,14) + lib.increment_list(2,2,14,True)[1:]
    spike_args = [(x, {'throughput_time': 0.1}) for x in spikes]

    if verbose:
        print(f'spikes for the experiment: \n{spikes}\n')
        print('========== starting experiment invocations ==========')

    for args in spike_args:
        for i in range(iterations):
            if verbose:
                print(f'doing baseline invocations for {baseline_seconds} seconds')
            lib.baseline(baseline_seconds, 0.3, baseline_functions, baseline_args)
            if verbose:
                print(f'iteration {i}: concurrent spike: {args}')
            invoke_concurrently(args)

    # =====================================================================================
    # end of the experiment, results are logged to database
    benchmarker.end_experiment()
    # =====================================================================================
    # log experiments specific results, hence results not obtainable from the generic Invocation object
    lib.log_experiment_specifics(experiment_name,
                                 experiment_uuid,
                                 len(errors),
                                 True)

except Exception as e:
    # this will print to logfile
    print(f'Ending experiment {experiment_name} due to fatal runtime error')
    print(str(datetime.now()))
    print('Error message: ', str(e))
    print('Trace: {0}'.format(traceback.format_exc()))
    print('-----------------------------------------')
    benchmarker.end_experiment()

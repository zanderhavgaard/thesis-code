import sys
import json
import time
from pprint import pprint
from benchmarker import Benchmarker
from mysql_interface import SQL_Interface as database
import function_lib as lib

# =====================================================================================
# Read cli arguments from calling script

# name of the terraform experiment
experiment_name = 'test'

# unique identifier string tying this experiment together with the
# experiments conducted for the other cloud providers in this round
experiment_meta_identifier = 'meta'

# name of cloud function provider for this experiment
provider = 'openfaas'

# name of the client provider
client_provider = 'client'

# relative path to experiment.env file
env_file_path = 'somefile'

# dev_mode
dev_mode = True

# verbose mode
verbose = False

if len(sys.argv) > 1:

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

    # verbose mode
    verbose = eval(sys.argv[7]) if len(sys.argv) > 7 else False

# =====================================================================================

# describe experiment, should be verbose enough to figure
# out what the experiment does and what it attempts to test
description = f"""
{experiment_name}: this experiment tests the implmentation of the benchmarking platform
"""

def create_benchmarker(exp_name:str,desc:str,verbose= False):
    benchmarker = Benchmarker(experiment_name=exp_name,
                          experiment_meta_identifier=experiment_meta_identifier,
                          provider=provider,
                          client_provider=client_provider,
                          experiment_description=desc,
                          env_file_path=env_file_path,
                          dev_mode=dev_mode,
                          verbose=verbose)
    
    print('=============================================')
    print(f'Experiment {experiment_name}\n')

    return benchmarker


db = database(dev_mode)
# =====================================================================================

def sequential_sanity_check():
    benchmarker = create_benchmarker(experiment_name,'testing linked invocations')
    # name of function to be invoked
    fx_name = 'function'
    sleep_amount = 0.5

    print('invoking with no arguments: ')
    response = benchmarker.invoke_function(f'{fx_name}1')
    pprint(response)
    print()

    print('invoking with sleep argument')
    response = benchmarker.invoke_function(function_name=f'{fx_name}2',
                                        function_args={'sleep':sleep_amount})
    pprint(response)
    print()

    sleep_amount = 0.5

    print('invoking with no arguments: ')
    response = benchmarker.invoke_function(
        function_name="function1"
        )
    pprint(response)
    print()


    print('invoking with sleep argument')
    response = benchmarker.invoke_function(
        function_name="function2"
        )
    pprint(response)
    print()

    print('invoking with 1 second throughput argument: ')
    response = benchmarker.invoke_function(function_name='function3',
                                        function_args= {'throughput_time': 1.0})
    pprint(response)
    print()


    invoke_1_nested = [
        {
            "function_name": f"{experiment_name}-function2",
            "invoke_payload": {
                "StatusCode": 200,
                "sleep": 0.1
            }
        }
    ]

    print('invoking function1 with 1 nested invocation')
    response = benchmarker.invoke_function(function_name='function1',
                                        function_args= {'invoke_nested': invoke_1_nested})
    pprint(response)
    print()



    invoke_1_nested = [
        {
            "function_name": f"{experiment_name}-function3",
            "invoke_payload": {
                "StatusCode": 200,
                "sleep": 0.1
            }
        }
    ]

    print('invoking function2 with 1 nested invocation')
    response = benchmarker.invoke_function(
        function_name='function2',
        function_args={"invoke_nested":invoke_1_nested}
        )
    pprint(response)
    print()

    invoke_1_nested = [
        {
            "function_name": f"{experiment_name}-function1",
            "invoke_payload": {
                "StatusCode": 200,
                "sleep": 0.1
            }
        }
    ]

    print('invoking function3 with 1 nested invocation')
    response = benchmarker.invoke_function(
        function_name='function3',
        function_args={"invoke_nested":invoke_1_nested}
        )
    pprint(response)
    print()

 
    invoke_nested = [
        {
            "function_name": f"{experiment_name}-function2",
            "invoke_payload": {
                "StatusCode": 200,
                "invoke_nested": [
                        {
                        "function_name": f"{experiment_name}-function3",
                        "invoke_payload": {
                            "StatusCode": 200,
                            }
                        },
                        {
                        "function_name": f"{experiment_name}-function3",
                        "invoke_payload": {
                            "StatusCode": 200,
                            }
                        }
                    ]
                }
            }
        ]

    print('invoking with double nested invocation')
    response = benchmarker.invoke_function(
        function_name='function1',
        function_args={"invoke_nested":invoke_nested}
        )
    pprint(response)
    print()

   

    # =====================================================================================
    # end of the experiment
    benchmarker.end_experiment()
    # =====================================================================================

def concurrent_sanity_check():
    benchmarker = create_benchmarker(experiment_name, 'run with different thread counts')
    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=8)
    pprint(response)
    print()

    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=1)
    pprint(response)
    print()
   
    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=2)
    pprint(response)
    print()
   
    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=3)
    pprint(response)
    print()
    args = {
        'throughput_time': 0.2
    }
    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=7,function_args=args)
    pprint(response)
    print()
    args['sleep'] = 0.1
    response = benchmarker.invoke_function_conccurrently(function_name='function1',numb_threads=7,function_args=args)
    pprint(response)
    print()

    invoke_1_nested = [
        {
            "function_name": f"{experiment_name}-function1",
            "invoke_payload": {
                "StatusCode": 200,
                "sleep": 0.1
            }
        }
    ]

    response = benchmarker.invoke_function_conccurrently(function_name='function1',
                                                        numb_threads=7,
                                                        function_args={'invoke_nested':invoke_1_nested})
    pprint(response)
    print()
    
    # =====================================================================================
    # end of the experiment
    benchmarker.end_experiment()
    # =====================================================================================


def test_monolith():
    benchmarker = create_benchmarker(experiment_name, 'monolith feature test')
    
    args = {
        'args': 8,
        'run_function': 'random',
        'seed': 2,
        }
    response = benchmarker.invoke_function(function_name='monolith',function_args=args)
    pprint(response)
    print()


    args['run_function'] = 'matrix_mult'
    response = benchmarker.invoke_function(function_name='monolith',function_args=args)
    pprint(response)
    print()

    benchmarker.invoke_function_conccurrently(function_name='monolith',numb_threads=6,function_args=args)
    pprint(response)
    print()

   
    f_list = [
            'fib', 
            'isSymmetric', 
            'levelOrder',
            'maxDepth', 
            'levelOrderBottom', 
            'sortedArrayToBST', 
            'zigzagLevelOrder', 
            'sortedListToBST', 
            'isBalanced', 
            'minDepth',
            'flatten', 
            'maxPathSum', 
            'preorderTraversal', 
            'rightSideView', 
            'dummie_webpage', 
            'docker_documentation', 
            'use_arrow', 
            'pandas_numpy', 
    ]
    for f in f_list:
        args['run_function'] = f
        response = benchmarker.invoke_function(function_name='monolith',function_args=args)
        d = lib.get_dict(response)
        if 'error' in d:
            pprint(d)

# ============================================================
# EXPERIMENT LOGIC

    

# ============================================================
# run the tests - comment out to leave out
sequential_sanity_check()
concurrent_sanity_check()
test_monolith()


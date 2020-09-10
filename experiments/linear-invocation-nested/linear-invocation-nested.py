
import sys
import json
import time
from datetime import datetime
import traceback
from benchmarker import Benchmarker
from mysql_interface import SQL_Interface as database
import function_lib as lib
from pprint import pprint

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
{experiment_name}: invokes all cloud function a 1000 times in a lab-like environment as it
is done from one cloud function to another. 
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
# fx = None
# nested_fx = None
fx_list = ['function1','function2','function3','monolith']


# =====================================================================================
# meassured time for a function to be cold in a sequantial environment
# default value set to 15 minutes if the experiment has not been run
coldtime = db.get_delay_between_experiment(provider,threaded=False) 
# =====================================================================================

# sleep for 15 minutes to ensure coldstart
if not dev_mode:
    time.sleep(coldtime)  

# results specific gathered and logged from logic of this experiment
results = []

# sift away errors at runtime and report them later
errors = []
# ======================================================================================
# def get_nested(nested_fx):
#     return [
#             {
#                 "function_name": f"{experiment_name}-{nested_fx}",
#                 "invoke_payload": {}
#             }
#         ]

def create_nesting(function:str):
    nested = {
        "function_name": f"{experiment_name}-{function}",
        "invoke_payload": {}
        }
    
    return {'invoke_nested':[nested]}


def invoke( args ):
    print('\nfunction:',args[0])
    print('dict:',args[1])
    print()
    response = benchmarker.invoke_function(function_name=args[0], function_args=args[1])
 
    if 'error' in response:
        return errors.append(response)
    nested_dict = response[list(response.keys())[1]]
  
    return nested_dict if 'error' not in nested_dict else errors.append(nested_dict)

# function to be given to validate function if not successful
# if other action is desired give other function as body
def err_func(): benchmarker.end_experiment()

# convinience for not having to repeat values
# x = function to apply, y:str = context, z = arguments for x, if any
def validate(x, y, z=None): return lib.iterator_wrapper(
    x, y, experiment_name, z, err_func)


# =====================================================================================

try:
    
    for i in range(len(fx_list)):
        time.sleep(coldtime if not dev_mode else 1.0)
        fx = fx_list[i]
        nested_fx = fx_list[(i+1) % len(fx_list)]
        for n in range(1000):
            validate(invoke,f'invoking {fx} at iteration {n}',(fx_list[i],create_nesting(nested_fx)))


   # =====================================================================================
    # end of the experiment, results are logged to database
    benchmarker.end_experiment()
    # =====================================================================================
    
except Exception as e:
    # this will print to logfile
    print(f'Ending experiment {experiment_name} due to fatal runtime error')
    print(str(datetime.now()))
    print('Error message: ', str(e))
    print('Trace: {0}'.format(traceback.format_exc()))
    print('-----------------------------------------')
    benchmarker.end_experiment()

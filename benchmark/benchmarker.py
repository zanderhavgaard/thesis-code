#!/bin/python

import sys
import time
import json
import requests
import multiprocessing as mp
from provider_abstract import AbstractProvider
from provider_aws_lambda import AWSLambdaProvider
from provider_azure_functions import AzureFunctionsProvider
from provider_openfaas import OpenFaasProvider
from experiment import Experiment
from mysql_interface import SQL_Interface

from pprint import pprint


class Benchmarker:

    def __init__(self, experiment_name: str, provider: str, client_provider:str, experiment_description: str, env_file_path: str, dev_mode: bool = False) -> None:

        # do not log anything if running in dev mode
        self.dev_mode = dev_mode

        # log the experiment name
        self.experiment_name = experiment_name

        # log the time of experiment start
        self.start_time = time.time()

        # desribe experiment, to be logged along with results
        self.experiment_description = experiment_description

        # get function execution provider
        self.provider = self.get_provider(
            provider=provider, env_file_path=env_file_path)
        
        self.experiment = Experiment(experiment_name,provider,client_provider,experiment_description)

        print('\n=================================================')
        print('FaaS Benchmarker --> Starting Experiment ...')
        print('=================================================')
        print(f'Python version: {sys.version}')
        print('=================================================')
        print(f'dev_mode: {self.dev_mode}')
        print('=================================================')
        print(f'Experiment name:         {experiment_name}')
        print(f'Using provider:          {provider}')
        print(f'Using environment file:  {env_file_path}')
        print(f'Experiment start time:   {time.ctime(int(self.experiment.get_start_time()))}')
        print('=================================================')
        print(f'Experiment description: {self.experiment.get_experiment_description()}')
        print('=================================================\n')

    # create cloud function execution provider

    def get_provider(self, provider: str, env_file_path: str) -> AbstractProvider:
        # implemented providers
        providers = ['aws_lambda', 'azure_functions', 'openfaas']

        # choose provider to invoke cloud function
        if provider in providers:
            if provider == 'aws_lambda':
                return AWSLambdaProvider(env_file_path=env_file_path)
            elif provider == 'azure_functions':
                return AzureFunctionsProvider(env_file_path=env_file_path)
            elif provider == 'openfaas':
                return OpenFaasProvider(env_file_path=env_file_path)
        else:
            raise RuntimeError(
                'Error: Please use an implemented provider, options are: ' +
                f'{str(self.providers)}')

    # log the total time of running an experiment
    # call this method as the last thing in experiment clients
    def log_experiment_running_time(self) -> None:
        (end_time,total_time) = self.experiment.end_experiment()
        # experiment_running_time = end_time - self.start_time
        print('=================================================')
        print(f'Experiment end time: {time.ctime(int(end_time))}')
        print('Experiment running time: ' +
              f'{time.strftime("%H:%M:%S", time.gmtime(total_time))}')
        print('=================================================')
        
        # store all data from experiment in database
        db = SQL_Interface(self.experiment)
        db.log_experiment()


    def end_experiment(self) -> None:
        # log the experiment running time, and print to log
        self.log_experiment_running_time()


    # main method to be used by experiment clients
    def invoke_function(self,
                        function_endpoint: str,
                        sleep: float = 0.0,
                        invoke_nested: dict = None) -> None:

        response = self.provider.invoke_function(function_endpoint=function_endpoint,
                                                 sleep=sleep,
                                                 invoke_nested=invoke_nested)

        if response is None:
            raise EmptyResponseError(
                'Error: Empty response from cloud function invocation.')

        self.experiment.add_invocations([response])

        # return response


    def invoke_function_conccurrently(self,
                                      function_endpoint: str,
                                      sleep: float = 0.0,
                                      invoke_nested: dict = None,
                                      numb_threads: int = 1
                                      ) -> None:

        response_list = self.provider.invoke_function_conccrently(function_endpoint,
                                                             sleep,
                                                             invoke_nested,
                                                             numb_threads
                                                             )

        if response_list is None:
            raise EmptyResponseError(
                'Error: Empty response from cloud function invocation.')

        # log repsonse to db
        self.experiment.add_invocations(response_list)


# create exception class for empty responses

# do something smarter here 
class EmptyResponseError(RuntimeError):
    def __ini__(self, error_msg: str):
        super(error_msg)



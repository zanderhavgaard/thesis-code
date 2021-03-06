
import pymysql
import sshtunnel
import paramiko
import numpy as np
import pandas as pd
import os
import subprocess
from sshtunnel import SSHTunnelForwarder
import datetime
import dotenv
import traceback
import time
import function_lib as lib

from os.path import expanduser



class SSH_query:
    # set variables for connection to MySql on DB server via ssh tunnel
    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.ssh_address = (os.getenv('DB_HOSTNAME'), 22)
        # comment below lines out if you do not want to use default variable names
        self.ssh_username = 'ubuntu'
        # comment below line in and the line below that out for production
        if dev_mode:
            self.ssh_pkey = paramiko.RSAKey.from_private_key_file(os.environ['fbrd']+'/secrets/ssh_keys/db_server' )
        else:
            self.ssh_pkey = paramiko.RSAKey.from_private_key_file('/home/docker/key/id_rsa')
        self.remote_bind_address = ('127.0.0.1', 3306)
        self.db_user = os.getenv('DB_SQL_USER')
        self.db_password = os.getenv('DB_SQL_PASS')
        self.database = 'Benchmarks'

        # comment below lines in if you want to load it from environment variables instead of default
        # # self.ssh_username = os.getenv('ssh_username')
        # # self.ssh_pkey = paramiko.RSAKey.from_private_key_file(os.getenv('ssh_pkey_path'))
        # # self.remote_bind_address = (os.getenv('remote_bind_ip'), int(os.getenv('remote_bind_port')))
        # # self.db_user = os.getenv('db_user')
        # # self.db_password = os.getenv('db_password')
        # # self.database = os.getenv('database')

    # apply arbitrary many insert queries on MySql
    def insert_queries(self, queries: list) -> bool:
        # try up 10 times to establish an ssh tunnel
        for x in range(10):
            try:
                with SSHTunnelForwarder(
                    ssh_address=self.ssh_address,
                    ssh_username=self.ssh_username,
                    ssh_private_key=self.ssh_pkey,
                    remote_bind_address=self.remote_bind_address,
                ) as tunnel:

                    try:
                        conn = pymysql.connect(host=self.remote_bind_address[0],
                                               user=self.db_user,
                                               passwd=self.db_password,
                                               db=self.database,
                                               port=tunnel.local_bind_port
                                               )

                        cur = conn.cursor()
                        list_length = len(queries)
                        error_list = []
                        # iterate over list of queries and execute. Try up to 3 times if exception is thrown
                        for i in range(list_length):
                            for x in range(3):
                                try:
                                    res = cur.execute(queries[0])
                                    # if query is successful then remove it from list
                                    conn.commit()
                                    queries.pop(0)
                                    break

                                except Exception as qe:
                                    time.sleep(1)
                                    if(x == 2):
                                        # if not successful remove query from list and log error message
                                        q = queries.pop(0)
                                        error_list.append(q)
                                        lib.write_errorlog(qe, 'Sql error with query:',self.dev_mode, q)
                                        

                        conn.close()
                        tunnel.stop()
                        # return true or false depending on number of errors, true if at least 50% was successful
                        return len(queries) / 2 >= len(error_list)

                    except Exception as ex:
                        if('conn' in locals()):
                            conn.close()
                        # log error message if database connection failed
                        res = lib.write_errorlog(ex, 'MySql connection error',self.dev_mode)
                        

            except Exception as e:
                if(x == 9):
                    # if all 10 atempts failed log error and return False
                    lib.write_errorlog(e, "Caught tunnel exception while inserting",self.dev_mode)
                    return False

    # set return_type to False if list representation is wanted
    def retrive_query(self, query: str):
        # try up 10 times to establish an ssh tunnel
        for x in range(10):
            try:
                with SSHTunnelForwarder(
                    ssh_address=self.ssh_address,
                    ssh_username=self.ssh_username,
                    ssh_private_key=self.ssh_pkey,
                    remote_bind_address=self.remote_bind_address,
                ) as tunnel:
                    # try query up to 3 times
                    for i in range(3):
                        try:
                            # consider executemany if more complicated queries has to be made
                            conn = pymysql.connect(host=self.remote_bind_address[0],
                                                   user=self.db_user,
                                                   passwd=self.db_password,
                                                   db=self.database,
                                                   port=tunnel.local_bind_port
                                                   )

                            # retrive and read data
                            data = pd.read_sql_query(query, conn)
                            conn.close()
                            tunnel.stop()

                            return data

                        except Exception as ex:
                            # log error message if its the third atempt
                            if('conn' in locals()):
                                conn.close()
                            if(i == 2):
                                lib.write_errorlog(ex, "Exception caught at remote site while retriving data",self.dev_mode)
                                return None

            # log error message if tunnel could not be established within 10 atempts
            except Exception as e:
                if(x == 9):
                    lib.write_errorlog(e, 'Caught tunnel exception while retriving data',self.dev_mode)
                    return None


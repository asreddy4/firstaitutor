import yaml
import os
import sys


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import api_user,qualification,subject,school,learning_network

configfile = {}
scriptDir = os.path.dirname(os.path.abspath(__file__))
config_filepath = str(os.path.dirname(scriptDir)+"/configfile.yml")

if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

async def create_table():
    await api_user.create_table_user(configfile)
    await subject.create_table_subject(configfile)
    await qualification.create_table_qualification(configfile)

    await school.create_table_school(configfile)
    await learning_network.create_table_learning_network(configfile)

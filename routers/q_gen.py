## File located in FastAPI environment

import os
import sys
from pathlib import Path
import inspect
import ast
from copy import deepcopy

routers_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
firstaitutor_dir = os.path.dirname(routers_dir)
fait_backend_dir = os.path.dirname(firstaitutor_dir)
home_dir = os.path.dirname(fait_backend_dir)

sys.path.insert(0, f'{fait_backend_dir}/fait_python/gen_raw_questions')


##  from 0001a match,  from 0200a blank,  from 0400a selection
qt_id = '001a-001a-001a-001a-0405a'
q_numb_to_generate = 3
q_var_to_generate = 0
action_code = 0    ## value 0 for writing to database, 1 for test html generation


import subprocess

#p= subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/match.py", f"{qt_id}", f"{q_numb_to_generate}", f"{q_var_to_generate}", f"{action_code}"],
#p= subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/blank.py", f"{qt_id}", f"{q_numb_to_generate}", f"{q_var_to_generate}", f"{action_code}"],
p= subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/selection.py", f"{qt_id}", f"{q_numb_to_generate}", f"{q_var_to_generate}", f"{action_code}"],
#p= subprocess.run([f"{fait_backend_dir}/fait_python/windowsenv/Scripts/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/match.py", f"{qt_id}", f"{q_numb}", f"{is_test}"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=False,
                           text=True
                           )

###########
### After generation update the json file for q_num_dict for each variation
###########



print("Here is the Error:", p.stderr)

if action_code == 1:
    output_dict = deepcopy(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1])
elif action_code == 0:
    output_dict = deepcopy(ast.literal_eval(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1]))
    
print("output:", output_dict)





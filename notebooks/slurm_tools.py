import sys
from pathlib import Path
import importlib
import os
import stat
import subprocess
import inspect
import random
import string

_slurm_script = """#! {python}
import sys
sys.path.append("{module_folder}")



from {module_name} import {func_name}

{func_name}(\n    {args}, \n    {kwargs})

"""

def arg_to_str(v):
    if isinstance(v, Path):
        v = str(v)
    
    if isinstance(v, str):
        return f"'{v}'"
    elif isinstance(v, (float, int, bool)):
        return f"{v}"
    else:
        raise ValueError("args and kwargs must be str, int, float")




def push_to_slurm(func,
    *args, 
    slurm_option=dict(mincpus=20, mem = '150G'),
    block_mode=False,
    **kwargs,
):

    file = Path(inspect.getfile(func))
    module_folder = file.parent
    slurm_script_folder = module_folder / 'slurm_scripts'
    slurm_script_folder.mkdir(exist_ok=True)
    module_name = file.stem
    func_name = func.__name__
    python = sys.executable
    # print(module_folder)
    # print(module_name, funarg_to_strc_name)
    
    args_txt = ",\n    ".join(f"{arg_to_str(v)}" for v in args)
    kwargs_txt = ",\n    ".join(f"{k}={arg_to_str(v)}" for k, v in kwargs.items())


    slum_script = _slurm_script.format(
        python=sys.executable,
        module_folder=str(module_folder),
        module_name=str(module_name),
        func_name=func_name,
        args=args_txt,
        kwargs=kwargs_txt,

    )
    
    name = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    script_name = slurm_script_folder / f'run_{name}.py'
    output_name = slurm_script_folder / f'slurm-{name}.out'
    # print(script_name)
    
    with open(script_name, 'w') as f:
        f.write(slum_script)
        os.fchmod(f.fileno(), mode = stat.S_IRWXU)


    options = []
    for k, v in slurm_option.items():
        options.append(f'--{k}={v}')

        
    if block_mode:
        command = ['srun']
    else:
        command = ['sbatch']
    command += options
    if not block_mode:
        command += [f'--output={output_name}']
    command += [

        # for os.command
        # f'--output="{output_name}"',
        # f'"{script_name}"',

        # for subprocess.run
        f'--job-name={func_name}{name}',
        f'{script_name}',
    ]
    print(command)
    
    out = subprocess.run(command) #, stdout=fo, stderr=fo)  shell=True,
    # print(out)

    # comnand_txt = ' '.join(command)
    # print(comnand_txt)
    # os.system(comnand_txt)

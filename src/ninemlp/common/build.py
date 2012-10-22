"""

    This module defines common methods used in simulator specific build modules

    @author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import platform
import os.path
import subprocess as sp

def path_to_exec(exec_name):
    """
    Returns the full path to an executable by calling either 'which' or 'where' depending on OS
    
    @param exec_name[str]: Name of executable to search the execution path for
    @return [str]: Full path to executable
    """
    if platform.system() == 'Windows':
        exec_name += '.exe'
    # Check the system path for the 'nrnivmodl' command
    exec_path = None
    for dr in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(dr, exec_name)
        if os.path.exists(path):
            exec_path = path
            break
    if not exec_path:
        raise Exception("Could not find nrnivmodl on the system path '%s'" % os.environ['PATH'])
    return exec_path

def path_to_exec_old(exec_name):
    """
    Returns the full path to an executable by calling either 'which' or 'where' depending on OS
    
    @param exec_name[str]: Name of executable to search the execution path for
    @return [str]: Full path to executable
    """
    if platform.system() == 'Windows':
        try:
            sp.check_call('where mkdir', shell=True)
        except sp.CalledProcessError as e:
            raise Exception("Could not execute 'where' command from cmd.exe, check to see if it is installed.")
    else:
        try:
            sp.check_call('which mkdir', shell=True)
        except sp.CalledProcessError as e:
            raise Exception("Could not execute 'which' command from bash shell, check to see if it is installed.")
    try:
        if platform.system() == 'Windows':
            path = sp.check_output('where ' + exec_name, shell=True)
        else:
            path = sp.check_output('which ' + exec_name, shell=True)
    except sp.CalledProcessError as e:
        raise Exception("Could not find the executable '{}' on system path (try manually searching \
for executable and adding its folder to the 'PATH' environment variable".format(exec_name))
    return path

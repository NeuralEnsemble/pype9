#!/usr/bin/env python
import sys
from nineline.hpc.sge import SGESubmitter

if len(sys.argv) < 2:
    raise Exception("At least one argument (the script name to submit to the que) should be "
                    "passed to que_sge.py")
submitter = SGESubmitter(sys.argv[1])
args = submitter.parse_arguments(sys.argv[2:])
submitter.submit(args)

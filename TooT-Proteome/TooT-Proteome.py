#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import argparse
import shutil
import subprocess
import traceback
import logging

parser = argparse.ArgumentParser(description="A tool to classify transporter proteins. It will filter a fasta-formatted file through TooT-T before sending it through TooT-SC and collating the results.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-query", help="a fasta formatted file", required=True)
parser.add_argument("-work", help="a working directory for intermediate files", default=os.path.join(os.getcwd(), "work"))
parser.add_argument("-out", help="an output directory where the final results will be stored", default=os.getcwd())
parser.add_argument("-db", help="the location of the required TCDB and Swissprot databases", default=os.path.join(os.getcwd(), "db"))
parser.add_argument("-TooTT", help="the location of the TooT-T script that will be run", default=shutil.which("TooT-TTool.R"))
parser.add_argument("-TooTSC", help="the location of the TooT-SC script that will be run", default=shutil.which("TooT-SCTool.R"))

args = parser.parse_args()

#Validate that everything seems ready
##Validate that the scripts can be found
if args.TooTT is None:
    sys.exit("Could not locate a default executable script for TooT-T.")
if not os.path.exists(args.TooTT):
    sys.exit("Could not find a valid TooT-T script located at: " + args.TooTT)
if not os.access(args.TooTT, os.X_OK):
    sys.exit("Cannot execute TooT-T script located at: " + args.TooTT)
if args.TooTSC is None:
    sys.exit("Could not locate a default executable script for TooTSC.")
if not os.path.exists(args.TooTSC):
    sys.exit("Could not find a valid TooT-SC script located at: " + args.TooTSC)
if not os.access(args.TooTSC, os.X_OK):
    sys.exit("Cannot execute TooT-SC script located at: " + args.TooTSC)

##Validate that the query exists
if not os.path.exists(args.query):
    sys.exit("Query does not exist at location: " + args.query)
if not os.path.isfile(args.query):
    sys.exit("Query file specifies a directory instead of a file: " + os.path.abspath(args.query))

##Validate that the database directory exists
if not os.path.exists(args.db):
    sys.exit("Database directory does not exist at location: " + args.db)
if not os.path.isdir(args.db):
    sys.exit("Database directory specifies a file instead of a directory: " + os.path.abspath(args.db))

##Validate that the output directory exists
if not os.path.exists(args.out):
    sys.exit("Output directory does not exist at location: " + args.out)
if not os.path.isdir(args.out):
    sys.exit("Output directory specifies a file instead of a directory: " + os.path.abspath(args.out))
if not os.access(args.out, os.W_OK):
    sys.exit("Output directory specifies a directory without permission to write: " + os.path.abspath(args.out))

##Validate that the work directory exists
if not os.path.exists(args.work):
    try:
        Path(args.work).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(traceback.format_exc())
        sys.exit("There was a problem with the specified output directory: " + args.out)
if not os.path.isdir(args.work):
    sys.exit("Work directory specifies a file instead of a directory: " + os.path.abspath(args.work))
if not os.access(args.work, os.W_OK):
    sys.exit("Work directory specifies a directory without permission to write: " + os.path.abspath(args.work))



# Run TooT-T on target query, with output going to <work>/TooT-Proteome/<query-filename>/
TooTTCommand = args.TooTT + " -query=" + args.query + " -db=" + args.db + " -out=" + args.out + " -work=" + args.work
print("Executing: " + TooTTCommand) 
TooTTOut = subprocess.run([args.TooTT, "-query=" + args.query, "-db=" + args.db, "-out=" + args.out, "-work=" + args.work])
print(TooTTOut.returncode)
## If exit code is bad, exit
if TooTTOut.returncode != 0:
    sys.exit("TooT-T script returned non-zero exit! Aborting TooT-Proteome.")

# Filter initial query into intermediate fasta file in <work>/TooT-Proteome/<query-filename>/<query-filename>
# Run TooT-SC on the filtered query with output going to <work>/TooT-Proteome/<query-filename>/
TooTSCOut = subprocess.run([args.TooTSC, "-query=" + os.path.join(args.work, ""), "-db=" + args.db, "-out=" + args.out, "-work=" + args.work])
## If exit code is bad, exit
# Copy output to <out>

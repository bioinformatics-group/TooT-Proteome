#!/usr/bin/env python3

from Bio import SeqIO
import csv
import sys
import os
from pathlib import Path
import argparse
import shutil
import subprocess
import traceback
import logging

TooTTScript = "TooT_TTool.R";
TooTSCScript = "TooT_SCTool.R";

parser = argparse.ArgumentParser(description="A tool to classify transporter proteins. It will filter a fasta-formatted file through TooT-T before sending it through TooT-SC and collating the results.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-query", help="a fasta formatted file", required=True)
parser.add_argument("-work", help="a working directory for intermediate files", default=os.path.join(os.getcwd()))
parser.add_argument("-out", help="an output directory where the final results will be stored", default=os.getcwd())
parser.add_argument("-db", help="the location of the required TCDB and Swissprot databases", default=os.path.join(os.getcwd(), "db"))
parser.add_argument("-TooTT", help="the location of the TooT-T script that will be run", default=shutil.which(TooTTScript))
parser.add_argument("-TooTSC", help="the location of the TooT-SC script that will be run", default=shutil.which(TooTSCScript))

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
TooTPWork = os.path.join(args.work, "work", "TooT-P");
if not os.path.exists(TooTPWork):
    try:
        print("Creating: " + TooTPWork)
        Path(TooTPWork).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(traceback.format_exc())
        sys.exit("There was a problem creating working directories: " + os.path.abspath(TooTPWork))
if not os.path.isdir(TooTPWork):
    sys.exit("TooT-P work directory specifies a file instead of a directory: " + os.path.abspath(TooTPWork))
if not os.access(TooTPWork, os.W_OK):
    sys.exit("TooT-P work directory specifies a directory without permission to write: " + os.path.abspath(TooTPWork))


# Run TooT-T on target query, with output going to <work>/TooT-Proteome/<query-filename>/
TooTTCommand = args.TooTT + " -query=" + args.query + " -db=" + args.db + " -out=" + args.out + " -work=" + args.work
print("Executing: " + TooTTCommand) 
TooTTOut = subprocess.run([args.TooTT, "-query=" + args.query, "-db=" + args.db, "-out=" + TooTPWork, "-work=" + args.work])
print(TooTTOut.returncode)
## If exit code is bad, exit
if TooTTOut.returncode != 0:
    sys.exit("TooT-T script returned non-zero exit! Aborting TooT-Proteome.")


# Filter initial query into intermediate fasta file (TooTTout.fasta in work dir) in <work>/TooT-P/TooTTout.fasta
MembraneFasta = os.path.join(TooTPWork, "TooTTout.fasta")
# Get rid of any old version
if os.path.exists(MembraneFasta):
    os.remove(MembraneFasta)

MembraneProts = []

with open(os.path.join(TooTPWork, "TooTTout.csv")) as csvFile:
     csvReader = csv.reader(csvFile, delimiter=',')
     for row in csvReader:
         if row[2] == "1":
             MembraneProts.append(row[1])
for record in SeqIO.parse(args.query, "fasta"):
    if record.id in MembraneProts:
        with open(MembraneFasta, "a") as output_handle:
            SeqIO.write(record, output_handle, "fasta")

if not os.path.exists(MembraneFasta):
    print("No membrane proteins were detected in: " + args.query)
    sys.exit(0)

# Run TooT-SC on the filtered query with output going to <work>/TooT-Proteome/<query-filename>/
TooTSCOut = subprocess.run([args.TooTSC, "-query=" + MembraneFasta, "-db=" + args.db, "-out=" + args.out, "-work=" + args.work])
## If exit code is bad, exit
# Copy output to <out>

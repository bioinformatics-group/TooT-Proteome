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

TooTTScript = "TooT-T.R";
TooTSCScript = "TooT-SC.R";

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


#Create a TooT-P output file:
TooTSCOutheaders = ["", "UniProtID", "pred", "1",  "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
TooTSCOutFile = os.path.join(args.out, "TooTSCOut.csv")
with open(TooTSCOutFile, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(TooTSCOutheaders)


SCClasses = ["Nonselective", "water", "inorganic cation", "inorganic anion", "organic anion", 
    "organooxogyn", "amino acid and derivatives", "other Organonitrogen compound", "nucleotide", 
    "Organic heterocyclic", "Miscellaneous"]
SCClassDict = {}


#Clean stuff up if it already exists:
if os.path.exists(os.path.join(TooTPWork, "TooT-TProblemSeq.txt")):
    os.remove(os.path.join(TooTPWork, "TooT-TProblemSeq.txt"))

#Let's look at looping around the query to identify problem sequences instead of letting
for record in SeqIO.parse(args.query, "fasta"):
    seqDir = os.path.join(TooTPWork, record.id)
    if os.path.exists(seqDir):
        shutil.rmtree(seqDir)
    Path(seqDir).mkdir(parents=True, exist_ok=True)
    seqFile = os.path.join(seqDir, record.id + ".fasta")
    with open(seqFile, "a") as f:
        SeqIO.write(record, f, "fasta")

    TooTTCommandArgs = [args.TooTT, "-query=" + seqFile, "-db=" + args.db, "-out=" + seqDir, "-work=" + args.work]
    print("Executing: " + ' '.join(TooTTCommandArgs))
    TootOutStdout = open(os.path.join(seqDir, "log.stdout"), "w")
    TootOutStderr = open(os.path.join(seqDir, "log.stderr"), "w")
    TooTTOut = subprocess.run(TooTTCommandArgs, stdout=TootOutStdout, stderr=TootOutStderr)
    TootOutStdout.close();
    TootOutStderr.close();
    if TooTTOut.returncode != 0:
        with open(os.path.join(TooTPWork, "TooT-TProblemSeq.txt"), "a") as f:
            print("\tProblem with sequence: " + record.id)
            f.write(record.id + "\n")
        continue
    else:
        os.remove(os.path.join(seqDir, "log.stdout"))
        os.remove(os.path.join(seqDir, "log.stderr"))

    #Check to make sure this was a transporter, continuing if it was not.
    with open(os.path.join(seqDir, "TooTTout.csv")) as csvFile:
        csvReader = csv.reader(csvFile, delimiter=',')
        next(csvReader)
        row = next(csvReader)
        seqID = row[1]
        #Clean out TooT-T because it's a hog and if things worked we don't care
        shutil.rmtree(os.path.join(args.work, "work", "TooT-T", seqID))
        if row[2] == "0":
            continue



    TootOutStdout = open(os.path.join(seqDir, "log.stdout"), "w")
    TootOutStderr = open(os.path.join(seqDir, "log.stderr"), "w")
    TooTSCCommandArgs = [args.TooTSC, "-query=" + seqFile, "-db=" + args.db, "-out=" + seqDir, "-work=" + args.work]
    print("Executing: " + ' '.join(TooTSCCommandArgs))
    TooTSCOut = subprocess.run(TooTSCCommandArgs, stdout=TootOutStdout, stderr=TootOutStderr)
    TootOutStdout.close();
    TootOutStderr.close();
    if TooTSCOut.returncode != 0:
        with open(os.path.join(TooTPWork, "TooT-SCProblemSeq.txt"), "a") as f:
            print("\tProblem with sequence: " + record.id)
            f.write(record.id + "\n")
        continue
    else:
        os.remove(os.path.join(seqDir, "log.stdout"))
        os.remove(os.path.join(seqDir, "log.stderr"))

    #Merge the results into the TooTSCOutFile
    with open(TooTSCOutFile, 'a') as f:
        writer = csv.writer(f)
        with open(os.path.join(seqDir, "TooTSCout.csv")) as csvFile:
            csvReader = csv.reader(csvFile, delimiter=',')
            next(csvReader)
            row = next(csvReader)
            seqID = row[1]
            #Clean out TooT-SC for consistency, though these seem like smaller files
            shutil.rmtree(os.path.join(args.work, "work", "TooT-SC", seqID))
            SCClassDict[row[2]] = SCClassDict.get(row[2], 0) + 1
            writer.writerow(row)


with open("TestOut.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Class", "Occurrence"])
    totalClasses = 0;
    for i in range(0, 11):
        writer.writerow([SCClasses[i], SCClassDict.get(SCClasses[i], 0)])
        totalClasses = totalClasses + SCClassDict.get(SCClasses[i], 0)
    writer.writerow(["total", totalClasses])


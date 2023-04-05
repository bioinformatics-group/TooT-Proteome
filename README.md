# Toot-Proteome
A tool to combine Toot-T and Toot-SC to more quickly classify transporter proteins

Chat GPT gave me a nice summary:
 * It accepts command-line arguments using the argparse module.
 * It validates the existence and permissions of directories and scripts specified by the user.
 * It reads in a fasta file of protein sequences.
 * It runs the TooT-T script on each sequence to predict whether it's a transporter or not, and saves the output in a directory.
 * It checks whether the TooT-T script ran successfully for each sequence and skips over problem sequences.
 * For sequences that are predicted as transporters by TooT-T, it runs the TooT-SC script to classify them by substrate, and saves the output in a directory.
 * It merges the output from all sequences into a single CSV file containing predicted substrate labels.
 * It provides some basic statistics on the predicted substrate labels.



## HOW TO USE
 - This tool requires that `TOOT-T` and `TOOT-SC` be pre-installed
 - Usage: `./TooT-P.py -query=<input> [-out=<outdir>] [-db=<path to db>] [-work=<Workdir>] [-TooTT=<TooTTTool>] [-TooTSC=<TooTSCTool>]`
  - `<input>` is your sequence input file in fasta format
  - `<out>` is the output directory where you want the predicted 	results, formatted as two csv files, one with the per-sequence classification and one with a summary of how many of each type were found.
  - `<db>` is the directory where the database is stored, requiring the databases specified for TooT-T and TooT-SC respectively. It should default to `<CWD>/db`.
  - `<Workdir>` is the directory where intermediate files will be stored after each run. It should default to `<CWD>/work`.
  - `<TooTTTool>` is the path to the TooT-T script (otherwise it finds it in the path).
  - `<TooTSCTool>` is the path to the TooT-SC script (otherwise it finds it in the path).

Errors from each tool will be logged in TooT-P's working directory as `TooT-TProblemSeq.txt` and `TooT-SCProblemSeq.txt` respectively. Cleanup is attempted on successful sequences, but effort is made to leave behind useful trace information for sequences that cause things to crash. The number of sequences that cause errors is not reported in the output CSV, but can be found in the specified text files and will be output to `stdout` during a run.
  

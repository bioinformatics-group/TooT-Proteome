package org.htmlweb.fasta.app;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Callable;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Option;
import picocli.CommandLine.ParameterException;
import picocli.CommandLine.Parameters;
import picocli.CommandLine.Spec;

@Command(name = "splitfasta", mixinStandardHelpOptions = true, version = "splitfasta 1.0",
description = "Splits a FASTA file into many smaller fasta files.")
public class SplitFasta implements Callable<Integer> {


    @Parameters(index = "0", description = "The FASTA file to be split.")
    private File fastaInput;
	
    @Option(names = {"-s", "--size"}, description = "The maximum number of files to split your fasta file into.")
    private int size = 100;
    
    @Option(names = {"-o", "--out"}, description = "The output directory to store pieces of your FASTA file.")
    private File out = new File("out");
    
    @Option(names = {"-v", "--verbose"}, description = "Produces more detailed output.")
    private Boolean verbose = false;
    
    @Spec CommandSpec spec; // injected by picocli
    
	@Override
	public Integer call() throws Exception {
		if(!out.exists()) {
			out.mkdir();
		} 

		if(!Files.isDirectory(out.toPath())) {
			throw new ParameterException(spec.commandLine(),
                    "The directory '" + out.getAbsolutePath() + "' specified with the '-o'/'--out' option must reference a directory.");
		}
		
        try (DirectoryStream<Path> directory = Files.newDirectoryStream(out.toPath())) {
            if(directory.iterator().hasNext()) {
            	throw new ParameterException(spec.commandLine(),
	                    "The directory '" + out.getAbsolutePath() + "' specified with the '-o'/'--out' option must be empty.");	
            }
        }
        
        BufferedReader br = new BufferedReader(new FileReader(fastaInput));
		String line;
		int spCount = 0;
		int trCount = 0;
		int pCount = 0;
		int count = 0;
		while((line = br.readLine()) != null) {
			count++;
			if(line.startsWith(">")) pCount++;
			if(line.startsWith(">tr")) trCount++;
			else if(line.startsWith(">sp")) spCount++;
		}
		br.close();
		if(verbose) {
			System.err.println("Detecting for " + fastaInput.getName());
			System.err.println("Detected " + count + " lines.");
			System.err.println("Detected " + pCount + " seqences.");
			System.err.println("Detected " + trCount + " 'tr' seqences.");
			System.err.println("Detected " + spCount + " 'sp' seqences.");
			System.err.println("Detected " + (pCount - (trCount + spCount)) + " other seqences.");
		}

		int leftovers = pCount % size;
		int perPiece = pCount / size;
		if(pCount < size) {
			System.err.println("There were fewer than " + size + " proteins. Resetting size to " + pCount + ".");
			size = pCount;
		}

		br = new BufferedReader(new FileReader(fastaInput));
		line = br.readLine();


		for(int pieceFileCount = 1; pieceFileCount <= size; pieceFileCount++) {
			int size = perPiece + ((pieceFileCount<=leftovers)?1:0);
			if(size==0) break;
			File pieceFile = new File(out, String.format("%d.fasta", pieceFileCount));
			PrintWriter pw = new PrintWriter(pieceFile);
			
			int currentPCount = 0;
			while(line != null && currentPCount < size) {
				do {
					pw.println(line);
				} while((line = br.readLine()) != null && !line.startsWith(">"));
				currentPCount++;
			}
			pw.close();
		}
		
        System.out.println(size);
        
		return 0;
	}

    public static void main(String... args) {
        int exitCode = new CommandLine(new SplitFasta()).execute(args);
        System.exit(exitCode);
    }
	
}

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Merger {

	public static void main(String[] args) throws IOException {
		// TODO Auto-generated method stub

		String seq = "C_albicans_SC5314_proteins";
		
		Set<String> transporterPredictions = new HashSet<String>();
		
		//Read the predicted protein file and build a map
		BufferedReader br = new BufferedReader(new FileReader(new File("newest_predictions/predictions_out_"+seq)));
		String line = "";
		while((line = br.readLine()) != null) {
			transporterPredictions.add(line);
		}
		System.out.println(transporterPredictions);
		br.close();
		
		
		//Read The fasta
		File out = new File("newest_out/transportome/"+seq +".fasta");
		PrintWriter pw = new PrintWriter(out);
		br = new BufferedReader(new FileReader(new File("done/"+seq +".fasta")));
		line = br.readLine();
		Pattern pattern1 = Pattern.compile("^>(?:sp|tr|)\\|([^|]*)\\|");
		Pattern pattern2 = Pattern.compile(">(.*?) ");

		//As I read in from the fasta one protein at a time, check if it's in the map. If it is, output to the final file.
		while(line != null) {
			Matcher matcher = null;
			if(line.trim().startsWith(">")) {
				matcher = pattern1.matcher(line.trim());
				if(!matcher.find()) {
					matcher = pattern2.matcher(line.trim());
					if(!matcher.find()) {
						System.out.println("Something bad happened!");
						System.exit(1);
					}
				}
				if(transporterPredictions.contains(matcher.group(1).replaceAll("\\.", ""))) {
					System.out.println(matcher.group(1));
					pw.println(line.trim());
					while((line = br.readLine()) != null && !line.startsWith(">"))pw.println(line);
				} else {
					line = br.readLine();
				}
			} else {
				while((line = br.readLine()) != null && !line.startsWith(">")); 
			}
			

		}
		pw.close();
		br.close();
	
		
	}

}

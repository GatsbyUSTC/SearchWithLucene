package newpackage;

//This is a temporary class used to create index. 
public class Main {

	public static void main(String[] args) {
		long startTime = System.currentTimeMillis();
		System.out.println("index write starts");
		Indexer.indexAllDocs("WebContent/WEB-INF/index_files/index");
		Suggester.indexSpellCheker("WebContent/WEB-INF/index_files/spellCheckerDic/4000-most-common-english-words-csv.csv", 
				"WebContent/WEB-INF/index_files/spellCheckerIndex");
		long endTime = System.currentTimeMillis();
		System.out.println("index write finishes");
		System.out.println("total time: " + (endTime - startTime) + " ms");
	}
}

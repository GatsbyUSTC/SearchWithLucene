package com.socialtv.search;


//This is a temporary class used to create index. 
public class Main {

	public static void main(String[] args) {
		String indexPath = "WebContent/WEB-INF/index_files/index";
		String spellCheckerDictPath = "WebContent/WEB-INF/index_files/spellCheckerDic/4000-most-common-english-words-csv.csv";
		String spellCheckerIndexPath = "WebContent/WEB-INF/index_files/spellCheckerIndex";
		long startTime = System.currentTimeMillis();
		System.out.println("index write starts");
		Indexer.indexAllDocs(indexPath, spellCheckerDictPath, spellCheckerIndexPath);
		long endTime = System.currentTimeMillis();
		System.out.println("index write finishes");
		System.out.println("total time: " + (endTime - startTime) + " ms");
	}
}

package com.socialtv.search;

//This is a temporary class used to create index. 
public class Main {

	public static void main(String[] args) {
		long startTime = System.currentTimeMillis();
		System.out.println("index write starts");
		//Indexer.indexAllDocs("WebContent/WEB-INF/index_files/index");
		long endTime = System.currentTimeMillis();
		System.out.println("index write finishes");
		System.out.println("total time: " + (endTime - startTime) + " ms");
	}
}

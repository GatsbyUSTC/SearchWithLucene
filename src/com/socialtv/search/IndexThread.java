package com.socialtv.search;

public class IndexThread implements Runnable {
	private String indexPath;
	private String spellCheckerIndexPath;
	private String spellCheckerDictPath;

	public IndexThread(String iP, String sCIP, String sCDP) {
		indexPath = iP;
		spellCheckerIndexPath = sCIP;
		spellCheckerDictPath = sCDP;
	}

	@Override
	public void run() {
		Indexer.indexAllDocs(indexPath, spellCheckerDictPath, spellCheckerIndexPath);
	}

}

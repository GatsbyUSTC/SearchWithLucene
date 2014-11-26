package com.socialtv.search;

import java.util.logging.Logger;

public class IndexThread implements Runnable {

	private static final Logger logger = Logger.getLogger("indexlog");

	private String indexPath;
	private String spellCheckerIndexPath;
	private String spellCheckerDictPath;

	public IndexThread(String iP, String sCDP, String sCIP) {
		indexPath = iP;
		spellCheckerIndexPath = sCIP;
		spellCheckerDictPath = sCDP;
	}

	@Override
	public void run() {
		logger.info("index writing starts");
		Indexer.indexAllDocs(indexPath, spellCheckerDictPath,
				spellCheckerIndexPath);
		logger.info("index writing completes");
	}

}

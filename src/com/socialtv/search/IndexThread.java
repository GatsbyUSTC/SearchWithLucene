package com.socialtv.search;

import java.util.logging.Logger;

public class IndexThread implements Runnable {

	private static final Logger logger = Logger.getLogger("indexlog");

	private String indexPath;
	private String spellCheckerIndexPath;
	private String spellCheckerDictPath;
	private String xmlPath;

	public IndexThread(String iP, String sCDP, String sCIP, String xP) {
		indexPath = iP;
		spellCheckerIndexPath = sCIP;
		spellCheckerDictPath = sCDP;
		xmlPath = xP;
	}

	@Override
	public void run() {
		logger.info("index writing starts");
		Indexer.indexAllDocs(indexPath, spellCheckerDictPath,
				spellCheckerIndexPath, xmlPath);
		logger.info("index writing completes");
	}

}

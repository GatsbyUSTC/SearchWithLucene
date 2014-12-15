package com.socialtv.search;

import java.util.logging.Logger;

public class IndexThread implements Runnable {

	private static final Logger logger = Logger.getLogger("indexlog");

	private String indexPath;
	private String xmlPath;

	public IndexThread(String iP, String xP) {
		indexPath = iP;
		xmlPath = xP;
	}

	@Override
	public void run() {
		logger.info("index writing starts");
		Indexer.indexAllDocs(indexPath, xmlPath);
		logger.info("index writing completes");
	}

}

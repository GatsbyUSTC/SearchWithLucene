package com.socialtv.search;

import java.io.File;
import java.util.logging.Logger;

import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;
import org.json.JSONObject;

public class Deleter {
	private static final Logger logger = Logger.getLogger("indexlog");

	public Deleter() {
		// TODO Auto-generated constructor stub
	}

	public static void delete(JSONObject requestJson, String indexPath) {
		try {
			String id = requestJson.getString("id");
			Directory directory = FSDirectory.open(new File(indexPath));
			IndexWriterConfig iwc = new IndexWriterConfig(Version.LATEST,
					new StandardAnalyzer());
			IndexWriter indexWriter = new IndexWriter(directory, iwc);
			Term[] terms = { new Term("id", id) };
			indexWriter.deleteDocuments(terms);
			indexWriter.close();
			directory.close();
		} catch (Exception e) {
			logger.severe(e.getLocalizedMessage());
		}
	}

	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

}

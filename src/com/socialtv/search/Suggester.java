package com.socialtv.search;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.logging.Logger;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.MultiFields;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.search.suggest.Lookup.LookupResult;
import org.apache.lucene.search.suggest.analyzing.BlendedInfixSuggester;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.store.RAMDirectory;
import org.apache.lucene.util.BytesRef;
import org.apache.lucene.util.Version;
import org.json.JSONObject;
import org.wltea.analyzer.lucene.IKAnalyzer;

public class Suggester {

	private static final Logger logger = Logger.getLogger("searchlog");
	private BlendedInfixSuggester suggester;
	private JSONObject requestJson;
	private Directory directory;

	public Suggester(JSONObject jsonObject, String indexPath) {
		// TODO Auto-generated constructor stub
		requestJson = jsonObject;
		TitleIterator titleIterator = new TitleIterator(indexPath);
		directory = new RAMDirectory();
		try {
			suggester = new BlendedInfixSuggester(Version.LATEST, directory,
					new IKAnalyzer());
			suggester.build(titleIterator);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getLocalizedMessage());
		}
	}

	public JSONObject suggest() {
		JSONObject responseJson = new JSONObject();
		try {
			String prefix = requestJson.getString("prefix");
			List<LookupResult> results = suggester.lookup(prefix, false, 10);
			for (LookupResult lookupResult : results) {
				responseJson.append("suggest", lookupResult.key);
			}
			directory.close();
			suggester.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			logger.severe(e.getLocalizedMessage());
		}
		return responseJson;
	}

	// For testing
	public static void main(String[] args) {
		Directory directory;
		DirectoryReader directoryReader;
		TermsEnum titleIterator;
		String indexPath = "WebContent/WEB-INF/index";
		try {
			directory = FSDirectory.open(new File(indexPath));
			directoryReader = DirectoryReader.open(directory);
			titleIterator = MultiFields
					.getTerms(directoryReader, "whole_title").iterator(null);
			BytesRef temp;
			while ((temp = titleIterator.next()) != null) {
				System.out.println(temp.utf8ToString());
				System.out.println(titleIterator.docFreq());
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}

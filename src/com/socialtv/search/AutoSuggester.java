package com.socialtv.search;

import java.io.IOException;
import java.util.List;
import java.util.logging.Logger;

import org.apache.lucene.search.suggest.Lookup.LookupResult;
import org.apache.lucene.search.suggest.analyzing.BlendedInfixSuggester;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.RAMDirectory;
import org.apache.lucene.util.Version;
import org.json.JSONObject;
import org.wltea.analyzer.lucene.IKAnalyzer;

public class AutoSuggester {
	
	private static final Logger logger = Logger.getLogger("searchlog");
	private BlendedInfixSuggester suggester;
	private JSONObject requestJson;
	
	public AutoSuggester(JSONObject jsonObject, String indexPath) {
		// TODO Auto-generated constructor stub
		requestJson = jsonObject;
		TitleIterator titleIterateor = new TitleIterator(indexPath);
		Directory directory = new RAMDirectory();
		try {
			suggester = new BlendedInfixSuggester(Version.LATEST, directory, new IKAnalyzer());
			suggester.build(titleIterateor);
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
		} catch (Exception e) {
			// TODO Auto-generated catch block
			logger.severe(e.getLocalizedMessage());
		}
		return responseJson;
	}
	
	
}

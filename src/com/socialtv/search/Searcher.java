package com.socialtv.search;

import java.io.File;
import java.sql.Date;
import java.util.logging.Logger;

import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queries.TermsFilter;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.search.Filter;
import org.apache.lucene.search.FilteredQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.NumericRangeFilter;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.Sort;
import org.apache.lucene.search.SortField;
import org.apache.lucene.search.SortField.Type;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.json.JSONArray;
import org.json.JSONObject;
import org.wltea.analyzer.lucene.IKAnalyzer;

public class Searcher {

	// Get searchlog logger
	private static final Logger logger = Logger.getLogger("searchlog");
	// When searching, there is a default max response count, I make it 500.
	private static final int DEFAULTRESPONSECOUNT = 500;

	private String indexPath;
	private String spellCheckerIndexPath;
	private JSONObject requestJson;
	private JSONObject responseJson;

	public Searcher(JSONObject json, String iP, String sCIP) {
		indexPath = iP;
		spellCheckerIndexPath = sCIP;
		requestJson = json;
		responseJson = new JSONObject();
	}

	private void search() {

		// The fields we want to search.
		String[] fields = { "title", "description" };
		try {
			// Get search keywords from request
			String keywords = requestJson.getString("keywords");
			// With MultiFieldQueryPaser, we specify fields and analyzer
			MultiFieldQueryParser mfqp = new MultiFieldQueryParser(fields,
					new IKAnalyzer(true));
			// Get Query after parsing the keywords with the help of
			// MultiFieldQueryParser.
			Query query = mfqp.parse(keywords);

			String owner_id = null, category_id = null;
			TermsFilter ownerIdFilter = null, categoryIdFilter = null;
			if (requestJson.has("filter")) {
				JSONObject filter = requestJson.getJSONObject("filter");
				if (filter.has("owner_id")) {
					owner_id = filter.getString("owner_id");
					// Create a TermsFilter when user specify an owner_id.
					ownerIdFilter = new TermsFilter(new Term("owner_id",
							owner_id));
				}
				if (filter.has("category_id")) {
					category_id = filter.getString("category_id");
					// Create a TermsFilter when user specify a category_id.
					categoryIdFilter = new TermsFilter(new Term("category_id",
							category_id));
				}
			}

			int inDays = Integer.MAX_VALUE;
			Filter inDaysFilter = null;
			if (requestJson.has("inDays")) {
				inDays = requestJson.getInt("inDays");
				Date startDate = new Date(System.currentTimeMillis()
						- (long) inDays * 24l * 3600l * 1000l);
				String temp = startDate.toString();
				int startTime = Integer.parseInt(temp.substring(0, 4)
						+ temp.substring(5, 7) + temp.substring(8, 10));

				Date endDate = new Date(System.currentTimeMillis());
				temp = endDate.toString();
				int endTime = Integer.parseInt(temp.substring(0, 4)
						+ temp.substring(5, 7) + temp.substring(8, 10));

				// Create a NumericRangeFilter when user specify the creation
				// time.
				inDaysFilter = NumericRangeFilter.newIntRange("tempDate",
						startTime, endTime, true, true);
			}

			String sortWay = null;
			Sort sort = null;
			if (requestJson.has("sortWay")) {
				sortWay = requestJson.getString("sortWay");
				if (sortWay.equals("v"))
					sort = new Sort(new SortField("watch_count", Type.LONG,
							true));
				// Create a Sort when user specify a sort way.
				else if (sortWay.equals("t"))
					sort = new Sort(new SortField("tempTime", Type.LONG, true));
			}

			int startIndex = 0, requestCount = DEFAULTRESPONSECOUNT;
			if (requestJson.has("startIndex"))
				startIndex = requestJson.getInt("startIndex");
			if (requestJson.has("requestCount"))
				requestCount = requestJson.getInt("requestCount");

			// Attach the filters to the query if they exist.
			if (ownerIdFilter != null)
				query = new FilteredQuery(query, ownerIdFilter);
			if (categoryIdFilter != null)
				query = new FilteredQuery(query, categoryIdFilter);
			if (inDaysFilter != null)
				query = new FilteredQuery(query, inDaysFilter);

			Directory directory = FSDirectory.open(new File(indexPath));
			// Create an IndexSearcher
			IndexSearcher searcher = new IndexSearcher(
					DirectoryReader.open(directory));

			TopDocs topDocs = null;
			// Start to search
			if (sort == null)
				topDocs = searcher.search(query, startIndex + requestCount * 2);
			else
				topDocs = searcher.search(query, startIndex + requestCount * 2,
						sort);
			// Get hit documents
			ScoreDoc[] hits = topDocs.scoreDocs;
			// Get hit document number
			int responseCount = Math.min(topDocs.totalHits - startIndex,
					requestCount);
			responseCount = responseCount < 0 ? 0 : responseCount;

			// When there is few hits, we generate some suggest words
			if (responseCount < 3) {
				String[] sugWrods = Suggester.suggestSpellChecker(keywords,
						spellCheckerIndexPath);

				JSONArray jsonArray = new JSONArray();
				for (String string : sugWrods) {
					jsonArray.put(string);
				}
				responseJson.put("suggestWords", jsonArray);
			}

			responseJson.put("responseCount", responseCount);

			// Put all data into responseJson
			JSONArray data = new JSONArray();
			for (int i = startIndex; i < responseCount + startIndex; i++) {
				Document doc = searcher.doc(hits[i].doc);
				JSONObject json = new JSONObject();
				json.put("id", doc.get("id"));
				data.put(json);
			}
			responseJson.put("data", data);
		} catch (Exception e) { /* report an error */
			logger.severe(e.getLocalizedMessage());
		}
	}

	public JSONObject getResponse() {
		search();
		return responseJson;
	}

}

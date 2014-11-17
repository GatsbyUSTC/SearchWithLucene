package newpackage;

import java.io.File;
import java.sql.Date;

import org.apache.lucene.analysis.standard.StandardAnalyzer;
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
import org.apache.lucene.util.Version;
import org.json.JSONArray;
import org.json.JSONObject;

public class Searcher {
	private JSONObject requestJson;
	private JSONObject responseJson;

	public Searcher(JSONObject json){
		requestJson = json;
		responseJson = new JSONObject();
	}

	private void search(){
		String indexPath = "/home/hongwei/workspace/stvsearch/index";
		String[] fields = { "title", "description" };
		try {
			String keywords = requestJson.getString("keywords");
			String[] sugWrods = Suggester.suggestSpellChecker(keywords);
			
			JSONArray jsonArray = new JSONArray();
			for (String string : sugWrods) {
				jsonArray.put(string);
			}
			responseJson.put("suggestWords", jsonArray);
			@SuppressWarnings("deprecation")
			MultiFieldQueryParser mfqp = new MultiFieldQueryParser(
					Version.LUCENE_CURRENT, fields, new StandardAnalyzer());
			Query query = mfqp.parse(keywords);

			String owner_id = null, category_id = null;
			TermsFilter ownerIdFilter = null, categoryIdFilter = null;
			if (requestJson.has("filter")) {
				JSONObject filter = requestJson.getJSONObject("filter");
				if (filter.has("owner_id")) {
					owner_id = filter.getString("owner_id");
					ownerIdFilter = new TermsFilter(new Term("owner_id",
							owner_id));
				}
				if (filter.has("category_id")) {
					category_id = filter.getString("category_id");
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

				inDaysFilter = NumericRangeFilter.newIntRange("tempDate",
						startTime, endTime, true, true);
				/*
				 * Date startDate = new Date(System.currentTimeMillis() -
				 * (long)inDays 24l * 3600l * 1000l); Date endDate = new
				 * Date(System.currentTimeMillis()); String startTime =
				 * startDate.toString() + " 00:00:00.0", endTime = endDate
				 * .toString() + " 23:59:59.0"; out.print(startTime);
				 * out.print(endTime); inDaysFilter = new
				 * TermRangeFilter("creation_time", new
				 * BytesRef(startTime.getBytes()), new BytesRef(
				 * endTime.getBytes()), true, true);
				 */
			}

			String sortWay = null;
			Sort sort = null;
			if (requestJson.has("sortWay")) {
				sortWay = requestJson.getString("sortWay");
				if (sortWay.equals("v"))
					sort = new Sort(new SortField("watch_count", Type.LONG,
							true));
				else if (sortWay.equals("t"))
					sort = new Sort(new SortField("tempTime", Type.LONG, true));
			}

			int startIndex = 0, requestCount = 500;
			if (requestJson.has("startIndex"))
				startIndex = requestJson.getInt("startIndex");
			if (requestJson.has("requestCount"))
				requestCount = requestJson.getInt("requestCount");

			if (ownerIdFilter != null)
				query = new FilteredQuery(query, ownerIdFilter);
			if (categoryIdFilter != null)
				query = new FilteredQuery(query, categoryIdFilter);
			if (inDaysFilter != null)
				query = new FilteredQuery(query, inDaysFilter);

			Directory directory = FSDirectory.open(new File(indexPath));
			IndexSearcher searcher = new IndexSearcher(
					DirectoryReader.open(directory));

			TopDocs topDocs = null;
			if (sort == null)
				topDocs = searcher.search(query, startIndex + requestCount * 2);
			else
				topDocs = searcher.search(query, startIndex + requestCount * 2,
						sort);
			ScoreDoc[] hits = topDocs.scoreDocs;
			int responseCount = Math.min(topDocs.totalHits - startIndex,
					requestCount);
			responseCount = responseCount < 0 ? 0 : responseCount;
			responseJson.put("responseCount", responseCount);
			JSONArray data = new JSONArray();
			for (int i = startIndex; i < responseCount + startIndex; i++) {
				Document doc = searcher.doc(hits[i].doc);
				JSONObject json = new JSONObject();
//				json.put("creation_time", doc.get("creation_time"));
//				json.put("owner_id", doc.get("owner_id"));
//				json.put("category_id", doc.get("category_id"));
				json.put("id", doc.get("id"));
				json.put("description", doc.get("description"));
				System.out.println(doc.get("description"));
//				json.put("watch_count", doc.get("watch_count"));
				json.put("title", doc.get("title"));
				data.put(json);
			}
			responseJson.put("data", data);
		} catch (Exception e) { /* report an error */
			System.out.print(e);
		}
	}

	public JSONObject getResponse(){
		search();
		return responseJson;
	}
	
}

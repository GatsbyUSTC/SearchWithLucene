<%@ page language="java" contentType="text/html; charset=utf-8"
	pageEncoding="utf-8"%>
<%@ page import="java.io.File"%>
<%@ page import="java.sql.Date"%>
<%@ page import="java.io.BufferedReader"%>
<%@ page import="org.json.*"%>
<%@ page import="org.apache.lucene.analysis.Analyzer"%>
<%@ page import="org.apache.lucene.search.Filter"%>
<%@ page import="org.apache.lucene.search.NumericRangeFilter"%>
<%@ page import="org.apache.lucene.search.SortField"%>
<%@ page import="org.apache.lucene.search.Sort"%>
<%@ page import="org.apache.lucene.search.SortField.Type"%>
<%@ page import="org.apache.lucene.document.Document"%>
<%@ page import="org.apache.lucene.index.DirectoryReader"%>
<%@ page
	import="org.apache.lucene.queryparser.classic.MultiFieldQueryParser"%>
<%@ page import="org.apache.lucene.search.Query"%>
<%@ page import="org.apache.lucene.search.FilteredQuery"%>
<%@ page import="org.apache.lucene.search.TopDocs"%>
<%@ page import="org.apache.lucene.search.ScoreDoc"%>
<%@ page import="org.apache.lucene.queries.TermsFilter"%>
<%@ page import="org.apache.lucene.index.IndexReader"%>
<%@ page import="org.apache.lucene.index.Term"%>
<%@ page import="org.apache.lucene.search.IndexSearcher"%>
<%@ page import="org.apache.lucene.store.Directory"%>
<%@ page import="org.apache.lucene.store.FSDirectory"%>
<%@ page import="org.apache.lucene.util.*"%>
<%@ page import="org.apache.lucene.analysis.standard.StandardAnalyzer"%>
<%@ page import="org.apache.lucene.search.TermRangeFilter"%>

<%
	String indexPath = "/home/liu/workspace/stvent-search/index";
	String[] fields = { "title", "description" };
	StringBuffer jb = new StringBuffer();
	String line = null;
	try {
		BufferedReader reader = request.getReader();
		while ((line = reader.readLine()) != null)
			jb.append(line);
	} catch (Exception e) { /*report an error*/
		e.printStackTrace();
	}
	JSONObject jsonObject = new JSONObject(jb.toString());
	String keywords = jsonObject.getString("keywords");
	String UTFKeywords = new String(keywords.getBytes("ISO-8859-1"),
			"UTF-8");
	MultiFieldQueryParser mfqp = new MultiFieldQueryParser(
			Version.LUCENE_CURRENT, fields, new StandardAnalyzer());
	Query query = mfqp.parse(UTFKeywords);

	String owner_id = null, category_id = null;
	TermsFilter ownerIdFilter = null, categoryIdFilter = null;
	if (jsonObject.has("filter")) {
		JSONObject filter = jsonObject.getJSONObject("filter");
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
	if (jsonObject.has("inDays")) {
		inDays = jsonObject.getInt("inDays");
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
		/* Date startDate = new Date(System.currentTimeMillis() - (long)inDays
		 * 24l * 3600l * 1000l);
		Date endDate = new Date(System.currentTimeMillis());
		String startTime = startDate.toString() + " 00:00:00.0", endTime = endDate
				.toString() + " 23:59:59.0";
		out.print(startTime);
		out.print(endTime);
		inDaysFilter = new TermRangeFilter("creation_time",
				new BytesRef(startTime.getBytes()), new BytesRef(
						endTime.getBytes()), true, true); */
	}

	String sortWay = null;
	Sort sort = null;
	if (jsonObject.has("sortWay")) {
		sortWay = jsonObject.getString("sortWay");
		if (sortWay.equals("v"))
			sort = new Sort(new SortField("watch_count", Type.LONG,
					true));
		else if (sortWay.equals("t"))
			sort = new Sort(new SortField("tempTime", Type.LONG, true));
	}

	int startIndex = 0, requestCount = 500;
	if (jsonObject.has("startIndex"))
		startIndex = jsonObject.getInt("startIndex");
	if (jsonObject.has("requestCount"))
		requestCount = jsonObject.getInt("requestCount");

	try {
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
			topDocs = searcher.search(query, startIndex + requestCount
					* 2);
		else
			topDocs = searcher.search(query, startIndex + requestCount
					* 2, sort);
		ScoreDoc[] hits = topDocs.scoreDocs;
		int responseCount = Math.min(topDocs.totalHits - startIndex,
				requestCount);
		JSONObject responseJO = new JSONObject();
		responseCount = responseCount < 0 ? 0 : responseCount;
		responseJO.put("responseCount", responseCount);
		JSONArray data = new JSONArray();
		for (int i = startIndex; i < responseCount + startIndex; i++) {
			Document doc = searcher.doc(hits[i].doc);
			JSONObject json = new JSONObject();
			json.put("creation_time", doc.get("creation_time"));
			json.put("owner_id", doc.get("owner_id"));
			json.put("category_id", doc.get("category_id"));
			json.put("id", doc.get("id"));
			json.put("watch_count", doc.get("watch_count"));
			json.put("title", doc.get("title"));
			data.put(json);
		}

		responseJO.put("data", data);
		out.print(responseJO.toString());
	} catch (Exception e) {
		e.printStackTrace();
	}
%>

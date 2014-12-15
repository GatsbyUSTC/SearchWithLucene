package com.socialtv.search;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.util.logging.Logger;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field.Store;
import org.apache.lucene.document.LongField;
import org.apache.lucene.document.StoredField;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;
import org.json.JSONException;
import org.json.JSONObject;
import org.wltea.analyzer.lucene.IKAnalyzer;

import com.mysql.jdbc.Driver;

public class Indexer {

	// Get the indexlog logger
	private static final Logger logger = Logger.getLogger("indexlog");
	// This is the java format url of the database
	private static String dburl;
	// This is the username of the database
	private static String username;
	// This is the password of the database
	private static String password;
	// This is the database query
	private static String dbquery;

	public Indexer() {
	}

	public static void getConfig(String xmlpath) {
		ConfigReader reader = new ConfigReader();
		if (!reader.readXML(xmlpath)) {
			logger.severe("config.xml reading fault");
			return;
		}
		dburl = reader.geturl();
		username = reader.getusername();
		password = reader.getpassword();
		dbquery = reader.getqeury();
	}

	public static boolean indexOneDoc(JSONObject json, String indexPath,
			String xmlpath) {

		getConfig(xmlpath);
		// Construct database query
		String id = null;
		try {
			id = json.getString("id");
		} catch (JSONException e1) {
			e1.printStackTrace();
		}

		String onesdbquery = dbquery + " WHERE content.id = '" + id + "'";

		try {
			DriverManager.registerDriver(new Driver());
			// Get the connection
			Connection con = DriverManager.getConnection(dburl, username,
					password);
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(onesdbquery);

			// We want to add the information of the video to the index, so the
			// OpenMoode should be APPEND.
			if (rs.first()) {
				rs.beforeFirst();
				addDocument(rs, OpenMode.APPEND, indexPath);
				rs.close();
				stmt.close();
				con.close();
			} else {
				rs.close();
				stmt.close();
				con.close();
				return false;
			}
		} catch (Exception e) {
			logger.severe(e.getLocalizedMessage());
		}
		return true;
	}

	// This static method is called when user wants to reindex all videos'
	// information.
	public static void indexAllDocs(String indexPath,
			String xmlpath) {

		getConfig(xmlpath);
		try {
			DriverManager.registerDriver(new Driver());
			// Get the connection
			Connection con = DriverManager.getConnection(dburl, username,
					password);
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);

			// We want to recreate an index, so the OpenMode should be CREATE.
			addDocument(rs, OpenMode.CREATE, indexPath);

			rs.close();
			stmt.close();
			con.close();
		} catch (Exception e) {
			logger.severe(e.getLocalizedMessage());
		}
	}

	private static void addDocument(ResultSet rs, OpenMode om, String indexPath)
			throws Exception {

		// IKanalyzer is a good analyzer for both Chinese and English.
		Analyzer analyzer = new IKAnalyzer(true);
		// This IndexWriterConfig is used to specify the version and analyzer.
		IndexWriterConfig iwc = new IndexWriterConfig(Version.LATEST, analyzer);
		// OpenMode refers to the open mode of index: CREATE or APPEND can be
		// chosen.
		iwc.setOpenMode(om);

		Directory indexDir = FSDirectory.open(new File(indexPath));
		// After several configurations, we can create a IndexWriter now.
		IndexWriter indexWriter = new IndexWriter(indexDir, iwc);

		String id = null, title = null, owner_id = null, category_id = null, description = null;
		long watch_count = 0, tempTime = 0;

		// Get some key attributes from ResultSet.
		// For the output of database is "UTF-8", we need to make some
		// transcoding here.
		while (rs.next()) {

			id = rs.getString("content_id");

			title = rs.getString("content_title");
			title = title != null ? title : "null";

			description = rs.getString("content_description");
			description = description != null ? description : "null";

			owner_id = rs.getString("auth_user_id");
			owner_id = owner_id != null ? owner_id : "null";

			category_id = rs.getString("category_id");
			category_id = category_id != null ? category_id : "null";

			watch_count = rs.getLong("content_watch_count");

			tempTime = rs.getTimestamp("content_update_time").getTime();

			// Create a new Document for each video's information.
			Document doc = new Document();

			// Add all fields of a video to the document
			// As the title is more important than description, the title
			// field boost is set as 2.0 here.
			TextField titleField = new TextField("title", title, Store.NO);
			titleField.setBoost(2.0f);
			doc.add(titleField);

			// Text Field, indexed, analyzed
			doc.add(new TextField("description", description, Store.NO));

			// String Field, indexed, not analyzed
			doc.add(new StringField("id", id, Store.NO));
			doc.add(new StringField("owner_id", owner_id, Store.NO));
			doc.add(new StringField("category_id", category_id, Store.NO));
			doc.add(new StringField("whole_title", title, Store.NO));

			// long field is used to filter and sort
			doc.add(new LongField("watch_count", watch_count, Store.NO));
			doc.add(new LongField("tempTime", tempTime, Store.NO));

			// stored field, not indexed ,stored
			ResultSetMetaData rsmd = rs.getMetaData();
			int columnCount = rsmd.getColumnCount();
			for (int i = 1; i < columnCount + 1; i++) {
				String label = rsmd.getColumnLabel(i);
				byte[] column = rs.getBytes(i);
				column = column == null ? "null".getBytes("UTF-8") : column;
				doc.add(new StoredField(label, new String(column, "UTF-8")));
			}

			// Index the video using IndexWriter.
			indexWriter.addDocument(doc);
		}
		indexWriter.close();
	}

	// Test indexing all files
	public static void main(String[] args) {
		String indexPath = "WebContent/WEB-INF/index";
		String xmlPath = "WebContent/WEB-INF/config/config.xml";
		long startTime = System.currentTimeMillis();
		System.out.println("index write starts");
		Indexer.indexAllDocs(indexPath, xmlPath);
		long endTime = System.currentTimeMillis();
		System.out.println("index write finishes");
		System.out.println("total time: " + (endTime - startTime) + " ms");
	}

}
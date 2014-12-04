package com.socialtv.search;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
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
import com.sun.org.apache.bcel.internal.generic.NEW;

public class Indexer {

	// Get the indexlog logger
	private static final Logger logger = Logger.getLogger("indexlog");
	// This is the java format url of the database
	private static final String dburl = "jdbc:mysql://155.69.146.44:3306/socialtv";
	// This is the username of the database
	private static final String username = "socialtv";
	// This is the password of the database
	private static final String password = "SocialTV";

	private static final String dbquery = "SELECT content.id AS content_id, content.title AS content_title, "
			+ "content.video_info AS content_video_info, content.description AS content_description, "
			+ "content.update_time AS content_update_time, content.rating_total AS content_rating_total, "
			+ "content.rating_count AS content_rating_count, content.watch_count AS content_watch_count, "
			+ "category.id AS category_id, category.name AS category_name, "
			+ "tag.id AS tag_id, tag.name AS tag_name, "
			+ "auth_user.id AS auth_user_id, auth_user.username AS auth_user_username, "
			+ "ott_content.original_link AS ott_content_original_link "
			+ "FROM content LEFT JOIN category ON content.category_id = category.id "
			+ "LEFT JOIN tag ON content.id = tag.content_id "
			+ "LEFT JOIN auth_user ON content.owner_id = auth_user.id "
			+ "LEFT JOIN ott_content ON content.id = ott_content.content_id ";

	public Indexer() {

	}

	// This method is used to get a Connection from database
	private static Connection connectToDatabase() throws SQLException {
		// Before get connection, the mysql driver should be registered
		// first.
		DriverManager.registerDriver(new Driver());
		// Get the connection
		Connection con = DriverManager.getConnection(dburl, username, password);
		return con;
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

			byte[] tempTitle = rs.getBytes("content_title");
			title = new String(tempTitle, "UTF-8");

			owner_id = rs.getString("auth_user_id");
			owner_id = owner_id != null ? owner_id : "null";
			category_id = rs.getString("category_id");
			category_id = category_id != null ? category_id : "null";

			watch_count = rs.getLong("content_watch_count");
			
			byte[] tempDescription = rs.getBytes("content_description");
			description = new String(tempDescription, "UTF-8");

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
			doc.add(new StringField("category_id", category_id, Store.YES));

			// long field is used to filter and sort
			doc.add(new LongField("watch_count", watch_count, Store.NO));
			doc.add(new LongField("tempDate", tempTime, Store.NO));

			// Index the video using IndexWriter.
			indexWriter.addDocument(addStoredField(rs, doc));
		}
		indexWriter.close();

	}

	// This static method is used to add stored field to document
	private static Document addStoredField(ResultSet rs, Document doc)
			throws Exception {
		byte[] content_id = rs.getBytes("content_id");
		System.out.println(content_id);
		content_id = content_id != null ? content_id : "null".getBytes("UTF-8");
		byte[] content_title = rs.getBytes("content_title");
		content_title = content_title != null ? content_title : "null"
				.getBytes("UTF-8");
		byte[] content_video_info = rs.getBytes("content_video_info");
		content_video_info = content_video_info != null ? content_video_info
				: "null".getBytes("UTF-8");
		byte[] content_description = rs.getBytes("content_description");
		content_description = content_description != null ? content_description
				: "null".getBytes("UTF-8");
		byte[] content_update_time = rs.getBytes("content_update_time");
		content_update_time = content_update_time != null ? content_video_info
				: "null".getBytes("UTF-8");
		byte[] content_rating_total = rs.getBytes("content_rating_total");
		content_rating_total = content_rating_total != null ? content_rating_total
				: "null".getBytes("UTF-8");
		byte[] content_rating_count = rs.getBytes("content_rating_count");
		content_rating_count = content_rating_count != null ? content_rating_count
				: "null".getBytes("UTF-8");
		byte[] category_id = rs.getBytes("category_id");
		category_id = category_id != null ? category_id : "null"
				.getBytes("UTF-8");
		byte[] category_name = rs.getBytes("category_name");
		category_name = category_name != null ? category_name : "null"
				.getBytes("UTF-8");
		byte[] tag_id = rs.getBytes("tag_id");
		tag_id = tag_id != null ? tag_id : "null".getBytes("UTF-8");
		byte[] tag_name = rs.getBytes("tag_name");
		tag_name = tag_name != null ? tag_name : "null".getBytes("UTF-8");
		byte[] auth_user_id = rs.getBytes("auth_user_username");
		auth_user_id = auth_user_id != null ? auth_user_id : "null"
				.getBytes("UTF-8");
		byte[] auth_user_username = rs.getBytes("auth_user_username");
		auth_user_username = auth_user_username != null ? auth_user_username
				: "null".getBytes("UTF-8");
		byte[] ott_content_original_link = rs
				.getBytes("ott_content_original_link");
		ott_content_original_link = ott_content_original_link != null ? ott_content_original_link
				: "null".getBytes("UTF-8");

		doc.add(new StoredField("content_id", new String(content_id, "UTF-8")));
		doc.add(new StoredField("content_title",new String(content_title, "UTF-8")));
		doc.add(new StoredField("content_video_info", new String(
				content_video_info, "UTF-8")));
//		doc.add(new StoredField("content_description", content_description));
//		doc.add(new StoredField("content_update_time", content_update_time));
//		doc.add(new StoredField("content_rating_total", content_rating_total));
//		doc.add(new StoredField("content_rating_count", content_rating_count));
//		doc.add(new StoredField("scategory_id", category_id));
//		doc.add(new StoredField("category_name", category_name));
//		doc.add(new StoredField("tag_id", tag_id));
//		doc.add(new StoredField("tag_name", tag_name));
//		doc.add(new StoredField("auth_user_id", auth_user_id));
//		doc.add(new StoredField("auth_user_username", auth_user_username));
//		doc.add(new StoredField("ott_content_original_link",
//				ott_content_original_link));
		return doc;
	}

	// This static method is called when user wants to index one new video's
	// information with its id.
	public static boolean indexOneDoc(JSONObject json, String indexPath) {

		// Construct database query
		String id = null;
		try {
			id = json.getString("id");
		} catch (JSONException e1) {
			e1.printStackTrace();
		}

		String onesdbquery = dbquery + " WHERE id = '" + id + "'";

		try {
			Connection con = connectToDatabase();
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
			String spellCheckerDictPath, String spellCheckerIndexPath) {

		try {
			Connection con = connectToDatabase();
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);
			// We want to recreate an index, so the OpenMode should be CREATE.
			addDocument(rs, OpenMode.CREATE, indexPath);

			rs.close();
			stmt.close();
			con.close();
			Suggester.indexSpellCheker(spellCheckerDictPath,
					spellCheckerIndexPath);
		} catch (Exception e) {
			logger.severe(e.getLocalizedMessage());
		}
	}
}

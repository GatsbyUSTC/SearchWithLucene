package com.socialtv.search;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
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
	private static final String dburl = "jdbc:mysql://155.69.146.44:3306/socialtv";
	// This is the username of the database
	private static final String username = "socialtv";
	// This is the password of the database
	private static final String password = "SocialTV";

	// This is the database query
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

	public static ArrayList<String> getFields() {

		ArrayList<String> fields = new ArrayList<String>();
		try {
			DriverManager.registerDriver(new Driver());
			Connection con = DriverManager.getConnection(dburl, username,
					password);
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);
			ResultSetMetaData rsmt = rs.getMetaData();

			for (int i = 1; i < rsmt.getColumnCount() + 1; i++) {
				fields.add(rsmt.getColumnLabel(i));
			}

			rs.close();
			stmt.close();
		} catch (SQLException e) {
			logger.severe(e.getLocalizedMessage());
		}
		return fields;
	}

	public static boolean indexOneDoc(JSONObject json, String indexPath) {

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
			String spellCheckerDictPath, String spellCheckerIndexPath) {

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
			Suggester.indexSpellCheker(spellCheckerDictPath,
					spellCheckerIndexPath);
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

}
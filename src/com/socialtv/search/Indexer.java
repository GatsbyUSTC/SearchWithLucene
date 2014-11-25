package com.socialtv.search;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field.Store;
import org.apache.lucene.document.IntField;
import org.apache.lucene.document.LongField;
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

	// This is the java format url of the database
	private static String dburl = "jdbc:mysql://155.69.146.44:3306/socialtv";
	// This is the username of the database
	private static String username = "socialtv";
	// This is the password of the database
	private static String password = "SocialTV";


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

		String id = null, title = null, owner_id = null, category_id = null, description = null, creation_time = null;
		// String update_time = null, status = null, rating_total = null,
		// rating_count = null, video_info = null, check_sum = null;
		long watch_count = 0, tempTime = 0;
		int tempDate = 0;

		// Get some key attributes from ResultSet.
		// For the output of database is "UTF-8", we need to make some
		// transcoding here.
		while (rs.next()) {

			id = rs.getString("id");

			byte[] tempTitle = rs.getBytes("title");
			title = new String(tempTitle, "UTF-8");

			owner_id = rs.getString("owner_id") == null ? "0" : rs
					.getString("owner_id");

			category_id = rs.getString("category_id");
			watch_count = rs.getLong("watch_count");

			byte[] tempDescription = rs.getBytes("description");
			description = new String(tempDescription, "UTF-8");

			creation_time = rs.getString("creation_time");
			tempDate = Integer.parseInt(creation_time.substring(0, 4)
					+ creation_time.substring(5, 7)
					+ creation_time.substring(8, 10));
			tempTime = Long.parseLong(creation_time.substring(0, 4)
					+ creation_time.substring(5, 7)
					+ creation_time.substring(8, 10)
					+ creation_time.substring(11, 13)
					+ creation_time.substring(14, 16)
					+ creation_time.substring(17, 19));

			// Create a new Document for each video's information.
			Document doc = new Document();
			doc.add(new TextField("id", id, Store.YES));

			// As the title is more important than description, the title
			// field boost is set as 2.0 here.
			TextField titleField = new TextField("title", title, Store.YES);
			titleField.setBoost(2.0f);
			doc.add(titleField);

			// Add all fields of a video to the document
			doc.add(new TextField("owner_id", owner_id, Store.YES));
			doc.add(new TextField("category_id", category_id, Store.YES));
			doc.add(new TextField("creation_time", creation_time, Store.YES));
			doc.add(new LongField("watch_count", watch_count, Store.YES));
			doc.add(new TextField("description", description, Store.YES));
			doc.add(new IntField("tempDate", tempDate, Store.YES));
			doc.add(new LongField("tempTime", tempTime, Store.YES));

			// Index the video using IndexWriter.
			indexWriter.addDocument(doc);
		}
		indexWriter.close();

	}

	// This static method is called when user wants to index one new video's
	// information with its id.
	public static void indexOneDoc(JSONObject json, String indexPath) {

		// Construct database query
		String id = null;
		try {
			id = json.getString("id");
		} catch (JSONException e1) {
			e1.printStackTrace();
		}
		String dbquery = "SELECT " + "id, " + "title, " + "owner_id, "
				+ "category_id," + "creation_time," + "update_time,"
				+ "watch_count," + "status," + "description," + "rating_total,"
				+ "rating_count," + "video_info," + "checksum FROM content"
				+ " WHERE id = '" + id + "'";

		try {
			Connection con = connectToDatabase();
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);
			// We want to add the information of the video to the index, so the
			// OpenMoode should be APPEND.
			addDocument(rs, OpenMode.APPEND, indexPath);

			rs.close();
			stmt.close();
			con.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	// This static method is called when user wants to reindex all videos'
	// information.
	public static void indexAllDocs(String indexPath, String spellCheckerDictPath, String spellCheckerIndexPath) {

		// Construct database query
		String dbquery = "SELECT " + "id, " + "title, " + "owner_id, "
				+ "category_id," + "creation_time," + "update_time,"
				+ "watch_count," + "status," + "description," + "rating_total,"
				+ "rating_count," + "video_info," + "checksum FROM content";

		try {
			Connection con = connectToDatabase();
			Statement stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);
			// We want to recreate an index, so the OpenMode should be CREATE.
			addDocument(rs, OpenMode.CREATE, indexPath);

			rs.close();
			stmt.close();
			con.close();
			Suggester.indexSpellCheker(spellCheckerDictPath, spellCheckerIndexPath);
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

}

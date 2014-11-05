package test;

import java.io.File;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.util.CharArraySet;
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

public class SocialTVAnalyticsSearchPart {

	public SocialTVAnalyticsSearchPart() {

	}

	private Connection connectToDatabase() {
		String username = "socialtv";
		String password = "SocialTV";
		String url = "jdbc:mysql://155.69.146.44:3306/socialtv";
		Connection con = null;
		try {
			con = DriverManager.getConnection(url, username, password);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return con;
	}

	public void writeIndex() {
		String indexPath = "index";
		Directory indexDir = null;
		IndexWriter indexWriter = null;
		/*
		 * CharArraySet temp = new CharArraySet(Version.LUCENE_CURRENT,5,false);
		 * temp.add("p");
		 */
		Analyzer analyzer = new StandardAnalyzer(CharArraySet.EMPTY_SET);
		//System.out.println(StandardAnalyzer.STOP_WORDS_SET);
		IndexWriterConfig iwc = new IndexWriterConfig(Version.LUCENE_CURRENT,
				analyzer);
		iwc.setOpenMode(OpenMode.CREATE);
		try {
			indexDir = FSDirectory.open(new File(indexPath));
			indexWriter = new IndexWriter(indexDir, iwc);
		} catch (IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}

		String dbquery = "SELECT " + "id, " + "title, " + "owner_id, "
				+ "category_id," + "creation_time," + "update_time,"
				+ "watch_count," + "status," + "description," + "rating_total,"
				+ "rating_count," + "video_info," + "checksum FROM content";
		String id = null, title = null, owner_id = null, category_id = null, creation_time = null, update_time = null, status = null, description = null, rating_total = null, rating_count = null, video_info = null, check_sum = null;
		long watch_count = 0, tempTime = 0;
		int tempDate = 0;
		Connection con = this.connectToDatabase();
		Statement stmt;
		try {
			stmt = con.createStatement();
			ResultSet rs = stmt.executeQuery(dbquery);
			while (rs.next()) {
				id = rs.getString("id");
				title = rs.getString("title");
				owner_id = rs.getString("owner_id") == null ? "0" : rs
						.getString("owner_id");
				category_id = rs.getString("category_id");
				creation_time = rs.getString("creation_time");
				//update_time = rs.getString("update_time");
				watch_count = rs.getLong("watch_count");
				//status = rs.getString("status");
				description = rs.getString("description");
				//rating_total = rs.getString("rating_total");
				//rating_count = rs.getString("rating_count");
				//video_info = rs.getString("video_info");
				//check_sum = rs.getString("checksum");

				tempDate = Integer.parseInt(creation_time.substring(0, 4)
						+ creation_time.substring(5, 7)
						+ creation_time.substring(8, 10));
				tempTime = Long.parseLong(creation_time.substring(0, 4)
						+ creation_time.substring(5, 7)
						+ creation_time.substring(8, 10)
						+ creation_time.substring(11, 13)
						+ creation_time.substring(14, 16)
						+ creation_time.substring(17, 19));

				Document doc = new Document();
				doc.add(new TextField("id", id, Store.YES));
				TextField titleField = new TextField("title", title, Store.YES);
				titleField.setBoost(2.0f);
				doc.add(titleField);
				doc.add(new TextField("owner_id", owner_id, Store.YES));
				doc.add(new TextField("category_id", category_id, Store.YES));
				doc.add(new TextField("creation_time", creation_time, Store.YES));
				//doc.add(new TextField("update_time", update_time, Store.YES));
				doc.add(new LongField("watch_count", watch_count, Store.YES));
				//doc.add(new TextField("status", status, Store.YES));
				doc.add(new TextField("description", description, Store.YES));
				//doc.add(new TextField("rating_total", rating_total, Store.YES));
				//doc.add(new TextField("rating_count", rating_count, Store.YES));
				//doc.add(new TextField("video_info", video_info, Store.YES));
				//doc.add(new TextField("checksum", check_sum, Store.YES));

				doc.add(new IntField("tempDate", tempDate, Store.YES));
				doc.add(new LongField("tempTime", tempTime, Store.YES));

				indexWriter.addDocument(doc);
			}
			rs.close();
			stmt.close();
			con.close();
			indexWriter.close();
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}

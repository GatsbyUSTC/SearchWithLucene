import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Enumeration;
import java.util.Properties;
import java.util.StringTokenizer;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.queryparser.xml.CorePlusExtensionsParser;
import org.apache.lucene.queryparser.xml.QueryTemplateManager;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.RAMDirectory;
import org.apache.lucene.util.Version;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;



/**
 * Example servlet that uses the XML queryparser.
 * <p>
 * NOTE: you must provide CSV data in <code>/WEB-INF/data.tsv</code>
 * for the demo to work!
 */
public class socialTVAnalyticsSearchPart extends HttpServlet {

  /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private QueryTemplateManager queryTemplateManager;
  private CorePlusExtensionsParser xmlParser;
  private IndexSearcher searcher;
  private Analyzer analyzer = new StandardAnalyzer();

  /** for instantiation by the servlet container */
  public socialTVAnalyticsSearchPart() {}

  public Connection getConnection() throws SQLException {

	    Connection conn = null;
	    String userName = "";
	    String password = "";
	    Properties connectionProps = new Properties();
	    connectionProps.put("user", userName);
	    connectionProps.put("password", password);

	    if (this.dbms.equals("mysql")) {
	        conn = DriverManager.getConnection(
	                   "jdbc:" + this.dbms + "://" +
	                   this.serverName +
	                   ":" + this.portNumber + "/",
	                   connectionProps);
	    } else if (this.dbms.equals("derby")) {
	        conn = DriverManager.getConnection(
	                   "jdbc:" + this.dbms + ":" +
	                   this.dbName +
	                   ";create=true",
	                   connectionProps);
	    }
	    System.out.println("Connected to database");
	    return conn;
	}
  @Override
  public void init(ServletConfig config) throws ServletException {
    super.init(config);
    try {
      openExampleIndex();

      //load servlet configuration settings
      String xslFile = config.getInitParameter("xslFile");
      String defaultStandardQueryParserField = config.getInitParameter("defaultStandardQueryParserField");


      //Load and cache choice of XSL query template using QueryTemplateManager
      queryTemplateManager = new QueryTemplateManager(
          getServletContext().getResourceAsStream("/WEB-INF/" + xslFile));

      //initialize an XML Query Parser for use by all threads
      xmlParser = new CorePlusExtensionsParser(defaultStandardQueryParserField, analyzer);
    } catch (Exception e) {
      throw new ServletException("Error loading query template", e);
    }
  }

  @Override
  protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    //Take all completed form fields and add to a Properties object
    Properties completedFormFields = new Properties();
    Enumeration<?> pNames = request.getParameterNames();
    while (pNames.hasMoreElements()) {
      String propName = (String) pNames.nextElement();
      String value = request.getParameter(propName);
      if ((value != null) && (value.trim().length() > 0)) {
        completedFormFields.setProperty(propName, value);
      }
    }

    try {
      //Create an XML query by populating template with given user criteria
      org.w3c.dom.Document xmlQuery = queryTemplateManager.getQueryAsDOM(completedFormFields);

      //Parse the XML to produce a Lucene query
      Query query = xmlParser.getQuery(xmlQuery.getDocumentElement());

      //Run the query
      TopDocs topDocs = searcher.search(query, 10);

      //and package the results and forward to JSP
      if (topDocs != null) {
        ScoreDoc[] sd = topDocs.scoreDocs;
        Document[] results = new Document[sd.length];
        for (int i = 0; i < results.length; i++) {
          results[i] = searcher.doc(sd[i].doc);
          request.setAttribute("results", results);
        }
      }
      RequestDispatcher dispatcher = getServletContext().getRequestDispatcher("/index.jsp");
      dispatcher.forward(request, response);
    }
    catch (Exception e) {
      throw new ServletException("Error processing query", e);
    }
  }

  private void openExampleIndex() throws IOException {
    //Create a RAM-based index from our test data file
    RAMDirectory rd = new RAMDirectory();
    IndexWriterConfig iwConfig = new IndexWriterConfig(Version.LUCENE_CURRENT, analyzer);
    IndexWriter writer = new IndexWriter(rd, iwConfig);
    InputStream dataIn = getServletContext().getResourceAsStream("/WEB-INF/data.tsv");
    BufferedReader br = new BufferedReader(new InputStreamReader(dataIn, StandardCharsets.UTF_8));
    String line = br.readLine();
    final FieldType textNoNorms = new FieldType(TextField.TYPE_STORED);
    textNoNorms.setOmitNorms(true);
    while (line != null) {
      line = line.trim();
      if (line.length() > 0) {
        //parse row and create a document
        StringTokenizer st = new StringTokenizer(line, "\t");
        Document doc = new Document();
        doc.add(new Field("location", st.nextToken(), textNoNorms));
        doc.add(new Field("salary", st.nextToken(), textNoNorms));
        doc.add(new Field("type", st.nextToken(), textNoNorms));
        doc.add(new Field("description", st.nextToken(), textNoNorms));
        writer.addDocument(doc);
      }
      line = br.readLine();
    }
    writer.close();

    //open searcher
    // this example never closes it reader!
    IndexReader reader = DirectoryReader.open(rd);
    searcher = new IndexSearcher(reader);
  }
}

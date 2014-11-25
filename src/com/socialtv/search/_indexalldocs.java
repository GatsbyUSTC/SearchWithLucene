package com.socialtv.search;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.logging.FileHandler;
import java.util.logging.Handler;
import java.util.logging.LogManager;
import java.util.logging.Logger;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.store.FSDirectory;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Servlet implementation class _indexalldocs This Servlet is called when all
 * videos' information needs to be re-indexed.
 */
@WebServlet("/_indexalldocs")
public class _indexalldocs extends HttpServlet {
	private static final long serialVersionUID = 1L;

	// Create indexlog logger
	private static final Logger logger = Logger.getLogger("indexlog");
	private String rootPath;

	/**
	 * @see HttpServlet#HttpServlet()
	 */
	public _indexalldocs() {
		super();
		// TODO Auto-generated constructor stub
	}

	public void init(ServletConfig config) throws ServletException {
		super.init(config);

		// Get root path
		rootPath = config.getServletContext().getRealPath("");
		String logPath = rootPath + "/WEB-INF/log/index.log";

		// Redirect the logger to a file handler
		Handler fh = null;
		try {
			fh = new FileHandler(logPath, true);
		} catch (Exception e) {
			e.printStackTrace();
		}
		LogManager.getLogManager().reset();
		logger.addHandler(fh);
	}

	/**
	 * @see HttpServlet#doGet(HttpServletRequest request, HttpServletResponse
	 *      response)
	 */
	protected void doGet(HttpServletRequest request,
			HttpServletResponse response) throws ServletException, IOException {
		// TODO Auto-generated method stub
		doPost(request, response);

	}

	/**
	 * @see HttpServlet#doPost(HttpServletRequest request, HttpServletResponse
	 *      response)
	 */
	protected void doPost(HttpServletRequest request,
			HttpServletResponse response) throws ServletException, IOException {

		// Get index path and spell checker index path
		String indexPath = rootPath + "/WEB-INF/index_files/index";
		String spellCheckerIndexPath = rootPath
				+ "/WEB-INF/index_files/spellCheckerIndex";
		String spellCheckerDictPath = rootPath
				+ "/WEB-INF/index_files/spellCheckerDic/4000-most-common-english-words-csv.csv";

		// Set response configuration
		response.setContentType("application/json; charset=UTF-8");
		PrintWriter out = response.getWriter();
		JSONObject jsonObject = new JSONObject();

		// See if the directory is locked which means another IndexWriter is
		// writing
		if (IndexWriter.isLocked(FSDirectory.open(new File(indexPath)))) {
			try {
				jsonObject.put("status", "fail");
				jsonObject.put("info", "index_locked");
			} catch (JSONException e) {
				// TODO Auto-generated catch block
				logger.severe(e.getLocalizedMessage());
			}
			out.print(jsonObject.toString());
			return;
		}

		// Create a new thread to do the index process
		IndexThread indexThread = new IndexThread(indexPath,
				spellCheckerIndexPath, spellCheckerDictPath);
		Thread thread = new Thread(indexThread);

		// Return success
		try {
			jsonObject.put("status", "success");
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getLocalizedMessage());
		}
		out.print(jsonObject.toString());

		// Start the thread
		thread.start();
	}

}

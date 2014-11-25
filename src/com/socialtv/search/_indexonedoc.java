package com.socialtv.search;

import java.io.BufferedReader;
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
 * Servlet implementation class HttpIndexer This Servlet is called when one new
 * video is created and its information needs to be indexed.
 */
@WebServlet("/_indexonedoc")
public class _indexonedoc extends HttpServlet {
	private static final long serialVersionUID = 1L;

	// Create the indexlog logger
	private static final Logger logger = Logger.getLogger("indexlog");
	private String rootPath;

	/**
	 * @see HttpServlet#HttpServlet()
	 */
	public _indexonedoc() {
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

		// Set response configuration
		response.setContentType("application/json; charset=UTF-8");
		PrintWriter out = response.getWriter();
		JSONObject jsonObject = new JSONObject();

		// Get request and parse it to JSON
		StringBuffer jb = new StringBuffer();
		BufferedReader reader = request.getReader();
		String line = null;
		while ((line = reader.readLine()) != null)
			jb.append(line);
		JSONObject requestJson = null;
		try {
			requestJson = new JSONObject(jb.toString());
		} catch (JSONException e) {
			// See if Json fail
			try {
				jsonObject.put("status", "fail");
				jsonObject.put("info", "json_error");
			} catch (JSONException e1) {
				logger.severe(e1.getLocalizedMessage());
			}
			out.print(jsonObject.toString());
			return;
		}

		// See if the directory is locked which means another IndexWriter is
		// writing
		if (IndexWriter.isLocked(FSDirectory.open(new File(indexPath)))) {
			try {
				jsonObject.put("status", "fail");
				jsonObject.put("info", "index_locked");
			} catch (JSONException e) {
				logger.severe(e.getLocalizedMessage());
			}
			out.print(jsonObject.toString());
			return;
		}

		// Index the document
		Indexer.indexOneDoc(requestJson, indexPath);

		// Output a success information
		try {
			jsonObject.put("status", "success");
		} catch (JSONException e) {
			logger.severe(e.getLocalizedMessage());
		}
		out.print(jsonObject.toString());
	}

}

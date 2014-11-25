package com.socialtv.search;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;

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

	/**
	 * @see HttpServlet#HttpServlet()
	 */
	public _indexalldocs() {
		super();
		// TODO Auto-generated constructor stub
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
		String rootPath = getServletContext().getRealPath("");
		String indexPath = rootPath + "/WEB-INF/index_files/index";
		String spellCheckerIndexPath = rootPath
				+ "/WEB-INF/index_files/spellCheckerIndex";
		String spellCheckerDictPath = rootPath
				+ "/WEB-INF/index_files/spellCheckerDic/4000-most-common-english-words-csv.csv";


		// Set response configuration
		response.setContentType("application/json; charset=UTF-8");
		PrintWriter out = response.getWriter();
		JSONObject jsonObject = new JSONObject();
		
		//See if the directory is locked which means another IndexWriter is writing
		if(IndexWriter.isLocked(FSDirectory.open(new File(indexPath)))){
			try {
				jsonObject.append("status", "fail");
				jsonObject.append("info", "index_locked");
			} catch (JSONException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
			out.print(jsonObject.toString());
			return ;
		}
		
		// Create a new thread to do the index process
		IndexThread indexThread = new IndexThread(indexPath,
				spellCheckerIndexPath, spellCheckerDictPath);
		Thread thread = new Thread(indexThread);

		//Return success
		try {
			jsonObject.append("status", "success");
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		out.print(jsonObject.toString());
		
		//Start the thread
		thread.start();
	}

}

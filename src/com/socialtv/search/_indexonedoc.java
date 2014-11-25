package com.socialtv.search;

import java.io.BufferedReader;
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
 * Servlet implementation class HttpIndexer This Servlet is called when one new
 * video is created and its information needs to be indexed.
 */
@WebServlet("/_indexonedoc")
public class _indexonedoc extends HttpServlet {
	private static final long serialVersionUID = 1L;

	/**
	 * @see HttpServlet#HttpServlet()
	 */
	public _indexonedoc() {
		super();
		// TODO Auto-generated constructor stub
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
		String rootPath = getServletContext().getRealPath("");
		String indexPath = rootPath + "/WEB-INF/index_files/index";

		//Set response configuration
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
			//See if Json fail
			try {
				jsonObject.append("status", "fail");
				jsonObject.append("info", e.getLocalizedMessage());
			} catch (JSONException e1) {
				e1.printStackTrace();
			}
			out.print(jsonObject.toString());
			return;
		}

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
		
		// Index the document
		Indexer.indexOneDoc(requestJson, indexPath);
		
		// Output a success information
		try {
			jsonObject.append("status", "success");
		} catch (JSONException e) {
			e.printStackTrace();
		}
		out.print(jsonObject.toString());
	}

}

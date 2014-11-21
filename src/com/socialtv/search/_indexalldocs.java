package com.socialtv.search;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

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
		
		//Get index path and spell checker index path
		String rootPath = getServletContext().getRealPath("");
		String indexPath = rootPath + "/WEB-INF/index_files/index";
		String spellCheckerIndexPath = rootPath + "/WEB-INF/index_files/spellCheckerIndex";
		String spellCheckerDicPath = rootPath + "/WEB-INF/index_files/spellCheckerDic/4000-most-common-english-words-csv.csv";
		
		//index all files
		Indexer.indexAllDocs(indexPath);
		Suggester.indexSpellCheker(spellCheckerDicPath, spellCheckerIndexPath);
	}

}

package newpackage;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Servlet implementation class _search This Servlet is called when searching.
 */
@WebServlet("/_search")
public class _search extends HttpServlet {
	private static final long serialVersionUID = 1L;

	/**
	 * @see HttpServlet#HttpServlet()
	 */
	public _search() {
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
		
		// Get request and parse it to JSON
		StringBuffer jb = new StringBuffer();
		BufferedReader reader = request.getReader();
		String line = null;
		while ((line = reader.readLine()) != null)
			jb.append(line);
		JSONObject requestJson = null;
		try {
			 requestJson = new JSONObject(jb.toString());
			// search and output the results
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		//construct Searcher
		Searcher indexSearcher = new Searcher(requestJson, indexPath, spellCheckerIndexPath);
		
		// Set response content type and get response writer.
		response.setContentType("application/json; charset=UTF-8");
		PrintWriter out = response.getWriter();
		out.print(indexSearcher.getResponse());
	}
}

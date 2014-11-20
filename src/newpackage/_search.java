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
		// TODO Auto-generated method stub

		// Set response content type and get response writer.
		response.setContentType("application/json; charset=UTF-8");
		PrintWriter out = response.getWriter();

		// Get request and parse it to JSON
		StringBuffer jb = new StringBuffer();
		BufferedReader reader = request.getReader();
		String line = null;
		while ((line = reader.readLine()) != null)
			jb.append(line);

		try {

			// search and output the results
			Searcher indexSearcher = new Searcher(new JSONObject(jb.toString()));
			out.print(indexSearcher.getResponse());

		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}

package com.socialtv.search;

import java.io.BufferedReader;
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

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Servlet implementation class _suggest
 */
@WebServlet("/_suggest")
public class _suggest extends HttpServlet {
	private static final long serialVersionUID = 1L;
    private static final Logger logger = Logger.getLogger("searchlog");
    private static String rootPath;
    
    /**
     * @see HttpServlet#HttpServlet()
     */
    public _suggest() {
        super();
        // TODO Auto-generated constructor stub
    }

    public void init(ServletConfig config) throws ServletException {
		super.init(config);

		// Get root path
		rootPath = config.getServletContext().getRealPath("");
		String logPath = rootPath + "/WEB-INF/log/search.log";

		// Redirect logger to a file handler
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
	 * @see HttpServlet#doGet(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// TODO Auto-generated method stub
		doGet(request, response);
	}

	/**
	 * @see HttpServlet#doPost(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		// TODO Auto-generated method stub

		// Get index path and spell checker index path
		String indexPath = rootPath + "/WEB-INF/index";

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
			try {
				jsonObject.put("status", "fail");
				jsonObject.put("info", "json_error");
			} catch (JSONException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			}
			out.print(jsonObject.toString());
			return;
		}
		AutoSuggester suggester = new AutoSuggester(requestJson, indexPath);
		out.print(suggester.suggest());
	}

}

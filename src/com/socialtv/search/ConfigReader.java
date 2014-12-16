package com.socialtv.search;

import java.io.FileOutputStream;
import java.io.IOException;
import javax.xml.parsers.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.xml.sax.*;
import org.w3c.dom.*;

public class ConfigReader {

	private String url;
	private String username;
	private String password;
	private String query;

	public String geturl() {
		return url;
	}

	public String getusername() {
		return username;
	}

	public String getpassword() {
		return password;
	}

	public String getqeury() {
		return query;
	}

	public boolean readXML(String xml) {
		Document dom;
		// Make an instance of the DocumentBuilderFactory
		DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		try {
			// use the factory to take an instance of the document builder
			DocumentBuilder db = dbf.newDocumentBuilder();
			// parse using the builder to get the DOM mapping of the
			// XML file
			dom = db.parse(xml);

			Element doc = dom.getDocumentElement();

			url = getTextValue(url, doc, "url");
			username = getTextValue(username, doc, "username");
			password = getTextValue(password, doc, "password");
			query = getTextValue(query, doc, "query");
			return true;

		} catch (ParserConfigurationException pce) {
			System.out.println(pce.getMessage());
		} catch (SAXException se) {
			System.out.println(se.getMessage());
		} catch (IOException ioe) {
			System.err.println(ioe.getMessage());
		}
		return false;
	}

	private String getTextValue(String def, Element doc, String tag) {
		String value = def;
		NodeList nl;
		nl = doc.getElementsByTagName(tag);
		if (nl.getLength() > 0 && nl.item(0).hasChildNodes()) {
			value = nl.item(0).getFirstChild().getNodeValue();
		}
		return value;
	}

	public ConfigReader() {
		// TODO Auto-generated constructor stub
	}

	// for testing
	public static void main(String[] args) {
		ConfigReader create = new ConfigReader();
		create.readXML("/home/hongwei/workspace/stvsearch/WebContent/WEB-INF/config/config.xml");
	}

	// for testing
	public void saveToXML(String xml) {
		String dburl = "jdbc:mysql://155.69.146.82:3306/socialtv";
		String username = "socialtv";
		String password = "SocialTV";
		String dbquery = "SELECT content.id AS content_id, content.title AS content_title, "
				+ "content.video_info AS content_video_info, content.description AS content_description, "
				+ "content.update_time AS content_update_time, content.rating_total AS content_rating_total, "
				+ "content.rating_count AS content_rating_count, content.watch_count AS content_watch_count, "
				+ "category.id AS category_id, category.name AS category_name, "
				+ "tag.id AS tag_id, tag.name AS tag_name, "
				+ "auth_user.id AS auth_user_id, auth_user.username AS auth_user_username, "
				+ "ott_content.original_link AS ott_content_original_link "
				+ "FROM content LEFT JOIN category ON content.category_id = category.id "
				+ "LEFT JOIN tag ON content.id = tag.content_id "
				+ "LEFT JOIN auth_user ON content.owner_id = auth_user.id "
				+ "LEFT JOIN ott_content ON content.id = ott_content.content_id";
		Document dom;
		Element e = null;

		// instance of a DocumentBuilderFactory
		DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		try {
			// use factory to get an instance of document builder
			DocumentBuilder db = dbf.newDocumentBuilder();
			// create instance of DOM
			dom = db.newDocument();

			// create the root element
			Element rootEle = dom.createElement("database");

			// create data elements and place them under root
			e = dom.createElement("url");
			e.appendChild(dom.createTextNode(dburl));
			rootEle.appendChild(e);

			e = dom.createElement("username");
			e.appendChild(dom.createTextNode(username));
			rootEle.appendChild(e);

			e = dom.createElement("password");
			e.appendChild(dom.createTextNode(password));
			rootEle.appendChild(e);

			e = dom.createElement("query");
			e.appendChild(dom.createTextNode(dbquery));
			rootEle.appendChild(e);

			dom.appendChild(rootEle);

			try {
				Transformer tr = TransformerFactory.newInstance()
						.newTransformer();
				tr.setOutputProperty(OutputKeys.INDENT, "yes");
				tr.setOutputProperty(OutputKeys.METHOD, "xml");
				tr.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
				// tr.setOutputProperty(OutputKeys.DOCTYPE_SYSTEM, "roles.dtd");
				// tr.setOutputProperty("{http://xml.apache.org/xslt}indent-amount",
				// "4");

				// send DOM to file
				tr.transform(new DOMSource(dom), new StreamResult(
						new FileOutputStream(xml)));

			} catch (TransformerException te) {
				te.printStackTrace();
			} catch (IOException ioe) {
				ioe.printStackTrace();
			}
		} catch (ParserConfigurationException pce) {
			pce.printStackTrace();
		}
	}

}

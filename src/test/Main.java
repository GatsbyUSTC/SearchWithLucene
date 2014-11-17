package test;

import org.json.JSONException;
import org.json.JSONObject;

public class Main {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		JSONObject jsonObject = new JSONObject();
		change(jsonObject);
		System.out.println(jsonObject);
	}
	public static void change(JSONObject a)
	{
		try {
			a.append("a", "nothing");
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}

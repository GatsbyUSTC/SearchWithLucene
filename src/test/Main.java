package test;




public class Main {

	public static void main(String[] args) {
		SocialTVAnalyticsSearchPart stasp = new SocialTVAnalyticsSearchPart();
		long startTime = System.currentTimeMillis();
		System.out.println("index write starts");
		stasp.writeIndex();
		long endTime = System.currentTimeMillis();
		System.out.println("index write finishes");
		System.out.println("total time: " + (endTime - startTime) + " ms");
	}
}

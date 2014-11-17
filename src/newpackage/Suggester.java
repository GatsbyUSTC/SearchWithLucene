package newpackage;

import java.io.File;
import java.io.IOException;

import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.spell.LuceneLevenshteinDistance;
import org.apache.lucene.search.spell.PlainTextDictionary;
import org.apache.lucene.search.spell.SpellChecker;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

public class Suggester {

	private static int suggestionNum = 5;
	private static String spellCheckerPath = "/home/hongwei/workspace/stvsearch/spellcheck";
	private static String spellCheckerDictPath = "/home/hongwei/workspace/stvsearch/spellcheckdic/4000-most-common-english-words-csv.csv";

	public static void indexSpellCheker() {

		try {
			Directory dir = FSDirectory.open(new File(spellCheckerPath));
			SpellChecker spellChecker = new SpellChecker(dir);
			@SuppressWarnings("deprecation")
			IndexWriterConfig iwc = new IndexWriterConfig(
					Version.LUCENE_CURRENT, new StandardAnalyzer());
			spellChecker.indexDictionary(new PlainTextDictionary(new File(
					spellCheckerDictPath)), iwc, false);
			spellChecker.close();
			dir.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public static String[] suggestSpellChecker(String originWord) {

		String[] suggestionWords = null;
		SpellChecker spellChecker = null;
		try {
			Directory dir = FSDirectory.open(new File(spellCheckerPath));
			spellChecker = new SpellChecker(dir,
					new LuceneLevenshteinDistance());
			suggestionWords = spellChecker.suggestSimilar(originWord,
					suggestionNum);
			spellChecker.close();
			dir.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return suggestionWords;
	}

}

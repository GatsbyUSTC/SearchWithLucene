package newpackage;

import java.io.File;
import java.io.IOException;

import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.spell.LuceneLevenshteinDistance;
import org.apache.lucene.search.spell.PlainTextDictionary;
import org.apache.lucene.search.spell.SpellChecker;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;
import org.wltea.analyzer.lucene.IKAnalyzer;

public class Suggester {
	// Make a default suggestion number
	private static int suggestionNum = 5;
	// Spell Checker Index Path
	private static String spellCheckerIndexPath = "/home/hongwei/workspace/stvsearch/spellcheck";
	// Spell Checker Dictionary Path
	private static String spellCheckerDictPath = "/home/hongwei/workspace/stvsearch/spellcheckdic/4000-most-common-english-words-csv.csv";

	// This method is used to index spell checker dictionary
	public static void indexSpellCheker() {

		try {
			Directory dir = FSDirectory.open(new File(spellCheckerIndexPath));
			SpellChecker spellChecker = new SpellChecker(dir);
			IndexWriterConfig iwc = new IndexWriterConfig(Version.LATEST,
					new IKAnalyzer(true));
			spellChecker.indexDictionary(new PlainTextDictionary(new File(
					spellCheckerDictPath)), iwc, false);
			spellChecker.close();
			dir.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	// This method is used to provide suggestions based on the origin word.
	public static String[] suggestSpellChecker(String originWord) {

		String[] suggestionWords = null;
		SpellChecker spellChecker = null;
		try {
			Directory dir = FSDirectory.open(new File(spellCheckerIndexPath));
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

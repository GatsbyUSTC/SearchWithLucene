package com.socialtv.search;

import java.io.File;
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
	private static final int suggestionNum = 5;

	// This method is used to index spell checker dictionary
	public static void indexSpellCheker(String spellCheckerDictPath, String spellCheckerIndexPath) throws Exception{

			Directory dir = FSDirectory.open(new File(spellCheckerIndexPath));
			SpellChecker spellChecker = new SpellChecker(dir);
			IndexWriterConfig iwc = new IndexWriterConfig(Version.LATEST,
					new IKAnalyzer(true));
			spellChecker.indexDictionary(new PlainTextDictionary(new File(
					spellCheckerDictPath)), iwc, false);
			spellChecker.close();
			dir.close();
	}

	// This method is used to provide suggestions based on the origin word.
	public static String[] suggestSpellChecker(String originWord,
			String spellCheckerIndexPath) throws Exception {

		String[] suggestionWords = null;
		SpellChecker spellChecker = null;
		Directory dir = FSDirectory.open(new File(spellCheckerIndexPath));
		spellChecker = new SpellChecker(dir, new LuceneLevenshteinDistance());
		suggestionWords = spellChecker
				.suggestSimilar(originWord, suggestionNum);
		spellChecker.close();
		dir.close();
		return suggestionWords;
	}

}

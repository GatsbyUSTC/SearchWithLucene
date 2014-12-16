package com.socialtv.search;

import java.io.File;
import java.io.IOException;
import java.util.Comparator;
import java.util.Set;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.MultiFields;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.search.suggest.InputIterator;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.BytesRef;

public class TitleIterator implements InputIterator {

	private DirectoryReader directoryReader;
	private Directory directory;
	private TermsEnum titleIterator;
	private int weight;

	public TitleIterator(String indexPath) {
		try {
			directory = FSDirectory.open(new File(indexPath));
			directoryReader = DirectoryReader.open(directory);
			titleIterator = MultiFields
					.getTerms(directoryReader, "whole_title").iterator(null);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	@Override
	public Comparator<BytesRef> getComparator() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public BytesRef next() throws IOException {
		BytesRef temp = titleIterator.next();
		if (temp != null)
			weight = titleIterator.docFreq();
		else {
			directoryReader.close();
			directory.close();
		}
		return temp;
	}

	@Override
	public Set<BytesRef> contexts() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public boolean hasContexts() {
		// TODO Auto-generated method stub
		return false;
	}

	@Override
	public boolean hasPayloads() {
		// TODO Auto-generated method stub
		return false;
	}

	@Override
	public BytesRef payload() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public long weight() {
		return weight;
	}

}

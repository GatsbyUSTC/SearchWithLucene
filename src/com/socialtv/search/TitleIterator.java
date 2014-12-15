package com.socialtv.search;

import java.io.File;
import java.io.IOException;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexableField;
import org.apache.lucene.search.suggest.InputIterator;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.BytesRef;

public class TitleIterator implements InputIterator {

	private DirectoryReader directoryReader;
	private Directory directory;
	private int currentDocID;
	private int totalDocNum;
	private Set<String> titlefield;
	private Set<String> watchfield;
	
	
	public TitleIterator(String indexPath) {
		try {
			directory = FSDirectory.open(new File(indexPath));
			directoryReader = DirectoryReader.open(directory);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		currentDocID = 0;
		totalDocNum = directoryReader.numDocs();
		titlefield = new HashSet<String>();
		titlefield.add("content_title");
		watchfield = new HashSet<String>();
		watchfield.add("content_watch_count");
	}

	@Override
	public Comparator<BytesRef> getComparator() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public BytesRef next() throws IOException {
		// TODO Auto-generated method stub
		if(currentDocID < totalDocNum)
		{
			Document doc = directoryReader.document(currentDocID, titlefield);
			currentDocID ++;
			IndexableField title = doc.getField("content_title");
			return new BytesRef(title.stringValue().getBytes("UTF-8"));
		}
		directoryReader.close();
		directory.close();
		return null;
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
		if(currentDocID < totalDocNum)
		{
			Document doc;
			try {
				doc = directoryReader.document(currentDocID, watchfield);
				IndexableField watch_count = doc.getField("content_watch_count");
				return Long.parseLong(watch_count.stringValue());
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
		return 0;
	}

}

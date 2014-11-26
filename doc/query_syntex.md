Query Syntax:

1.Fields:

  - You can search any field by typing the field name followed by a colon ":" and then the term you are looking for. As an example, let's assume a Lucene index contains two fields, title and text and text is the default field. If you want to find the document entitled "The Right Way" which contains the text "don't go this way", you can enter:
	
	    title:"The Right Way" AND text:go

2.Wildcard Searches:

  - To perform a single character wildcard search use the "?" symbol. To perform a multiple character wildcard search use the "*" symbol. The single character wildcard search looks for terms that match that with the single character replaced. For example, to search for "text" or "test" you can use the search:
	
	    te?t

3.Regular Expression Searches:

  - Lucene supports regular expression searches matching a pattern between forward slashes "/". The syntax may change across releases, but the current supported syntax is documented in the RegExp class. For example to find documents containing "moat" or "boat":
	
        /[mb]oat/
	
4.Fuzzy Searches:

  - Lucene supports fuzzy searches based on Damerau-Levenshtein Distance. To do a fuzzy search use the tilde, "~", symbol at the end of a Single word Term. For example to search for a term similar in spelling to "roam" use the fuzzy search:(This search will find terms like foam and roams.)
	
	    roam~


5.Boosting a Term:

  - Boosting allows you to control the relevance of a document by boosting its term. For example, if you are searching for "jakarta apache" and you want the term "jakarta" to be more relevant boost it using the ^ symbol along with the boost factor next to the term. You would type:
	
	    jakarta^4 apache
	
  - This will make documents with the term jakarta appear more relevant. You can also boost Phrase Terms as in the example:
	
	    "jakarta apache"^4 "Apache Lucene"

6.Boolean Operators: OR, AND, +, NOT

  - The OR operator is the default conjunction operator.
  - The AND operator matches documents where both terms exist anywhere in the text of a single document.
  - The "+" or required operator requires that the term after the "+" symbol exist somewhere in a the field of a single document.
  - The NOT operator excludes documents that contain the term after NOT. 


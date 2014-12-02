##Interfaces: Now, there are three interfaces in total.

1.The first interace is used to index all files. When first time used or the system crashes, this interface can be used to create new index files.
  - url: 	IP:PORT/stvsearch/_indexalldocs
  - http verb :	POST
  - request parameter: 	none
  - request example preview:
```http
POST /stvsearch/_indexalldocs HTTP/1.1
Host: localhost:8080
Cache-Control: no-cache
```
  - response parameter: 
```js
{
"status":"fail" // sucess or fail
"info":"index_locked" //opt,only shows when status fail."index_locked" means there is another index writer writing the index.
}
```
  - response example preview:
```js
{"status":"success"}
```

2.The second interface is used to index one specific document. In our project, when a new video is uploaded, its information needs to be indexed. This interface is used to do it.
  - url: IP:PORT/stvsearch/_indexonedoc
  - http verb: POST
  - request parameter: 
```js
{id: "c98cf336a4fa11e39aff74867ade5224" //str}
```
  - request example preview:
```http
POST /stvsearch/_indexonedoc HTTP/1.1
Host: localhost:8080
Cache-Control: no-cache

{ id: "c98cf336a4fa11e39aff74867ade5224" }
```
  - response parameter: 
```js
{
"status":"fail" // success or fail
"info":"index_locked" // fail information
}
```
  - response example preview:
```js
{"status":"success"}
```

3.The third interface is used to search.
  - url:	IP:PORT/stvsearch/_search
  - http verb: 	POST
  - request parameter:
```js
{
keywords: "good",
filter:
 {
 owner_id:"3",	//string, opt
 category_id:"3"	//string, opt
 },
startIndex: 1, 	//int, opt, no less than zero
requestCount: 20,	//int, opt
inDays: 300, 	//int, opt, days after update
sortWay: "s", 	//string, opt, s:relevant sort; t:create_time sort; v:watch_count sort;
}
```
  - request example preview:
```http
POST /stvsearch/_search HTTP/1.1
Host: localhost:8080
Cache-Control: no-cache

{ keywords: "千与千寻", startIndex: 0, requestCount: 20, inDays: 500, sortWay: "s" }
```
  - response parameter:
```js
{
reponseCount: 30,				//int
data: [{id:"sfada"},...]		//json array
suggestWords: [“a”,”b”,”c”,”d”] 	//json array,optioanl,only shows when responseCount < 3
}
```
  - response example preview:
```js
{"data":[{"id":"c98cf336a4fa11e39aff74867ade5224","title":"千与千寻","description":"a good movie"},{"id":"366f0bacb62f11e38b1e74867ade5224","title":"千与千寻4","description":"enjoy this movie"},{"id":"c64eb82cb62e11e39b8974867ade5224","title":"千与千寻2","description":"enjoy this movie"},{"id":"f0cf62a4b62e11e38b1e74867ade5224","title":"千与千寻3","description":"enjoy this movie"}],
"responseCount":4}
```

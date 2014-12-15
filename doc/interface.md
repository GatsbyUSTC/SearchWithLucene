##Interfaces Specification

###Initial Index

The first interface is used to index all files. When first time used or the system crashes, this interface can be used to create new index files.
* **URL**
/stvsearch/_indexalldocs

* **Method**
`POST`

* **Parameter**
`None`

* **Response**
    * **Code:** 200
    * **Content:**
```js
{
    "status": "fail" // sucess or fail
    "info": "index_locked" //opt,only shows when status fail."index_locked" means there is another index writer writing the index.
}
```



* **Notes**


###Incremental Index

The second interface is used to index one specific document. In our project, when a new video is uploaded, its information needs to be indexed. This interface is used to do it.

* **URL**
/stvsearch/_indexonedoc

* **Method**
`POST`

* **Parameter**
```js
{id: "c98cf336a4fa11e39aff74867ade5224" //str}
```

* **Response**
    * **Code:** 200
    * **Content:**
```js
{
    "status": "fail" // success or fail
    "info": "index_locked" // fail information
}
```

* **Notes**

###Search
The third interface is used to search.

* **URL**
/stvsearch/_search

* **Method**
`POST`

* **Parameter**
```js
{
    keywords: "good",
    filter: {
        owner_id: "3", //string, opt
        category_id: "3" //string, opt
    },
    startIndex: 1, //int, opt, no less than zero
    requestCount: 20, //int, opt
    inDays: 300, //int, opt, days after update
    sortWay: "s", //string, opt, s:relevant sort; t:update_time sort; v:watch_count sort;
}
```

* **Response**
```js
{
    reponseCount: 30, //int
    data: [{
            id: "sfada"
        }, ...] //json array
}
```
* **Note**

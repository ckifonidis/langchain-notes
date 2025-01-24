# **API Technical Design** **Developers Portal**  Domain: Article 

## Document Version: 4.0

Section Headers \*\*  
Subsection Headers\*  
End of Section \- \- \-

# \*\*Overview\*\*

The purpose of this documentation is to describe in detail the functionality of the Core Developers Portal backend  API  
\- \- \-

# \*\*Web API Ground Rules Section\*\*

## \*Requests\*

Each API request is wrapped in a Request object and has its payload \- mentioned as T. T is specified in each endpoint’s technical description.

**Example Request**

```javascript
{
    "header": {
        "ID": "{{$guid}}",
        "application": "03FC0B90-DFAD-11EE-8D86-0800200C9A66",
        "bank": "NBG",
        "UserId": "{{$user_guid}}"
    },
    "payload": {}
}
```

* request.Header.ID is a new GUID for each request. This way the request can be tracked down in the future.  
* request.Header.application is a GUID for each application that invokes our web API.  
* request.Header.bank always has the value “BANK”  
* request.Header.UserId is the GUID Id for each user.

## \*Responses\*

Each API response is wrapped in a Response object. 

* All the exceptions thrown during the execution of an endpoint are caught and the response.exception field is assigned the related exception info and response.payload \= null  
* In case of success (no exception thrown), the response.payload is described in each endpoint’s technical description. The response.exception \= null

**Example Response**

```javascript
{
    "payload": {},
    "exception": {
        "id": "guid",
        "code": "string",
        "description": "string"
    }
}
```

## \*Endpoint Execution Logic\*

All endpoints are asynchronous.

No matter what happens during the execution of an endpoint’s logic, the HTTP response code is always 200-OK. To achieve this, the execution of each endpoint is handled by a mechanism called SafeExecutor.

SafeExecutor is a static class.

SafeExecutor wraps the provided action in a try-catch block. If any exception occurs, the response.exception field is assigned the exception information.

Exceptions are categorized as Business or Technical. They have their own class extending the system exception class, with additional fields: 

* Code: string  
* Description: string

When the SafeExecutor catches a Business/Technical exception, the mapping is straightforward. When it catches a simple exception, it is handled as a technical exception with a fixed code of “1001” and description “A technical exception has occurred, please contact your system administrator”.

Each endpoint’s logic is exposed as a method in the service layer and is also described in an interface. The controllers inject the interface of the service and safely via SafeExecutor invoke the corresponding method. The service layer is not aware of the Request/Response wrapper objects. There is a one-to-one mapping for endpoints and service methods. For example, for an endpoint named “CreateUser”, there should be a method “CreateUser” defined in the interface and implemented in the service layer. Types, Interfaces and Services are defined in separate files.

## \*Database Layer Rules\*

Dapper ORM is used to access, add, update or delete database data. We only use parameterized queries to avoid SQL-Injection scenarios. Database access has its own layer, usually mentioned as “Repositories”. Method signatures must describe what the method is about. For example, 

| Task\<Article\> SelectArticleAsync(Guid articleId) |
| :------------------------------------------------- |

The service layer injects the database access service and invokes its methods by providing the required data, without knowing any details about the queries that actually run.

Also, in terms of database structure, we never use foreign keys.

\- \- \-

# \*\*Common Types Section\*\*

| Request    |                           |
| :--------- | :------------------------ |
| Field Name | Type                      |
| Header     | [RequestHeader](#heading) |
| Payload    | T                         |

| RequestHeader |                                                                                                                                                     |
| :------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| Field Name    | Type                                                                                                                                                |
| Id            | guid (Always new guid)                                                                                                                              |
| Application   | guid (Always constant), Request Header Application Guid is constant and read-only and the default value is **03FC0B90-DFAD-11EE-8D86-0800200C9A66** |
| Bank          | string                                                                                                                                              |
| UserId        | guid                                                                                                                                                |

| Response   |                                 |
| :--------- | :------------------------------ |
| Field Name | Type                            |
| Payload    | T                               |
| Exception  | [ResponseException](#heading-1) |

| ResponseException |        |
| :---------------- | :----- |
| Field Name        | Type   |
| Id                | guid   |
| Code              | string |
| Description       | string |
| Category          | string |

# 

\- \- \-

# \*\*Database Layer Section\*\*

| Database         | Description                                                                                                   |
| :--------------- | :------------------------------------------------------------------------------------------------------------ |
| DevelopersPortal | Provides a detailed structure of Developers Portal tables including field names, data types, and constraints. |

## \*Environments\*

| Environment | Database Server | Database  |
| :---------- | :-------------- | :-------- |
| Development | V00008065       | DevPortal |
| QA          |                 |           |
| Production  |                 |           |

# 

## \*DB Tables\*

### \*Articles\*

| Name          | Data Type        | Nullable | Unique | Description                                                         |
| :------------ | :--------------- | :------- | :----- | :------------------------------------------------------------------ |
| Id            | uniqueidentifier | false    | true   | Unique entry’s identifier to the table                              |
| Title         | nvarchar(200)    | false    | false  | Article title                                                       |
| AuthorId      | uniqueidentifier | false    | false  | Author Id                                                           |
| Summary       | nvarchar(500)    | true     | false  | Summary / auto generated when is null                               |
| Body          | nvarchar(max)    | true     | false  | Article body in HTML \- Sanitize HTML                               |
| GoogleDriveId | nvarchar(50)     | true     | false  | Google Drive Id                                                     |
| HideScrollSpy | bit              | true     | false  | Hide the left sidebar                                               |
| ImageId       | uniqueidentifier | true     | false  | Image Id of the Article                                             |
| PdfId         | uniqueidentifier | true     | false  | Attachment file Id of the Pdf                                       |
| Langcode      | nvarchar(4)      | false    | false  | Shows the Language of the article                                   |
| Status        | bit              | true     | false  | Show if the article is visible                                      |
| Sticky        | bit              | true     | false  | Keeps an article on top                                             |
| Promote       | bit              | true     | false  | Shows article in the frontpage                                      |
| UrlAlias      | nvarchar(200)    | true     | false  | UrlAlias path                                                       |
| Published     | bit              | true     | false  | Show if the entity is published                                     |
| Version       | int              | true     | false  | Indicates the current version number (increase by 1 on each update) |
| Created       | datetime2(7)     | true     | false  | Show when the entity is created                                     |
| Changed       | datetime2(7)     | true     | false  | Show when the entity is updated                                     |
| CreatorId     | uniqueidentifier | true     | false  | Creator Id                                                          |
| ChangedUserId | uniqueidentifier | true     | false  | Last user that change the entity                                    |

### 

### 

### \*ArticleBlogCategories\*

| Name           | Data Type        | Nullable | Unique | Description                            |
| :------------- | :--------------- | :------- | :----- | :------------------------------------- |
| Id             | uniqueidentifier | false    | true   | Unique entry’s identifier to the table |
| ArticleId      | uniqueidentifier | false    | false  | Article id                             |
| BlogCategoryId | uniqueidentifier | false    | false  | BlogCategory id                        |

### \*ArticleBlogTags\*

| Name      | Data Type        | Nullable | Unique | Description                            |
| :-------- | :--------------- | :------- | :----- | :------------------------------------- |
| Id        | uniqueidentifier | false    | true   | Unique entry’s identifier to the table |
| ArticleId | uniqueidentifier | false    | false  | Article id                             |
| BlogTagId | uniqueidentifier | false    | false  | BlogTags id                            |

\- \- \-


# \*\*Mapping Definitions Section\*\*

### CreateArticleDto to Article

Source: CreateArticleDto  
Target: Article  
Map: CreateArticleDto to Article

| Source        | Target        | Mapping Details                               |
| :------------ | :------------ | :-------------------------------------------- |
| \-            | Id            | Guid.NewGuid()                                |
| Title         | Title         | Mandatory                                     |
| AuthorId      | AuthorId      | Mandatory                                     |
| Summary       | Summary       | if provided                                   |
| Body          | Body          | if provided                                   |
| GoogleDriveId | GoogleDriveId | if provided                                   |
| HideScrollSpy | HideScrollSpy | if provided                                   |
| ImageId       | ImageId       | Conditional mapping (Create or mapping null). |
| PdfId         | PdfId         | Conditional mapping (Create or mapping null). |
| Langcode      | Langcode      | Mandatory                                     |
| Status        | Status        | if provided                                   |
| Sticky        | Sticky        | if provided                                   |
| Promote       | Promote       | if provided                                   |
| UrlAlias      | UrlAlias      | if provided                                   |
| Published     | Published     | if provided                                   |
|               | Version       | 1 (Initial version)                           |
|               | Created       | DateTime.Now                                  |
|               | CreatorId     | userId                                        |

### 

### Article to ArticleDto

Source: Article  
Target: ArticleDto  
Map: Article to ArticleDto

| Source        | Target        | Mapping Details                                                      |
| :------------ | :------------ | :------------------------------------------------------------------- |
| Id            | Id            | Direct mapping                                                       |
| Title         | Title         | Direct mapping                                                       |
| AuthorId      | Author        | Fetch the authorDto object if available. Otherwise it remains null.  |
| Summary       | Summary       | Direct mapping                                                       |
| Body          | Body          | Direct mapping                                                       |
| GoogleDriveId | GoogleDriveId | Direct mapping                                                       |
| HideScrollSpy | HideScrollSpy | Direct mapping                                                       |
| ImageId       | Image         | Fetch the image object if available. Otherwise it remains null.      |
| PdfId         | Pdf           | Fetch the attachment object if available. Otherwise it remains null. |
| Langcode      | Langcode      | Direct mapping                                                       |
| Status        | Status        | Direct mapping                                                       |
| Sticky        | Sticky        | Direct mapping                                                       |
| Promote       | Promote       | Direct mapping                                                       |
| UrlAlias      | UrlAlias      | Direct mapping                                                       |
| Published     | Published     | Direct mapping                                                       |
| Version       | Version       | Direct mapping                                                       |
| Created       | Created       | Direct mapping                                                       |
| Changed       | Changed       | Direct mapping                                                       |
| CreatorId     | CreatorId     | Direct mapping                                                       |
| ChangedUserId | ChangedUserId | Direct mapping                                                       |

### 

### CreateArticleDto to ArticleDto

Source: CreateArticleDto  
Target: ArticleDto  
Map: CreateArticleDto to ArticleDto

| Source         | Target         | Mapping Details                              |
| :------------- | :------------- | :------------------------------------------- |
| BlogCategories | BlogCategories | Fetch the list of BlogCategories.            |
| BloTags        | BlogTags       | Conditional mapping (Fetch, Create or null). |

### UpdateArticleDto to Article

Source: UpdateArticleDto  
Target: Article  
Map: UpdateArticleDto to Article

| Source        | Target        | Mapping Details                                    |
| :------------ | :------------ | :------------------------------------------------- |
| Title         | Title         | If not null or empty                               |
| AuthorId      | AuthorId      | If not null or empty                               |
| Summary       | Summary       | if provided                                        |
| Body          | Body          | if provided                                        |
| GoogleDriveId | GoogleDriveId | if provided                                        |
| HideScrollSpy | HideScrollSpy | if provided                                        |
| ImageId       | ImageId       | Conditional mapping (Create, Update or No Change). |
| PdfId         | PdfId         | Conditional mapping (Create, Update or No Change). |
| Langcode      | Langcode      | If not null or empty                               |
| Status        | Status        | if provided                                        |
| Sticky        | Sticky        | if provided                                        |
| Promote       | Promote       | if provided                                        |
| UrlAlias      | UrlAlias      | if provided                                        |
| Published     | Published     | if provided                                        |
|               | Version       | Existing Version \+ 1                              |
|               | Changed       | DateTime.Now                                       |
|               | ChangedUserId | userId                                             |

### UpdateArticleDto to ArticleDto

Source: UpdateArticleDto  
Target: ArticleDto  
Map: UpdateArticleDto to ArticleDto

| Source         | Target         | Mapping Details                                   |
| :------------- | :------------- | :------------------------------------------------ |
| BlogCategories | BlogCategories | Fetch the list of BlogCategories.                 |
| BloTags        | BlogTags       | Conditional mapping (Fetch, Create or No Change). |

### ListArticleRequestDto to ReturnListArticleDto

Source: ListArticleRequestDto  
Target: ReturnListArticleDto  
Map: ListArticleRequestDto to ReturnListArticleDto

| Source     | Target              | Mapping Details            |
| :--------- | :------------------ | :------------------------- |
| PageLimit  | Metadata.PageLimit  | Provided pageLimit value.  |
| PageOffset | Metadata.PageOffset | Provided pageOffset value. |

### PagedResult to ReturnListArticleDto

Source: pagedResult  
Target: ReturnListArticleDto  
Map: pagedResult to ReturnListArticleDto

| Source       | Target             | Mapping Details                                                                                                                                              |
| :----------- | :----------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Records      | List\<ArticleDto\> | ToList()                                                                                                                                                     |
| TotalRecords | Metadata.Total     | (pagedResult.TotalRecords % request.PageLimit \== 0\)  ? pagedResult.TotalRecords / request.PageLimit  : (pagedResult.TotalRecords / request.PageLimit) \+ 1 |

### 

\- \- \-

# \*\*Types Layer Section\*\*

### 

### \*Article\*

Table Annotation: This entity maps to the database table Articles.

| Name          | Data Type | Description                                                         |
| :------------ | :-------- | :------------------------------------------------------------------ |
| Id            | guid      | Unique entry’s identifier                                           |
| Title         | string    | Article title                                                       |
| AuthorId      | guid      | Author entity                                                       |
| Summary       | string    | Summary                                                             |
| Body          | string    | Article body in HTML \- Sanitize HTML                               |
| GoogleDriveId | string    | Google Drive Id                                                     |
| HideScrollSpy | bool      | Hide the left sidebar                                               |
| ImageId       | guid      | Image Id of the Article. It can be null.                            |
| PdfId         | guid      | Attachment file Id of the Pdf. It can be null.                      |
| Langcode      | string    | Language of the article                                             |
| Status        | bool      | Article status                                                      |
| Sticky        | bool      | Keeps an article on top                                             |
| Promote       | bool      | Article in the frontpage                                            |
| UrlAlias      | string    | UrlAlias path                                                       |
| Published     | bool      | Show if the entity is published                                     |
| Version       | int       | Indicates the current version number (increase by 1 on each update) |
| Created       | datetime  | Show when the entity is created                                     |
| Changed       | datetime  | Show when the entity is updated                                     |
| CreatorId     | guid      | Creator Id                                                          |
| ChangedUserId | guid      | Last user that change the entity                                    |

###  \*ArticleDto\* {#*articledto*}

| Name           | Data Type            | Description                                                         |
| :------------- | :------------------- | :------------------------------------------------------------------ |
| Id             | guid                 | Unique entry’s identifier                                           |
| Title          | string               | Article title                                                       |
| Author         | AuthorDto            | Author entity                                                       |
| Summary        | string               | Summary                                                             |
| Body           | string               | Article body in HTML \- Sanitize HTML                               |
| GoogleDriveId  | string               | Google Drive Id                                                     |
| HideScrollSpy  | bool                 | Hide the left sidebar                                               |
| Image          | Image                | Article image. It can be null.                                      |
| Pdf            | Attachment           | Attachment file entity of the Pdf. It can be null.                  |
| Langcode       | string               | Language of the article                                             |
| Status         | bool                 | Article status                                                      |
| Sticky         | bool                 | Keeps an article on top                                             |
| Promote        | bool                 | Article in the frontpage                                            |
| UrlAlias       | string               | UrlAlias path                                                       |
| Published      | bool                 | Show if the entity is published                                     |
| BlogCategories | List\<BlogCategory\> | List of BlogCategories                                              |
| BlogTags       | List\<BlogTag\>      | List of BlogTags. It can be null.                                   |
| Version        | int                  | Indicates the current version number (increase by 1 on each update) |
| Created        | datetime             | Show when the entity is created                                     |
| Changed        | datetime             | Show when the entity is updated                                     |
| CreatorId      | guid                 | Creator Id                                                          |
| ChangedUserId  | guid                 | Last user that change the entity                                    |

###  \*ArticleBlogCategory\* {#*articleblogcategory*}

Table Annotation: This entity maps to the database table ArticleBlogCategories.

| Name           | Data Type | Description                            |
| :------------- | :-------- | :------------------------------------- |
| Id             | guid      | Unique entry’s identifier to the table |
| ArticleId      | guid      | Article id                             |
| BlogCategoryId | guid      | BlogCategory id                        |

### \*ArticleBlogTag\*

Table Annotation: This entity maps to the database table ArticleBlogTags.

| Name      | Data Type | Description                            |
| :-------- | :-------- | :------------------------------------- |
| Id        | guid      | Unique entry’s identifier to the table |
| ArticleId | guid      | Article id                             |
| BlogTagId | guid      | BlogTags id                            |

###  \*CreateArticleDto\*

| Name           | Data Type           | Description                                        |
| :------------- | :------------------ | :------------------------------------------------- |
| Title          | string              | Article title                                      |
| AuthorId       | guid                | Author Id                                          |
| Summary        | string              | Summary                                            |
| Body           | string              | Article body in HTML \- Sanitize HTML              |
| GoogleDriveId  | string              | Google Drive Id                                    |
| HideScrollSpy  | bool                | Hide the left sidebar                              |
| Image          | CreateImageDto      | Article image. It can be null.                     |
| Pdf            | CreateAttachmentDto | Attachment file entity of the Pdf. It can be null. |
| Langcode       | string              | Language of the article                            |
| Status         | bool                | Article status                                     |
| Sticky         | bool                | Keeps an article on top                            |
| Promote        | bool                | Article in the frontpage                           |
| UrlAlias       | string              | UrlAlias path                                      |
| Published      | bool                | Show if the entity is published                    |
| BlogCategories | List\<Guid\>        | List of BlogCategory Ids                           |
| BlogTags       | List\<string\>      | List of BlogTag names. It can be null.             |

### \*ArticleRequestDto\* {#*articlerequestdto*}

| Name  | Data Type | Description                    |
| :---- | :-------- | :----------------------------- |
| Id    | guid      | Article Id. It can be null.    |
| Title | string    | Article title. It can be null. |

### 

### 

### 

### \*UpdateArticleDto\* {#*updatearticledto*}

| Name           | Data Type           | Description                           |
| :------------- | :------------------ | :------------------------------------ |
| Id             | guid                | Unique entry’s identifier             |
| Title          | string              | Article title                         |
| AuthorId       | guid                | Author Id                             |
| Summary        | string              | Summary                               |
| Body           | string              | Article body in HTML \- Sanitize HTML |
| GoogleDriveId  | string              | Google Drive Id                       |
| HideScrollSpy  | bool                | Hide the left sidebar                 |
| Image          | UpdateImageDto      | Article image                         |
| Pdf            | UpdateAttachmentDto | Attachment file entity of the Pdf     |
| Langcode       | string              | Language of the article               |
| Status         | bool                | Article status                        |
| Sticky         | bool                | Keeps an article on top               |
| Promote        | bool                | Article in the frontpage              |
| UrlAlias       | string              | UrlAlias path                         |
| Published      | bool                | Show if the entity is published       |
| BlogCategories | List\<Guid\>        | List of BlogCategory Ids              |
| BlogTags       | List\<string\>      | List of BlogTag names                 |

### \*DeleteArticleDto\* {#*deletearticledto*}

| Name           | Data Type      | Description                   |
| :------------- | :------------- | :---------------------------- |
| Id             | guid           | Unique entry’s identifier.    |
| FieldsToDelete | List\<string\> | List of fields to be deleted. |

### \*ListArticleRequestDto\* {#*listarticlerequestdto*}

| Name           | Data Type | Description          |
| :------------- | :-------- | :------------------- |
| PageLimit      | int       | Page limit           |
| PageOffset     | int       | Page offset          |
| SortField      | string    | Sort field           |
| SortOrder      | string    | Sort order           |
| SearchTerm     | string    | Search               |
| Title          | string    | Title of the article |
| AuthorId       | guid      | Author Id            |
| BlogCategoryId | guid      | BlogCategory Id      |
| BlogTagId      | guid      | BlogTag Id           |

### \*MetadataDto\*

| Name       | Data Type | Description            |
| :--------- | :-------- | :--------------------- |
| PageLimit  | int       | Page limit             |
| PageOffset | int       | Page offset            |
| Total      | int       | Total number of pages. |

### \*ReturnListArticleDto\* {#*returnlistarticledto*}

| Name     | Data Type          | Description                 |
| :------- | :----------------- | :-------------------------- |
| Data     | List\<ArticleDto\> | List of ArticleDto objects. |
| Metadata | MetadataDto        | Pagination parameters.      |

### 

\- \- \-

# \*\*Implementation Layer Section\*\*

## \*ArticleService\*

### 

### \*Create\*

Creates an article with the specified details

| Arguments        | [CreateArticleDto](#*articleblogcategory*) request, Guid userId |
| :--------------- | :-------------------------------------------------------------- |
| **Return value** | string                                                          |

**Implementation**

1. **Validate** the request and its parameters:  
   1. “AuthorId” must not be null.  
   2. “Title”, “Langcode” and “BlogCategories” must not be null or empty.  
   3. If the request or the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. Initialize an empty object of type Article, named article.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Create operation.  
4. **Fetch and Validate** **Author** using IAuthorService.Get from the Core Service Dependencies Section.  
   1. If not found, throw the [DP-404](#dp-404) exception.  
5. **Fetch and Validate BlogCategories** using IBlogCategoryService.Get from the Core Service Dependencies Section  
   1. If not found, throw the [DP-404](#dp-404) exception  
6. **Fetch or Create BlogTags:**  
   1. If request.BlogTags is not null,   
      1. Retrieve BlogTags with no filter from the database.  
      2. If retrieval fails, throw the [DP-500](#dp-500) exception.  
      3. Create an empty list of Guid?, named blogTags.  
      4. Identify existing BlogTags in request.BlogTags and add their Ids to a list (blogTags).  
      5. Identify new BlogTags and add their names to a list (newBlogTags).  
   1. For each name in newBlogTags:  
      1. Use IBlogTagService.Create from the Core Service Dependencies Section with { Name \= newBlogTag, Langcode \= request.Langcode } to create the BlogTag.  
         2. Add the returned Id to the blogTags list.  
7. **Create Attachment File:**  
   1. If request.Pdf is not null,  
      1. Map request.Pdf to a CreateAttachmentDto object and call the IAttachment.Create method from the Core Service Dependencies Section.  
      2. If the return value of the Create is string, then save the return value parsed to Guid to an **pdfId** variable.  
8. **Create Image File:**  
   1. If request.Image is not null,  
      1. Map request.Image to a CreateImageDto object and call the IImageService.Create method from the Core Service Dependencies Section.  
      2. If the return value of the Create is string, then save the return value parsed to Guid to an **imageId** variable.  
9. **Map** the Article based on the CreateArticleDto to Article from the Mapping Definition Section.  
10. **Create new list** of ArticleBlogCategories objects (**articleBlogCategories**) as follows:  
    1. For each **blogCategoryId** in request.BlogCategories  
       create new **articleBlogCategory** object as follows and add it to articleBlogCategories list:  
       1. Id: new Guid  
       2. ArticleId: ArticleId  
       3. BlogCategoryId: blogCategoryId  
11. **Create new list** of ArticleBlogTags objects (**articleBlogTags**) as follows:  
    1. For each blogTagId in the **blogTags** list create a new ArticleBlogTag object and add it to the list.  
       1. Id: new Guid  
       2. ArticleId: ArticleId  
       3. BlogTagId: blogTagId  
12. **Perform Database Operations**:  
    1. Insert the Article along with its related entities (ArticleBlogCategories, ArticleBlogTags).  
    2. Retrieve Articles by Id.  
    3. Assign the first of the retrieved articles to the article.  
    4. Handle errors during insertions or retrievals by throwing the [DP-500](#dp-500) exception.  
    5. If not found, throw the [DP-404](#dp-404) exception.  
    6. Return the Article’s Id.

### \*Get\*

Get the specified article

| Arguments        | [ArticleRequestDto](#*articlerequestdto*) request, Guid userId |
| :--------------- | :------------------------------------------------------------- |
| **Return value** | [ArticleDto](#*articledto*)                                    |

**Implementation**

1. **Validate** the request and its parameters:  
   1. “Id” must not be null.  
   2. “Title” must not be null or empty.  
   3. If the request or the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. **Fetch Article:**  
   1. Retrieve Articles first by Id and then by Title, depending which one is provided.  
   2. Assign the first of the retrieved articles to the article.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Read operation.  
4. **Fetch and Validate Author**:  
   1. Try to fetch the Author using IAuthorService.Get from the Core Service Dependencies Section.  
   2. Handle errors during fetching by logging the error and continue.  
   3. Otherwise, the author remains null.  
5. **Fetch Attachment**:  
   1. If article.PdfId is not null,  
      1. Try to fetch the Attachment using IAttachmentService.Get from the Core Service Dependencies Section.  
      2. Handle errors during fetching by logging the error and continue.  
   2. Otherwise, the attachment remains null.  
6. **Fetch Image**:  
   1. If article.ImageId is not null,  
      1. Try to fetch the Image using IImageService.Get from the Core Service Dependencies Section.  
      2. Handle errors during fetching by logging the error and continue.Handle errors during fetching by logging the error and continue.  
   2. Otherwise, the image remains null.  
7. **Fetch Associated BlogCategories**:  
   1. Create an empty list of type BlogCategories, named temporaryBlogCategories.  
   2. Create an empty list of type Guid?, named blogCategoriesIds.  
   3. **Retrieve all** ArticleBlogCategories by ArticleId \= request.Id.  
   4. For each item in articleBlogCategories:  
      1. Add the Id to the blogCategoriesIds list.  
   5. If blogCategoriesIds is not empty:  
      1. For each BlogCategoryId:  
         1. Try to fetch the BlogCategory using IBlogCategory.Get from the Core Service Dependencies Section.  
         2. Add it to a new list **temporaryBlogCategories**.  
         3. Handle exceptions during fetching operation, log error and continue without throwing an error.   
8. **Fetch Associated BlogTags**:  
   1. Create an empty list of type BlogTags, named temporaryBlogTags.  
      1. Create an empty list of type Guid?, named blogTagsIds.  
      2. **Retrieve all** ArticleBlogTags by ArticleId \= request.Id.  
      3. For each item in articleBlogTags:  
         1. Add the Id to the blogTagsIds list.  
      4. If blogTagsIds is not empty:  
         1. For each blogTagsId:  
            1. Try to fetch the BlogTag using IBlogTag.Get from the Core Service Dependencies Section.  
            2. Add it to a new list **temporaryBlogTags**.  
            3. Handle exceptions during fetching operation, log error and continue without throwing an error.  
9. **Map** the ArticleDto based on the Article to ArticleDto and CreateArticleDto to ArticleDto from the Mapping Definition Section.  
   1. Include the related BlogCategories.  
   2. Include the related BlogTags.  
10. **Return** the articleDto.

### 

### 

### \*Update\*

Updates an article with the specified details

| Arguments        | [UpdateArticleDto](#*updatearticledto*) request, Guid userId |
| :--------------- | :----------------------------------------------------------- |
| **Return value** | string                                                       |

**Implementation**:

1. **Validate** the request and its parameters:  
   1. “Id” must not be null.  
   2. "Title" and "Langcode" must not be empty strings (""), but they can be null.  
   3. “BlogCategories” can be null but not empty.  
   4. If the request or the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. **Fetch Article:**  
   1. Retrieve Articles by Id.  
   2. Assign the first of the retrieved articles to the article.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Update operation.  
4. **Fetch and Validate Author:**  
   1. If request.AuthorId is not null,  
      1. **Fetch and Validate** **Author** using IAuthorService.Get from the Core Service Dependencies Section.  
         1. If not found, throw the [DP-404](#dp-404) exception.  
   2. Otherwise, keep the same Author  
5. **Fetch and Validate BlogCategories:**  
   1. If request.BlogCategories is not null:  
      1. For each one,  fetch the BlogCategory using IBlogCategoryService.Get from the Core Service Dependencies Section  
      2. If not found, throw the [DP-404](#dp-404) exception  
6. **Fetch or Create BlogTags:**  
   1. If request.BlogTags is not null,   
      1. Retrieve BlogTags with no filter using the Database Service.  
      2. If retrieval fails, throw the [DP-500](#dp-500) exception.  
      3. Create an empty list of Guid?, named blogTags.  
      4. Identify existing BlogTags in request.BlogTags and add their Ids to a list (blogTags).  
      5. Identify new BlogTags and add their names to a list (newBlogTags).  
   2. For each name in newBlogTags:  
      1. Use IBlogTagService.Create from the Core Service Dependencies Section with { Name \= newBlogTag, Langcode \= request.Langcode } to create the BlogTag.  
         2. Add the returned Id to the blogTags list.  
7. **Update Image:**  
   1. If request.Image is not null,  
      1. If request.Image.Id is null:  
         1. Map request.Image to a CreateImageDto object.  
         2. Call the IImageService.Create method from the Core Service Dependencies Section.  
         3. If the return value of the Create is string, then save the return value parsed to Guid to an **imageId** variable.  
      2. If request.Image.Id is not null:  
         1. Map request.Image to an UpdateImageDto object.  
         2.  Call the IImageService.Update method from the Core Service Dependencies Section.  
         3. If the return value of the Update is string, then save the return value parsed to Guid to an **imageId** variable.  
   2. Otherwise, keep the same Image.  
8. **Update Attachment:**  
   1. If request.Pdf is not null,  
      1. If request.Pdf.Id is null:  
         1. Map request.Pdf to a CreateAttachmentDto object.  
         2. Call the IAttachmentService.Create method from the Core Service Dependencies Section.  
         3. If the return value of the Create is string, then save the return value parsed to Guid to an **pdfId** variable.  
      2. If request.Pdf.Id is not null:  
         1. Map request.Pdf to an UpdateAttachmentDto object.  
         2. Call the IAttachmentService.Update method from the Core Service Dependencies Section.  
         3. If the return value of the Update is string, then save the return value parsed to Guid to an **pdfId** variable.  
   2. Otherwise, keep the same Pdf.  
9. **Map** the Article based on the UpdateArticleDto to Article from the Mapping Definition Section.  
10. Prepare ArticleBlogCategories for Database Operation:  
    1. Create an empty list of ArticleBlogCategory, named articleBlogCategories.  
    2. Retrieve ArticleBlogCategories by Article Id using the Database Service and map it to the articleBlogCategories list.  
    3. If request.BlogCategories is not null:  
       1. Clear the list  
       2. For each **blogCategoryId** in request.BlogCategories  
          create new **articleBlogCategory** object as follows and add it to articleBlogCategories list:  
          1. Id: new Guid  
          2. ArticleId: ArticleId  
          3. BlogCategoryId: blogCategoryId  
11. **Create new list** of ArticleBlogTags objects (**articleBlogTags**) as follows:  
    1. For each blogTagId in the **blogTags** list create a new ArticleBlogTag object and add it to the list.  
       1. Id: new Guid  
       2. ArticleId: ArticleId  
       3. BlogTagId: blogTagId  
12. **Perform Database Operations**:  
    1. Update the Article along with its related entities (ArticleBlogCategories, ArticleBlogTags) by Id.  
    2. Retrieve Articles by Id.  
    3. Assign the first of the retrieved articles to the article.  
    4. Handle errors during insertions or retrievals by throwing the [DP-500](#dp-500) exception.  
    5. If not found, throw the [DP-404](#dp-404) exception.  
    6. Return the Article’s Id.

       

### \*Delete\*

Deletes an article with the specified details

| Arguments        | [DeleteArticleDto](#*deletearticledto*) request, Guid userId |
| :--------------- | :----------------------------------------------------------- |
| **Return value** | bool                                                         |

**Implementation**:

1. **Validate** the request and its parameters:  
   1. “Id” must not be null.  
   2. If the request or the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. **Fetch Article:**  
   1. Retrieve Articles by Id.  
   2. Assign the first of the retrieved articles to the article.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Delete operation.  
4. **Perform Database Operations:**  
   1. If request.FieldsToDelete is null:  
      1. Perform a complete deletion:  
         1. If article.ImageId is not null, delete the image record by ImageId.  
         2. If article.PdfId is not null, delete the attachment record by PdfId.  
         3. Delete the Article along with its related entities (ArticleBlogCategories, ArticleBlogTags).  
      2. Return true.  
   2. Else If request.FieldsToDelete is not null:  
      1. Perform a partial deletion:  
         1. For each field in request.FieldsToDelete:  
            1. If the field is "ImageId" and article.ImageId is not null:  
               1. Delete the Image record by ImageId.  
               2. Nullify the "ImageId" column for the article.  
            2. If the field is "PdfId" and article.PdfId is not null:  
               1. Delete the Attachment record by PdfId.  
               2. Nullify the "PdfId" column for the article.  
            3. For other fields (excluding "Title", “AuthorId”, "LangCode", and "CreatorId"):  
               1. Nullify the specified field for the article.  
      2. Return true.  
   3. Handle errors during deletions by throwing the [DP-500](#dp-500) exception.  
5. Return false

### \*GetList\*

Get an article list with the specified details

| Arguments        | [ListArticleRequestDto](#*listarticlerequestdto*) request, Guid userId |
| :--------------- | :--------------------------------------------------------------------- |
| **Return value** | [ReturnListArticleDto](#*returnlistarticledto*)                        |

**Implementation**:

1. **Validate** the request and its parameters:  
   1. "PageLimit” must not be null or \> 0\.  
   2. “PageOffset” must not be null or ≥ 0\.  
   3. If the request or the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. Initialize an empty object of type Article, named article.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Read operation.  
4. **Retrieve Paged Articles:**  
   1. Fetch paged Articles using the following parameters:  
      1. Pagination: Use request.PageLimit and request.PageOffset for PageSize and Offset.  
      2. Sorting: Default to SortField \= "Created" and SortOrder \= "desc" if not provided.  
      3. Filter:   
         1. If request.Title is not null, user “Title”  
         2. Else If request.AuthorId is not null, user “AuthorId”  
         3. Else if request.BlogCategory is not null, user “BlogCategory”  
         4. Else if request.Tag is not null, user “BlogTag”  
         5. Else, leave filter null  
      4. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
5. Create a List of ArticleDtos type  
6. **For each item in articles:**  
1. Create an empty object of type ArticleDto, named articleDto.  
2. **Fetch and Validate Author**:  
   1. Try to fetch the Author using IAuthorService.Get from the Core Service Dependencies Section.  
   2. Handle errors during fetching by logging the error and continue.  
   3. Otherwise, the author remains null.  
3. **Fetch Attachment**:  
   1. If article.PdfId is not null,  
      1. Try to fetch the Attachment using IAttachmentService.Get from the Core Service Dependencies Section.  
      2. Handle errors during fetching by logging the error and continue.  
   2. Otherwise, the attachment remains null.  
4. **Fetch Image**:  
   1. If article.ImageId is not null,  
      1. Try to fetch the Image using IImageService.Get from the Core Service Dependencies Section.  
      2. Handle errors during fetching by logging the error and continue.Handle errors during fetching by logging the error and continue.  
   2. Otherwise, the image remains null.  
5. **Fetch Associated BlogCategories**:  
   1. Create an empty list of type BlogCategories, named temporaryBlogCategories.  
   2. Create an empty list of type Guid?, named blogCategoriesIds.  
   3. **Retrieve all** ArticleBlogCategories by ArticleId \= request.Id.  
   4. For each item in articleBlogCategories:  
      1. Add the Id to the blogCategoriesIds list.  
   5. If blogCategoriesIds is not empty:  
      1. For each BlogCategoryId:  
         1. Try to fetch the BlogCategory using IBlogCategory.Get from the Core Service Dependencies Section.  
         2. Add it to a new list **temporaryBlogCategories**.  
         3. Handle exceptions during fetching operation, log error and continue without throwing an error.   
6. **Fetch Associated BlogTags**:  
   1. Create an empty list of type BlogTags, named temporaryBlogTags.  
   2. Create an empty list of type Guid?, named blogTagsIds.  
   3. **Retrieve all** ArticleBlogTags by ArticleId \= request.Id.  
   4. For each item in articleBlogTags:  
      1. Add the Id to the blogTagsIds list.  
   5. If blogTagsIds is not empty:  
      1. For each blogTagsId:  
         1. Try to fetch the BlogTag using IBlogTag.Get from the Core Service Dependencies Section.  
         2. Add it to a new list **temporaryBlogTags**.  
         3. Handle exceptions during fetching operation, log error and continue without throwing an error.  
7. **Map** the ArticleDto based on the Article to ArticleDto from the Mapping Definition Section.  
   1. Include the related BlogCategories.  
   2. Include the related BlogTags.  
7. **Map** the RerunListArticleDto based on the ListArticleRequestDto to List\<ArticleDto\> and PagedResult to List\<ArticleDto\> from the Mapping Definition Section.  
8. Return the ReturnListArticleDto object.

## \*Core Service Dependencies\*

This section lists all internal services referenced in the implementation text.

| Service              | Method | Arguments                                   | Return value | Argument Details                                                                                                                                                               |
| :------------------- | :----- | :------------------------------------------ | :----------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IAuthorService       | Get    | AuthorRequestDto request, Guid userId       | AuthorDto    | AuthorRequestDto: \- Id (guid): Unique identifier for the author                                                                                                               |
| IBlogCategoryService | Get    | BlogCategoryRequestDto request, Guid userId | BlogCategory | BlogCategoryRequestDto:- Id (guid): Unique identifier for the BlogCategory                                                                                                     |
| IBlogTagService      | Create | CreateBlogTagDto request, Guid userId       | string       | CreateBlogTagDto: \- Name (string): BlogTag name \- Langcode (string): Language code                                                                                           |
| IBlogTagService      | Get    | BlogTagRequestDto request, Guid userId      | BlogTag      | BlogTagRequestDto: \- Id (guid): Unique identifier for the tag \- Name (string): BlogTag name                                                                                  |
| IAttachmentService   | Create | CreateAttachmentDto request, Guid userId    | string       | CreateAttachmentDto: \- FileName (string): Name of the file \- FileData (string): File data in base64 format                                                                   |
| IAttachmentService   | Get    | AttachmentRequestDto request, Guid userId   | Attachment   | AttachmentRequestDto: \- Id (guid): Unique identifier for the attachment                                                                                                       |
| IAttachmentService   | Update | UpdateAttachmentDto request, Guid userId    | string       | UpdateAttachmentDto: \- Id (guid):  Id of the attachment \- FileName (string): Name of the file \- FileData (string): File data in base64 format                               |
| IImageService        | Create | CreateImageDto request, Guid userId         | string       | CreateImageDto: \- ImageName (string): Image file name \- ImageFile (string): Image data in base64 format \- AltText (string): Image description                               |
| IImageService        | Get    | ImageRequestDto request, Guid userId        | Image        | ImageRequestDto: \- Id (guid): Unique identifier for the image                                                                                                                 |
| IImageService        | Update | UpdateImageDto request, Guid userId         | string       | UpdateImageDto: \- Id (guid): Id of the Image \- ImageName (string): Image file name \- ImageFile (string): Image data in base64 format \- AltText (string): Image description |

\- \- \-


# \*\*API Exceptions\*\*

| Code       | Description     | Category  |
| :--------- | :-------------- | :-------- |
| **DP-500** | Technical Error | Technical |
| **DP-422** | Client Error    | Business  |
| **DP-404** | Technical Error | Technical |
| **DP-400** | Technical Error | Technical |

\- \- \-


# \*\*Interface Layer Section\*\*

## \*IArticleService\*

| Method  | Arguments                                                              | Return value                                    |
| :------ | :--------------------------------------------------------------------- | :---------------------------------------------- |
| Create  | [CreateArticleDto](#*articleblogcategory*) request, Guid userId        | string                                          |
| Get     | [ArticleRequestDto](#*articlerequestdto*) request, Guid userId         | [ArticleDto](#*articledto*)                     |
| Update  | [UpdateArticleDto](#*updatearticledto*) request, Guid userId           | string                                          |
| Delete  | [DeleteArticleDto](#*deletearticledto*) request, Guid userId           | bool                                            |
| GetList | [ListArticleRequestDto](#*listarticlerequestdto*) request, Guid userId | [ReturnListArticleDto](#*returnlistarticledto*) |

\- \- \-


# \*\*Controller Layer Section\*\*


## \*ArticleController\*

### /article/create

| HTTP Request Method | POST                                                                |
| :------------------ | :------------------------------------------------------------------ |
| **Method**          | Create                                                              |
| **Request**         | [Request](#heading-2)\<[CreateArticleDto](#*articleblogcategory*)\> |
| **Response**        | [Response](#heading-3)\<string\>                                    |

### 

### /article/get

| HTTP Request Method | POST                                                               |
| :------------------ | :----------------------------------------------------------------- |
| **Method**          | Get                                                                |
| **Request**         | [Request](#heading-2)\<[ArticleRequestDto](#*articlerequestdto*)\> |
| **Response**        | [Response](#heading-3)\<[ArticleDto](#*articledto*)\>              |

### /article/update

| HTTP Request Method | POST                                                             |
| :------------------ | :--------------------------------------------------------------- |
| **Method**          | Update                                                           |
| **Request**         | [Request](#heading-2)\<[UpdateArticleDto](#*updatearticledto*)\> |
| **Response**        | [Response](#heading-3)\<string\>                                 |

### /article/delete

| HTTP Request Method | POST                                                             |
| :------------------ | :--------------------------------------------------------------- |
| **Method**          | Delete                                                           |
| **Request**         | [Request](#heading-2)\<[DeleteArticleDto](#*deletearticledto*)\> |
| **Response**        | [Response](#heading-3)\<bool\>                                   |

### /article/list

| HTTP Request Method | POST                                                                       |
| :------------------ | :------------------------------------------------------------------------- |
| **Method**          | GetList                                                                    |
| **Request**         | [Request](#heading-2)\<[ListArticleRequestDto](#*listarticlerequestdto*)\> |
| **Response**        | [Response](#heading-3)\<[ReturnListArticleDto](#*returnlistarticledto*)\>  |

\- \- \-

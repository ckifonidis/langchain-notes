# **API Technical Design** **Developers Portal**  Domain: BlogTag 

## Document Version: 1.0

# 

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

```json

{    
   "header": 
   {        
      "ID": "{{$guid}}",        
      "application": "03FC0B90-DFAD-11EE-8D86-0800200C9A66",        
      "bank": "NBG",        
      "UserId": "{{$user_guid}}"    
   },    
   "payload": {}
}
```

* request.header.ID is a new GUID for each request. This way the request can be tracked down in the future.  
* request.Header.application is a GUID for each application that invokes our web API.  
* request.Header.bank always has the value “BANK”  
* request.Header.UserId is the GUID Id for each user.

## \*Responses\*

Each API response is wrapped in a Response object. 

* All the exceptions thrown during the execution of an endpoint are caught and the response.exception field is assigned the related exception info and response.payload \= null  
* In case of success (no exception thrown), the response.payload is described in each endpoint’s technical description. The response.exception \= null

**Example Response**

``` json
{    "payload": {},    "exception": {        "id": "guid",        "code": "string",        "description": "string"    }}
```

## \*Endpoint Execution Logic\*

All endpoints are asynchronous.

No matter what happens during the execution of an endpoint’s logic, the HTTP response code is always 200-OK. To achieve this, the execution of each endpoint is handled by a mechanism that is called SafeExecutor.

SafeExecutor is a static class.

SafeExecutor wraps the provided action in a try-catch block. If any exception occurs, the response.exception field is assigned the exception information.

Exceptions are categorized as Business or Technical. They have their own class extending the system exception class, with additional fields: 

* Code: string  
* Description: string

When the SafeExecutor catches a Business/Technical exception the mapping is straightforward. When it catches a simple exception, it is handled as a technical exception with a fixed code of “1001” and description “A technical exception has occurred, please contact your system administrator”.

Each endpoint’s logic is exposed as a method in the service layer and is also described in an interface. The controllers inject the interface of the service and safely via SafeExecutor invoke the corresponding method. The service layer is not aware of the Request/Response wrapper objects. There is a one-to-one mapping for endpoints and service methods. For example, for an endpoint named “CreateUser”, there should be a method “CreateUser” defined in the interface and implemented in the service layer. Types, Interfaces and Services are defined in separate files.

## 

## 

## \*Database Layer Rules\*

Dapper ORM is used to access, add, update or delete database data. We only use parameterized queries to avoid SQL-Injection scenarios. Database access has its own layer, usually mentioned as “Repositories”. Method signatures must describe what the method is about. For example, 

| Task\<BlogTag\> SelectBlogTagAsync(Guid blogTagId) |
| :------------------------------------------------- |

The service layer injects the database access service and invokes its methods by providing the required data, without knowing any details about the queries that actually run.

Also, in terms of database structure, we never use foreign keys.

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

### \*BlogTags\*

| Name          | Data Type        | Nullable | Unique | Description                                                         |
| :------------ | :--------------- | :------- | :----- | :------------------------------------------------------------------ |
| Id            | uniqueidentifier | false    | true   | Unique entry’s identifier to the table                              |
| Name          | nvarchar(200)    | true     | true   | BlogTag name                                                        |
| Description   | nvarchar(200)    | true     | false  | Description of the Entity                                           |
| Langcode      | nvarchar(4)      | false    | false  | Shows the Language of the entity                                    |
| Sticky        | bit              | true     | false  | Keeps the entity on top                                             |
| Promote       | bit              | true     | false  | Entity in the frontpage                                             |
| Published     | bit              | true     | false  | Show if the entity is published                                     |
| UrlAlias      | nvarchar(200)    | true     | false  | UrlAlias path                                                       |
| Version       | int              | true     | false  | Indicates the current version number (increase by 1 on each update) |
| Created       | datetime2(7)     | true     | false  | Show when the entity is created                                     |
| Changed       | datetime2(7)     | true     | false  | Show when the entity is updated                                     |
| CreatorId     | uniqueidentifier | true     | false  | Creator Id                                                          |
| ChangedUserId | uniqueidentifier | true     | false  | Last user that change the entity                                    |

\- \- \-

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

# 

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

\- \- \-

# \*\*Mapping Definitions Section\*\*

### CreateBlogTagDto to BlogTag

| Source (CreateBlogTagDto) | Target (BlogTag) | Mapping Details               |
| :------------------------ | :--------------- | :---------------------------- |
| Id                        | Id               | Guid.NewGuid()                |
| Name                      | Name             | dto.Name                      |
| Description               | Description      | dto.Description (If provided) |
| Langcode                  | Langcode         | dto.Langcode                  |
| Sticky                    | Sticky           | dto.Sticky (If provided)      |
| Promote                   | Promote          | dto.Promote (If provided)     |
| UrlAlias                  | UrlAlias         | dto.UrlAlias (If provided)    |
| Published                 | Published        | dto.Published (If provided)   |
|                           | Version          | 1 (Initial version)           |
|                           | Created          | DateTime.Now                  |
|                           | CreatorId        | userId                        |

### UpdateBlogTagDto to BlogTag

| Source (UpdateBlogTagDto) | Target (BlogTag) | Mapping Details                     |
| :------------------------ | :--------------- | :---------------------------------- |
| Name                      | Name             | dto.Name (If provided)              |
| Description               | Description      | dto.Description (If provided)       |
| Langcode                  | Langcode         | dto.Langcode (If not null or empty) |
| Sticky                    | Sticky           | dto.Sticky  (If provided)           |
| Promote                   | Promote          | dto.Promote (If provided)           |
| UrlAlias                  | UrlAlias         | dto.UrlAlias (If provided)          |
| Published                 | Published        | dto.Published (If provided)         |
|                           | Version          | existingBlogTag.Version \+ 1        |
|                           | Changed          | DateTime.Now                        |
|                           | ChangedUserId    | userId                              |

### 

### ListBlogTagRequestDto to ReturnListBlogTagDto

| Source (ListBlogTagRequestDto) | Target (ReturnListBlogTagDto) | Mapping Details            |
| :----------------------------- | :---------------------------- | :------------------------- |
| PageLimit                      | Metadata.PageLimit            | Provided pageLimit value.  |
| PageOffset                     | Metadata.PageOffset           | Provided pageOffset value. |

### 

### PagedResult to ReturnListBlogTagDto

| Source (pagedResult) | Target (ReturnListBlogTagDto) | Mapping Details                                                                                                                                              |
| :------------------- | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Records              | List\<BlogTag\>               | ToList()                                                                                                                                                     |
| TotalRecords         | Metadata.Total                | (pagedResult.TotalRecords % request.PageLimit \== 0\)  ? pagedResult.TotalRecords / request.PageLimit  : (pagedResult.TotalRecords / request.PageLimit) \+ 1 |

### 

\- \- \-

# 

# \*\*Types Layer Section\*\*

### 

### \*BlogTag\* {#*blogtag*}

Table Annotation: This entity maps to the database table BlogTags.

| Name          | Data Type | Description                                                         |
| :------------ | :-------- | :------------------------------------------------------------------ |
| Id            | guid      | Unique entry’s identifier                                           |
| Name          | string    | BlogTag name                                                        |
| Description   | string    | Description of the entity                                           |
| Langcode      | string    | Shows the Language of the entityValues: \[“el”, “en”\]             |
| Sticky        | bool      | Keeps the entity on top                                             |
| Promote       | bool      | Entity in the frontpage                                             |
| UrlAlias      | string    | UrlAlias path                                                       |
| Published     | bool      | Show if the entity is published                                     |
| Version       | int       | Indicates the current version number (increase by 1 on each update) |
| Created       | datetime  | Show when the entity is created                                     |
| Changed       | datetime  | Show when the entity is updated                                     |
| CreatorId     | guid      | Creator Id                                                          |
| ChangedUserId | guid      | Last user that change the entity                                    |

### 

### \*CreateBlogTagDto\* {#*createblogtagdto*}

| Name        | Data Type | Description                                             |
| :---------- | :-------- | :------------------------------------------------------ |
| Name        | string    | BlogTag name                                            |
| Description | string    | Description of the entity                               |
| Langcode    | string    | Shows the Language of the entityValues: \[“el”, “en”\] |
| Sticky      | bool      | Keeps the entity on top                                 |
| Promote     | bool      | Entity in the frontpage                                 |
| UrlAlias    | string    | UrlAlias path                                           |
| Published   | bool      | Show if the entity is published                         |

### 

### \*UpdateBlogTagDto\* {#*updateblogtagdto*}

| Name        | Data Type | Description                                             |
| :---------- | :-------- | :------------------------------------------------------ |
| Id          | guid      | Unique entry’s identifier                               |
| Name        | string    | BlogTag name                                            |
| Description | string    | Description of the entity                               |
| Langcode    | string    | Shows the Language of the entityValues: \[“el”, “en”\] |
| Sticky      | bool      | Keeps the entity on top                                 |
| Promote     | bool      | Entity in the frontpage                                 |
| UrlAlias    | string    | UrlAlias path                                           |
| Published   | bool      | Show if the entity is published                         |

### 

### \*DeleteBlogTagDto\* {#*deleteblogtagdto*}

| Name | Data Type | Description               |
| :--- | :-------- | :------------------------ |
| Id   | guid      | Unique entry’s identifier |

### \*BlogTagRequestDto\* {#*blogtagrequestdto*}

| Name | Data Type | Description               |
| :--- | :-------- | :------------------------ |
| Id   | guid      | Unique entry’s identifier |
| Name | string    | BlogTag name              |

### 

### \*ListBlogTagRequestDto\* {#*listblogtagrequestdto*}

| Name       | Data Type | Description |
| :--------- | :-------- | :---------- |
| PageLimit  | int       | Page limit  |
| PageOffset | int       | Page offset |
| SortField  | string    | Sort field  |
| SortOrder  | string    | Sort order  |
| SearchTerm | string    | Search      |

### \*MetadataDto\*

| Name       | Data Type | Description            |
| :--------- | :-------- | :--------------------- |
| PageLimit  | int       | Page limit             |
| PageOffset | int       | Page offset            |
| Total      | int       | Total number of pages. |

### \*ReturnListBlogTagDto\* {#*returnlistblogtagdto*}

| Name     | Data Type       | Description               |
| :------- | :-------------- | :------------------------ |
| Data     | List\<BlogTag\> | List of BlogTags objects. |
| Metadata | MetadataDto     | Pagination parameters.    |

\- \- \-

# 

# 

# 

# 

# 

# \*\*Implementation Layer Section\*\*

## \*BlogTagService\*

### 

### \*Create\*

Creates a BlogTag with the specified details

| Arguments        | [CreateBlogTagDto](#*createblogtagdto*) request, Guid userId |
| :--------------- | :----------------------------------------------------------- |
| **Return value** | string                                                       |

**Implementation**:

1. **Validate** that the request contains the necessary parameters ("Name", “LangCode”).  
   1. If the necessary parameters are missing, throw the [DP-422](#dp-422) exception.  
2. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Create operation.   
3. **Check** if a BlogTag with the same Name already exists:  
   1. Retrieve the BlogTags by Name.  
   2. Assign the Id from the first of the retrieved BlogTags to the blogTagId.  
   3. If found, return the existing blogTagId.  
   4. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
4. **Map** the BlogTag based on the CreateBlogTagDto to BlogTag from the Mapping Definition Section.  
5. **Perform Database Operations**:  
   1. Insert the BlogTag.  
   2. Retrieve BlogTags by Id.  
   3. Assign the first of the retrieved blogTags to the blogTag.  
   4. Handle errors during insertions or retrievals by throwing the [DP-500](#dp-500) exception.  
   5. If not found, throw the [DP-404](#dp-404) exception.  
   6. Return the BlogTag’s Id.  
      

### 

### \*Get\*

Get a BlogTag with the specified details

| Arguments        | [BlogTagRequestDto](#*blogtagrequestdto*) request, Guid userId |
| :--------------- | :------------------------------------------------------------- |
| **Return value** | [BlogTag](#*blogtag*)                                          |

**Implementation**:

1. **Validate** that the request contains the necessary parameters ("Id", “Name”).  
   1. If the necessary parameters are missing, throw the [DP-422](#dp-422) exception.  
2. **Fetch BlogTag:**  
   1. Retrieve BlogTags first by Id and then by Name, depending which one is provided.  
   2. Assign the first of the retrieved blogTags to the blogTag.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Read operation.  
4. **Return** the blogTag as the response payload. 

### 

### 

### \*Update\*

Update a BlogTag with the specified details

| Arguments        | [UpdateBlogTagDto](#*updateblogtagdto*) request, Guid userId |
| :--------------- | :----------------------------------------------------------- |
| **Return value** | string                                                       |

**Implementation**:

1. **Validate** that the request contains the necessary parameter ("Id").  
   1. If the necessary parameter is missing, throw the [DP-422](#dp-422) exception.  
2. **Fetch BlogTag**  
   1. Retrieve the BlogTags by Id.  
   2. Assign the first of the retrieved blogTags to the blogTag.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Update operation.  
4. **Map** the BlogTag based on the UpdateBlogTagDto to BlogTag from the Mapping Definition Section.  
5. **Perform Database Operations**:  
   1. Update the BlogTag.  
   2. Retrieve BlogTags by Id.  
   3. Assign the first of the retrieved blogTags to the blogTag.  
   4. Handle errors during insertions or retrievals by throwing the [DP-500](#dp-500) exception.  
   5. If not found, throw the [DP-404](#dp-404) exception.  
   6. Return the Blog Tag’s Id.

   

### 

### 

### 

### 

### \*Delete\*

Delete a BlogTag with the specified details

| Arguments        | [DeleteBlogTagDto](#*deleteblogtagdto*) request, Guid userId |
| :--------------- | :----------------------------------------------------------- |
| **Return value** | bool                                                         |

**Implementation**:

1. **Validate** that the request contains the necessary parameter ("Id").  
   1. If the necessary parameter is missing, throw the [DP-422](#dp-422) exception.  
2. **Fetch BlogTag**  
   1. Retrieve the BlogTags by Id.  
   2. Assign the first of the retrieved blogTags to the blogTag.  
   3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
   4. If not found, throw the [DP-404](#dp-404) exception.  
3. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Delete operation.  
4. **Perform Database Operations:**  
   1. Delete the BlogTag and its related ArticleBlogTags in a single operation ensuring transactional consistency.  
   2. Return true.  
   3. Handle errors during deletions by throwing the [DP-500](#dp-500) exception.  
   4. Return false.

### 

### \*GetList\*

Get a BlogTag list with the specified details

| Arguments        | [ListBlogTagRequestDto](#*listblogtagrequestdto*) request, Guid userId |
| :--------------- | :--------------------------------------------------------------------- |
| **Return value** | [ReturnListBlogTagDto](#*returnlistblogtagdto*)                        |

**Implementation**:

1. **Validate** that the request contains valid pagination parameters ("PageLimit must not be null or \> 0" and “PageOffset must not be null or ≥ 0”).  
   1. If the necessary parameters are null or invalid, throw the [DP-422](#dp-422) exception.  
2. **Authorization Check:**  
   1. Validate that the user has the permission to perform the Read operation.  
3. **Retrieve Paged BlogTags:**  
   1. Fetch paged BlogTags using the following parameters:  
      1. Pagination: Use request.PageLimit and request.PageOffset for PageSize and Offset.  
      2. Sorting: Default to SortField \= "CreatorId" and SortOrder \= "desc" if not provided.  
      3. Handle errors during retrievals by throwing the [DP-500](#dp-500) exception.  
4. **Map** the RerunListBlogTagDto based on the ListBlogTagRequestDto to List\<BlogTag\> and PagedResult to List\<BlogTag\> from the Mapping Definition Section.  
5. Return the ReturnListBlogTagDto object.

\- \- \-

# 

# \*\*API Exceptions\*\*

| Code       | Description     | Category  |
| :--------- | :-------------- | :-------- |
| **DP-500** | Technical Error | Technical |
| **DP-422** | Client Error    | Business  |
| **DP-404** | Technical Error | Technical |
| **DP-400** | Technical Error | Technical |

\- \- \-

# 

# \*\*Interface Layer Section\*\*

## \*IBlogTagService\*

| Method  | Arguments                                                                           | Return value                                    |
| :------ | :---------------------------------------------------------------------------------- | :---------------------------------------------- |
| Create  | [CreateBlogTagDto](#*createblogtagdto*) request, Guid userId                        | string                                          |
| Get     | Blog[TagRequestDto](#*blogtagrequestdto*) request, Guid userId                      | Blog[Tag](#*blogtag*)                           |
| Update  | [UpdateBlogTagDto](#*updateblogtagdto*) request, Guid userId                        | string                                          |
| Delete  | [DeleteBlogTagDto](?tab=t.3qj9o6sgfybe#heading=h.1dq4v5t8pn2f) request, Guid userId | bool                                            |
| GetList | [ListBlogTagRequestDto](#*listblogtagrequestdto*) request, Guid userId              | [ReturnListBlogTagDto](#*returnlistblogtagdto*) |

\- \- \-

# 

# 

# \*\*Controller Layer Section\*\*

## \*BlogTagController\*

### /blogtag/create

| HTTP Request Method | POST                                                             |
| :------------------ | :--------------------------------------------------------------- |
| **Method**          | Create                                                           |
| **Request**         | [Request](#heading-2)\<[CreateBlogTagDto](#*createblogtagdto*)\> |
| **Response**        | [Response](#heading-3)\<string\>                                 |

### /blogtag/get

| HTTP Request Method | POST                                                               |
| :------------------ | :----------------------------------------------------------------- |
| **Method**          | Get                                                                |
| **Request**         | [Request](#heading-2)\<Blog[TagRequestDto](#*blogtagrequestdto*)\> |
| **Response**        | [Response](#heading-3)\<Blog[Tag](#*blogtag*)\>                    |

### /blogtag/update

| HTTP Request Method | POST                                                             |
| :------------------ | :--------------------------------------------------------------- |
| **Method**          | Update                                                           |
| **Request**         | [Request](#heading-2)\<[UpdateBlogTagDto](#*updateblogtagdto*)\> |
| **Response**        | [Response](#heading-3)\<string\>                                 |

### /blogtag/delete

| HTTP Request Method | POST                                                                                    |
| :------------------ | :-------------------------------------------------------------------------------------- |
| **Method**          | Delete                                                                                  |
| **Request**         | [Request](#heading-2)\<[DeleteBlogTagDto](?tab=t.3qj9o6sgfybe#heading=h.1dq4v5t8pn2f)\> |
| **Response**        | [Response](#heading-3)\<bool\>                                                          |

### /blogtag/list

| HTTP Request Method | POST                                                                       |
| :------------------ | :------------------------------------------------------------------------- |
| **Method**          | GetList                                                                    |
| **Request**         | [Request](#heading-2)\<[ListBlogTagRequestDto](#*listblogtagrequestdto*)\> |
| **Response**        | [Response](#heading-3)\<[ReturnListBlogTagDto](#*returnlistblogtagdto*)\>  |

### 

\- \- \-

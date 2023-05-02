Muzaffarhusain Turak mturak@stevens.edu
Dhanesh Akolu dakolu@stevens.edu

URL:https://github.com/tmuzu98/webForum



1) an estimate of how many hours you spent on the project

Ans: 15-20 hours

2) a description of how you tested your code

Ans: To test the code, we utilized Postman to create test cases for the POST, GET, UPDATE, and DELETE functionalities. In parallel, we also verified the behavior of the functionalities and the passing of test cases by examining the MongoDB database.


3)any bugs or issues you could not resolve

Ans: We encountered difficulty when attempting to create a test case for the Date and Time-based Range Query extension, which involved retrieving all posts within a designated time frame, including both a start time and end time.


4)An example of a difficult issue or bug and how you resolved

Ans: We encountered a challenge when attempting to implement DELETE Post functionality, specifically with regards to authentication. We were initially unsure whether to use the post key or user key for this purpose. After careful consideration, we determined that the post key should be used for posts that are not associated with any particular user, while the user key should be used for posts that are associated with a specific user.


5)a list of the five extensions you’ve chosen to implement; be sure to describe the endpoints you’ve added to support this, using a documentation format similar to ours

Ans:  *** EXTENSION 1:Users and user keys ***

When you go to the register endpoint it registers you as a new user and returns the user id and the user key.

Now when you post using the specific user id and key you can only post using the user specific key or else you are forbidden from posting.

1. Each post can be associated with a user by providing the user id and corresponding user key when creating the post.
2. Whenever you give information about a post that has an associated user, you should return the associated user id along with other data (e.g., when reading and deleting posts).
3. If a user created a post, it should be sufficient to provide the user’s key to delete the post. It should be clear whether the user is providing a post’s key or a user’s key.
4. There should be some way to create users (a new /user endpoint is added for user creation).

if post["key"] != key and (post["user_id"] is None or users.get(post["user_id"]) != key):
            return make_response(jsonify(err="Forbidden"), 403)


This line of code checks whether the provided key is valid for deleting a post. There are two possible ways a post can be deleted: using the post's key or using the user's key (if the post is associated with a user).
Here's a breakdown of the conditions being checked:
1. post["key"] != key: This checks whether the provided key does not match the post's key. If it does not match, the code will proceed to check the next condition.
2. (post["user_id"] is None or users.get(post["user_id"]) != key): This is checking two sub-conditions:
3. a. post["user_id"] is None: This checks whether the post is not associated with any user. If the post is not associated with a user, the provided key must be the post's key, and since it didn't match, the access is forbidden.
4. b. users.get(post["user_id"]) != key: This checks whether the provided key does not match the user's key associated with the post. If it does not match, the access is forbidden.
If both conditions are true, it means that the provided key is neither the post's key nor the associated user's key, so the request is denied with a "Forbidden" error and a 403 HTTP status code.

*** EXTENSION 2: User profiles ***

Our code satisfies the conditions as follows:
1. Add metadata to users: In the create_user() function, we store the unique username and non-unique real_name as metadata for the user. The username is required, while the real_name is optional.

username = data["username"] real_name = data.get("real_name")

2. User creation must specify the unique part: The username is a required field in the request JSON, and we check for it during user creation.

if not data or "username" not in data or not isinstance(data["username"], str): return make_response(jsonify(err="Bad request"), 400)

3. API endpoint to retrieve a user's metadata: The /user/<int:user_id> and /user/username/<username> endpoints allow us to retrieve a user's metadata using their user_id or unique username, respectively.

@app.route("/user/<int:user_id>", methods=["GET"]) def get_user(user_id): ... @app.route("/user/username/<username>", methods=["GET"]) def get_user_by_username(username): ...

4. API endpoint to edit a user's metadata: The /user/<int:user_id>/edit/<key> endpoint allows editing a user's metadata if the user's key is provided.

@app.route("/user/<int:user_id>/edit/<key>", methods=["PUT"]) def edit_user(user_id, key): ...

5. Including the user's unique metadata when returning post information: When reading (read_post()) or deleting a post (delete_post()), we include the username of the user associated with the post in the response, satisfying the requirement to return the unique metadata.

username = None if user_id is not None: with users_lock: user = users.get(user_id) if user: username = user["username"] return jsonify( id=post["id"], timestamp=post["timestamp"], msg=post["msg"], user_id=user_id, username=username, )

The code, as it stands, meets all the requirements mentioned in the problem statement.

*** EXTENSION 3 Threaded replies ***

1. When creating a post, it should be possible to specify a post id to which the new post is replying.
In the create_post function, we check if the "parent_post_id" field is present in the request data:
parent_post_id = data.get("parent_post_id", None)
If "parent_post_id" is provided, the new post will be associated with the parent post by setting the "parent_post_id" field in the post dictionary:

post = { ... "parent_post_id": parent_post_id, }

2. When returning information about a post that is a reply, include the id of the post to which it is replying.
In the read_post function, we return the post's data in the JSON response, which includes the "parent_post_id" field if the post is a reply:

return jsonify( ... parent_post_id=post.get("parent_post_id", None), ... )

3. When returning information about a post which has replies, include the ids of every reply to that post.
The replies dictionary stores the relationship between parent posts and their replies:

replies[parent_post_id].append(post_id)
In the read_post function, we retrieve the list of reply ids for the given post using the replies dictionary and include it in the JSON response:

reply_ids = replies.get(post_id, []) return jsonify( ... replies=reply_ids, )
This code satisfies all the conditions for threaded replies as described.

***Extension 4 Date- and time-based range queries***

The provided code satisfies the conditions of date- and time-based range queries by implementing an API endpoint /posts/search, which accepts GET requests.
When a client makes a request to this endpoint, the client can provide optional query parameters start_datetime and end_datetime. These parameters specify the starting and ending date-time of the range for which the posts should be fetched.
The code first checks if the start_datetime and end_datetime query parameters are provided. If they are, it converts them from ISO 8601 formatted strings to Python datetime objects.
Next, it builds a query for MongoDB based on the provided date-time range. If start_datetime and/or end_datetime are provided, the code adds conditions to the query to filter the posts based on the timestamp field.
The code then executes the query against the MongoDB collection, fetching the posts that match the date-time range conditions. Finally, it returns a JSON response containing a list of post information (id, message, timestamp, user_id) for each post within the specified range.
This implementation allows searching with a starting date and time, an ending date and time, or both, as per the requirements.


***Extension 5 User-based range queries***

1. We have already implemented the users, so this extension is applicable.
2. A new API endpoint /posts/user/<int:user_id> is added to search for posts by a given user. This endpoint accepts GET requests and takes the user ID as a path parameter.
3. In the get_posts_by_user function, we first look for the user in the users collection with the provided user ID. If the user is not found, a 404 error is returned.
4. If the user exists, we query the posts collection for posts with the specified user_id. The find method is used to search for all the posts in the collection that match the given user_id.
5. The found posts are then processed, and for each post, we create a dictionary containing post information like id, message, timestamp, user_id, parent_post_id, and replies. We then append this dictionary to the response list.
6. The response list containing post information for each post created by the specified user is returned as a JSON object.
By implementing this new endpoint and its corresponding function, our code now allows users to search for posts based on a given user, returning a list of post information as specified in the conditions.


6) detailed summaries of your tests for each of your extensions, i.e., how to interpret your testing framework and the tests you’ve written

Ans: We have uploaded a single json file that contains all of our testcases where we have tried to cover all the edgecases. All the testcases were performed on Postman.
For eg:
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has 'id' and 'key'", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('key');
});

var jsonData = pm.response.json();
pm.environment.set("userKey", jsonData.key);
pm.environment.set("userId", jsonData.id);

This is a test that we've written for POST request for creating a new user and following is the request body:
{
    "username":"muzaff",
    "email":"muzaffar@gmail.com",
    "real_name":"Muzaffar Turak"
}

likewise we have written testcases for all the functionalities and the extensions.



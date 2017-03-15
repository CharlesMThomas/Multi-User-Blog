Multi User Blog
==============
Author: Charles M Thomas

App URL: https://inlaid-span-160415.appspot.com/

Description: A basic blog complete with user authentication and permissions. Code written in Python and uses the WebApp2 framework on Google App Engine.

Guest Instructions
------------------
**Sign Up**

(URL: /signup)
- Fill out the sign up form and submit to create a user account.
* User account will allow you to create, edit and delete posts and comments. You can also like/unlike posts.

**Login**

(URL: /login)
- After a user account has been created, enter your username and password to login.

**Logout**

(URL: /logout)
- Click the logout link in the navigation to logout.

**Blog**

(URL: /blog)
- Shows all of the current blog posts.

**Post**

(URL: /*POST ID*)
- Shows a single post.

Registered User Instructions
----------------------------
**Sign Up**

(URL: /signup)
- Fill out the sign up form and submit to create a user account.
* User account will allow you to create, edit and delete posts and comments. You can also like/unlike posts.

**Login**

(URL: /login)
- After a user account has been created, enter your username and password to login.

**Logout**

(URL: /logout)
- Click the logout link in the navigation to logout.


**Blog**

(URL: /blog)
- Shows all of the current blog posts.

**Post**

(URL: /*POST ID*)
- Shows a single post.

**Create New Post**

(URL: /newpost)
- Fill in the post subject and content and click the submit button.

**Edit Post**

(URL: /edit/*POST ID*)
- Click the edit button on the post page. Update the post subject and/or content and click the submit button.
* Users can only edit their own posts.

**Delete Post**

(URL: /delete/*POST ID*)
- Click the delete button on the post page. The post will be PERMANENTLY deleted.
* Users can only delete their own posts.

**Like Post**

(URL: /like/*POST ID*)
- Click the like button on the post page.
* Users can not like their own posts.

**Unlike Post**

(URL: /unlike/*POST ID*)
- Click the unlike button on the post page. Unlike button will only appear if the post has already been liked.
* Users can only unlike a post if they have liked it previously.

**Create Comment**

(URL: /comment/new/*POST ID*)
- Click the create comment button on the post page. Fill out the comment box and click the submit button.

**Edit Comment**

(URL: /comment/edit/*POST ID*)
- Click the edit comment button below the comment. Edit the comment box contents and click the submit button.
* Users can only edit their own comments.

**Delete Comment**

(URL: /comment/delete/*POST ID*)
- Click the delete comment button below the comment. The comment will be PERMANENTLY deleted.
* Users can only delete their own comments.

from google.appengine.ext import db
from models import User, Post, Like, Comment
import random
import string
import hashlib
import os
import jinja2
import re
import webapp2
import logging
import time

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

SECRET = 'imasecretstring'


class Utils(webapp2.RequestHandler):
    """ General hashing, verification and template functions"""
    def render_jinja_template(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def make_salt(self):
    	return ''.join(random.choice(string.letters) for x in xrange(5))

    def make_pw_hash(self, name, pw, salt=None):
        if not salt:
            salt = self.make_salt()
        h = hashlib.sha256(name + pw + salt).hexdigest()
        return '%s|%s' % (h, salt)

    def validate_pw_hash(self, name, pw, h):
        salt = h.split('|')[1]
        return h == self.make_pw_hash(name, pw, salt)

    def make_id_hash(self, user_id):
        h = hashlib.md5(SECRET + str(user_id)).hexdigest()
        return '%s|%s' % (user_id, h)

    def check_login(self, cookie_id_hash):
        if self.validate_id_hash(cookie_id_hash):
            user_id = int(cookie_id_hash.split('|')[0])
            username = User.get_by_id(user_id).username
            if username:
                return username

    def validate_id_hash(self, user_id_from_cookie):
        id_from_cookie = user_id_from_cookie.split('|')[0]
        h = self.make_id_hash(id_from_cookie)
        if h == user_id_from_cookie:
            return True

    def valid_username(self, username):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        return USER_RE.match(username)

    def valid_password(self, password):
        PASS_RE = re.compile(r"^.{3,20}$")
        return PASS_RE.match(password)

    def valid_email(self, email):
        EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
        return EMAIL_RE.match(email)


class BlogHandler(Utils):
    """
    Functions for handling common blog related tasks, such as login & logout
    """
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return self.render_jinja_template(template, **params)

    def set_secure_cookie(self, name, val):
        cookie_val = self.make_id_hash(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header(
            'Set-Cookie',
            'user_id=; Path=/')


class Blog(BlogHandler):
    """ Functions for rendering the main blog overview page"""
    def get(self):
        # get all posts.
        posts = Post.all().order('-created')

        # if logged in show user navigation, if not show guest navigation.
        username = self.check_login(self.request.cookies.get('user_id'))

        if username:
            self.render('/blog.html', username=username, posts=posts)
        else:
            self.render('/blog.html', posts=posts)


class NewPost(BlogHandler):
    """ functions for creating a new post"""
    def get(self):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))

        if username:
            self.render('new-post.html', username=username)
        # if not logged in, redirect to login.
        else:
            self.redirect('/login')

    def post(self):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # get form contents.
            subject = self.request.get("subject")
            content = self.request.get("content")

            # if info is missing, show alert.
            if not subject or not content:
                error = "We need both a title and some blog content!"
                self.render("new-post.html", error=error)
            # if all required info is present create post.
            else:
                p = Post(username=username, subject=subject, content=content)
                p.put()
                self.redirect('/%s' % str(p.key().id()))


class PostPage(BlogHandler):
    """ functions for rendering a post"""
    def get(self, post_id):
        # get post content, likes and comments from id passed in the url.
        post = db.get(db.Key.from_path('Post', int(post_id)))
        likes = Like.all().filter('post_id =', post_id).count()
        comments = Comment.all().filter('post_id = ', post_id)

        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        # detect if user already liked the post.
        already_like = Like.all().filter(
                                         'username=', username).filter(
                                         'post_id=', post_id).get()

        # if post does not exist based id, show alert.
        if not post:
            self.render('alerts.html',
                        alert='Post does not exist',
                        path='/blog')
        # show the form.
        else:
            self.render('post-page.html',
                        post=post,
                        likes=likes,
                        already_like=already_like,
                        username=username,
                        comments=comments)


class EditPost(BlogHandler):
    """ functions for editing a post"""
    def get(self, post_id):

        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # get the post.
            post = db.get(db.Key.from_path('Post', int(post_id)))

            # if post does not exist, show alert.
            if not post:
                self.render('alerts.html',
                            alert='Post does not exist',
                            path='/blog')
            # if post does not belong to user, show alert.
            elif post.username != username:
                self.render('alerts.html',
                            alert='Only the author can edit this post',
                            path='/%s' % post_id)
            else:
                self.render('/edit-post.html',
                            subject=post.subject,
                            content=post.content,
                            post_id=post_id,
                            username=username)

    def post(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # get form contents.
            subject = self.request.get("subject")
            content = self.request.get("content")

            # get the post.
            post = db.get(db.Key.from_path('Post', int(post_id)))
            # show alert if post does not exist.
            if not post:
                self.render('alerts.html',
                            alert="Post does not exist!",
                            path='/blog')
            if post.username != username:
                self.render('alerts.html',
                            alert='Only the author can edit this post.',
                            path='/%s' % post_id)
            # if subject or content are missing show alert.
            if not subject or not content:
                error = "We need both a title and some blog content!"
                self.render("edit-post.html",
                            subject=subject,
                            content=content,
                            error=error)
            # update the post.
            else:
                post.subject = subject
                post.content = content
                post.put()
                self.render('alerts.html',
                            alert='Post has been updated.',
                            path='/%s' % post_id)


class DeletePost(BlogHandler):
    """ functions for deleting a post"""
    def get(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            post = db.get(db.Key.from_path('Post', int(post_id)))
            # if post does not belong to user, show alert.
            if post.username != username:
                self.render('alerts.html',
                            alert='Only the author can delete this post',
                            path='/%s' % post_id)
            else:
                post.delete()
                self.render('alerts.html',
                            alert='Post has been deleted',
                            path='/blog')


class LikePost(BlogHandler):
    """ functions for liking a post"""
    def get(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # get the post.
            post = db.get(db.Key.from_path('Post', int(post_id)))
            # if post belongs to user, show alert.
            if post.username == username:
                self.render('alerts.html',
                            alert='You cannot like your own post',
                            path='/%s' % post_id)
            else:
                already_like = Like.all().filter(
                                                 'username=', username).filter(
                                                 'post_id=', post_id).get()
                # if user hasn't liked the post, create like.
                if not already_like:
                    l = Like(username=username, post_id=post_id)
                    l.put()
                    self.render('alerts.html',
                                alert='Like added to post',
                                path='/%s' % post_id)
                # if user has already liked the post, show alert.
                else:
                    self.render('alerts.html',
                                alert='You can only like a post once',
                                path='/%s' % post_id)


class UnlikePost(BlogHandler):
    """ functions for unliking a post"""
    def get(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        # get like for given post and given user.
        else:
            l = Like.all().filter(
                                  'username=', username).filter(
                                  'post_id=', post_id).get()
            if not l:
                self.render('alerts.html',
                            alert='You have not liked this post',
                            path='/%s' % post_id)
            else:
                l.delete()
                self.render('alerts.html',
                            alert='Like removed from post',
                            path='/%s' % post_id)


class AddComment(BlogHandler):
    """ funcitons for adding a comment to a post"""
    def get(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            self.render('new-comment.html', username=username, post_id=post_id)

    def post(self, post_id):
        # check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # get contents of comment form.
            content = self.request.get("content")
            # if comment content is empty, show alert.
            if not content:
                error = "No comment content. Please try again"
                self.render("new-comment.html",
                            error=error,
                            username=username,
                            post_id=post_id)
            # if comment form is filled in, create comment.
            else:
                c = Comment(username=username,
                            post_id=post_id,
                            content=content)
                c.put()
                self.render('alerts.html',
                            alert="Comment successfully added to post",
                            path='/%s' % post_id)


class EditComment(BlogHandler):
    """ functions for editing a post"""
    def get(self, comment_id):
        # check if logged in an get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            comment = db.get(db.Key.from_path('Comment', int(comment_id)))

            # If comment does not exist, show alert.
            if not comment:
                self.render('alerts.html',
                            alert='Comment does not exist',
                            path='/blog')
            # If comment does not belong to user, show alert.
            elif comment.username != username:
                self.render('alerts.html',
                            alert='Only the author can edit this comment',
                            path='/%s' % comment.post_id)
            else:
                self.render('/edit-comment.html',
                            content=comment.content,
                            post_id=comment.post_id,
                            username=username)

    def post(self, comment_id):
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            # Get form contents.
            content = self.request.get("content")

            # Get the comment.
            comment = db.get(db.Key.from_path('Comment', int(comment_id)))

            if not content:
                error = "No comment content. Please try again."
                self.render("edit-comment.html", content=content, error=error)
            elif username != comment.username:
                error = "Only the author can edit this comment"
                self.render("edit-comment.html", content=content, error=error)
            else:
                comment.content = content
                comment.put()
                self.render('alerts.html',
                            alert='Comment has been successfully updated',
                            path='/%s' % comment.post_id)


class DeleteComment(BlogHandler):
    """ functions for deleting a post"""
    def get(self, comment_id):
        # Check if logged in and get username.
        username = self.check_login(self.request.cookies.get('user_id'))
        if not username:
            self.redirect('/login')
        else:
            comment = db.get(db.Key.from_path('Comment', int(comment_id)))
            if not comment:
                self.render('alerts.html',
                            alert='Comment does not exist',
                            path='/blog')
            # If comment does not belong to user, show alert.
            elif comment.username != username:
                self.render('alerts.html',
                            alert='Only the author can delete this comment',
                            path='/%s' % comment.post_id)
            else:
                comment.delete()
                self.render('alerts.html',
                            alert='Comment has been deleted',
                            path='/%s' % comment.post_id)


class Register(BlogHandler):
    """ functions for handling user sign up"""
    def get(self):
        self.render("signup.html")

    def post(self):
        # validate sign up form input
        username = self.request.get('username')
        username_match = self.valid_username(username)
        username_error = ""
        if not username or not username_match:
            username_error = "That's not a valid username."
        userNameExists = db.GqlQuery(
                                     "SELECT * FROM User WHERE username = :1",
                                     username).get()
        if userNameExists:
            username_error = "That username is already in use."
        password = self.request.get('password')
        password_match = self.valid_password(password)
        password_error = ""
        if not password or not password_match:
            password_error = "That wasn't a valid password"
        verify = self.request.get('verify')
        verify_match = password == verify
        verify_error = ""
        if not verify or not verify_match:
            verify_error = "Your passwords didn't match"
        email = self.request.get('email')
        email_match = self.valid_email(email)
        email_error = ""
        if email and not email_match:
            email_error = "That's not a valid email"

        if (username_error == "" and password_error == "" and
                verify_error == "" and email_error == ""):

            # if form passes validation create new User in datastore
            u = User(username=username,
                     password=self.make_pw_hash(username, password),
                     email=email)

            # store User in datastore
            u.put()
            # set secure cookie and redirect to welcome page
            self.login(u)
            self.redirect('/blog')
        else:
            # if form is invalid re-render signup form
            self.render('signup.html',
                        username=username,
                        email=email,
                        username_error=username_error,
                        password_error=password_error,
                        verify_error=verify_error,
                        email_error=email_error)


class Login(BlogHandler):
    """ functions for rendering the login page"""
    def get(self):
        self.render('login.html')

    def post(self):
        # get login form contents.
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            user = db.GqlQuery('SELECT * FROM User WHERE username= :1',
                               username).get()
            if user:
                user_pw = user.password
                user_pw_salt = user_pw.split('|')[1]
                pw_hash = self.make_pw_hash(username, password, user_pw_salt)

                # if datastore pw hash matches form pw hash set user_id cookie.
                if user_pw == pw_hash:
                    self.login(user)
                    self.redirect('/blog')
                else:
                    self.render('/login.html', login_error="Invalid login")
            else:
                self.render('/login.html', login_error="User does not exist")
        else:
            self.render('/login.html',
                        login_error="Username and password required")


class Logout(BlogHandler):
    """ functions for logging a user out"""
    def get(self):
        # clear the user_id cookie.
        self.logout()
        self.redirect('/login')

app = webapp2.WSGIApplication([('/', Login),
                              ('/signup', Register),
                              ('/login', Login),
                              ('/logout', Logout),
                              ('/blog', Blog),
                              ('/newpost', NewPost),
                              ('/([0-9]+)', PostPage),
                              ('/edit/([0-9]+)', EditPost),
                              ('/delete/([0-9]+)', DeletePost),
                              ('/like/([0-9]+)', LikePost),
                              ('/unlike/([0-9]+)', UnlikePost),
                              ('/comment/new/([0-9]+)', AddComment),
                              ('/comment/edit/([0-9]+)', EditComment),
                              ('/comment/delete/([0-9]+)', DeleteComment)
                               ],
                              debug=True)

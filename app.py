from datetime import datetime
import os
import re
from secrets import token_urlsafe
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from models import *

app = Flask(__name__)
# app.secret_key = token_urlsafe(32)
app.secret_key = os.environ.get("SECRET_KEY", "safe-for-committing")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DEBUG = os.environ.get("PRODUCTION", False) is False

Base = declarative_base()
user = os.environ.get("DB_USER", "postgres")
host = os.environ.get("DB_HOST", "127.0.0.1")
port = os.environ.get("DB_PORT", "5432")
sslmode = "require" if os.environ.get("PRODUCTION", False) else None
password = os.environ.get("DB_PASSWORD", "P7COFca3DBgu3j")

engine = create_engine( 
	f"postgresql://{user}:{password}@{host}:{port}/beginnerpy",
	connect_args = {
		"sslmode": sslmode
	}
)

Session = sessionmaker(bind=engine)

csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
	s = Session()
	u = s.query(Useraccount).get(int(user_id))
	user = u
	s.close()
	return user


class RegistrationForm(FlaskForm):
	email = StringField('Email',
		validators=[DataRequired(), Email()])
	displayname = StringField('Display Name',
		validators=[DataRequired()])
	password = PasswordField('Password',
		validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password',
		validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Register')

	def validate_email(self, email):
		session = Session()
		user = session.query(Useraccount).filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one.')
		session.close()


class LoginForm(FlaskForm):
	email = StringField('Email',
		validators=[DataRequired(), Email()])
	password = PasswordField('Password',
		validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


@app.route('/register', methods=['POST', 'GET'])
def register():
	session = Session()
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_pw = generate_password_hash(form.password.data).decode("utf-8")
		user = Useraccount(
			email=form.email.data,
			password=hashed_pw,
			displayname=form.displayname.data
		)
		session.add(user)
		session.commit()
		flash(f"Your registration for {form.email.data} was successful!", "success")
		session.close()
		return redirect(url_for("login"))
	session.close()
	context = {
		"form": form,
		"sidenav": getSideNav(),
		"property": "front",
		"endpoint": "register"
	}
	return render_template("register.html", **context)


@app.route('/login', methods=['POST', 'GET'])
def login():
	session = Session()
	form = LoginForm()
	if form.validate_on_submit():
		user = session.query(Useraccount).filter_by(email=form.email.data).first()
		if user and check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			user.last_login = datetime.now()
			session.commit()
			session.close()
			return redirect(url_for("admin"))
		else:
			flash("Your email or password doesn't match.", "danger")
	session.close()
	context = {
		"form": form,
		"sidenav": getSideNav(),
		"property": "front",
		"endpoint": "login"
	}
	return render_template("login.html", **context)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/', methods = ['POST', 'GET'])
def index():
	session = Session()
	latest = session.query(Article).filter_by(draft=0).order_by(desc(Article.date_created)).limit(20).all()
	session.close()
	context = {
		"sidenav": getSideNav(),
		"content": latest,
		"title": "Welcome to Beginner Python!",
		"endpoint": "/",
		"property": "front"
	}
	return render_template("index.html", **context)


@app.route('/module/<module_link>', methods = ['POST', 'GET'])
def module(module_link):
	session = Session()
	module = session.query(Module).filter_by(link=module_link).first()
	module.clickCount = module.clickCount + 1
	session.commit()
	articles = session.query(Article).filter_by(draft=0).join(articleModules).filter(articleModules.c.module_id==module.id).order_by(Article.date_created)
	session.close()
	context = {
		"sidenav": getSideNav(),
		"title": f"{module.title}",
		"content": articles,
		"endpoint": "module",
		"property": "front"
	}
	return render_template("index.html", **context)


@app.route('/tag/<tag_link>', methods = ['POST', 'GET'])
def tag(tag_link):
	session = Session()
	tag = session.query(Tag).filter_by(link=tag_link).first()
	tag.clickCount = tag.clickCount + 1
	session.commit()
	articles = session.query(Article).filter_by(draft=0).join(articleTags).filter(articleTags.c.tag_id==tag.id).order_by(Article.date_created)
	session.close()
	context = {
		"sidenav": getSideNav(),
		"content": articles,
		"title": f"{tag.title}",
		"endpoint": "tag",
		"property": "front"
	}
	return render_template("index.html", **context)


# Displays the category homepage to the user
@app.route('/category/<category_link>')
def category(category_link):
	sidenav = getSideNav()
	cat = [item for item in sidenav if item['link'] == category_link][0]
	session = Session()
	if cat['active'] == False:
		return redirect(url_for('index'))
	else:
		category = session.query(Category).filter_by(id=int(cat["id"])).first()
		category.viewCount = category.viewCount + 1
		session.commit()
		items = session.query(Article).filter_by(draft=0, category_id=int(cat["id"]))
	session.close()
	context = {
		"cat_id": cat["id"],
		"sidenav": sidenav,
		"articles": items,
		"endpoint": cat['name'],
		"property": "front"
	}
	return render_template("category.html", **context)


# Displays an article to the user
@app.route('/<category>/<link>')
def page(category, link):
	session = Session()
	article = session.query(Article).filter_by(link=link).first()
	article.viewCount = article.viewCount + 1
	session.commit()
	session.close()

	sidenav = getSideNav()

	session = Session()
	article = session.query(Article).filter_by(link=link).first()
	session.close()
	# We have to insert a <code> tag into the page inside every <pre></pre> tag to make the code highlighting work
	try:
		x = article.content
		parts = re.split('<pre>|</pre>', x)
		ispre = x.endswith("</pre>")
		end = len(parts)
		if end > 1:
			x = ""
			for i in range(0, end):
				x += parts[i]
				if i < end - 1:
					if i % 2 == 0:
						x += "<pre><code class='language-python'>"
					else:
						x += "</code></pre>"
		article.content = x
		if article.summary:
			x = article.summary
			parts = re.split('<pre>|</pre>', x)
			ispre = x.endswith("</pre>")
			end = len(parts)
			if end > 1:
				x = ""
				for i in range(0, end):
					x += parts[i]
					if i < end - 1:
						if i % 2 == 0:
							x += "<pre><code class='language-python'>"
						else:
							x += "</code></pre>"
			article.summary = x
	except ValueError:
		pass
	context = {
		"sidenav": sidenav,
		"article": article,
		"endpoint": "article_view",
		"property": "front"
	}
	return render_template("page.html", **context)


# Main admin page, displays all the data we collect and create throughout the site
@app.route('/admin')
@login_required
def admin():
	context = {
		"sidenav": getSideNav(),
		"endpoint": "admin",
		"property": "admin"
	}
	return render_template("admin/admin.html", **context)


# Lists out the categories
@app.route('/admin/categories')
@login_required
def admin_categories():
	sidenav = getSideNav()
	session = Session()
	items = session.query(Category).order_by(Category.name)
	session.close()
	context = {
		"sidenav": sidenav,
		"categories": items,
		"endpoint": "categories",
		"property": "admin"
	}
	return render_template("admin/categories.html", **context)


# Lists out the articles from the specified category
@app.route('/admin/category/<category_link>')
@login_required
def admin_category(category_link):
	sidenav = getSideNav()
	cat = [item for item in sidenav if item['link'] == category_link][0]
	cid = cat["id"]
	session = Session()
	if cat['name'] == "Modules":
		items = session.query(Module)
	elif cat['name'] == "Tags":
		items = session.query(Tag)
	else:
		items = session.query(Article).filter_by(category_id=int(cid)).order_by(desc(Article.id))
		draft = session.query(Article).filter_by(category_id=int(cid), draft=1).count()
		live = session.query(Article).filter_by(category_id=int(cid), draft=0).count()
	session.close()
	context = {
		"category": cat,
		"sidenav": sidenav,
		"articles": items,
		"property": "admin"
	}
	if cat['name'] != "Modules" and cat['name'] != "Tags":
		context['draft'] = draft
		context['live'] = live
	return render_template("admin/category.html", **context)


# Loads an empty creator page to write content
@app.route('/admin/create/<category_id>', methods=["POST", "GET"])
@login_required
def create_content(category_id):
	cid = int(category_id)
	session = Session()
	sidenav = getSideNav()
	cat = [item for item in sidenav if item['id'] == int(category_id)][0]
	tags = session.query(Tag)
	modules = session.query(Module)
	session.close()
	context = {
		"category": cat,
		"sidenav": sidenav,
		"tags": tags,
		"modules": modules,
		"endpoint": "create_"+cat['name'],
		"property": "admin"
	}
	return render_template("admin/create_content.html", **context)


# Loads an empty creator page to write content
@app.route('/admin/createcategory', methods=["POST", "GET"])
@login_required
def create_category():
	session = Session()
	sidenav = getSideNav()
	session.close()
	context = {
		"sidenav": sidenav,
		"endpoint": "createcategory",
		"property": "admin"
	}
	return render_template("admin/create_category.html", **context)


# Saves a new tag or a new module
@app.route('/admin/save_item', methods=["POST"])
@login_required
def save_item():
	item_type = request.form.get("type")
	item_name = request.form.get("name")
	item_title = request.form.get("title")
	item_link = request.form.get("link")
	session = Session()
	if item_type == "Tags":
		typelink = "tags"
		item = Tag(name = item_name, title = item_title, link = item_link)
	elif item_type == "Modules":
		typelink = "modules"
		item = Module(name = item_name, title = item_title, link = item_link)
	session.add(item)
	session.commit()
	session.close()
	flash(f"<strong>{item_name}</strong> {item_type[:-1].lower()} has been successfully added.", "success")
	return redirect(url_for('admin_category', category_link=typelink))


# Loads an existing article for editing
@app.route('/admin/edit/<link>')
@login_required
def edit(link):
	session = Session()
	tags = session.query(Tag)
	modules = session.query(Module)
	article = session.query(Article).filter_by(link=link).first()
	session.close()
	context = {
		"sidenav": getSideNav(),
		"tags": tags,
		"modules": modules,
		"article": article,
		"endpoint": "edit",
		"property": "admin"
	}
	return render_template("admin/edit_content.html", **context)


# Loads an existing article for editing
@app.route('/admin/edititem/<cat>/<link>')
@login_required
def edititem(cat, link):
	session = Session()
	if cat == "modules":
		item = session.query(Module).filter_by(link=link).first()
	elif cat == "tags":
		item = session.query(Tag).filter_by(link=link).first()
	session.close()
	context = {
		"sidenav": getSideNav(),
		"item": item,
		"category": cat,
		"endpoint": "edit",
		"property": "admin"
	}
	return render_template("admin/edit_item.html", **context)


# Loads an existing category for editing
@app.route('/admin/editcategory/<link>')
@login_required
def editcategory(link):
	session = Session()
	category = session.query(Category).filter_by(link=link).first()
	session.close()
	context = {
		"sidenav": getSideNav(),
		"tags": tags,
		"modules": modules,
		"category": category,
		"endpoint": "editcategory",
		"property": "admin"
	}
	return render_template("admin/edit_category.html", **context)


# Saves new categories and category updates
@app.route('/admin/save_category', methods=["POST"])
@login_required
def save_category():
	title = request.form.get("title")
	link = request.form.get("link")
	buttonlabel = request.form.get("buttonlabel")
	formtitle = request.form.get("formtitle")
	description = request.form.get("description")
	session = Session()
	category = session.query(Category).filter_by(link=link).first()
	# If the category exists, update it.
	if category:
		category.name = title
		category.link = link
		category.buttonlabel = buttonlabel
		category.formtitle = formtitle
		category.description = description if description not in [None, "None", "<p>None</p>", "<p><br></p>"] else None
		session.commit()
		session.close()
		flash(f"<strong>{title}</strong> category was successfully updated.", "success")
	# If the category doesn't exist, create it.
	else:
		category = Category(
			name = title,
			link = link,
			description = description,
			buttonlabel = buttonlabel,
			formtitle = formtitle
		)
		session.add(category)
		session.commit()
		session.close()
		flash(f"<strong>{title}</strong> category was successfully created.", "success")

	return redirect(url_for('admin_categories'))


# Deletes a category
@app.route('/admin/delete_category/<cid>', methods=["POST", "GET"])
@login_required
def delete_category(cid):
	session = Session()
	category = session.query(Category).filter_by(id=int(cid)).first()
	if not category.articles:
		session.delete(category)
		session.commit()
		flash(f"<strong>{category.name}</strong> category was successfully deleted.", "success")
	else:
		flash(f"<strong>{category.name}</strong> category has articles, it cannot be deleted.", "danger")
	session.close()
	
	return redirect(url_for('admin_categories'))


# Deletes an article
@app.route('/admin/delete_article/<category_link>/<article_id>', methods=["POST", "GET"])
@login_required
def delete_article(category_link, article_id):
	session = Session()
	article = session.query(Article).filter_by(id=int(article_id)).first()
	if article:
		session.execute(articleTags.delete().where(articleTags.c.article_id==article.id))
		session.execute(articleModules.delete().where(articleModules.c.article_id==article.id))
		session.commit()
		session.delete(article)
		session.commit()
		session.close()

	return redirect(url_for('admin_category', category_link=category_link))


# Deletes a tag or a module
@app.route('/admin/delete_item/<category_link>/<item_id>', methods=["POST", "GET"])
@login_required
def delete_item(category_link, item_id):
	session = Session()
	if category_link == "modules":
		item = session.query(Module).filter_by(id=int(item_id)).first()
	elif category_link == "tags":
		item = session.query(Tag).filter_by(id=int(item_id)).first()
	if item:
		session.execute(articleTags.delete().where(articleTags.c.tag_id==item.id))
		session.execute(articleModules.delete().where(articleModules.c.module_id==item.id))
		session.commit()
		session.delete(item)
		session.commit()
		session.close()
		flash(f"<strong>{item.name}</strong> has been removed from {category_link}.", "success")
	else:
		flash(f"An item with the id <strong>{item_id}</strong> in <strong>{category_link}</strong> wasn't found in the database.", "danger")

	return redirect(url_for('admin_category', category_link=category_link))


# Saves any other type of new content except tag or module
@app.route('/admin/save_article', methods=["POST"])
@login_required
def save_article():
	title = request.form.get("title")
	link = request.form.get("link")
	content = request.form.get("content")
	summary = request.form.get("summary")
	modules = []
	tags = []
	session = Session()

	moduleslist = session.query(Module)
	counter = 0
	while counter < moduleslist.count():
		counter += 1
		if request.form.get(f"module_{counter}") == "on":
			modules.append(counter)
	tagslist = session.query(Tag)
	counter = 0
	while counter < tagslist.count():
		counter += 1
		if request.form.get(f"tag_{counter}") == "on":
			tags.append(counter)

	category = request.form.get("cat_id")
	cat_link = request.form.get("cat_link")
	draft = request.form.get("draft")
	if not draft:
		draft = 1
	else:
		draft = 0
	
	article = session.query(Article).filter_by(link=link).first()
	# If the article exists, update it.
	if article:
		article.title = title
		urlsafe = link[-7:]
		article.link = title.replace(" ", "-").replace("()", "").lower() + "-" + urlsafe
		article.content = content
		article.summary = summary
		article.draft = draft
		article.last_modified = datetime.now()

		session.execute(articleTags.delete().where(articleTags.c.article_id==article.id))
		session.execute(articleModules.delete().where(articleModules.c.article_id==article.id))
		session.commit()

		for item in tags:
			session.execute(articleTags.insert().values(article_id=article.id, tag_id=item))
		for item in modules:
			session.execute(articleModules.insert().values(article_id=article.id, module_id=item))

		session.commit()
		session.close()
		flash(f"The article <strong>{title}</strong> was successfully updated.", "success")
	else:
		link = title.replace(" ", "-").lower() + "-" + token_urlsafe(5)
		article = Article(
			title = title,
			author_id = current_user.id,
			link = link,
			content = content,
			summary = summary,
			category_id = int(category),
			draft = int(draft),
			author = current_user,
			date_created = datetime.now()
		)
		session.add(article)
		session.commit()
		article = session.query(Article).filter_by(link=link).first()
		for item in tags:
			session.execute(articleTags.insert().values(article_id=article.id, tag_id=item))
		for item in modules:
			session.execute(articleModules.insert().values(article_id=article.id, module_id=item))
		session.commit()
		session.close()
		flash(f"The article <strong>{title}</strong> was successfully created.", "success")
	return redirect( url_for('admin_category', category_link=cat_link) )


# Returns the sidebar navigation elements in alphabetical order
def getSideNav():
	session = Session()
	nav_src = session.query(Category)
	nav = []
	for item in nav_src:
		nav.append({"id": item.id, "name": item.name, "link": item.link, "active": item.active, "viewCount": item.viewCount, "formtitle": item.formtitle, "buttonlabel": item.buttonlabel})
	nav = sorted(nav, key=lambda x: x['name'])
	session.close()
	return nav


# Allows to activate or inactivate a sidemenu category so they become visible or hidden to users
# They remain visible in admin either way
@app.route("/admin/toggle_active")
@login_required
def toggle_active():
	active = request.args.get("active")
	if active == 'True':
		active = False
	elif active == 'False':
		active = True
	cat = int(request.args.get("cat"))
	session = Session()
	category = session.query(Category).filter_by(id=cat).first()
	category.active = active
	link = category.link
	session.commit()
	session.close()
	return redirect(url_for('admin_category', category_link=link))


@app.route("/admin/users")
@login_required
def users():
	session = Session()
	userlist = session.query(Useraccount)
	session.close()
	context = {
		"sidenav": getSideNav(),
		"users": userlist,
		"endpoint": "edit",
		"property": "admin"
	}
	return render_template("admin/users.html", **context)


@app.route("/admin/build")
def build_db():
    if not engine.table_names():
        session = Session()
        build(engine, session)
    return redirect(url_for('admin'))



if __name__ == "__main__":
	app.run(debug=DEBUG)

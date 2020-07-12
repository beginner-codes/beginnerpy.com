from datetime import datetime
import os
import re
import psycopg2
import pickle
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from beginnerpy.models import *
from beginnerpy.func import getSideNav
from beginnerpy.bot.challenges import challenges_blueprint
from beginnerpy.bot.rules import rules_blueprint

app = Flask(__name__)
app.register_blueprint(challenges_blueprint)
app.register_blueprint(rules_blueprint)

app.secret_key = os.environ.get("SECRET_KEY", "safe-for-committing")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
DEBUG = os.environ.get("PRODUCTION", False) is False

Base = declarative_base()
dbname = os.environ.get("DB_NAME", "bpydb")
user = os.environ.get("DB_USER", "postgresadmin")
host = os.environ.get("DB_HOST", "0.0.0.0")
port = os.environ.get("DB_PORT", "5432")
sslmode = "require" if os.environ.get("PRODUCTION", False) else None
password = os.environ.get("DB_PASSWORD", "dev-env-password-safe-to-be-public")

engine = create_engine(
    f"postgresql://{user}:{password}@{host}:{port}/{dbname}",
    connect_args={"sslmode": sslmode},
)

Session = sessionmaker(bind=engine)

csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    s = Session()
    u = s.query(Useraccount).get(int(user_id))
    user = u
    s.close()
    return user


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    displayname = StringField("Display Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        session = Session()
        user = session.query(Useraccount).filter_by(email=email.data).first()
        session.close()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


@app.route("/challenges/pip-version")
def challenge_version():
    session = Session()
    row = session.query(Settings).filter_by(name="PIP_CHALLENGE_VERSION").first()
    version = pickle.loads(row.value.encode())
    return f'{{"version": "{version}"}}', 200, {"content-type": "application/json"}


@app.route("/register", methods=["POST", "GET"])
def register():
    if os.environ.get("PRODUCTION", "DEV") != "DEV":
        return redirect(url_for("admin"))

    session = Session()
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data).decode("utf-8")
        user = Useraccount(
            email=form.email.data, password=hashed_pw, displayname=form.displayname.data
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
        "endpoint": "register",
    }
    return render_template("register.html", **context)


@app.route("/login", methods=["POST", "GET"])
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
        "endpoint": "login",
    }
    return render_template("login.html", **context)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/", methods=["POST", "GET"])
def index():
    session = Session()
    latest = (
        session.query(Article)
        .filter_by(draft=0)
        .order_by(desc(Article.date_created))
        .limit(20)
        .all()
    )
    session.close()
    context = {
        "sidenav": getSideNav(),
        "content": latest,
        "title": "Welcome to Beginner Python!",
        "endpoint": "/",
        "property": "front",
    }
    return render_template("index.html", **context)


@app.route("/module/<module_link>", methods=["POST", "GET"])
def module(module_link):
    session = Session()
    module = session.query(Module).filter_by(link=module_link).first()
    module.clickCount = module.clickCount + 1
    session.commit()
    articles = (
        session.query(Article)
        .filter_by(draft=0)
        .join(articleModules)
        .filter(articleModules.c.module_id == module.id)
        .order_by(Article.date_created)
    )
    session.close()
    context = {
        "sidenav": getSideNav(),
        "title": f"{module.title}",
        "content": articles,
        "endpoint": "module",
        "property": "front",
    }
    return render_template("index.html", **context)


@app.route("/tag/<tag_link>", methods=["POST", "GET"])
def tag(tag_link):
    session = Session()
    tag = session.query(Tag).filter_by(link=tag_link).first()
    tag.clickCount = tag.clickCount + 1
    session.commit()
    articles = (
        session.query(Article)
        .filter_by(draft=0)
        .join(articleTags)
        .filter(articleTags.c.tag_id == tag.id)
        .order_by(Article.date_created)
    )
    session.close()
    context = {
        "sidenav": getSideNav(),
        "content": articles,
        "title": f"{tag.title}",
        "endpoint": "tag",
        "property": "front",
    }
    return render_template("index.html", **context)


# Displays the category homepage to the user
@app.route("/category/<category_link>")
def category(category_link):
    sidenav = getSideNav()
    cat = [item for item in sidenav if item["link"] == category_link][0]
    session = Session()
    if cat["active"] == False:
        session.close()
        return redirect(url_for("index"))
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
        "endpoint": cat["name"],
        "property": "front",
    }
    return render_template("category.html", **context)


# Displays an article to the user
@app.route("/<category>/<link>")
@app.route("/<category>/<module>/<link>")
def page(category, link, module=None):
    session = Session()
    if module:
        article = session.query(Article).filter_by(link=module + "/" + link).first()
    else:
        article = session.query(Article).filter_by(link=link).first()
    article.viewCount = article.viewCount + 1
    session.commit()
    session.close()

    sidenav = getSideNav()

    session = Session()
    if module:
        article = session.query(Article).filter_by(link=module + "/" + link).first()
    else:
        article = session.query(Article).filter_by(link=link).first()
    session.close()

    # Some unnecessary elements the editor places into the html structure needfixing
    article.content = article.content.replace(' contenteditable="true"', "")
    article.content = article.content.replace("ck ck-widget__selection-handle", "hide")
    article.summary = article.summary.replace(' contenteditable="true"', "")
    article.summary = article.summary.replace("ck ck-widget__selection-handle", "hide")

    # Fix removed <br> tags in code blocks by replacing them with \n
    article.summary = replaceBr(article.summary)
    article.content = replaceBr(article.content)

    if (current_user.is_authenticated and current_user.is_admin) or article.draft == 0:
        context = {
            "sidenav": sidenav,
            "article": article,
            "endpoint": "article_view",
            "property": "front",
        }
        return render_template("page.html", **context)

    return redirect(url_for("index"))


def replaceBr(string):
    summ = re.findall(r"<code|</code>|.+?(?=<code|</code>|$)", string)
    insidePre = False
    for item in summ:
        if insidePre:
            summ[summ.index(item)] = item.replace("<br>", "\n")
        if item == "<code":
            insidePre = True
        else:
            insidePre = False
    string = "".join(summ)
    return string


# Main admin page, displays all the data we collect and create throughout the site
@app.route("/admin")
@login_required
def admin():
    context = {"sidenav": getSideNav(), "endpoint": "admin", "property": "admin"}
    return render_template("admin/admin.html", **context)


@app.route("/admin/db/<id>")
@login_required
def admin_db(id):
    if current_user.is_authenticated and current_user.is_admin:
        sidenav = getSideNav()
        session = Session()
        item = session.query(Article).filter_by(id=int(id)).first()
        print(item.title, item.content, item.summary)
        session.close()
        context = {
            "sidenav": sidenav,
            "article": item,
            "endpoint": "db",
            "property": "admin",
        }
        return render_template("admin/db.html", **context)

    return redirect(url_for("index"))


# Lists out the categories
@app.route("/admin/categories")
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
        "property": "admin",
    }
    return render_template("admin/categories.html", **context)


# Lists out the articles from the specified category
@app.route("/admin/category/<category_link>")
@login_required
def admin_category(category_link):
    sidenav = getSideNav()
    try:
        cat = [item for item in sidenav if item["link"] == category_link][0]
    except IndexError:
        cat = [item for item in sidenav if item["title"] == category_link][0]
    cid = cat["id"]
    session = Session()
    if cat["name"] == "Modules":
        items = session.query(Module).order_by(Module.name)
    elif cat["name"] == "Tags":
        items = session.query(Tag).order_by(Tag.name)
    elif category_link == "messages":
        items = session.query(Message).order_by(Message.title)
    else:
        items = (
            session.query(Article)
            .filter_by(category_id=int(cid))
            .order_by(desc(Article.id))
        )
        draft = session.query(Article).filter_by(category_id=int(cid), draft=1).count()
        live = session.query(Article).filter_by(category_id=int(cid), draft=0).count()
    session.close()
    context = {
        "category": cat,
        "sidenav": sidenav,
        "articles": items,
        "property": "admin",
    }
    if cat["name"] not in ["Modules", "Tags"] and category_link != "messages":
        context["draft"] = draft
        context["live"] = live
    return render_template("admin/category.html", **context)


# Loads an empty creator page to write content
@app.route("/admin/create/<category_id>", methods=["POST", "GET"])
@login_required
def create_content(category_id):
    cid = int(category_id)
    session = Session()
    sidenav = getSideNav()
    cat = [item for item in sidenav if item["id"] == int(category_id)][0]
    tags = session.query(Tag)
    modules = session.query(Module)
    session.close()
    context = {
        "category": cat,
        "sidenav": sidenav,
        "tags": tags,
        "modules": modules,
        "endpoint": "create_" + cat["name"],
        "property": "admin",
    }
    return render_template("admin/create_content.html", **context)


# Loads an empty creator page to write content
@app.route("/admin/createcategory", methods=["POST", "GET"])
@login_required
def create_category():
    sidenav = getSideNav()
    context = {"sidenav": sidenav, "endpoint": "createcategory", "property": "admin"}
    return render_template("admin/create_category.html", **context)


# Saves a new tag or module, or updates an existing one
@app.route("/admin/save_item", methods=["POST"])
@login_required
def save_item():
    item_type = request.form.get("type")
    item_name = request.form.get("name")
    item_title = request.form.get("title")
    item_link = request.form.get("link")
    session = Session()
    if item_type.lower() == "tags":
        tag = session.query(Tag).filter_by(link=item_link).first()
        if tag:
            print("Element exists.")
            tag.name = item_name
            tag.title = item_title
        else:
            item = Tag(name=item_name, title=item_title, link=item_link)
            session.add(item)
        session.commit()
        session.close()
        flash(
            f"<strong>{item_title}</strong> {item_type[:-1].lower()} has been successfully updated.",
            "success",
        )
    elif item_type.lower() == "modules":
        module = session.query(Module).filter_by(link=item_link).first()
        if module:
            print("Element exists.")
            module.name = item_name
            module.title = item_title
        else:
            item = Module(name=item_name, title=item_title, link=item_link)
            session.add(item)
        session.commit()
        session.close()
        flash(
            f"<strong>{item_title}</strong> {item_type[:-1].lower()} has been successfully added.",
            "success",
        )
    return redirect(url_for("admin_category", category_link=item_type.lower()))


# Loads an existing article for editing
@app.route("/admin/edit/<link>")
@app.route("/admin/edit/<module>/<link>")
@login_required
def edit(link, module=None):
    session = Session()
    tags = session.query(Tag)
    modules = session.query(Module)
    if module:
        article = session.query(Article).filter_by(link=module + "/" + link).first()
    else:
        article = session.query(Article).filter_by(link=link).first()
    print(article.link)
    article.summary = replaceBr(article.summary)
    article.content = replaceBr(article.content)
    session.close()
    context = {
        "sidenav": getSideNav(),
        "tags": tags,
        "modules": modules,
        "article": article,
        "endpoint": "edit",
        "property": "admin",
    }
    return render_template("admin/edit_content.html", **context)


# Loads an existing article for editing
@app.route("/admin/edititem/<cat>/<link>")
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
        "property": "admin",
    }
    return render_template("admin/edit_item.html", **context)


# Loads an existing category for editing
@app.route("/admin/editcategory/<link>")
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
        "property": "admin",
    }
    return render_template("admin/edit_category.html", **context)


# Saves new categories and category updates
@app.route("/admin/save_category", methods=["POST"])
@login_required
def save_category():
    title = request.form.get("title")
    link = request.form.get("link")
    buttonlabel = request.form.get("buttonlabel")
    formtitle = request.form.get("formtitle")
    description = request.form.get("description")
    bot = request.form.get("bot")
    if bot == "on":
        bot = 1
    else:
        bot = 0
    session = Session()
    category = session.query(Category).filter_by(link=link).first()
    # If the category exists, update it.
    if category:
        category.name = title
        category.link = link
        category.bot = bot
        category.buttonlabel = buttonlabel
        category.formtitle = formtitle
        category.description = (
            description
            if description not in [None, "None", "<p>None</p>", "<p><br></p>"]
            else None
        )
        session.commit()
        session.close()
        flash(f"<strong>{title}</strong> category was successfully updated.", "success")
    # If the category doesn't exist, create it.
    else:
        category = Category(
            name=title,
            link=link,
            bot=bot,
            description=description,
            buttonlabel=buttonlabel,
            formtitle=formtitle,
        )
        session.add(category)
        session.commit()
        session.close()
        flash(f"<strong>{title}</strong> category was successfully created.", "success")

    return redirect(url_for("admin_categories"))


# Deletes a category
@app.route("/admin/delete_category/<cid>", methods=["POST", "GET"])
@login_required
def delete_category(cid):
    session = Session()
    category = session.query(Category).filter_by(id=int(cid)).first()
    if not category.articles:
        session.delete(category)
        session.commit()
        flash(
            f"<strong>{category.name}</strong> category was successfully deleted.",
            "success",
        )
    else:
        flash(
            f"<strong>{category.name}</strong> category has articles, it cannot be deleted.",
            "danger",
        )
    session.close()

    return redirect(url_for("admin_categories"))


# Deletes an article
@app.route(
    "/admin/delete_article/<category_link>/<article_id>", methods=["POST", "GET"]
)
@login_required
def delete_article(category_link, article_id):
    session = Session()
    article = session.query(Article).filter_by(id=int(article_id)).first()
    if article:
        session.execute(
            articleTags.delete().where(articleTags.c.article_id == article.id)
        )
        session.execute(
            articleModules.delete().where(articleModules.c.article_id == article.id)
        )
        session.commit()
        session.delete(article)
        session.commit()

    session.close()

    return redirect(url_for("admin_category", category_link=category_link))


# Deletes a tag or a module
@app.route("/admin/delete_item/<category_link>/<item_id>", methods=["POST", "GET"])
@login_required
def delete_item(category_link, item_id):
    session = Session()
    if category_link == "modules":
        item = session.query(Module).filter_by(id=int(item_id)).first()
    elif category_link == "tags":
        item = session.query(Tag).filter_by(id=int(item_id)).first()
    if item:
        session.execute(articleTags.delete().where(articleTags.c.tag_id == item.id))
        session.execute(
            articleModules.delete().where(articleModules.c.module_id == item.id)
        )
        session.commit()
        session.delete(item)
        session.commit()
        flash(
            f"<strong>{item.name}</strong> has been removed from {category_link}.",
            "success",
        )
    else:
        flash(
            f"An item with the id <strong>{item_id}</strong> in <strong>{category_link}</strong> wasn't found in the database.",
            "danger",
        )
    session.close()

    return redirect(url_for("admin_category", category_link=category_link))


# Saves any other type of new content except tag or module
@app.route("/admin/save_article", methods=["POST"])
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
        if category == "9":
            modulename = ""
            for module in moduleslist:
                if module.id == int(modules[0]):
                    modulename = module.link
                    break
            article.link = (
                modulename
                + "/"
                + title.replace(" ", "-").replace("(", "").replace(")", "").lower()
            )
        else:
            article.link = (
                title.replace(" ", "-").replace("(", "").replace(")", "").lower()
            )
        article.content = content
        article.summary = summary
        if article.draft == 0 and draft == 1:
            article.date_created = datetime.now()
        article.draft = draft
        article.last_modified = datetime.now()

        session.execute(
            articleTags.delete().where(articleTags.c.article_id == article.id)
        )
        session.execute(
            articleModules.delete().where(articleModules.c.article_id == article.id)
        )
        session.commit()

        for item in tags:
            session.execute(
                articleTags.insert().values(article_id=article.id, tag_id=item)
            )
        for item in modules:
            session.execute(
                articleModules.insert().values(article_id=article.id, module_id=item)
            )

        flash(
            f"The article <strong>{title}</strong> was successfully updated.", "success"
        )
    else:
        if category == "9":
            modulename = ""
            for module in moduleslist:
                if module.id == int(modules[0]):
                    modulename = module.link
                    break
            link = (
                modulename
                + "/"
                + title.replace(" ", "-").replace("(", "").replace(")", "").lower()
            )
        else:
            link = title.replace(" ", "-").replace("(", "").replace(")", "").lower()
        article = Article(
            title=title,
            author_id=current_user.id,
            link=link,
            content=content,
            summary=summary,
            category_id=int(category),
            draft=int(draft),
            author=current_user,
            date_created=datetime.now(),
        )
        session.add(article)
        session.commit()
        article = session.query(Article).filter_by(link=link).first()
        for item in tags:
            session.execute(
                articleTags.insert().values(article_id=article.id, tag_id=item)
            )
        for item in modules:
            session.execute(
                articleModules.insert().values(article_id=article.id, module_id=item)
            )

        flash(
            f"The article <strong>{title}</strong> was successfully created.", "success"
        )
    session.commit()
    session.close()
    return redirect(url_for("admin_category", category_link=cat_link))


# Allows to activate or inactivate a sidemenu category so they become visible or hidden to users
# They remain visible in admin either way
@app.route("/admin/toggle_active")
@login_required
def toggle_active():
    active = request.args.get("active")
    if active == "True":
        active = False
    elif active == "False":
        active = True
    cat = int(request.args.get("cat"))
    session = Session()
    category = session.query(Category).filter_by(id=cat).first()
    category.active = active
    link = category.link
    session.commit()
    session.close()
    return redirect(url_for("admin_category", category_link=link))


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
        "property": "admin",
    }
    return render_template("admin/users.html", **context)


@app.route("/admin/build")
def build_db():
    tables = {
        "useraccount",
        "article",
        "category",
        "articleTags",
        "module",
        "tag",
        "articleModules",
    }
    if not tables.issubset(engine.table_names()):
        session = Session()
        build(engine, session)
        session.close()

    with engine.connect() as connection:
        connection.execute(
            "ALTER TABLE category ADD COLUMN IF NOT EXISTS bot INTEGER NOT NULL DEFAULT 0;"
        )

        connection.execute(
            "CREATE TABLE IF NOT EXISTS message (id serial PRIMARY KEY, message_type varchar(20) NOT NULL, message varchar(2000) NOT NULL, title varchar(200) NOT NULL, label varchar(100) NOT NULL, author varchar(100) NOT NULL);"
        )

    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=DEBUG)

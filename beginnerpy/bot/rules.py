from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from beginnerpy.models import *
from beginnerpy.func import getSideNav
from flask_login import login_required

dbname = os.environ.get("DB_NAME", "beginnerpy")
user = os.environ.get("DB_USER", "postgres")
host = os.environ.get("DB_HOST", "127.0.0.1")
port = os.environ.get("DB_PORT", "5432")
sslmode = "require" if os.environ.get("PRODUCTION", False) else None
password = os.environ.get("DB_PASSWORD", "P7COFca3DBgu3j")

engine = create_engine(
	f"postgresql://{user}:{password}@{host}:{port}/{dbname}",
	connect_args={"sslmode": sslmode},
)

Session = sessionmaker(bind=engine)

static_folder = "../static/bot"
template_folder = "../templates/bot"
rules_blueprint = Blueprint(
	"rules",
	__name__,
	static_folder=str(static_folder),
	static_url_path="/static/bot",
	template_folder=str(template_folder),
	url_prefix="/admin/bot",
)


@rules_blueprint.route("/rules")
def rules():
	context = {
		"sidenav": getSideNav(),
		"endpoint": "rules",
		"property": "admin",
	}
	return render_template("rule_list.html", **context)


@rules_blueprint.route("/edit_rule/<rule_title>")
def edit_rule(rule_title):
	print(rule_title)
	session = Session()
	item = session.query(Message).filter_by(title=rule_title).first()
	session.close()
	context = {
		"sidenav": getSideNav(),
		"item": item,
		"category": "rules",
		"endpoint": "edit",
		"property": "admin",
	}
	return render_template("edit_rule.html", **context)


# Saves a new rule or updates an existing one
@rules_blueprint.route("/save_rule", methods=["POST"])
@login_required
def save_rule():
	item_type = request.form.get("message_type")
	item_title = request.form.get("title")
	previous_title = request.form.get("previous_title")
	item_author = request.form.get("author")
	item_labels = request.form.get("label")
	item_message = request.form.get("message")
	session = Session()
	msg = session.query(Message).filter_by(title=previous_title).first()
	if msg:
		msg.message_type = item_type
		msg.title = item_title
		msg.author = item_author
		msg.label = item_labels
		msg.message = item_message
		flash(f"<strong>{item_title}</strong> rule has been successfully updated.", "success")
	else:
		item = Message(
			message_type = item_type,
			title = item_title,
			author = item_author,
			label = item_labels,
			message = item_message
		)
		session.add(item)
		flash(f"<strong>{item_title}</strong> rule has been successfully created.", "success")
	session.commit()
	session.close()
	return redirect(url_for("admin_category", category_link="messages"))


# Deletes a tag or a module
@rules_blueprint.route("/delete_rule/<item_title>", methods=["POST", "GET"])
@login_required
def delete_rule(item_title):
	session = Session()
	item = session.query(Message).filter_by(title=item_title).first()
	if item:
		session.delete(item)
		session.commit()
		flash(f"<strong>{item.title}</strong> has been removed from Rules.", "success")
	else:
		flash(f"A rule with the title <strong>{item_title}</strong> wasn't found in the database.", "danger")
	session.close()

	return redirect(url_for("admin_category", category_link="messages"))
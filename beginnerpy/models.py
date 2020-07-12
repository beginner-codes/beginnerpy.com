from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, BIGINT, String, Boolean, ForeignKey, Table, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os

Base = declarative_base()

categories = [
    {"name": "Articles", "link": "articles", "active": True, "buttonlabel": "Article", "formtitle": "New Article"},									# explanatios of things, interesting stuff, new info about something relevant
    {"name": "Bite Sized Projects", "link": "mini-projects", "active": True, "buttonlabel": "Project", "formtitle": "New Bite Sized Project"},		# small projects that can be done in 1-2 hours
    {"name": "Blender 3D", "link": "blender", "active": False, "buttonlabel": "Blender Article", "formtitle": "New Blender Article"},				# python code done in Blender 3D
    {"name": "Coding Help", "link": "coding-help", "active": True, "buttonlabel": "Coding Help", "formtitle": "New Coding Help"},					# questions like what people ask on beginner.py, and their answers
    {"name": "Errors", "link": "errors", "active": True, "buttonlabel": "Error", "formtitle": "New Error"},											# explanation of common cases when an error happens, and how to fix them
    {"name": "Glossary", "link": "glossary", "active": True, "buttonlabel": "Item", "formtitle": "New Glossary Item"},								# concepts and terms, and their definitions
    {"name": "Modules", "link": "modules", "active": False, "buttonlabel": "Module", "formtitle": "New Module"},
    {"name": "Practices", "link": "practices", "active": False, "buttonlabel": "Practice", "formtitle": "New Practice"},							# example codes and descriptions to practice certain concepts or syntax elements
    {"name": "Python Syntax", "link": "python-syntax", "active": True, "buttonlabel": "Syntax Element", "formtitle": "New Python Syntax Element"},	# python syntax elements' explanation and code examples
    {"name": "Raspberry Pi", "link": "raspi", "active": True, "buttonlabel": "RasPi Project", "formtitle": "New RasPi Project"},					# raspberry pi projects done with python code
    {"name": "Tags", "link": "tags", "active": False, "buttonlabel": "Tag", "formtitle": "New Tag"},
    {"name": "Tutorials", "link": "tutorials", "active": False, "buttonlabel": "Tutorial", "formtitle": "New Tutorial"},							# longer, more complex projects
]

tags = [
    {"name": "binaries", "title": "Binaries", "link": "binaries"},
    {"name": "booleans", "title": "Booleans", "link": "booleans"},
    {"name": "concepts", "title": "Concepts", "link": "concepts"},
    {"name": "functional programming", "title": "Functional Programming", "link": "functionalprogramming"},
    {"name": "functions", "title": "Functions", "link": "functions"},
    {"name": "iterables", "title": "Iterables", "link": "iterables"},
    {"name": "keywords", "title": "Keywords", "link": "keywords"},
    {"name": "loops", "title": "Loops", "link": "loops"},
    {"name": "mapping", "title": "Mapping", "link": "mapping"},
    {"name": "numbers", "title": "Numbers", "link": "numbers"},
    {"name": "OOP", "title": "Object Oriented Programming", "link": "oop"},
    {"name": "operators", "title": "Operators", "link": "operators"},
    {"name": "sets", "title": "Sets", "link": "sets"},
    {"name": "sequences", "title": "Sequences", "link": "sequences"},
    {"name": "strings", "title": "Strings", "link": "strings"},
    {"name": "data types", "title": "Data Types", "link": "datatypes"}
]

modules = [
    {"name": "python core", "title": "Python Core", "link": "core"},
    {"name": "discord.py", "title": "Discord.py Module", "link": "discord"}
]


# Quotes and Topics
articleTags = Table("articleTags", Base.metadata,
    Column("article_id", Integer, ForeignKey("article.id")),
    Column("tag_id", Integer, ForeignKey("tag.id"))
)


# Quotes and Topics
articleModules = Table("articleModules", Base.metadata,
    Column("article_id", Integer, ForeignKey("article.id")),
    Column("module_id", Integer, ForeignKey("module.id"))
)


class Useraccount(Base, UserMixin):
    __tablename__ = "useraccount"

    id = Column(Integer, primary_key=True)
    displayname = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    image_file = Column(String(20), nullable=False, default='default.jpg')
    description = Column(Text)
    is_admin = Column(Boolean, default=True)
    discord_id = Column(BIGINT, index=True)
    last_login = Column(DateTime(), index=True)


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(50), unique=True, nullable=False)
    link = Column(String(50), unique=True, nullable=False)
    clickCount = Column(Integer, default=0)
    articleCount = Column(Integer, default=0)


class Module(Base):
    __tablename__ = "module"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(50), unique=True, nullable=False)
    link = Column(String(50), unique=True, nullable=False)
    clickCount = Column(Integer, default=0)
    articleCount = Column(Integer, default=0)


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False, index=True)
    link = Column(String(50), unique=True, nullable=False)
    bot = Column(Integer, nullable = False, default = 0)
    formtitle = Column(String(50), nullable=False)
    buttonlabel = Column(String(50), nullable=False)
    description = Column(String(), default=None)
    active = Column(Boolean, default=False)
    viewCount = Column(Integer, default=0)


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False, index=True)
    link = Column(String(150), unique=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    draft = Column(Integer, nullable=False, default=1, index=True)
    author_id = Column(Integer, ForeignKey('useraccount.id'))
    author = relationship("Useraccount", backref="articles", lazy='joined')
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Category", backref="articles", lazy='joined')
    date_created = Column(DateTime(), nullable=False, index=True)
    last_modified = Column(DateTime(), index=True)
    viewCount = Column(Integer, default=0, index=True)
    usefulCount = Column(Integer, default=0, index=True)
    notUsefulCount = Column(Integer, default=0)
    modules = relationship('Module', secondary='articleModules', backref='articles', lazy='joined')
    tags = relationship('Tag', secondary='articleTags', backref='articles', lazy='joined')


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, index=True)
    message_type = Column(String(20))  # RULE, TIP, etc.
    message = Column(String(2000), nullable=False, default="")
    title = Column(String(200), unique=True, nullable=False, default="")
    label = Column(String(100), nullable=False, default="")
    author = Column(String(100), nullable=False, default="")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, unique=True, nullable=False, index=True)
    name = Column(String(256))
    value = Column(String(2048))


def build(engine, session):
    Base.metadata.create_all(bind=engine)

    for category in categories:
        item = Category(
            name = category["name"],
            link = category["link"],
            formtitle = category["formtitle"],
            buttonlabel = category["buttonlabel"],
            active = category["active"]
        )
        session.add(item)
        session.commit()
        print("Category", category["name"])

    for tag in tags:
        item = Tag(
            name = tag["name"],
            title = tag["title"],
            link = tag["link"]
        )
        session.add(item)
        session.commit()
        print("Tag", tag)

    for module in modules:
        item = Module(
            name = module["name"],
            title = module["title"],
            link = module["link"]
        )
        session.add(item)
        session.commit()
        print("Module", module)

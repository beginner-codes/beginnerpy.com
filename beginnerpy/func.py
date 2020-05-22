import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from beginnerpy.models import Category

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

# Returns the sidebar navigation elements in alphabetical order
def getSideNav():
	session = Session()
	nav_src = session.query(Category)
	nav = []
	for item in nav_src:
		nav.append(
			{
				"id": item.id,
				"name": item.name,
				"link": item.link,
				"active": item.active,
				"viewCount": item.viewCount,
				"formtitle": item.formtitle,
				"buttonlabel": item.buttonlabel,
			}
		)
	nav = sorted(nav, key=lambda x: x["name"])
	session.close()
	return nav


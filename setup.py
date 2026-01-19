from setuptools import setup, find_packages

setup(
    name="pos_system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.0.5",
        "Flask-Login==0.6.2",
        "Flask-WTF==1.1.1",
        "Werkzeug==2.3.7",
        "SQLAlchemy==2.0.19",
        "python-dotenv==1.0.0",
    ],
)
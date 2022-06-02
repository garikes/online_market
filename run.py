from shop import app

SQLALCHEMY_TRACK_MODIFICATIONS = False
# new comment
if __name__ == "__main__":
    app.run(debug=True)

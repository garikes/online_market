from  shop import app
SQLALCHEMY_TRACK_MODIFICATIONS = False

if __name__ == "__main__":
    app.run(debug=True)
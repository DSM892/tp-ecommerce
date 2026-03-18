from flask import Flask, render_template
from database import DatabaseManager

app = Flask(__name__)
db = DatabaseManager()

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/catalogue')
def catalogue():
    produits = db.get_produits()
    return render_template('catalogue.html', produits=produits)

if __name__ == '__main__':
    app.run(debug=True)
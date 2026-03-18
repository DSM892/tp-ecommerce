from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/catalogue')
def catalogue():
    produits = [
        {"id" : 1, "nom" : "T-shirt", "prix" : 25.99, "description" : "Coton bio"},
        {"id" : 2, "nom" : "Jean", "prix" : 59.99, "description" : "Coupe slim"},
        {"id" : 3, "nom" : "Casquette", "prix" : 15.00, "description" : "Style urbain"}
    ]
    return render_template('catalogue.html', produits=produits)

if __name__ == '__main__':
    app.run(debug=True)
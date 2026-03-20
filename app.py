from flask import Flask, render_template, request, redirect, session
from database import DatabaseManager
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète_ici'
db = DatabaseManager()

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/catalogue')
def catalogue():
    produits = db.get_produits()
    return render_template('catalogue.html', produits=produits)

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mdp = request.form['mot_de_passe']
        if db.inscrire(nom, email, mdp):
            user = db.connecter(email, mdp)
            if user:
                session['user_id'] = user['id']
                session['user_nom'] = user['nom']
                session['user_role'] = user['role']
                return redirect('/')
            else:
                return redirect('/login')
        else:
            return render_template('register.html', erreur='Email déjà utilisé')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mdp = request.form['mot_de_passe']
        user = db.connecter(email, mdp)
        if user:
            session['user_id'] = user['id']
            session['user_nom'] = user['nom']
            session['user_role'] = user['role']
            return redirect('/')
        else:
            return render_template('login.html', erreur='Email ou mot de passe incorrect')
    return render_template('login.html')

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')

@app.route('/ajouter_au_panier/<int:produit_id>')
def ajouter_au_panier(produit_id):
    produit = db.get_produit(produit_id)
    if produit:
        panier = session.get('panier', [])
        for article in panier:
            if article['id'] == produit_id:
                article['quantite'] += 1
                session['panier'] = panier
                session.modified = True
                return redirect('/panier')

        panier.append({
            'id': produit['id'],
            'nom': produit['nom'],
            'prix': produit['prix'],
            'quantite': 1
        })
        session['panier'] = panier
        return redirect('/panier')

@app.route('/panier')
def panier():
    panier = session.get('panier', [])
    total = sum(a['prix'] * a['quantite'] for a in panier)
    return render_template('panier.html', panier=panier, total=total)

@app.route('/supprimer_panier/<int:produit_id>')
def supprimer_du_panier(produit_id):
    panier = session.get('panier', [])
    for article in panier:
        panier = [a for a in panier if a['id'] != produit_id]
        session['panier'] = panier
        session.modified = True
        return redirect('/panier')

@app.route('/vider_panier')
def vider_panier():
    session.pop('panier', None)
    return redirect('/panier')

@app.route('/valider_commande')
def valider_commande():
    if 'user_id' not in session:
        return redirect('/login')
    panier = session.get('panier', [])
    if not panier:
        return redirect('/panier')
    total = sum(a['prix'] * a['quantite'] for a in panier)
    db.creer_commande(session['user_id'], panier, total,)
    session.pop('panier', None)
    return render_template('commande_confirmee.html',total=total)

@app.route('/mes_commandes')
def mes_commandes():
    if 'user_id' not in session:
        return redirect('/login')
    commandes = db.get_commandes_utilisateur(session['user_id'])
    return render_template('mes_commandes.html', commandes=commandes)

@app.route('/admin', endpoint='admin')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect('/login')
    produits = db.get_produits()
    commandes = db.get_toutes_commandes()
    return render_template('admin.html', produits=produits, commandes=commandes)

@app.route('/admin/ajouter_produit', methods=['POST'])
def admin_ajouter_produit():
    if session.get('user_role') != 'admin':
        return redirect('/login')
    db.ajouter_produit(
        request.form['nom'],
        float(request.form['prix']),
        request.form['description'],
        request.form['categorie'],
        int(request.form['stock'])
    )
    return redirect('/admin')

@app.route('/admin/supprimer_produit/<int:produit_id>')
def admin_supprimer_produit(produit_id):
    if session.get('user_role') != 'admin':
        return redirect('/login')
    db.supprimer_produit(produit_id)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

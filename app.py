from flask import Flask, render_template, request, redirect, session
from database import DatabaseManager    
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clé_secrète' # Pour chiffrer cookie
db = DatabaseManager()

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/catalogue')
def catalogue():
    produits = db.get_produits()
    return render_template('catalogue.html', produits=produits)

@app.route('/produit/<int:produit_id>')
def produit(produit_id):
    produit = db.get_produit(produit_id)
    if not produit:
        return redirect('/catalogue')
    avis = db.get_avis_produit(produit_id)
    moyenne_note = db.get_moyenne_note_produit(produit_id)
    nombre_avis = db.get_nombre_avis_produit(produit_id)
    return render_template('produit.html', produit=produit, avis=avis, moyenne_note=moyenne_note, nombre_avis=nombre_avis)

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

@app.route('/compte')
def compte():
    if 'user_id' not in session:
        return redirect('/login')
    utilisateur = db.get_utilisateur(session['user_id'])
    return render_template('compte.html', utilisateur=utilisateur)

@app.route('/modifier_mot_de_passe', methods=['POST'])
def modifier_mot_de_passe():
    if 'user_id' not in session:
        return redirect('/login')
    
    ancien_mdp = request.form.get('ancien_mdp')
    nouveau_mdp = request.form.get('nouveau_mdp')
    confirmer_mdp = request.form.get('confirmer_mdp')
    
    utilisateur = db.get_utilisateur(session['user_id'])
    
    if not ancien_mdp or not nouveau_mdp or not confirmer_mdp:
        return render_template('compte.html', utilisateur=utilisateur, erreur='Tous les champs sont requis')
    
    if nouveau_mdp != confirmer_mdp:
        return render_template('compte.html', utilisateur=utilisateur, erreur='Les nouveaux mots de passe ne correspondent pas')
    
    if len(nouveau_mdp) < 6:
        return render_template('compte.html', utilisateur=utilisateur, erreur='Le mot de passe doit contenir au moins 6 caractères')
    
    if db.modifier_mot_de_passe(session['user_id'], ancien_mdp, nouveau_mdp):
        return render_template('compte.html', utilisateur=utilisateur, succes='Mot de passe modifié avec succès')
    else:
        return render_template('compte.html', utilisateur=utilisateur, erreur='Ancien mot de passe incorrect')

@app.route('/supprimer_compte', methods=['POST'])
def supprimer_compte():
    if 'user_id' not in session:
        return redirect('/login')
    
    confirmation = request.form.get('confirmation')
    
    if confirmation != 'SUPPRIMER':
        utilisateur = db.get_utilisateur(session['user_id'])
        return render_template('compte.html', utilisateur=utilisateur, erreur='Confirmation incorrecte')
    
    db.supprimer_utilisateur(session['user_id'])
    session.clear()
    return redirect('/')

@app.route('/ajouter_avis/<int:produit_id>', methods=['POST'])
def ajouter_avis(produit_id):
    if 'user_id' not in session:
        return redirect(f'/login?next=/produit/{produit_id}')
    
    note = request.form.get('note', 0)
    commentaire = request.form.get('commentaire', '')
    
    try:
        note = int(note)
        if note < 1 or note > 5:
            note = 5
    except:
        note = 5
    
    db.ajouter_avis(
        produit_id=produit_id,
        utilisateur_id=session.get('user_id'),
        utilisateur_nom=session.get('user_nom'),
        note=note,
        commentaire=commentaire
    )
    
    return redirect(f'/produit/{produit_id}')

@app.route('/ajouter_au_panier/<int:produit_id>', methods=['GET', 'POST'])
def ajouter_au_panier(produit_id):
    produit = db.get_produit(produit_id)
    if not produit:
        return redirect('/catalogue')
    
    # Récupérer la quantité du formulaire ou par défaut 1
    quantite = 1
    if request.method == 'POST':
        try:
            quantite = int(request.form.get('quantite', 1))
        except:
            quantite = 1
    
    # Vérifier que la quantité n'est pas supérieure au stock
    if quantite > produit['stock']:
        return render_template('erreur_stock.html', produit=produit, quantite_demandee=quantite)
    
    panier = session.get('panier', [])
    
    # Vérifier si le produit est déjà dans le panier
    produit_existe = False
    for article in panier:
        if article['id'] == produit_id:
            # Vérifier que la nouvelle quantité ne dépasse pas le stock
            nouvelle_quantite = article['quantite'] + quantite
            if nouvelle_quantite > produit['stock']:
                return render_template('erreur_stock.html', produit=produit, quantite_demandee=nouvelle_quantite, quantite_actuelle=article['quantite'])
            article['quantite'] = nouvelle_quantite
            produit_existe = True
            break
    
    # Si le produit n'existe pas, l'ajouter
    if not produit_existe:
        panier.append({
            'id': produit['id'],
            'nom': produit['nom'],
            'prix': produit['prix'],
            'quantite': quantite
        })
    
    session['panier'] = panier
    session.modified = True
    return redirect('/panier')
    

@app.route('/panier')
def panier():
    panier = session.get('panier', [])
    total = sum(a['prix'] * a['quantite'] for a in panier)
    return render_template('panier.html', panier=panier, total=total)

@app.route('/supprimer_du_panier/<int:produit_id>')
def supprimer_du_panier(produit_id):
    panier = session.get('panier', [])
    panier = [a for a in panier if a['id'] != produit_id]
    session['panier'] = panier
    session.modified = True
    return redirect('/panier')

@app.route('/diminuer_quantite/<int:produit_id>')
def diminuer_quantite(produit_id):
    panier = session.get('panier', [])
    for article in panier:
        if article['id'] == produit_id:
            article['quantite'] -= 1
            if article['quantite'] <= 0:
                panier = [a for a in panier if a['id'] != produit_id]
            break
    session['panier'] = panier
    session.modified = True
    return redirect('/panier')

@app.route('/augmenter_quantite/<int:produit_id>')
def augmenter_quantite(produit_id):
    produit = db.get_produit(produit_id)
    if not produit:
        return redirect('/panier')
    
    panier = session.get('panier', [])
    for article in panier:
        if article['id'] == produit_id:
            # Vérifier que la quantité ne dépasse pas le stock
            if article['quantite'] + 1 > produit['stock']:
                return render_template('erreur_stock.html', produit=produit, quantite_demandee=article['quantite'] + 1, quantite_actuelle=article['quantite'])
            article['quantite'] += 1
            break
    
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

@app.route('/detail_commande/<int:commande_id>')
def detail_commande(commande_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    commande = db.get_commandes_utilisateur(session['user_id'])
    commande_trouvee = None
    
    for c in commande:
        if c['id'] == commande_id:
            commande_trouvee = c
            break
    
    if not commande_trouvee and session.get('user_role') != 'admin':
        return redirect('/mes_commandes')
    
    if not commande_trouvee:
        toutes_commandes = db.get_toutes_commandes()
        for c in toutes_commandes:
            if c['id'] == commande_id:
                commande_trouvee = c
                break
    
    if not commande_trouvee:
        return redirect('/mes_commandes')
    
    articles = db.get_articles_commande(commande_id)
    return render_template('detail_commande.html', commande=commande_trouvee, articles=articles)

@app.route('/admin', endpoint='admin')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect('/login')
    produits = db.get_produits()
    commandes = db.get_toutes_commandes()
    utilisateurs = db.get_utilisateurs()
    return render_template('admin.html', produits=produits, commandes=commandes, utilisateurs=utilisateurs)

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

@app.route('/admin/modifier_produit', methods=['POST'])
def admin_modifier_produit():
    if session.get('user_role') != 'admin':
        return redirect('/login')
    produit_id = request.form['id']
    updates = {}
    if request.form.get('nom'):
        updates['nom'] = request.form['nom']
    if request.form.get('prix'):
        updates['prix'] = float(request.form['prix'])
    if request.form.get('description'):
        updates['description'] = request.form['description']
    if request.form.get('categorie'):
        updates['categorie'] = request.form['categorie']
    if request.form.get('stock'):
        updates['stock'] = int(request.form['stock'])
    if updates:
        db.modifier_produit(produit_id, updates)
    return redirect('/admin')

@app.route('/admin/supprimer_produit/<int:produit_id>')
def admin_supprimer_produit(produit_id):
    if session.get('user_role') != 'admin':
        return redirect('/login')
    db.supprimer_produit(produit_id)
    return redirect('/admin')

@app.route('/admin/modifier_role_utilisateur/<int:user_id>', methods=['POST'])
def admin_modifier_role_utilisateur(user_id):
    if session.get('user_role') != 'admin':
        return redirect('/login')
    
    new_role = request.form.get('role')
    if new_role not in ['admin', 'client']:
        new_role = 'client'
    
    db.modifier_role_utilisateur(user_id, new_role)
    return redirect('/admin')

@app.route('/admin/supprimer_utilisateur/<int:user_id>', methods=['POST'])
def admin_supprimer_utilisateur(user_id):
    if session.get('user_role') != 'admin':
        return redirect('/login')
    
    # Prevent admin from deleting themselves
    if session.get('user_id') == user_id:
        return redirect('/admin')
    
    db.supprimer_utilisateur(user_id)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

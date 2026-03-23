import sqlite3

class DatabaseManager:
    def __init__(self, db_name='shop.db'):
        self.dbname = db_name
        self.creer_tables()
        self.creer_admin_default()
    
    def get_connexion(self):
        conn = sqlite3.connect(self.dbname, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    
    def creer_tables(self):
        conn = self.get_connexion()
        try:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prix REAL NOT NULL,
                    description TEXT,
                    categorie TEXT,
                    stock INTEGER DEFAULT 10
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utilisateurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    mot_de_passe TEXT NOT NULL,
                    role TEXT DEFAULT 'client'
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commandes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    utilisateur_id INTEGER,
                    date TEXT,
                    total REAL,
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commande_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commande_id INTEGER,
                    produit_nom TEXT,
                    quantite INTEGER,
                    prix_unitaire REAL
                )
            ''')

            conn.commit()
        finally:
            conn.close()

    def ajouter_produit(self, nom, prix, description, categorie, stock=10):
        conn = self.get_connexion()
        try:
            conn.execute(
                'INSERT INTO produits (nom, prix, description, categorie, stock) VALUES (?,?,?,?,?)',
                (nom, prix, description, categorie, stock)
            )
            conn.commit()
        finally:
            conn.close()

    def get_produits(self):
        conn = self.get_connexion()
        try:
            produits = conn.execute('SELECT * FROM produits').fetchall()
        finally:
            conn.close()
        return produits
    
    def get_produit(self, id):
        conn = self.get_connexion()
        try:
            produit = conn.execute('SELECT * FROM produits WHERE id=?', (id,)).fetchone()
        finally:
            conn.close()
        return produit
    
    def modifier_produit(self, id, updates):
        if not updates:
            return
        conn = self.get_connexion()
        try:
            set_clause = ', '.join([f'{key}=?' for key in updates.keys()])
            values = list(updates.values()) + [id]
            query = f'UPDATE produits SET {set_clause} WHERE id=?'
            conn.execute(query, values)
            conn.commit()
        finally:
            conn.close()
    
    def supprimer_produit(self, id):
        conn = self.get_connexion()
        try:
            conn.execute('DELETE FROM produits WHERE id=?', (id,))
            conn.commit()
        finally:
            conn.close()
    
    def inscrire(self, nom, email, mot_de_passe, role='client'):
        import hashlib
        mdp_hash = hashlib.sha256(mot_de_passe.encode('utf-8')).hexdigest()
        conn = self.get_connexion()
        try:
            conn.execute(
                'INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES (?,?,?,?)',
                (nom, email, mdp_hash, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def connecter(self, email, mot_de_passe):
        import hashlib
        mdp_hash = hashlib.sha256(mot_de_passe.encode('utf-8')).hexdigest()
        conn = self.get_connexion()
        try:
            user = conn.execute(
                'SELECT * FROM utilisateurs WHERE email=? AND mot_de_passe=?',
                (email, mdp_hash)
            ).fetchone()
        finally:
            conn.close()
        return user
    
    def creer_admin_default(self):
        self.inscrire('Admin', 'admin@shop.com', 'admin123', 'admin')
    
    def creer_commande(self, user_id, panier, total):
        from datetime import datetime
        conn = self.get_connexion()
        try:
            date = datetime.now().strftime('%Y-%m-%d %H:%M')
            cursor = conn.execute(
                'INSERT INTO commandes (utilisateur_id, date, total) VALUES (?,?,?)',
                (user_id, date, total)
            )
            commande_id = cursor.lastrowid
            for article in panier:
                conn.execute(
                    'INSERT INTO commande_articles (commande_id, produit_nom, quantite, prix_unitaire) VALUES (?,?,?,?)',
                    (commande_id, article['nom'], article['quantite'], article['prix'])
                )
                stock = conn.execute(
                        'SELECT stock FROM produits WHERE nom=?',
                        (article['nom'],)
                    ).fetchone()[0]
                if stock < article['quantite']:
                    raise ValueError(f"Stock insuffisant pour {article['nom']}")
                stock -= article['quantite']
                conn.execute(
                    'UPDATE produits SET stock=? WHERE nom=?',
                    (stock, article['nom'])
                )
            conn.commit()
        finally:
            conn.close()
    
    def get_commandes_utilisateur(self, user_id):
        conn = self.get_connexion()
        try:
            commandes = conn.execute(
                'SELECT * FROM commandes WHERE utilisateur_id=? ORDER BY date DESC',
                (user_id,)
            ).fetchall()
        finally:
            conn.close()
        return commandes
    
    def get_toutes_commandes(self):
        conn = self.get_connexion()
        try:
            commandes = conn.execute(
                'SELECT commandes.*, utilisateurs.nom as client_nom FROM commandes '
                'JOIN utilisateurs ON commandes.utilisateur_id = utilisateurs.id '
                'ORDER BY date DESC'
            ).fetchall()
        finally:
            conn.close()
        return commandes
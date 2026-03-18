import sqlite3

class DatabaseManager:
    def __init__(self, db_name='shop.db'):
        self.dbname = db_name
        self.creer_tables()
    
    def get_connexion(self):
        conn = sqlite3.connect(self.dbname)
        conn.row_factory = sqlite3.Row
        return conn
    
    def creer_tables(self):
        conn = self.get_connexion()
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
                mot_de_passe TEXT NOT NULL
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

    def ajouter_produit(self, nom, prix, description, categorie, stock=10):
        conn = self.get_connexion()
        conn.execute(
            'INSERT INTO produits (nom, prix, description, categorie, stock) VALUES (?,?,?,?,?)',
            (nom, prix, description, categorie, stock)
        )
        conn.commit()
        conn.close()

    def get_produits(self):
        conn = self.get_connexion()
        produits = conn.execute('SELECT * FROM produits').fetchall()
        conn.close()
        return produits
    
    def get_produit(self, id):
        conn = self.get_connexion()
        produit = conn.execute('SELECT * FROM produits WHERE id=?', (id,)).fetchone()
        conn.close()
        return produit
    
    def modifier_produit(self, id, nom, prix, description, categorie, stock):
        conn = self.get_connexion()
        conn.execute(
            'UPDATE produits SET nom=?, prix=?, descritpion=?, categorie=?, stock=? WHERE id=?',
            (nom, prix, description, categorie, stock, id)
        )
        conn.commit()
        conn.close()
    
    def supprimer_produit(self, id):
        conn = self.get_connexion()
        conn.execute('DELETE FROM produits WHERE id=?', (id,))
        conn.commit()
        conn.close()
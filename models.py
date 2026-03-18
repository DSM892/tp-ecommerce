import hashlib

class Produit:
    def __init__(self, id, nom, prix, description, categorie, stock=10):
        self.id = id
        self.nom = nom
        self.prix = prix
        self.description = description
        self.categorie = categorie
        self.stock = stock

    def est_disponible(self):
        return self.stock > 0
    
    def __str__(self):
        return f"{self.nom} - {self.prix} €"
    
class utilisateur:
    def __init__(self, id, nom, email, mot_de_passe, role='client'):
        self.id = id
        self.nom = nom
        self.email = email
        self.mot_de_passe_hash = self.hasher(mot_de_passe)
        self.role = role
    @staticmethod
    def hasher(mdp):
        return hashlib.sha256(mdp.encode('utf-8')).hexdigest()

    def verifier_mdp(self, mdp_saisi):
        return self.mot_de_passe_hash == self.hasher(mdp_saisi)
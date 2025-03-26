# Bot Fruit Ninja

Un bot intelligent pour jouer à Fruit Ninja en utilisant la vision par ordinateur et l'apprentissage automatique.

## État Avant le PR

Le bot original était une implémentation basique avec les fonctionnalités suivantes :
- Détection des fruits et des bombes avec YOLO
- Mouvements de coupe verticaux simples
- Évitement basique des bombes
- Capture d'écran avec dxcam
- Contrôle de la souris avec pynput

## Améliorations Apportées

### 1. Optimisation des Performances
- Limitation des FPS à 60 pour réduire la charge CPU
- Système de skip frame intelligent
- Calcul et affichage des FPS en temps réel

### 2. Système de Prédiction de Trajectoire
- Suivi de l'historique des positions des fruits
- Calcul de la vitesse moyenne
- Prédiction de la position future
- Nettoyage automatique de l'historique obsolète

### 3. Patterns de Coupe Améliorés
- Pattern vertical (original)
- Pattern diagonal pour les cibles groupées
- Pattern en X pour les situations avec beaucoup de fruits
- Sélection automatique du meilleur pattern selon le contexte

### 4. Interface Visuelle
- Overlay en temps réel montrant :
  - Zones de sécurité des bombes
  - Cibles sûres
  - FPS actuels
- Transparence ajustable pour une meilleure visibilité

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/votre-username/bot-fruit-ninja.git
cd bot-fruit-ninja
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Télécharger le modèle YOLO :
```bash
# Le modèle doit être placé dans le dossier runs/detect/train3/weights/
```

## Utilisation

1. Lancer le jeu Fruit Ninja
2. Exécuter le bot :
```bash
python main.py
```
3. Appuyer sur 'q' pour quitter

## Configuration

Les paramètres principaux peuvent être ajustés dans le fichier `main.py` :
- `BOMB_SAFE_RADIUS` : Distance de sécurité autour des bombes
- `SLICE_STEPS` : Nombre d'étapes pour chaque mouvement de coupe
- `SLICE_SLEEP_TIME` : Délai entre chaque étape
- `FPS_LIMIT` : Limite de FPS
- `TARGET_TIMEOUT` : Durée de vie des cibles

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Crédits

Ce projet est inspiré par la vidéo d'Aywen : [Fruit Ninja Bot avec Python](https://www.youtube.com/watch?v=3ut6q5W4QVk)

### Auteur Original
- Aywen - Créateur du concept initial et de la vidéo tutorielle

### Contributeurs
- NailecMC - Optimisations et améliorations du code
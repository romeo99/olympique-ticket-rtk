# Plateforme d'achat des tickets des jeux olympiques en ligne

## Description
Ce projet est une application Django permettant aux utilisateurs d'acheter des tickets en ligne et de procéder au paiement sécurisé via Stripe. 

## Fonctionnalités
- Système d'achat de tickets en ligne
- Paiement sécurisé avec Stripe
- Gestion des Webhooks Stripe pour le suivi des paiements
- Interface utilisateur intuitive
- Gestion des offres par l'administrateur du site
- Génération de code Qr pour chaque ticket acheté


### 1. **Clonez le dépôt**
- git clone git@github.com:romeo99/olympique-ticket-rtk.git
- cd olympique-ticket

### 2. **Commandes à èxécuter**
- pip freeze > requirements.txt
- pip install stripe

### 3. **Stripe Webhook**
- Installez stripe : pip install stripe
- Dans le .env mettez les clés  ==> STRIPE_SECRET_KEY_TEST, STRIPE_PUBLIC_KEY_TEST
- Créez un compte Stripe et activez le webhook
- Configurez le webhook pour envoyer les données de paiement vers votre application
- Dans votre application, configurez le webhook pour recevoir les données de paiement
- Tester avec Sripe CLI
    Pour installer la CLI Stripe sous Linux sans gestionnaire de paquets :

        Téléchargez le dernier fichier tar.gz linux depuis GitHub.
        Décompressez le fichier : tar -xvf stripe_X.X.X_linux_x86_64.tar.gz.
        Déplacez ./stripe sur votre chemin d’exécution.

    Se connecter à l'interface de ligne de commande

        Èxécuter dans voter invite de commande stripe login
        Appuyez sur la touche Entrée de votre clavier pour effectuer le processus d’authentification dans votre navigateur.

    stripe listen --forward-to localhost:8000/webhook/stripe/ 
        Cette commande renvoie la clé secrète webhook qu'on met dans le point .env qu'on a nommé STRIPE_WEBHOOK_SECRET



    

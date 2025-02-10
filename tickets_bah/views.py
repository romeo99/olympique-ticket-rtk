from io import BytesIO
from math import frexp
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import Utilisateur, Offre, Reservation, Panier
from .forms import RegisterForm, LoginForm
from django.contrib.auth import authenticate, login, logout
import qrcode
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings
import uuid
from .utils import envoyer_confirmation_reservation  # Import depuis utils.py
from tickets_bah.core.permissions import is_super_admin, is_admin, user_is_authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password
import sweetify
from django.urls import reverse
from django.contrib import messages


# Create your views here.(vue pour la page d'acceuil)

def home(request):
    return render(request, 'tickets_bah/home.html')



#Poteger les pages necessitant une authentification
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return HttpResponseRedirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper

# vue pour afficher la liste des offres
def offres_list(request):
    offres = Offre.objects.all()
    return render(request, 'tickets_bah/offres_list.html', {'offres':offres})

@user_passes_test(user_is_authenticate, login_url="/login")
def reservation_create(request):
    """Affiche le formulaire de réservation"""
    offre = None
    offre_id = request.GET.get('offre_id')
    
    if offre_id:
        offre = get_object_or_404(Offre, id=offre_id)

    return render(request, 'tickets_bah/reservation_form.html', {'offre': offre})

@user_passes_test(user_is_authenticate, login_url="/login")
def reservation_store(request):
    """Stocke les données de réservation et génère le billet"""
    if request.method == 'POST':
        user = request.user
        utilisateur = get_object_or_404(Utilisateur, id=user.id)
        offre = get_object_or_404(Offre, id=request.POST.get('offre_id'))

        # Créer une clé unique pour la réservation
        cle_billet = str(uuid.uuid4())[:12]

        # Créer la réservation
        reservation = Reservation.objects.create(
            utilisateur=utilisateur,
            offre=offre,
            cle_billet=cle_billet
        )

        # Générer et sauvegarder le QR code
        reservation.generate_qr_code()
        reservation.save()

        # Stocker l'ID de la réservation dans la session
        request.session['reservation_id'] = reservation.id

        # Envoyer l'e-mail de confirmation
        envoyer_confirmation_reservation(utilisateur, reservation)
        sweetify.success(request, "Réservation effectuée avec succès !", button='Ok', timer=3000)
        return redirect("e_billet")
    

@user_passes_test(user_is_authenticate, login_url="/login")
def e_billet(request):
    reservation_id = request.session.get('reservation_id')  # Récupération de l'ID depuis la session

    if not reservation_id:
        sweetify.error(request, "Aucune réservation trouvée.", button='Ok')
        return redirect('accueil')  # Redirection en cas d'erreur

    reservation = get_object_or_404(Reservation, id=reservation_id)
    context = {
        "reservation": reservation
    }
    return render(request, "tickets_bah/e_billet.html", context)


#CREER LES VUES POUR: INSCRIPTION, CONNEXION, DECONNEXION

#1 INSCRIPTION
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            nom = form.cleaned_data.get("nom")
            prenom = form.cleaned_data.get("prenom")
            email = form.cleaned_data.get("email")
            password = make_password(form.cleaned_data.get("password"))
            cle_utilisateur = str(uuid.uuid4())[:12]
            utilisateur = Utilisateur.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                password=password,
                cle_utilisateur=cle_utilisateur
            )
            utilisateur.save()
            sweetify.success(request, "Inscription effectuée avec succès !", button='Ok', timer=3000)
            return redirect("login")
        else:
            errors = " ".join([f"{field}: {', '.join(messages)}" for field, messages in form.errors.items()])
            sweetify.error(request, f"Inscription échouée ! : {errors}", button='Ok', timer=5000)
            return redirect("offres.create")
    else:
        form = RegisterForm()
    return render(request, 'tickets_bah/register.html', {'form': form})


#2 CONNEXION
def customLogin(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Authentifier l'utilisateur avec Django
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)  # Connexion de l'utilisateur
                if user.default_role == "super-admin":
                    return redirect("dashboard")
                else:
                    return redirect("home")
            else:
                return HttpResponse("Email ou mot de passe incorrect")

    else:
        form = LoginForm()

    return render(request, 'tickets_bah/login.html', {'form': form})

#3 DECONNEXION
def logOut(request):
    logout(request)
    messages.success(request, 'Vous êtes bien déconnectés')
    return HttpResponseRedirect(reverse('login'))



#vue pour ajouter une offre dans le panier
@user_passes_test(user_is_authenticate, login_url="/login")
def ajouter_au_panier(request, offre_id):
    if request.user.is_authenticated:
        user = request.user
        utilisateur = get_object_or_404(Utilisateur, id=user.id)
        offre = get_object_or_404(Offre, id=offre_id)

        # Supprimer l'offre existante si elle existe
        Panier.objects.filter(utilisateur=utilisateur).delete()

        # Ajouter la nouvelle offre
        Panier.objects.create(utilisateur=utilisateur, offre=offre)
        sweetify.success(request, "Offre ajoutée au panier avec succès !", button='Ok', timer=3000)

        return redirect('panier')


#VUE POUR AFFICHER LAE PANIER
@user_passes_test(user_is_authenticate, login_url="/login")
def panier(request):
    if request.user.is_authenticated:
        user = request.user
        utilisateur = get_object_or_404(Utilisateur, id=user.id)
        panier_items = Panier.objects.filter(utilisateur=utilisateur)

        context = {
            "panier_items": panier_items
        }
        return render(request, 'tickets_bah/panier.html', context) 


# UNE FONCTION POUE ENVOYER EMEIL DE CONFIRMATION


#vue pour creer une reservation
"""def reservation_create(request):
    if request.method == 'POST':
        utilisateur_id = request.POST.get('utilisateur_id')
        offre_id = request.POST.get('offre_id')

        utilisateur =get_object_or_404(Utilisateur, id=utilisateur_id)
        offre = get_object_or_404(Offre, id=offre_id)

        #creer une reservation
        reservation = Reservation.objects.create(utilisateur=utilisateur, offre=offre,
        cle_billet="unique_key_here", #generer une clés ici
        qr_code="qr_code_placeholder.png" # generer le qr code
     )
        return HttpResponse("Reservation creer avec succes")
    return render(request, "tickets_bah/Reservation_form.html")"""



#CREER LA RESERVATION

#GENERATION DE QR CODE AVEC LES BILLETS
"""def generate_qr_code(reservation):
    qr_dara = f"{reservation.utilisateur.cle_utilisateur} - {reservation.cle_billet}"
    qr = qrcode.make(qr_dara)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=f"qrcode_{reservation.id}.png")"""

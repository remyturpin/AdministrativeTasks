import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Configuration de la page
st.set_page_config(page_title="Envoi d'e-mails personnalisé", layout="wide")

# Titre
st.title(" Envoi d'e-mails personnalisé avec Excel")

# Paramètres de l'expéditeur
st.sidebar.header(" Paramètres d'envoi")
email_sender = st.sidebar.text_input("Adresse e-mail expéditeur")
email_password = st.sidebar.text_input("Mot de passe", type="password")

smtp_server = st.sidebar.text_input("Serveur SMTP", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("Port SMTP", value=587, step=1)

# Upload du fichier Excel
uploaded_file = st.file_uploader(" Importer un fichier Excel contenant les e-mails et informations", type=["xlsx"])

# Rédaction du message avec placeholders
st.header("✉️ Rédaction du mail personnalisé")
subject = st.text_input("Objet du mail", "Votre produit {produit} est disponible !")
message_body = st.text_area("Message", 
                            """Bonjour {prenom} {nom},

Votre produit "{produit}" est maintenant disponible au prix de {montant}.
Votre position actuelle dans la liste est {position}.

N'hésitez pas à nous contacter si vous avez des questions.

Cordialement,
L'équipe Support""")

# Ajout de pièce jointe
attachment = st.file_uploader(" Ajouter une pièce jointe (PDF, DOCX, etc.)", type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"])

# Chargement du fichier Excel et affichage des données
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write(" Aperçu des données du fichier Excel :")
    st.dataframe(df)

    # Vérifier si la colonne Email existe
    if "Email" not in df.columns:
        st.error(" Le fichier Excel doit contenir une colonne 'Email'")
    else:
        # Bouton pour afficher un aperçu
        if st.button(" Aperçu d'un e-mail"):
            example_row = df.iloc[0].to_dict()
            preview_subject = subject.format(**example_row)
            preview_message = message_body.format(**example_row)

            st.subheader(" Aperçu du premier e-mail")
            st.write(f"**Objet:** {preview_subject}")
            st.write(f"**Message:**\n{preview_message}")

        # Bouton pour envoyer les emails
        if st.button(" Envoyer les e-mails"):
            try:
                # Connexion SMTP
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(email_sender, email_password)

                for index, row in df.iterrows():
                    email_receiver = row["Email"]
                    
                    # Personnalisation du message
                    try:
                        subject_email = subject.format(**row)
                        body_email = message_body.format(**row)
                    except KeyError as e:
                        st.error(f" Erreur: La colonne {e} est absente du fichier Excel !")
                        continue

                    # Création du mail
                    msg = MIMEMultipart()
                    msg["From"] = email_sender
                    msg["To"] = email_receiver
                    msg["Subject"] = subject_email
                    msg.attach(MIMEText(body_email, "plain"))

                    # Ajout de pièce jointe si existante
                    if attachment is not None:
                        file_name = attachment.name
                        attachment.seek(0)
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename={file_name}")
                        msg.attach(part)

                    # Envoi de l'e-mail
                    server.sendmail(email_sender, email_receiver, msg.as_string())
                    st.success(f" Email envoyé à {email_receiver}")

                server.quit()
                st.success(" Tous les e-mails ont été envoyés avec succès !")
            except Exception as e:
                st.error(f" Erreur : {e}")


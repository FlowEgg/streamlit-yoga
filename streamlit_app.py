# --pip install google-auth-oauthlib
# --streamlit run .\streamlit_app.py


#%%
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account

# --Authenticate to Firestore with the JSON account key.
# db = firestore.Client.from_service_account_json(".\\.streamlit\\firestore-key-yogaplayy1.json")
# --Authenticate to Firestore with toml secret.
import json
key_dict = json.loads(st.secrets["textkey"]) #--st.secrets knows to look for a file called .streamlit/secrets.toml
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

#%%
# Streamlit widgets to let a user create a new post
title = st.text_input("Post title")
user = st.text_input("Post url")
submit = st.button("Submit new post")

# Once the user has submitted, upload it to the database
if title and user and submit:
	doc_ref = db.collection("classes").document(title)
	doc_ref.set({
		"class": title,
		"user": user
	})

# And then render each post, using some light Markdown
posts_ref = db.collection("classes")
for doc in posts_ref.stream():
	post = doc.to_dict()
	title = post["class"]
	user = post["user"]

	st.subheader(f"Post: {title}")
	st.write(f":link: [{user}]({user})")


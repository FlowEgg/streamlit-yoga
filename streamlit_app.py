# --pip install -r requirements.txt
# --streamlit run .\streamlit_app.py


#%%
import streamlit as st
import streamlit_authenticator as stauth
from google.cloud import firestore
from google.oauth2 import service_account
import datetime as dt
from dateutil import tz

pst = tz.gettz('America/Los_Angeles')
str_pstnow = dt.datetime.today().strftime("%Y-%m-%d %H-%M-%S")


# --auth------------------------------------------------------------------------------------------------------------
# --Authenticate to Firestore with the JSON account key.
# db = firestore.Client.from_service_account_json(".\\.streamlit\\firestore-key-yogaplayy1.json")

# --Authenticate to Firestore with toml secret.
import json
key_dict = json.loads(st.secrets["textkey"]) #--st.secrets knows to look for a file called .streamlit/secrets.toml
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

# --user / password
def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            st.session_state["admin_flag"] = True if st.session_state["username"] == "admin" else False
            st.session_state["user"] = st.session_state["username"]
            # del st.session_state["password"]  # don't store username + password
            # del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
            st.session_state["admin_flag"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

def extract_list_1st(lst):
    return [item[0] for item in lst]

# --app------------------------------------------------------------------------------------------------------------
def text_field(label, columns=None, **input_params):
    c1, c2 = st.columns(columns or [1, 4])

    # Display field name with some alignment
    c1.markdown("##")
    c1.markdown(label)

    # Sets a default key parameter to avoid duplicate key errors
    input_params.setdefault("key", label)

    # Forward text input parameters
    return c2.text_input("", **input_params)


def add_user(userlist):
    c1, c2, c3, c4, c5,c6 = st.columns([1,2,1,2,1,2])
    c1.markdown("##")
    c1.markdown("user")
    user_name = c2.text_input("user_name",label_visibility='hidden')
    #
    c3.markdown("##")
    c3.markdown("display name")
    display_name = c4.text_input("display_name",label_visibility='hidden')
    # 
    c5.markdown("##")
    c5.markdown("credit (0~100)")
    credit = c6.number_input('credit', min_value = 0, max_value = 100,label_visibility='hidden')
    # 
    submit_add = st.button("Submit")

    if user_name and submit_add:
        # --add/update user document
        doc_ref = db.collection("users").document(user_name)
        if user_name not in userlist: #--new user
            log = "Add new user."
            doc_ref.set({
                "user": user_name,
                "displayName": display_name,
                "credit":credit, 
                "timeCreatedOn": firestore.SERVER_TIMESTAMP,
                "timeUpdatedOn": firestore.SERVER_TIMESTAMP
            })
        elif display_name!="" and display_name:
            log = "Reset user credit. credit is {}".format(credit)
            doc_ref.update({
                "displayName": display_name,
                "credit":credit, 
                "timeUpdatedOn": firestore.SERVER_TIMESTAMP
            })
        else:
            log = "Reset user credit. credit is {}".format(credit)
            doc_ref.update({
                "credit":credit, 
                "timeUpdatedOn": firestore.SERVER_TIMESTAMP
            })
        # st.success('This is a success message!', icon="✅")

        # --create/add to sub-collection: logs
        log_ref = doc_ref.collection("logs").document(str_pstnow)
        log_ref.set({str_pstnow:log})

        st.experimental_rerun()
        

def delete_user(user):
    if user:
        # print(f'Deleting doc {doc_ref.id} => {doc_ref.get().to_dict()}')
        doc_ref = db.collection("users").document(user)

        # --create/add to sub-collection: logs
        log = "Deleted user {}".format(user)
        log_ref = doc_ref.collection("logs").document(str_pstnow)
        log_ref.set({str_pstnow:log})

        # --delete user
        doc_ref.delete()
        # st.success('This is a success message!', icon="✅")

        st.experimental_rerun()

def credit_minusOne(user,credit):
    if user:
        # print(f'Updating user credit {doc_ref.id} => {doc_ref.get().to_dict()}')
        doc_ref = db.collection("users").document(user)
        doc_ref.update({
            "credit": credit-1, 
            "timeUpdatedOn": firestore.SERVER_TIMESTAMP
        })
        # st.success('This is a success message!', icon="✅")

        # --update sub-collection: logs
        log = "Minus 1 credit. Credit is {}".format(credit-1)
        log_ref = doc_ref.collection("logs").document(str_pstnow)
        log_ref.set({str_pstnow:log})

        st.experimental_rerun()

def list_users():
    user_collections = []

    colls_top = db.collection("users")
    for doc_top in colls_top.stream():
        post = doc_top.to_dict()
        user = post["user"]
        displayName = post["displayName"]
        credit = post["credit"]
        timeUpdatedOn = post["timeUpdatedOn"]
        user_collections.append([user,displayName,credit,timeUpdatedOn])

    return user_collections

def review_user(user):
    doc_ref = db.collection("users").document(user)
    if doc_ref:
        post = doc_ref.get().to_dict()
        # print(post)
        for key, value in post.items():
            st.write(key,':', value)

        # --sub-collections of logs
        colls_log = doc_ref.collection("logs")
        st.write("###### Logs:")
        for doc_log in colls_log.stream():
            dic = doc_log.to_dict()
            for k, v in sorted(dic.items(), key=lambda x: x[0], reverse=True):
                st.write(k, v)

if check_password():
    # print("QA: log on as " + st.session_state["username"])
    if st.session_state["user"]:
        logon_user = st.session_state["user"]
    else:
        print()

    # --layout by log on
    usercollections = list_users()
    userlist = extract_list_1st(usercollections)
    if st.session_state["admin_flag"]:
        st.write("Log on as **Admin**")
        # print(st.experimental_user)

        st.write("### User list: ")
        # st.markdown(" Name | Display Name | Credit | Updated Time | -- |")
        for ux in usercollections:
            x = ux[0]
            xd = '`{}`'.format(ux[1])
            y = ux[2]
            dt = ux[3].astimezone(pst).strftime("` %b %d %Y, %I:%M%p %Z `") #strftime("%Y/%m/%d %H:%M:%S")
            col1, col2, col3, col4, col5, col6 = st.columns((1,1,1,1,1,1))
            col1.write(x)
            col2.write(xd)
            col3.write(y)
            col4.write(dt)

            reduceCredit_action = col5.empty().button("Creadit - 1", key=x)
            if reduceCredit_action:
                credit_minusOne(x,y)

            deleteUser_action = col6.empty().button("Delete User", key=x+"_delete")
            if deleteUser_action:
                delete_user(x)

        st.write("---")
        st.write("### Add new user / reset user credit:")
        add_user(userlist)
    elif logon_user == "guest":
        st.write("Log on as **Guest**")
        # print(st.experimental_user)

        user = st.selectbox("Which user going to be reviewed?", userlist)
        st.write('---')
        review_user(user)
    else:
        st.write("Log on as **Viewer**")
        # print(st.experimental_user)

        if logon_user in userlist:
            st.write('**{}**'.format(logon_user))
            st.write('---')
            review_user(logon_user)
        else:
            st.write("log on user doesn't have any records.")


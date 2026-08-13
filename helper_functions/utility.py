import streamlit as st  
import random  
import hmac  

# """  
# This file contains the common components used in the Streamlit App.  
# This includes the sidebar, the title, the footer, and the password check.  
# """  

import hmac
import streamlit as st


def check_credentials():

    """Returns True if the user entered the correct username and password."""

    # --------------------------------------------------------
    # Already authenticated
    # --------------------------------------------------------

    if st.session_state.get("credentials_correct", False):

        return True


    # --------------------------------------------------------
    # Check username
    # --------------------------------------------------------

    def username_entered():

        """Checks whether the username entered is correct."""

        username_correct = hmac.compare_digest(
            st.session_state["username"],
            st.secrets["username"]
        )

        if username_correct:

            st.session_state["username_correct"] = True

        else:

            st.session_state["username_correct"] = False


    # --------------------------------------------------------
    # Check password
    # --------------------------------------------------------

    def password_entered():

        """Checks whether the password entered is correct."""

        password_correct = hmac.compare_digest(
            st.session_state["password"],
            st.secrets["password"]
        )

        if password_correct:

            st.session_state["password_correct"] = True

        else:

            st.session_state["password_correct"] = False


    # --------------------------------------------------------
    # Check whether both credentials are correct
    # --------------------------------------------------------

    if (
        st.session_state.get("username_correct", False)
        and st.session_state.get("password_correct", False)
    ):

        st.session_state["credentials_correct"] = True

        del st.session_state["username"]
        del st.session_state["password"]

        return True


    # --------------------------------------------------------
    # Show username input
    # --------------------------------------------------------

    st.text_input(
        "Username",
        on_change=username_entered,
        key="username"
    )


    # Show username error only if username has been checked
    # and is incorrect.

    if (
        "username_correct" in st.session_state
        and not st.session_state["username_correct"]
    ):

        st.error("😕 Username incorrect")


    # --------------------------------------------------------
    # Show password input
    # --------------------------------------------------------

    st.text_input(
        "Password",
        type="password",
        on_change=password_entered,
        key="password"
    )


    # Show password error only if password has been checked
    # and is incorrect.

    if (
        "password_correct" in st.session_state
        and not st.session_state["password_correct"]
    ):

        st.error("😕 Password incorrect")


    return False
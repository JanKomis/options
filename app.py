import streamlit as st

# Inicializace defaultních hodnot – pouze jednou
if "S" not in st.session_state:
    st.session_state["S"] = 142.27
if "K" not in st.session_state:
    st.session_state["K"] = 142.0
if "T_days" not in st.session_state:
    st.session_state["T_days"] = 25
if "r" not in st.session_state:
    st.session_state["r"] = 1.75
if "sigma" not in st.session_state:
    st.session_state["sigma"] = 22.69
if "dividend" not in st.session_state:
    st.session_state["dividend"] = 1.6
if "option_type" not in st.session_state:
    st.session_state["option_type"] = "call"

# Teď jen vykreslíme komponenty, které se samy napojí na session_state
st.sidebar.number_input("Aktuální cena (S)", min_value=0.01, key="S")
st.sidebar.number_input("Strike cena (K)", min_value=0.01, key="K")
st.sidebar.slider("Dny do expirace", min_value=1, max_value=300, key="T_days")
st.sidebar.number_input("Bezriziková sazba (r)", min_value=0.00, step=0.01, key="r")
st.sidebar.number_input("Volatilita (σ)", min_value=0.01, step=0.01, key="sigma")
st.sidebar.number_input("Dividenda (q)", min_value=0.00, step=0.01, key="dividend")
st.sidebar.selectbox("Typ opce", ["call", "put"], key="option_type")

# Použití hodnot
st.write("Zadány parametry:")
st.json({
    "Aktuální cena": st.session_state["S"],
    "Strike": st.session_state["K"],
    "Dny do expirace": st.session_state["T_days"],
    "Bezriziková sazba": st.session_state["r"],
    "Volatilita": st.session_state["sigma"],
    "Dividenda": st.session_state["dividend"],
    "Typ opce": st.session_state["option_type"]
})
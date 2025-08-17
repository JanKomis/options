import streamlit as st
from classes.option import Option
import streamlit_shadcn_ui as ui
import numpy as np
import plotly.graph_objects as go


st.set_page_config(layout="wide")

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
if "strike_range" not in st.session_state:
    st.session_state["strike_range"] = 10

K_int = int(round(st.session_state["K"]))
st.session_state["strikes"] = np.arange(
    max(0, K_int - st.session_state["strike_range"]),
    K_int + st.session_state["strike_range"] + 1,
    1
)


# Teď jen vykreslíme komponenty, které se samy napojí na session_state
st.sidebar.subheader("Parametry opce")
st.sidebar.number_input("Aktuální cena (S)", min_value=0.01, key="S")
st.sidebar.number_input("Strike cena (K)", min_value=0.01, key="K")
st.sidebar.slider("Dny do expirace", min_value=1, max_value=300, key="T_days")
st.sidebar.number_input("Bezriziková sazba (r)", min_value=0.00, step=0.01, key="r")
st.sidebar.number_input("Volatilita (σ)", min_value=0.01, step=0.01, key="sigma")
st.sidebar.number_input("Dividenda (q)", min_value=0.00, step=0.01, key="dividend")
st.sidebar.selectbox("Typ opce", ["call", "put"], key="option_type")
st.sidebar.subheader("Nastavení grafů")
st.sidebar.number_input("Rozsah striků", min_value=0, step=1, key="strike_range")




# Výpočet ceny opce
opt = Option(
    S=float(st.session_state["S"]),
    K=float(st.session_state["K"]),
    T_days=float(st.session_state["T_days"]),
    r=float(st.session_state["r"]),
    sigma=float(st.session_state["sigma"]),
    dividend=float(st.session_state["dividend"]),
    option_type=st.session_state["option_type"]
)

st.subheader("Parametry opce")
with st.container():
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.metric_card(title="Option type",content=f"{opt.option_type}")
    with col2:
        ui.metric_card(title="Cena opce",content=f"{opt.price()}")
    with col3:
        ui.metric_card(title="Strike cena",content=f"{opt.K}")
    with col4:
        ui.metric_card(title="Aktuální cena",content=f"{opt.S}")



with st.container():
    #col1, col2, col3 = st.columns([1, 1, 1, 1])[:3]  # vezmeme jen první 3 "čtvrtiny"
    col1, col2, col3, col4 = st.columns(4)  # vezmeme jen první 3 "čtvrtiny"

    with col1:
        ui.metric_card(title="Čas",content=f"{opt.T_days}")
    with col2:
        ui.metric_card(title="Bezriziková sazba (r)", content=f"{opt.r}")
    with col3:
        ui.metric_card(title="Volatilita (σ)", content=f"{opt.sigma}")
    with col4:
        ui.metric_card(title="Dividenda", content=f"{opt.dividend}")

st.subheader("Greeky")

with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        ui.metric_card(title="Delta",content=f"{opt.delta()}")
    with col2:
        ui.metric_card(title="Gamma",content=f"{opt.gamma()}")
    with col3:
        ui.metric_card(title="Vega",content=f"{opt.vega()}")
    with col4:
        ui.metric_card(title="Theta",content=f"{opt.theta()}")
    with col5:
        ui.metric_card(title="Rho",content=f"{opt.rho()}")

st.subheader("Grafy")
fig = go.Figure()
fig.add_trace(go.Scatter(x=st.session_state["strikes"], 
                         y=opt.price_for_strikes(st.session_state["strikes"]), 
                         mode="lines", name="sin(x)"))
fig.add_trace(go.Scatter(x=st.session_state["strikes"], 
                         y=opt.price_for_strikes_zero_time(st.session_state["strikes"]),
                        mode="lines", name="cos(x)"))

# Nastavení názvu a popisků os
fig.update_layout(
    title="Porovnání funkcí sin(x) a cos(x)",
    xaxis_title="Hodnoty X",
    yaxis_title="Hodnoty Y"
)

st.plotly_chart(fig, use_container_width=True)
import streamlit as st

st.set_page_config(page_title="Fintech Mini Bank UI")

st.title("🏦 Fintech Mini Bank")
st.write("Bienvenido al sistema bancario.")

st.sidebar.success("Interfaz conectada")

if st.button('Verificar Conexión con API'):
    st.info("Intentando conectar con el backend...")
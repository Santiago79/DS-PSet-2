import streamlit as st
import requests
import os
from datetime import datetime

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(page_title="Fintech Mini Bank UI", layout="wide")

st.title("Fintech Mini Bank")
st.write("Interfaz de gestion bancaria.")

# --- CONFIGURACION DE URL (DOCKER O LOCAL) ---
api_env = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
API_URL = api_env

# --- SIDEBAR: ESTADO Y NAVEGACION ---
st.sidebar.header("Configuracion de Red")
st.sidebar.text(f"Endpoint API: {API_URL}")

if st.sidebar.button("Verificar Estado API"):
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            st.sidebar.info("Estado: En linea")
        else:
            st.sidebar.error(f"Estado: Error {r.status_code}")
    except Exception as e:
        st.sidebar.error(f"Estado: Desconectado")

section = st.sidebar.radio(
    "Menu Principal", 
    ["Gestion de Clientes", "Operaciones Bancarias", "Consultas"]
)

# --- FUNCIONES AUXILIARES ---

def _show_error(resp):
    """Muestra errores de validacion o reglas de negocio."""
    try:
        data = resp.json()
        msg = data.get("detail") if isinstance(data, dict) else data
    except Exception:
        msg = resp.text
    
    st.error(f"Operacion Rechazada (Codigo {resp.status_code}): {msg}")

def _format_transaction(tx):
    """Formatea datos para la visualizacion en tabla."""
    try:
        dt_str = tx["created_at"].replace("Z", "+00:00")
        fecha = datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M")
    except:
        fecha = tx["created_at"]

    return {
        "Fecha": fecha,
        "Tipo": tx["type"],
        "Monto": f"{float(tx['amount']):.2f}",
        "Estado": tx["status"]
    }

# --- IMPLEMENTACION POR SECCIONES ---

if section == "Gestion de Clientes":
    col1, col2 = st.columns(2)

    with col1:
        st.header("Registro de Cliente")
        with st.form("form_customer"):
            name = st.text_input("Nombre completo")
            email = st.text_input("Correo electronico")
            submit_c = st.form_submit_button("Registrar")
        
        if submit_c:
            try:
                # Ruta correcta segun routes.py: /customers
                r = requests.post(f"{API_URL}/customers", json={"name": name, "email": email})
                if r.status_code == 201:
                    res = r.json()
                    st.success(f"ID Cliente generado: {res['id']}")
                else:
                    _show_error(r)
            except Exception as e:
                st.error(f"Error de conexion: {e}")

    with col2:
        st.header("Apertura de Cuenta")
        with st.form("form_account"):
            cust_id = st.text_input("ID del Cliente")
            submit_a = st.form_submit_button("Abrir Cuenta")
        
        if submit_a:
            try:
                # Ruta correcta segun routes.py: /accounts
                r = requests.post(f"{API_URL}/accounts", json={"customer_id": cust_id})
                if r.status_code == 201:
                    res = r.json()
                    st.success(f"ID Cuenta generado: {res['id']}")
                else:
                    _show_error(r)
            except Exception as e:
                st.error(f"Error de conexion: {e}")

elif section == "Operaciones Bancarias":
    st.header("Ejecucion de Transacciones")
    
    op = st.radio("Seleccione el tipo de movimiento", ["Deposito", "Retiro", "Transferencia"], horizontal=True)

    if op == "Deposito":
        with st.form("f_dep"):
            acc_id = st.text_input("ID Cuenta")
            amount = st.number_input("Monto", min_value=0.01)
            if st.form_submit_button("Procesar Deposito"):
                r = requests.post(f"{API_URL}/transactions/deposit", json={"account_id": acc_id, "amount": amount})
                
                # --- CAMBIO AQUÍ: Usar if/else normal ---
                if r.status_code == 201:
                    st.success("¡Depósito realizado con éxito!")
                    # Opcional: mostrar el ID de transacción que devuelve tu API
                    st.json(r.json()) 
                else:
                    _show_error(r)

    elif op == "Retiro":
        with st.form("f_wit"):
            acc_id = st.text_input("ID Cuenta")
            amount = st.number_input("Monto", min_value=0.01)
            if st.form_submit_button("Procesar Retiro"):
                r = requests.post(f"{API_URL}/transactions/withdraw", json={"account_id": acc_id, "amount": amount})
                if r.status_code == 201:
                    st.success("Retiro procesado correctamente")
                else:
                    _show_error(r)

    elif op == "Transferencia":
        with st.form("f_tra"):
            origin = st.text_input("ID Cuenta Origen")
            dest = st.text_input("ID Cuenta Destino")
            amount = st.number_input("Monto", min_value=0.01)
            if st.form_submit_button("Ejecutar Transferencia"):
                r = requests.post(f"{API_URL}/transactions/transfer", json={
                    "from_account_id": origin, 
                    "to_account_id": dest, 
                    "amount": amount
                })
                if r.status_code == 201:
                    st.success("Transferencia enviada con éxito")
                else:
                    _show_error(r)
                    
elif section == "Consultas":
    st.header("Estado de Cuenta y Movimientos")
    acc_id_search = st.text_input("Ingrese ID de la cuenta")

    if acc_id_search:
        col_a, col_b = st.columns([1, 2])
        
        # Consulta de Saldo
        try:
            r_acc = requests.get(f"{API_URL}/accounts/{acc_id_search}")
            if r_acc.ok:
                data = r_acc.json()
                with col_a:
                    # CAMBIO AQUÍ: Convertimos data['balance'] a float antes de formatear
                    balance_value = float(data['balance']) 
                    st.metric("Saldo Actual", f"{data['currency']} {balance_value:.2f}")
                    st.text(f"Estado de cuenta: {data['status']}")
            else:
                _show_error(r_acc)
        except Exception as e:
            st.error(f"Error al consultar saldo: {e}")

        # Consulta de Historial
        try:
            r_tx = requests.get(f"{API_URL}/accounts/{acc_id_search}/transactions")
            if r_tx.ok:
                transactions = r_tx.json()
                with col_b:
                    st.subheader("Historial de Transacciones")
                    if transactions:
                        formatted_txs = [_format_transaction(t) for t in transactions]
                        st.dataframe(formatted_txs, use_container_width=True)
                    else:
                        st.info("No se encontraron registros.")
            else:
                st.warning("No se pudo recuperar el historial.")
        except Exception as e:
            st.error(f"Error al consultar historial: {e}")
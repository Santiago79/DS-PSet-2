import streamlit as st
import requests
import os

# --- CONFIGURACION ---
st.set_page_config(page_title="Fintech Mini Bank", layout="wide")

# La URL interna de Docker segun tu docker-compose
API_URL = os.getenv("API_URL", "http://api:8000")
TIMEOUT = 5

# --- ESTILOS ---
st.title("Fintech Mini Bank - Gestion")

# --- NAVEGACION ---
st.sidebar.header("Menu de Navegacion")
page = st.sidebar.radio("Seleccione una pagina:", ["Crear Cliente", "Crear Cuenta", "Ver Cuenta", "Transacciones", "Historial"])

# --- FUNCIONES DE APOYO (Manejo de errores solicitado) ---

def call_api(method, endpoint, json=None):
    """Manejo basico de errores: timeout y conexion."""
    url = f"{API_URL}/{endpoint.lstrip('/')}"
    try:
        if method == "POST":
            return requests.post(url, json=json, timeout=TIMEOUT)
        return requests.get(url, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        st.error("Error: No se pudo conectar con la API. Verifique que el servicio api este corriendo.")
    except requests.exceptions.Timeout:
        st.error("Error: La respuesta de la API tardo demasiado (Timeout).")
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
    return None

def show_error(resp):
    """Manejo de errores de respuesta sin tocar el backend."""
    if resp.status_code == 500:
        st.error("Error 500: Error interno del servidor.")
        st.info("Nota: Esto ocurre usualmente por datos duplicados (como el email) o problemas en la base de datos.")
    else:
        try:
            # Si la API mando un 400 controlado
            detail = resp.json().get("detail", "Error desconocido")
            st.error(f"Error {resp.status_code}: {detail}")
        except:
            # Si no es un JSON valido
            st.error(f"Error {resp.status_code}: {resp.text}")

# --- PAGINA: CREAR CLIENTE ---
if page == "Crear Cliente":
    st.header("Pagina: Crear Cliente")
    with st.form("form_cliente"):
        name = st.text_input("Nombre completo")
        email = st.text_input("Correo electronico")
        submit = st.form_submit_button("Registrar")

    if submit:
        if name and email:
            res = call_api("POST", "/customers", {"name": name, "email": email})
            if res is not None:
                if res.status_code == 201:
                    data = res.json()
                    st.success("Cliente registrado exitosamente")
                    # Criterio: Muestra ID creado
                    st.code(f"ID del Cliente: {data['id']}", language="text")
                else:
                    show_error(res)
        else:
            st.warning("Debe completar todos los campos")

# --- PAGINA: CREAR CUENTA ---
elif page == "Crear Cuenta":
    st.header("Pagina: Crear Cuenta")
    with st.form("form_cuenta"):
        cust_id = st.text_input("ID del Cliente")
        submit = st.form_submit_button("Crear Cuenta")

    if submit:
        if cust_id:
            res = call_api("POST", "/accounts", {"customer_id": cust_id})
            if res is not None:
                if res.status_code == 201:
                    data = res.json()
                    st.success("Cuenta creada exitosamente")
                    # Criterio: Muestra datos cuenta
                    st.write("### Resumen de la Cuenta")
                    st.json(data)
                else:
                    show_error(res)
        else:
            st.warning("El ID del cliente es requerido")

# --- PAGINA: VER CUENTA ---
elif page == "Ver Cuenta":
    st.header("Pagina: Ver Cuenta")
    # Criterio: input account_id
    acc_id = st.text_input("Ingrese el ID de la cuenta")
    
    if acc_id:
        res = call_api("GET", f"/accounts/{acc_id}")
        if res is not None:
            if res.status_code == 200:
                data = res.json()
                # Criterio: muestra saldo y estado
                st.subheader("Informacion de la Cuenta")
                col1, col2 = st.columns(2)
                # Convertimos balance a float para el metric
                balance = float(data['balance'])
                col1.metric("Saldo Actual", f"{data['currency']} {balance:.2f}")
                col2.metric("Estado", data['status'])
            else:
                show_error(res)

# PARA EL MANEJO DE TRANSACCIONES

# --- FUNCIÓN PARA ERRORES CRÍTICOS ---
def parse_business_error(detail):
    """Mapea errores del backend a mensajes claros segun requerimientos."""
    
    # Convertimos a string por si detail es una lista o dict
    detail_str = str(detail).lower()
    
    if "insufficient" in detail_str:
        return "Fondos insuficientes"
    if "frozen" in detail_str or "operable" in detail_str or "congelada" in detail_str:
        return "Cuenta congelada - no puede operar"
    if "limit" in detail_str or "limite" in detail_str:
        return "Limite diario excedido"
    
    # Si no coincide con ninguno, devuelve el error original limpio
    return detail

# --- LÓGICA DE LA PÁGINA DE TRANSACCIONES ---
if page == "Transacciones":
    st.header("Pagina: Gestion de Transacciones")
    
    # Selector de tipo de operacion mediante pestañas
    tab_dep, tab_wit, tab_tra = st.tabs(["Depositar", "Retirar", "Transferir"])

    # --- PESTAÑA: DEPOSITAR ---
    with tab_dep:
        st.subheader("Deposito de Fondos")
        with st.form("form_deposit"):
            acc_id = st.text_input("ID de la Cuenta")
            amount = st.number_input("Monto a depositar", min_value=0.1, step=10.0, key="dep_amount")
            submit = st.form_submit_button("Ejecutar Deposito")
        
        if submit:
            with st.spinner("Procesando operacion..."):
                res = call_api("POST", "/transactions/deposit", {"account_id": acc_id, "amount": amount})
                if res is not None:
                    if res.status_code == 201:
                        st.success("Operacion realizada con exito")
                        st.json(res.json())
                    else:
                        
                        try:
                            error_data = res.json()
                            detail = error_data.get("detail", "Error desconocido")
                            st.error(parse_business_error(detail))
                        except Exception:
                            st.error(f"Error {res.status_code}: {res.text}")

    # --- PESTAÑA: RETIRAR ---
    with tab_wit:
        st.subheader("Retiro de Fondos")
        with st.form("form_withdraw"):
            acc_id = st.text_input("ID de la Cuenta", key="wit_acc")
            amount = st.number_input("Monto a retirar", min_value=0.1, step=10.0, key="wit_amount")
            submit = st.form_submit_button("Ejecutar Retiro")
        
        if submit:
            with st.spinner("Procesando operacion..."):
                res = call_api("POST", "/transactions/withdraw", {"account_id": acc_id, "amount": amount})
                if res is not None:
                    if res.status_code == 201:
                        st.success("Operacion realizada con exito")
                        st.json(res.json())
                    else:
                        
                        try:
                            error_data = res.json()
                            detail = error_data.get("detail", "Error desconocido")
                            st.error(parse_business_error(detail))
                        except Exception:
                            st.error(f"Error {res.status_code}: {res.text}")

    # --- PESTAÑA: TRANSFERIR ---
    with tab_tra:
        st.subheader("Transferencia entre Cuentas")
        with st.form("form_transfer"):
            origin = st.text_input("ID Cuenta Origen")
            destination = st.text_input("ID Cuenta Destino")
            amount = st.number_input("Monto a transferir", min_value=0.1, step=10.0, key="tra_amount")
            submit = st.form_submit_button("Ejecutar Transferencia")
        
        if submit:
            if origin == destination:
                st.warning("La cuenta de origen y destino no pueden ser la misma")
            else:
                with st.spinner("Procesando transferencia..."):
                    payload = {"from_account_id": origin, "to_account_id": destination, "amount": amount}
                    res = call_api("POST", "/transactions/transfer", payload)
                    if res is not None:
                        if res.status_code == 201:
                            st.success("Operacion realizada con exito")
                            st.json(res.json())
                        else:
                            
                            try:
                                error_data = res.json()
                                detail = error_data.get("detail", "Error desconocido")
                                st.error(parse_business_error(detail))
                            except Exception:
                                st.error(f"Error {res.status_code}: {res.text}")

# --- PÁGINA: HISTORIAL ---
elif page == "Historial":
    st.header("Pagina: Historial de Movimientos")
    acc_id = st.text_input("Ingrese el ID de la cuenta")
    
    if acc_id:
        with st.spinner("Buscando transacciones..."):
            res = call_api("GET", f"/accounts/{acc_id}/transactions")
            if res is not None:
                if res.status_code == 200:
                    txs = res.json()
                    if txs:
                        st.table(txs)
                    else:
                        st.info("No se registraron movimientos para esta cuenta")
                elif res:
                    show_error(res)
# Fintech Mini Bank

Sistema fintech que permite crear clientes, cuentas y realizar transacciones (depósito, retiro y transferencia).  
El proyecto sigue una arquitectura hexagonal con API, frontend y base de datos en contenedores.

Backend con FastAPI,  frontend con Streamlit y base de datos PostgreSQL.

----------

## Cómo ejecutar el proyecto

### Requisitos

-   Docker y Docker Compose instalados
    

### Ejecutar todo el sistema

docker compose up --build

### Accesos

API

http://localhost:8000

Swagger

http://localhost:8000/docs

Frontend

http://localhost:8501

----------
## Instrucciones de uso y despliegue

Ejecutar el sistema con Docker.

Abrir el frontend en:
http://localhost:8501

Desde la interfaz se puede:

Crear clientes

Crear cuentas

Realizar depósitos, retiros y transferencias

Consultar saldo

Ver historial de transacciones

Alternativamente, las operaciones pueden realizarse directamente desde Swagger:

http://localhost:8000/docs

El sistema se compone de tres servicios:

db: PostgreSQL

api: FastAPI

ui: Streamlit

Todos se levantan con un solo comando usando Docker Compose.

----------

## Cómo funciona el sistema

El flujo general es:

Usuario (Streamlit)  
 |
API (FastAPI)  
 | 
BankingFacade  
 |
Servicios de dominio  
 | 
PostgreSQL

### Funcionalidades principales

-   Crear clientes
    
-   Crear cuentas
    
-   Depositar dinero
    
-   Retirar dinero (valida fondos)
    
-   Transferir entre cuentas (operación atómica)
    
-   Consultar saldo
    
-   Ver historial de transacciones
    

### Reglas de negocio

-   No se permite operar con cuentas FROZEN o CLOSED
    
-   No se permiten retiros sin fondos suficientes
    
-   Las transferencias generan débito y crédito
    
-   Se aplican:
    
    -   Fees (comisiones)
        
    -   Reglas de riesgo (límites, validaciones)
        

El frontend no accede a la base de datos, solo consume la API.

----------


## Especificación de API (Endpoints)

### Clientes

#### POST /customers
Crea un nuevo cliente.

Request:

{
  "name": "Juan Perez",
  "email": "juan@example.com"
}

### Cuentas

#### POST /accounts
Crea una cuenta para un cliente.

{
  "customer_id": 1,
  "currency": "USD"
}

#### GET /accounts/{account_id}
Obtiene información de la cuenta y balance.

### Transacciones

#### POST /transactions/deposit

{
  "account_id": 1,
  "amount": 100
}

#### POST /transactions/withdraw

{
  "account_id": 1,
  "amount": 50
}

#### POST /transactions/transfer

{
  "source_account_id": 1,
  "destination_account_id": 2,
  "amount": 25
}

#### GET /accounts/{account_id}/transactions
Lista las transacciones de una cuenta.

----------

## Decisiones de Diseño

### Arquitectura Hexagonal

Se separa el sistema en capas:

-   Domain: entidades y reglas de negocio
    
-   Services: casos de uso
    
-   Repositories: persistencia
    
-   Application: API y DTOs
    
-   Frontend: interfaz de usuario
    

**Por qué:**  
Permite bajo acoplamiento, facilita pruebas y hace el sistema más mantenible.

----------

### Facade Pattern – `BankingFacade`

La API no accede directamente a servicios o repositorios.

Todos los endpoints llaman a:

-   `create_customer()`
    
-   `create_account()`
    
-   `deposit()`
    
-   `withdraw()`
    
-   `transfer()`
    
-   `get_account()`
    
-   `list_transactions()`
    

**Por qué:**  
Centraliza la lógica de entrada y simplifica la capa de aplicación.

----------

## Patrones Creacionales

### 1. Factory Method – `TransactionFactory`

Crea objetos `Transaction` según el tipo:

-   DEPOSIT
    
-   WITHDRAW
    
-   TRANSFER
    

También valida los campos requeridos para cada tipo.
Lo utilizamos para transacciones de DEPÓSITO y RETIRO (transacciones simples)

**Por qué:**

-   Evita lógica condicional repetida
    
-   Centraliza la creación de transacciones
    
-   Facilita agregar nuevos tipos de ser necesario
    

----------

### 2. Builder – `TransactionBuilder / TransferBuilder`


Se utiliza para construir transacciones complejas con múltiples atributos:

-   Cuenta origen y destino
    
-   Monto
    
-   Fee aplicado
    
-   Resultado de reglas de riesgo
    
-   Estado de la transacción
    
-   Timestamp
    
-   Metadata adicional

En este caso EXCLUSIVAMENTE para TRANSFERENCIAS, donde se necesita metadata adicional (fee y resultados de riesgo)

**Por qué:**

-   Las transferencias requieren varios pasos y datos intermedios
    
-   Mejora la legibilidad del código
    
-   Permite construir el objeto de forma controlada 
    

----------

## Frontend

El frontend permite:

-   Crear clientes y cuentas
    
-   Realizar depósitos, retiros y transferencias
    
-   Consultar saldo
    
-   Ver historial
    
-   Mostrar errores del backend (fondos insuficientes, límites, etc.)
    

Streamlit consume los endpoints REST y no contiene lógica de negocio.

---------


## Reglas de Contribución

### Para mantener la calidad del proyecto:

Crear una rama por feature o fix:

feature/nombre-funcionalidad

Cada cambio debe estar asociado a un Issue.

Crear Pull Request hacia main:

Descripción clara del cambio

Referencia al issue (Closes #XX)

Antes de hacer merge:

El proyecto debe levantar con Docker

No romper endpoints existentes

Mantener la estructura de arquitectura hexagonal

### Evitar:

Commits directamente a main

PRs demasiado grandes (mega PR)
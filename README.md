# Ektor Pool Services API

FastAPI & MySQL billing API with CRUD, filtering, and validation — portfolio project modeling real-world business logic.

This project models real-world billing workflows such as recurring invoices, customer ownership, and date-based filtering.

---

## Tech Stack

- **Python 3.12+**
- **FastAPI**
- **SQLAlchemy 2.0**
- **MySQL**
- **Pydantic v2**
- **Uvicorn**

---

## Features

- Customers
- Create customers
- List customers
- Get customer by ID
- Input validation and error handling

## Invoices
- Create invoices
- List invoices with filters:
- status
- customer_id
- property_id
- date ranges
- Get invoice by ID
- Business rule validations:
- period_start must be less than or equal to period_end
- total must equal subtotal plus tax
- valid invoice status only
- customer existence validation

---

## Database Schema

- **customers**
- **properties**
- **invoices**

All tables use proper primary keys, foreign keys, and constraints.

Schema and seed scripts are available in the `/sql` folder.

---

## Setup Instructions

## Clone repository
```git clone https://github.com/your-username/ektor-pool-services-api.git
cd ektor-pool-services-api
```

## Create virtual environment
```python -m venv .venv
Activate the virtual environment
On macOS or Linux:
source .venv/bin/activate
On Windows:
.venv\Scripts\activate
```

## Install dependencies
```
pip install -r requirements.txt
```

## Environment variables
```Create a .env file using the provided example
cp .env.example .env
```
Edit the file and set your database credentials

Run the API
uvicorn app.main:app --reload

---

## API Documentation

Once the server is running, open the following URL in your browser:
http://127.0.0.1:8000/docs

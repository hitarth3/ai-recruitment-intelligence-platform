# 🛒 Product Management REST API

A robust RESTful API for managing products, categories, programming languages, and users with authentication, input validation, and file upload support.

## 🚀 Tech Stack

- **Runtime:** Node.js
- **Framework:** Express.js
- **Database:** PostgreSQL
- **Authentication:** JWT (JSON Web Tokens)
- **Validation:** Express Validator
- **File Upload:** Multer
- **Password Hashing:** bcryptjs

## 📋 Features

- ✅ Full CRUD operations for Products, Categories, and Programming Languages
- ✅ JWT-based Authentication (Login, Register, Protected Routes)
- ✅ Input validation & sanitization using Express Validator
- ✅ Parameterized SQL queries (SQL injection prevention)
- ✅ File upload with Multer handling profile pictures/images
- ✅ Pagination support
- ✅ Centralized global error handling
- ✅ Environment-based configuration using `dotenv`

## ⚡ API Endpoints

### Authentication & Users
- `POST /createuser` - Register new user (validated)
- `POST /login` - Login and receive JWT token
- `POST /profile` - Retrieve user profile (Authorization required)
- `POST /upload` - Upload an image file

### Products
- `GET /product` - Get all products (paginated)
- `POST /product` - Create a new product
- `PUT /product/:id` - Update an existing product
- `DELETE /product/:id` - Delete a product

### Categories
- `GET /category` - Get all categories
- `POST /category` - Create a new category
- `PUT /category/:id` - Update category
- `DELETE /category/:id` - Delete category

### Programming Languages
- `GET /programming-languages` - Get all languages
- `POST /programming-languages` - Add a new language
- `PUT /programming-languages/:id` - Update a language
- `DELETE /programming-languages/:id` - Delete a language

## 🔧 Installation & Setup

### Prerequisites
- Node.js (v16+)
- PostgreSQL installed and running locally or remotely.

### Quick Start
1. Clone this repository and navigate to the root directory.
2. Install the necessary dependencies:
   ```bash
   npm install
   ```
3. Setup your environment variables by creating a `.env` file based off `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Start the application:
   ```bash
   npm run start
   ```

## 🛡️ Security Best Practices Addressed
- **SQL Injection Prevention:** Uses pg library's `$1, $2` parameterized query values in all models instead of template string interpolation.
- **Credential Protection:** Moved credentials to `.env` file outside of version control.
- **Password Security:** Hashes passwords with `bcryptjs` before persisting to database.

## 📄 License
MIT License

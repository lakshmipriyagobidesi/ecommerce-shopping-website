# E-Commerce Shopping Website (Python + Flask)

A beginner-friendly full-stack shopping website with HTML/CSS/JavaScript frontend, Flask backend, and SQLite database.

## Features
- Product catalog with product details
- Search and category filter
- Add, update, and remove cart items
- User registration and login (passwords hashed)
- Checkout with delivery address
- Demo order confirmation and order history
- Stock tracking in SQLite

## Requirements
- Python 3.10 or newer
- Internet connection for remote product images (optional)

## Run on Windows
1. Extract the ZIP.
2. Open the extracted `ecommerce_shopping_website` folder in VS Code.
3. Open Terminal in VS Code.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .venv\Scripts\activate
   ```
6. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the application:
   ```powershell
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then visit `http://127.0.0.1:5000`.

The SQLite database (`shop.db`) and sample products are created automatically on first run.

## Project structure
```text
ecommerce_shopping_website/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── product.html
│   ├── cart.html
│   ├── register.html
│   ├── login.html
│   ├── checkout.html
│   ├── order_confirmation.html
│   ├── my_orders.html
│   └── 404.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Important security notes
- This is a learning/demo project, not production-ready.
- Checkout simulates payment; no real payment provider is connected.
- Before deployment, set a strong random `SECRET_KEY`, turn off Flask debug mode, add CSRF protection, validate inputs more thoroughly, and use HTTPS.
- Product images are remote Unsplash URLs and require internet access.

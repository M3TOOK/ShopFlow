# ShopFlow

#### Video Demo: [https://youtu.be/UFEjXkLZZHo]

## Description

ShopFlow is a web-based inventory and sales management system designed for small businesses and local shops. The main goal of this project is to make daily business operations easier by organizing products, tracking inventory, recording sales, managing expenses, and displaying important business statistics in one place.

Small shop owners often manage their products and sales manually, which can lead to calculation mistakes, inaccurate inventory records, and difficulty tracking business performance. ShopFlow aims to solve these problems through a simple and organized web application.

## Technologies Used

- **Python:** Used for the application logic and server-side operations.
- **Flask:** Used to build the web application and handle routes and requests.
- **SQLite3:** Used to store and manage application data in a database.
- **HTML:** Used to structure the web pages.
- **CSS:** Used to style the interface.
- **JavaScript:** Used for client-side interactions.
- **Tailwind CSS:** Used to create a modern and responsive user interface.

## Features

### Dashboard

The dashboard provides an overview of the business through statistics and summaries, helping users understand the current state of their shop.

### Product Management

Users can add products and manage product information, including product names, prices, and available quantities. Product management is separate from the sales process and does not require creating a customer or sales user for every product.

### Inventory Management

ShopFlow tracks available product quantities. When a sale is recorded, the corresponding quantities are reduced to keep inventory information updated.

### Sales Management

Users can record sales, select products, specify quantities, and calculate the corresponding sale totals. The system stores sales information for later review.

### Sales History

Recorded sales can be reviewed to help users track previous transactions and understand their business activity.

### Expense Management

Users can record business expenses and review them as part of their financial tracking.

### Reports and Statistics

The application brings together important business information to help users monitor sales, expenses, inventory, and overall performance.

### Responsive Interface

The interface is designed to provide a clear and organized experience across different screen sizes.

## Project Files

The project is organized into separate files according to their responsibilities.

- **app.py:** Contains the Flask application, server-side routes, and application logic.
- **templates/:** Contains the HTML templates used to render the application's pages.
- **static/:** Contains static assets such as CSS, JavaScript, and other frontend resources, if included in the project structure.
- **requirements.txt:** Lists the external Python packages required to run the application.
- **README.md:** Documents the project, its features, technologies, and setup instructions.
- **app.db:** Stores the application's data using SQLite, depending on the configured database filename.

The exact files and responsibilities depend on the final project structure.

## Design Decisions

Flask was chosen because it provides a straightforward way to build a web application with Python without requiring a large framework. This allowed the project to focus on its main purpose: inventory and sales management.

SQLite was selected because it is lightweight and suitable for a small-business application that needs structured data storage without requiring a separate database server.

The interface uses a dashboard-based design so that important information is easy to find. Separating product management from sales operations also makes the workflow more logical: products can be added independently, while sales transactions update inventory as needed.

## How to Run the Project

1. Install Python.
2. Open a terminal in the project directory.
3. Install the required dependencies:

   `pip install -r requirements.txt`

4. Start the Flask application using the appropriate entry point. For example:

   `python -m flask --app app run --debug`

5. Open the local address shown in the terminal in your web browser.

The database should be initialized according to the application's database setup code.

## Future Improvements

Possible future improvements include user roles and permissions, exporting reports, printing invoices, advanced filtering, improved data visualization, automated database backups, and deployment to a production server.

## Conclusion

ShopFlow was developed as the final project for CS50x to apply programming concepts to a practical problem. It brings together Python, Flask, SQL, and frontend technologies in a single application intended to make managing a small shop more organized and efficient.

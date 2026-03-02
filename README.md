<p align="center">
  <img src="piggy/assets/piggy.svg" width="128" height="128" alt="Piggy Logo">
</p>

<h1 align="center">Piggy</h1>
<p align="center"><strong>Self-hosted Financial Planning & Budgeting</strong></p>

<p align="center">
  <img src="https://github.com/h4llow3en/piggy/actions/workflows/main.yml/badge.svg" alt="CI/CD Status">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=black" alt="Backend">
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react&logoColor=black" alt="Frontend">
  <img src="https://img.shields.io/badge/Coverage-54%25-brightgreen" alt="Coverage">
  <a href="https://www.buymeacoffee.com/h4llow3En"><img src="https://img.shields.io/badge/Support-Buy%20Me%20A%20Coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee"></a>
</p>

---

Piggy is a self-hosted personal finance application designed to provide clear insights into individual and shared
finances. By aggregating banking data and providing structured visualization, Piggy helps to manage budgets, track
spending habits and maintain a clear overview of financial health, all while keeping data private and under your
control.

---

## Key Features

* **Transaction Import** Fetching transactions from the bank via **FinTS (HBCI)** (currently only DKB implemented).
* **Financial Analytics** Detailed visualization of cashflow, account balances, and spending patterns using
  interactive charts.
* **Budget Management** Define and monitor category-based budgets with real-time progress tracking.
* **Recurring Payments** Automated detection and forecasting of subscriptions and regular expenses for accurate
  balance prognosis.
* **Mobile-Optimized PWA** Fully responsive interface, installable as a **Progressive Web App** for a native-like
  mobile experience.
* **Multi-User & Internationalization** Support for multiple users with role-based access control and full
  localization in **English** and **German**.
* **Theming** Native support for Light and Dark modes, respecting system preferences.

## Quick Start

Deploy your personal instance using Docker.

1.  **Start the environment:**
    Create a `.env` file based on `.env.example` and then run:
    ```bash
    docker compose up -d
    ```
    *Note: The default configuration expects a reverse proxy like **Traefik**. Otherwise, the frontend will not be able to access the API.*

2.  **Access the services:**
    *   **Web Interface:** [http://localhost](http://localhost)
    *   **API Documentation:** [http://localhost/api/docs](http://localhost/api/docs)

3.  **Initial Setup:** Create your account via the registration flow. The first registered user is automatically assigned administrative privileges.

---

## Security & Privacy

* **Self-Hosted** Your financial data remains on your infrastructure.
* **Security Best Practices** Docker images are configured to run as **non-root users**.
* **Robust Authentication** JWT-based authentication with secure refresh token logic and bcrypt password hashing.

---

<p align="center">
  <i>"Control your money, don't let your money control you."</i>
<br/><br/>
  <a href="https://www.buymeacoffee.com/h4llow3En">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" >
  </a>
</p>

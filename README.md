<p align="center">
  <img src="backend/piggy/assets/piggy.svg" width="128" height="128" alt="Piggy Logo">
</p>

<h1 align="center">Piggy</h1>
<p align="center"><strong>Self-hosted Financial Planning & Budgeting</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Development-yellow" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="Backend">
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react&logoColor=black" alt="Frontend">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white" alt="Database">
  <img src="https://img.shields.io/badge/Sync-FinTS-blue" alt="FinTS Sync">
  <img src="https://img.shields.io/badge/Coverage-54%25-brightgreen" alt="Coverage">
</p>

---

Piggy is a self-hosted personal finance application designed to provide clear insights into individual and shared
finances. By aggregating banking data and providing structured visualization, Piggy helps users manage budgets, track
spending habits, and maintain a clear overview of their financial health—all while keeping data private and under your
control.

---

## Key Features

* **Bank Synchronization** – Automated transaction fetching via **FinTS (HBCI)**.
* **Financial Analytics** – Detailed visualization of cashflow, account balances, and spending patterns using
  interactive charts.
* **Budget Management** – Define and monitor category-based budgets with real-time progress tracking.
* **Recurring Payments** – Automated detection and forecasting of subscriptions and regular expenses for accurate
  balance prognosis.
* **Mobile-Optimized PWA** – Fully responsive interface, installable as a **Progressive Web App** for a native-like
  mobile experience.
* **Multi-User & Internationalization** – Support for multiple users with role-based access control and full
  localization in **English** and **German**.
* **Theming** – Native support for Light and Dark modes, respecting system preferences.

---

## Security & Privacy

* **Self-Hosted** – Your financial data remains on your infrastructure.
* **Security Best Practices** – Docker images are configured to run as **non-root users**.
* **Robust Authentication** – JWT-based authentication with secure refresh token logic and bcrypt password hashing.

---

<p align="center">
  <i>"Control your money, don't let your money control you."</i>
</p>

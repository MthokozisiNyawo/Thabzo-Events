# 🎨 THABZO EVENTS - Event Decoration Management System

A comprehensive Flask-based web application for event decoration business management, featuring client booking, gallery management, admin dashboard, and client portal.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Admin Dashboard](#admin-dashboard)
- [Client Portal](#client-portal)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

THABZO EVENTS is a full-featured web application for event decoration businesses. It allows clients to browse services, book events, and manage their bookings, while administrators can manage inquiries, gallery images, team members, services, and more.

### Key Features

- **Unified Authentication** - One login system for both admins and clients
- **Client Portal** - Clients can book events, manage bookings, and view inquiries
- **Admin Dashboard** - Complete management of all site content
- **Gallery Management** - Organize images by event albums
- **Online Booking** - Clients can book events online
- **Blog System** - Publish news and articles
- **FAQ Management** - Manage frequently asked questions
- **Newsletter Subscriptions** - Collect and manage subscribers
- **Activity Logging** - Track all user activities
- **Email Notifications** - Automated email responses
- **Responsive Design** - Works on all devices

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Programming language |
| Flask | 2.3.3 | Web framework |
| SQLAlchemy | 2.0.25 | ORM |
| Flask-Migrate | 4.0.5 | Database migrations |
| Flask-Login | 0.6.3 | Authentication |
| Flask-WTF | 1.1.1 | Form handling |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| Alembic | 1.12.1 | Database migrations |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| HTML5 | - | Structure |
| CSS3 | - | Styling |
| JavaScript (jQuery) | 3.6.0 | Interactivity |
| Font Awesome | 6.4.0 | Icons |
| Google Fonts | - | Typography |
| Chart.js | 4.4.0 | Charts |
| AOS | 2.3.4 | Scroll animations |

### Database
| Technology | Purpose |
|------------|---------|
| SQLite | Development |
| PostgreSQL | Production (recommended) |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Git (optional)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/thabzo-events.git
cd thabzo-events
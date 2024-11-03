# README.md
# Fairness Factor Internal Tools Hub

A secure, authenticated platform for content generation and management tools.

## 🔐 Security Features

- Role-based access control (RBAC)

- JWT-based authentication

- Session management

- Rate limiting

- Audit logging

- Two-factor authentication (optional)

- Encrypted data storage

## 🚀 Quick Start

1. Clone the repository:

```bash

git clone https://github.com/your-org/fairness-factor-internal-tools.git

cd fairness-factor-internal-tools

```

2. Set up environment:

```bash

cp .env.example .env

cp .streamlit/secrets.toml.example .streamlit/secrets.toml

```

3. Configure environment variables in `.env` and secrets in `.streamlit/secrets.toml`

4. Build and run with Docker:

```bash

docker-compose up --build

```

## 🔑 Authentication

### User Roles

- Super Admin: Full system access

- Admin: User management and content tools

- Power User: Enhanced content creation access

- Standard User: Basic content creation

- Guest: View-only access

### Login

Access the application at `http://localhost:8501`

Default admin credentials:

- Username: admin@fairnessfactor.com

- Password: See `.env.example`

## 🛠️ Development Setup

1. Create virtual environment:

```bash

python -m venv venv

source venv/bin/activate # Linux/Mac

.\venv\Scripts\activate # Windows

```

2. Install dependencies:

```bash

pip install -r requirements.txt

```

3. Initialize database:

```bash

python init_db.py

```

4. Run tests:

```bash

pytest

```

5. Start development server:

```bash

streamlit run app.py

```

## 📚 Documentation

- [User Guide](docs/user_guide.md)

- [Admin Guide](docs/admin_guide.md)

- [API Documentation](docs/api.md)

- [Security Overview](docs/security.md)

## 🔒 Security Considerations

1. Change default credentials immediately

2. Rotate JWT keys regularly

3. Monitor audit logs

4. Keep dependencies updated

5. Regular security assessments

## 🧪 Testing

Run all tests:

```bash

pytest

```

Run specific test suite:

```bash

pytest tests/test_auth/

```

## 📝 Contributing

1. Fork the repository

2. Create feature branch

3. Commit changes

4. Push to branch

5. Create Pull Request

## 📄 License

Copyright © 2024 Fairness Factor. All rights reserved.

## 🤝 Support

For support, email support@fairnessfactor.com or create an issue.

## 🔄 Updates

Check [CHANGELOG.md](CHANGELOG.md) for version history.

## Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in required variables:
   - MONGODB_URI
   - JWT_SECRET_KEY
   - ANTHROPIC_API_KEY
3. Set appropriate development/production values
4. Validate environment setup

## Configuration Guide

1. Streamlit Configuration
   - CORS and XSRF settings
   - Server configuration
   - Security settings

2. Application Settings
   - Environment variables
   - API configurations
   - Security settings

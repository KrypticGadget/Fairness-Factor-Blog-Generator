# README.md
# Fairness Factor Blog Generator

## Overview
A professional blog content generation tool built for Fairness Factor, featuring secure authentication, MongoDB integration, and automated content workflows.

## Features
- Secure authentication with domain restriction
- Content generation workflows
- MongoDB integration for data persistence
- File upload and processing
- SEO optimization tools
- User management system

## Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/fairness-factor-blog-generator.git
cd fairness-factor-blog-generator
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize MongoDB:
```bash
python setup_mongodb.py
```

6. Run the application:
```bash
streamlit run app.py
```

## Environment Variables
Create a `.env` file with:
```
MONGODB_URI=your_mongodb_uri
JWT_SECRET_KEY=your_jwt_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
Internal use only - Fairness Factor
```

```text
# packages.txt
python3-dev
build-essential
git
curl
```

```text
# requirements.txt
streamlit==1.29.0
anthropic==0.8.1
python-dotenv==1.0.0
pymongo==4.6.1
dnspython==2.4.2
bcrypt==4.1.1
PyJWT==2.8.0
pandas==2.1.3
pytest==7.4.3
pytest-cov==4.1.0
python-multipart==0.0.6
watchdog==3.0.0
python-docx==1.0.1
PyPDF2==3.0.1
```

```text
# runtime.txt
python-3.9.16
```
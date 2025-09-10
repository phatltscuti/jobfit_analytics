# JobFit Analytics

A Flask-based web application for job and CV management with AI-powered analysis and matching system.

## 🚀 Features

### Core Functionality
- **User Authentication**: Login, logout, profile management
- **CV Management**: Upload PDF CVs with AI-powered analysis
- **Job Management**: Complete CRUD operations for job postings
- **AI-Powered Matching**: Intelligent job-CV compatibility analysis
- **Admin Dashboard**: Beautiful sidebar interface with statistics

### AI Features
- **OpenAI Integration**: Automatic CV text extraction and analysis
- **Smart Matching**: AI-powered job-CV compatibility scoring
- **Manual Editing**: Ability to manually adjust AI analysis results
- **Detailed Reports**: Comprehensive analysis with strengths, weaknesses, and recommendations

### User Interface
- **Modern Design**: Bootstrap 5 with custom styling
- **Responsive Layout**: Works on desktop and mobile devices
- **Sidebar Navigation**: Easy access to all features
- **Real-time Updates**: Dynamic content and statistics

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Modern web browser

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobfit_analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///jobfit_analytics.db
   OPENAI_API_KEY=your-openai-api-key-here
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   FLASK_DEBUG=True
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 🔑 Default Login

- **Username**: admin
- **Password**: password123

## 📖 Usage Guide

### 1. Dashboard
- View system statistics
- Quick access to all features
- Recent activity overview

### 2. CV Management
- Upload PDF CVs
- AI automatically extracts and analyzes information
- Edit CV details manually
- View CV analytics

### 3. Job Management
- Create new job postings
- Edit existing jobs
- Manage job status
- Set application deadlines

### 4. Job Matching
- Select CV and Job for analysis
- AI-powered compatibility scoring
- Detailed analysis with recommendations
- Manual editing of results
- Export analysis reports

### 5. Profile & Settings
- View user statistics
- Manage account settings
- Configure AI preferences

## 🎯 Key Features Explained

### AI-Powered CV Analysis
- Automatically extracts text from PDF CVs
- Uses OpenAI GPT to analyze and structure data
- Identifies key information: name, contact, education, experience, skills
- Generates SVG avatars for visual representation

### Smart Job Matching
- Compares CV qualifications with job requirements
- Provides compatibility score (0-100)
- Lists strengths and areas for improvement
- Offers actionable recommendations
- Allows manual adjustment of results

### Modern Admin Interface
- Clean, professional design
- Intuitive sidebar navigation
- Responsive layout
- Real-time statistics
- Flash message notifications

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask application secret key
- `DATABASE_URL`: Database connection string (SQLite by default)
- `OPENAI_API_KEY`: Required for AI features
- `FLASK_HOST`: Host address (default: 0.0.0.0)
- `FLASK_PORT`: Port number (default: 5000)
- `FLASK_DEBUG`: Debug mode (default: True)

### Database
- Uses SQLite by default
- Automatic table creation
- User relationships with CVs and Jobs
- Migrations handled automatically

## 📁 Project Structure

```
jobfit_analytics/
├── app.py                 # Main Flask application
├── run.py                 # Application runner
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── static/                # Static assets
│   ├── css/              # Custom styles
│   ├── js/               # JavaScript files
│   └── uploads/          # Uploaded files
│       ├── cvs/          # CV PDFs
│       └── avatars/      # Generated avatars
└── templates/            # HTML templates
    ├── layouts/          # Base templates
    ├── auth/             # Authentication pages
    ├── cvs/              # CV management pages
    ├── jobs/             # Job management pages
    └── matching.html     # Job matching page
```

## 🚀 Getting Started

1. **First Time Setup**
   - Run the application
   - Login with admin credentials
   - Upload a test CV
   - Create a sample job posting
   - Try the matching feature

2. **Adding CVs**
   - Go to CV Management
   - Click "Upload CV"
   - Select a PDF file
   - AI will automatically analyze and extract information
   - Review and edit if needed

3. **Creating Jobs**
   - Go to Job Management
   - Click "Create Job"
   - Fill in job details
   - Set requirements and benefits
   - Save the job posting

4. **Matching Analysis**
   - Go to Job Matching
   - Select a CV and Job
   - Click "Analyze Match"
   - Review AI analysis
   - Edit results if needed

## 🔒 Security Features

- Password hashing with Werkzeug
- User authentication with Flask-Login
- File upload validation
- SQL injection protection
- XSS protection

## 🎨 Customization

### Styling
- Modify CSS in `templates/layouts/base.html`
- Custom color scheme in CSS variables
- Responsive design with Bootstrap 5

### AI Analysis
- Adjust OpenAI prompts in `app.py`
- Modify analysis parameters
- Add custom analysis fields

## 📊 Database Schema

### Users
- id, username, email, password_hash, is_admin, created_at

### CVs
- id, name, email, phone, address, education, experience, skills, file_path, avatar, user_id, created_at, updated_at

### Jobs
- id, title, description, company, location, salary_range, employment_type, requirements, benefits, application_deadline, is_active, user_id, created_at, updated_at

### Settings
- id, auto_extract, email_notifications, created_at, updated_at

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the code comments
- Create an issue on GitHub

## 🔮 Future Enhancements

- Email notifications
- Advanced analytics dashboard
- Bulk CV processing
- Export functionality
- API endpoints
- Multi-language support
- Advanced matching algorithms
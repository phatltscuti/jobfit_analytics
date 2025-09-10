from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta, timezone
import PyPDF2
import openai
import requests
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory

# Make language detection deterministic
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root%40123@dev.scuti.works:3307/hakathon')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OpenAI configuration
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Default matching criteria used when user does not provide custom criteria
DEFAULT_MATCHING_CRITERIA = (
    "Bạn là một hệ thống chấm điểm mức độ phù hợp giữa Job Description (JD) và CV ứng viên.\n\n"
    "## Nhiệm vụ\n"
    "- So sánh JD và CV theo 15 tiêu chí sau.\n"
    "- Chấm điểm mỗi tiêu chí theo thang 0–100% theo đúng công thức.\n"
    "- Nhân với Trọng số để tính điểm quy đổi.\n"
    "- Tính tổng điểm = Σ(Điểm × Trọng số) / 30.\n"
    "- Xuất kết quả gồm:\n"
    "  1. Bảng chi tiết: [Tiêu chí | Điểm (%) | Trọng số | Điểm quy đổi | Giải thích]\n"
    "  2. Tổng điểm cuối cùng (%)\n"
    "  3. Mức đánh giá (Excellent / Good / Average / Low match / Not match)\n\n"
    "## Công thức cho từng tiêu chí\n"
    "1. Seniority / Level (Trọng số 3, Must-have)\n"
    "   - Bằng JD = 100%; Thấp hơn = 0%; Cao hơn 1 bậc = 75%; Cao hơn 2 bậc = 60%; Cao hơn ≥3 bậc = 50%\n\n"
    "2. Core Skills (Trọng số 3, Must-have)\n"
    "   - ≥80% skill JD có trong CV = 100%; 50–79% = 50%; <50% = 0%\n\n"
    "3. Ngôn ngữ yêu cầu (Trọng số 3, Must-have)\n"
    "   - Đúng yêu cầu = 100%; Thấp hơn 1 bậc = 70%; Thấp hơn ≥2 bậc hoặc không có = 0%\n\n"
    "4. Địa điểm / Work model (Trọng số 3, Must-have)\n"
    "   - Trùng = 100%; Khác = 0%\n\n"
    "5. Visa / Quyền lao động (Trọng số 3, Must-have)\n"
    "   - Đáp ứng = 100%; Không = 0%\n\n"
    "6. Secondary Skills (Trọng số 2, High)\n"
    "   - (Số skill khớp / Tổng skill nice-to-have) × 100%\n\n"
    "7. Số năm kinh nghiệm (Trọng số 2, High)\n"
    "   - CV ≥ JD = 100%; Nếu thiếu: 100% – (20% × số năm thiếu), min = 0%\n\n"
    "8. Recency (Trọng số 2, High)\n"
    "   - Skill chính JD xuất hiện trong: ≤2 năm = 100%; 3–5 năm = 70%; >5 năm = 40%; Không có = 0%\n\n"
    "9. Domain / Industry (Trọng số 2, High)\n"
    "   - Đúng domain = 100%; Gần giống = 70%; Khác hoàn toàn = 0%\n\n"
    "10. Thành tích / KPI (Trọng số 2, High)\n"
    "    - Có KPI định lượng liên quan JD = 100%; Có nhưng không định lượng = 70%; Không có = 0%\n\n"
    "11. Stack / Tool version (Trọng số 2, High)\n"
    "    - Đúng tool/version = 100%; Tool đúng nhưng version thấp hơn = 70%; Tool khác tương tự = 50%; Không liên quan = 0%\n\n"
    "12. Soft skills (Trọng số 1, Medium)\n"
    "    - Có rõ ràng (teamwork, leadership, communication) = 100%; Có nhưng chung chung = 50%; Không có = 0%\n\n"
    "13. Culture / Process fit (Trọng số 1, Medium)\n"
    "    - Agile/Scrum/Startup đúng JD = 100%; Khác framework = 50%; Không có = 0%\n\n"
    "14. Extra languages (Trọng số 1, Medium)\n"
    "    - Có đúng bonus = 100%; Có ngôn ngữ khác hữu ích = 50%; Không có = 0%\n\n"
    "15. Certificates (Trọng số 1, Low)\n"
    "    - Có đúng chứng chỉ bắt buộc = 100%; Có chứng chỉ liên quan khác = 50%; Không có = 0%\n\n"
    "## Thang đánh giá\n"
    "- Excellent: ≥85%\n"
    "- Good: 70–84%\n"
    "- Average: 50–69%\n"
    "- Low match: 30–49%\n"
    "- Not match: <30%\n\n"
    "## Output\n"
    "- Bảng chấm điểm chi tiết 15 tiêu chí\n"
    "- Tổng điểm (%)\n"
    "- Nhận xét mức độ phù hợp\n"
)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'cvs'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    cvs = db.relationship('CV', backref='uploaded_by', lazy=True)
    jobs = db.relationship('Job', backref='created_by', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    skills = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    avatar = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Matching criteria fields (candidate-side)
    cv_seniority = db.Column(db.String(50))
    cv_core_skills = db.Column(db.Text)
    cv_languages = db.Column(db.String(200))
    cv_work_model = db.Column(db.String(50))
    cv_visa_status = db.Column(db.String(50))
    cv_secondary_skills = db.Column(db.Text)
    cv_years_experience = db.Column(db.Integer)
    cv_recency_years = db.Column(db.Integer)
    cv_domain = db.Column(db.String(100))
    cv_kpi = db.Column(db.Text)
    cv_stack_versions = db.Column(db.Text)
    cv_soft_skills = db.Column(db.Text)
    cv_culture_process = db.Column(db.String(100))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(200))
    location = db.Column(db.String(200))
    salary_min = db.Column(db.Numeric(10, 2))
    salary_max = db.Column(db.Numeric(10, 2))
    employment_type = db.Column(db.String(50))
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)
    application_deadline = db.Column(db.DateTime)
    hiring_quantity = db.Column(db.Integer, default=1)
    experience_level = db.Column(db.String(50))  # Entry, Mid, Senior, Lead
    work_mode = db.Column(db.String(50))  # Remote, On-site, Hybrid
    industry = db.Column(db.String(100))
    skills_required = db.Column(db.Text)
    education_required = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Matching criteria fields (JD-side)
    criteria_seniority = db.Column(db.String(50))
    criteria_core_skills = db.Column(db.Text)
    criteria_language = db.Column(db.String(100))
    criteria_work_model = db.Column(db.String(50))
    criteria_visa_required = db.Column(db.Boolean)
    criteria_secondary_skills = db.Column(db.Text)
    criteria_years_experience = db.Column(db.Integer)
    criteria_recency_years = db.Column(db.Integer)
    criteria_domain = db.Column(db.String(100))
    criteria_kpi_required = db.Column(db.Boolean)
    criteria_stack_versions = db.Column(db.Text)
    criteria_soft_skills = db.Column(db.Text)
    criteria_culture_process = db.Column(db.String(100))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto_extract = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add CSRF token to template context
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# Utility functions
def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def analyze_cv_with_openai(text):
    """Analyze CV text using OpenAI API and extract full 13-field criteria."""
    try:
        # Try to detect source language to preserve original language in outputs
        src_lang = None
        try:
            src_lang = detect(text) if text and text.strip() else None
        except Exception:
            src_lang = None

        lang_instr = "Return ALL field values strictly in the ORIGINAL LANGUAGE of the CV. DO NOT TRANSLATE OR PARAPHRASE."  # default
        if src_lang == 'vi':
            lang_instr = (
                "Toan bo gia tri phai giu NGUYEN NGON NGU TIENG VIET nhu trong CV. KHONG dich, khong viet lai. "
                "Dung nguyen cum tu/ cau trong CV neu co the."
            )

        prompt = f"""
        You are a strict JSON generator. Extract CV info as a SINGLE JSON object.
        {lang_instr}
        All values MUST be strings, except years/recency which can be integers. No extra commentary.
        Required keys:
        {{
          "name": "",
          "email": "",
          "phone": "",
          "address": "",
          "education": "",
          "experience": "",
          "skills": "",
          "seniority": "Entry|Mid|Senior|Lead|",
          "core_skills": "comma separated",
          "languages": "e.g., English B2; Japanese N3",
          "work_model": "Remote|On-site|Hybrid|",
          "visa_status": "Eligible|Not Eligible|",
          "secondary_skills": "comma separated",
          "years_experience": 0,
          "recency_years": 0,
          "domain": "e.g., Fintech|E-commerce|",
          "kpi": "quantified achievements (use original phrases)",
          "stack_versions": "e.g., React 18, Node 18",
          "soft_skills": "comma separated",
          "culture_process": "e.g., Agile, Scrum"
        }}

        CV Text:
        {text[:3000]}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You must output ONLY a valid JSON object. Do not translate; preserve original language exactly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.2
        )

        result = response.choices[0].message.content.strip()
        # Attempt to find JSON object boundaries if model included extra text
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            result = result[start:end+1]
        data = json.loads(result)

        # Normalize to strings where applicable
        processed_data = {}
        for key, value in data.items():
            if key in ("years_experience", "recency_years"):
                try:
                    processed_data[key] = int(value) if value is not None and str(value).strip() != '' else None
                except Exception:
                    processed_data[key] = None
            else:
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        processed_data[key] = ', '.join(str(item) for item in value)
                    else:
                        processed_data[key] = str(value)
                else:
                    processed_data[key] = str(value) if value is not None else ""

        return processed_data
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "address": "",
            "education": "",
            "experience": "",
            "skills": "",
            "seniority": "",
            "core_skills": "",
            "languages": "",
            "work_model": "",
            "visa_status": "",
            "secondary_skills": "",
            "years_experience": None,
            "recency_years": None,
            "domain": "",
            "kpi": "",
            "stack_versions": "",
            "soft_skills": "",
            "culture_process": ""
        }


# Routes
@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        # Skip password verification; auto-create user if not exists
        if not username:
            flash('Username is required', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()
        if not user:
            # Auto-create a user without verifying password
            user = User(
                username=username,
                email=f"{username}@example.com",
                is_admin=True if username.lower() == 'admin' else False
            )
            # Set a default password to satisfy model constraints
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Clear any old flash messages when accessing dashboard
    session.pop('_flashes', None)
    cv_count = CV.query.count()
    job_count = Job.query.count()
    active_jobs = Job.query.filter_by(is_active=True).count()
    
    # Recent CVs (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_cvs = CV.query.filter(CV.created_at >= week_ago).count()
    
    # Jobs expiring soon (next 7 days)
    next_week = datetime.now(timezone.utc) + timedelta(days=7)
    expiring_jobs = Job.query.filter(
        Job.application_deadline <= next_week,
        Job.is_active == True
    ).count()
    
    # Get recent CVs and jobs for activity feed
    recent_cvs_list = CV.query.filter(CV.created_at >= week_ago).order_by(CV.created_at.desc()).limit(3).all()
    recent_jobs_list = Job.query.filter(Job.created_at >= week_ago).order_by(Job.created_at.desc()).limit(3).all()
    
    # Calculate CV uploads by day of week (last 7 days)
    cv_weekly_data = []
    for i in range(7):
        day_start = datetime.now(timezone.utc) - timedelta(days=6-i)
        day_end = day_start + timedelta(days=1)
        day_count = CV.query.filter(
            CV.created_at >= day_start,
            CV.created_at < day_end
        ).count()
        cv_weekly_data.append(day_count)
    
    # Calculate total matches (simplified - could be enhanced with actual matching logic)
    total_matches = min(cv_count, job_count) if cv_count > 0 and job_count > 0 else 0
    
    stats = {
        'total_cvs': cv_count,
        'total_jobs': job_count,
        'active_jobs': active_jobs,
        'recent_cvs': recent_cvs,
        'expiring_jobs': expiring_jobs,
        'total_matches': total_matches,
        'cv_weekly_data': cv_weekly_data
    }
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_cvs=recent_cvs_list, 
                         recent_jobs=recent_jobs_list)

@app.route('/cvs')
@login_required
def cvs_index():
    page = request.args.get('page', 1, type=int)
    
    # Calculate date ranges
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Filter CVs by current user or show all if admin
    if current_user.is_admin:
        cvs = CV.query.order_by(CV.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        # Calculate stats for admin (all CVs)
        this_week_cvs = CV.query.filter(CV.created_at >= week_start).count()
        this_month_cvs = CV.query.filter(CV.created_at >= month_start).count()
    else:
        cvs = CV.query.filter(
            (CV.user_id == current_user.id) | (CV.user_id.is_(None))
        ).order_by(CV.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        # Calculate stats for current user
        this_week_cvs = CV.query.filter(
            ((CV.user_id == current_user.id) | (CV.user_id.is_(None))),
            CV.created_at >= week_start
        ).count()
        this_month_cvs = CV.query.filter(
            ((CV.user_id == current_user.id) | (CV.user_id.is_(None))),
            CV.created_at >= month_start
        ).count()
    
    return render_template('cvs/index.html', 
                         cvs=cvs, 
                         this_week_cvs=this_week_cvs, 
                         this_month_cvs=this_month_cvs)

@app.route('/cvs/create', methods=['GET', 'POST'])
@login_required
def cvs_create():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render_template('cvs/create.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('cvs/create.html')
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            timestamp = int(datetime.now(timezone.utc).timestamp())
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cvs', filename)
            file.save(file_path)
            
            # Extract text from PDF
            text = extract_text_from_pdf(file_path)
            
            # Analyze with OpenAI
            ai_data = analyze_cv_with_openai(text)

            # Language detection fallback/merge
            try:
                detected_lang = detect(text) if text and text.strip() else None
            except Exception:
                detected_lang = None
            if detected_lang:
                if not ai_data.get('languages'):
                    ai_data['languages'] = detected_lang
                else:
                    langs = ai_data['languages']
                    if detected_lang.lower() not in langs.lower():
                        ai_data['languages'] = f"{langs}, {detected_lang}"
            
            # Fallback if AI analysis fails
            if not ai_data or not ai_data.get('name'):
                ai_data = {
                    'name': 'Unknown',
                    'email': '',
                    'phone': '',
                    'address': '',
                    'education': '',
                    'experience': '',
                    'skills': ''
                }
            
            # Create CV record
            cv = CV(
                name=ai_data.get('name', 'Unknown'),
                email=ai_data.get('email', ''),
                phone=ai_data.get('phone', ''),
                address=ai_data.get('address', ''),
                education=ai_data.get('education', ''),
                experience=ai_data.get('experience', ''),
                skills=ai_data.get('skills', ''),
                file_path=f"cvs/{filename}",
                user_id=current_user.id,
                # Try to prefill CV criteria if AI returned similar fields (best-effort)
                cv_seniority=ai_data.get('seniority'),
                cv_core_skills=ai_data.get('core_skills'),
                cv_languages=ai_data.get('languages'),
                cv_work_model=ai_data.get('work_model'),
                cv_visa_status=ai_data.get('visa_status'),
                cv_secondary_skills=ai_data.get('secondary_skills'),
                cv_years_experience=ai_data.get('years_experience'),
                cv_recency_years=ai_data.get('recency_years'),
                cv_domain=ai_data.get('domain'),
                cv_kpi=ai_data.get('kpi'),
                cv_stack_versions=ai_data.get('stack_versions'),
                cv_soft_skills=ai_data.get('soft_skills'),
                cv_culture_process=ai_data.get('culture_process')
            )
            
            # Use default avatar
            cv.avatar = "default-avatar.svg"
            
            db.session.add(cv)
            db.session.commit()
            
            flash('CV uploaded and analyzed successfully!', 'success')
            return redirect(url_for('cvs_index'))
        else:
            flash('Please upload a PDF file', 'error')
    
    return render_template('cvs/create.html')

@app.route('/cvs/<int:cv_id>')
@login_required
def cvs_show(cv_id):
    cv = CV.query.get_or_404(cv_id)
    return render_template('cvs/show.html', cv=cv)

@app.route('/cvs/<int:cv_id>/edit', methods=['GET', 'POST'])
@login_required
def cvs_edit(cv_id):
    cv = CV.query.get_or_404(cv_id)
    
    if request.method == 'POST':
        cv.name = request.form['name']
        cv.email = request.form['email']
        cv.phone = request.form['phone']
        cv.address = request.form['address']
        cv.education = request.form['education']
        cv.experience = request.form['experience']
        cv.skills = request.form['skills']
        # Matching criteria (CV) updates
        cv.cv_seniority = request.form.get('cv_seniority') or None
        cv.cv_core_skills = request.form.get('cv_core_skills') or None
        cv.cv_languages = request.form.get('cv_languages') or None
        cv.cv_work_model = request.form.get('cv_work_model') or None
        cv.cv_visa_status = request.form.get('cv_visa_status') or None
        cv.cv_secondary_skills = request.form.get('cv_secondary_skills') or None
        cv.cv_years_experience = int(request.form.get('cv_years_experience')) if request.form.get('cv_years_experience') else None
        cv.cv_recency_years = int(request.form.get('cv_recency_years')) if request.form.get('cv_recency_years') else None
        cv.cv_domain = request.form.get('cv_domain') or None
        cv.cv_kpi = request.form.get('cv_kpi') or None
        cv.cv_stack_versions = request.form.get('cv_stack_versions') or None
        cv.cv_soft_skills = request.form.get('cv_soft_skills') or None
        cv.cv_culture_process = request.form.get('cv_culture_process') or None
        cv.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('CV updated successfully!', 'success')
        return redirect(url_for('cvs_show', cv_id=cv.id, success='true'))
    
    return render_template('cvs/edit.html', cv=cv)

@app.route('/cvs/<int:cv_id>/view')
@login_required
def cvs_view_pdf(cv_id):
    """View PDF file"""
    cv = CV.query.get_or_404(cv_id)
    
    # Check if user owns this CV or is admin
    if cv.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this CV', 'error')
        return redirect(url_for('cvs_index'))
    
    if not cv.file_path:
        flash('No PDF file found for this CV', 'error')
        return redirect(url_for('cvs_index'))
    
    # Get the full path to the PDF file
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], cv.file_path)
    
    if not os.path.exists(pdf_path):
        flash('PDF file not found', 'error')
        return redirect(url_for('cvs_index'))
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=False, mimetype='application/pdf')

@app.route('/cvs/<int:cv_id>/delete', methods=['POST'])
@login_required
def cvs_delete(cv_id):
    cv = CV.query.get_or_404(cv_id)
    
    # Check if user has permission to delete this CV
    if not current_user.is_admin and cv.user_id != current_user.id:
        flash('You do not have permission to delete this CV.', 'error')
        return redirect(url_for('cvs_index'))
    
    try:
        # Delete files
        if cv.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], cv.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if cv.avatar:
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], cv.avatar)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        
        db.session.delete(cv)
        db.session.commit()
        
        flash('CV deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting CV. Please try again.', 'error')
        print(f"Error deleting CV: {e}")
    
    return redirect(url_for('cvs_index'))

@app.route('/jobs')
@login_required
def jobs_index():
    page = request.args.get('page', 1, type=int)
    
    # Calculate date ranges
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Filter Jobs by current user or show all if admin
    if current_user.is_admin:
        jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        # Get stats for admin (all jobs)
        this_week_jobs = Job.query.filter(
            Job.is_active == True,
            Job.created_at >= week_ago
        ).count()
        this_month_jobs = Job.query.filter(
            Job.is_active == True,
            Job.created_at >= month_ago
        ).count()
    else:
        jobs = Job.query.filter(
            ((Job.user_id == current_user.id) | (Job.user_id.is_(None))) & (Job.is_active == True)
        ).order_by(Job.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        # Get stats for user (their jobs only)
        this_week_jobs = Job.query.filter(
            ((Job.user_id == current_user.id) | (Job.user_id.is_(None))) & (Job.is_active == True),
            Job.created_at >= week_ago
        ).count()
        this_month_jobs = Job.query.filter(
            ((Job.user_id == current_user.id) | (Job.user_id.is_(None))) & (Job.is_active == True),
            Job.created_at >= month_ago
        ).count()
    
    return render_template('jobs/index.html', 
                         jobs=jobs, 
                         pagination=jobs,
                         this_week_jobs=this_week_jobs,
                         this_month_jobs=this_month_jobs)

@app.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def jobs_create():
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            description=request.form['description'],
            company=request.form['company'],
            location=request.form['location'],
            salary_min=float(request.form['salary_min']) if request.form['salary_min'] else None,
            salary_max=float(request.form['salary_max']) if request.form['salary_max'] else None,
            employment_type=request.form['employment_type'],
            requirements=request.form['requirements'],
            benefits=request.form.get('benefits', ''),
            application_deadline=datetime.strptime(request.form['application_deadline'], '%Y-%m-%d') if request.form.get('application_deadline') else None,
            hiring_quantity=int(request.form['hiring_quantity']) if request.form.get('hiring_quantity') else 1,
            experience_level=request.form.get('experience_level', ''),
            work_mode=request.form.get('work_mode', ''),
            industry=request.form.get('industry', ''),
            skills_required=request.form.get('skills_required', ''),
            education_required=request.form.get('education_required', ''),
            # Matching criteria inputs
            criteria_seniority=request.form.get('criteria_seniority') or None,
            criteria_core_skills=request.form.get('criteria_core_skills') or None,
            criteria_language=request.form.get('criteria_language') or None,
            criteria_work_model=request.form.get('criteria_work_model') or None,
            criteria_visa_required=(True if request.form.get('criteria_visa_required')=='true' else (False if request.form.get('criteria_visa_required')=='false' else None)),
            criteria_secondary_skills=request.form.get('criteria_secondary_skills') or None,
            criteria_years_experience=int(request.form.get('criteria_years_experience')) if request.form.get('criteria_years_experience') else None,
            criteria_recency_years=int(request.form.get('criteria_recency_years')) if request.form.get('criteria_recency_years') else None,
            criteria_domain=request.form.get('criteria_domain') or None,
            criteria_kpi_required=(True if request.form.get('criteria_kpi_required')=='true' else (False if request.form.get('criteria_kpi_required')=='false' else None)),
            criteria_stack_versions=request.form.get('criteria_stack_versions') or None,
            criteria_soft_skills=request.form.get('criteria_soft_skills') or None,
            criteria_culture_process=request.form.get('criteria_culture_process') or None,
            user_id=current_user.id
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job created successfully!', 'success')
        return redirect(url_for('jobs_index'))
    
    return render_template('jobs/create.html')

@app.route('/jobs/<int:job_id>')
@login_required
def jobs_show(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/show.html', job=job)

@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def jobs_edit(job_id):
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.company = request.form['company']
        job.location = request.form['location']
        job.salary_min = float(request.form['salary_min']) if request.form['salary_min'] else None
        job.salary_max = float(request.form['salary_max']) if request.form['salary_max'] else None
        job.employment_type = request.form['employment_type']
        job.requirements = request.form['requirements']
        job.benefits = request.form.get('benefits', '')
        job.application_deadline = datetime.strptime(request.form['application_deadline'], '%Y-%m-%d') if request.form.get('application_deadline') else None
        job.hiring_quantity = int(request.form['hiring_quantity']) if request.form.get('hiring_quantity') else 1
        job.experience_level = request.form.get('experience_level', '')
        job.work_mode = request.form.get('work_mode', '')
        job.industry = request.form.get('industry', '')
        job.skills_required = request.form.get('skills_required', '')
        job.education_required = request.form.get('education_required', '')
        # Matching criteria inputs
        job.criteria_seniority = request.form.get('criteria_seniority') or None
        job.criteria_core_skills = request.form.get('criteria_core_skills') or None
        job.criteria_language = request.form.get('criteria_language') or None
        job.criteria_work_model = request.form.get('criteria_work_model') or None
        job.criteria_visa_required = (True if request.form.get('criteria_visa_required')=='true' else (False if request.form.get('criteria_visa_required')=='false' else None))
        job.criteria_secondary_skills = request.form.get('criteria_secondary_skills') or None
        job.criteria_years_experience = int(request.form.get('criteria_years_experience')) if request.form.get('criteria_years_experience') else None
        job.criteria_recency_years = int(request.form.get('criteria_recency_years')) if request.form.get('criteria_recency_years') else None
        job.criteria_domain = request.form.get('criteria_domain') or None
        job.criteria_kpi_required = (True if request.form.get('criteria_kpi_required')=='true' else (False if request.form.get('criteria_kpi_required')=='false' else None))
        job.criteria_stack_versions = request.form.get('criteria_stack_versions') or None
        job.criteria_soft_skills = request.form.get('criteria_soft_skills') or None
        job.criteria_culture_process = request.form.get('criteria_culture_process') or None
        job.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('jobs_show', job_id=job.id, success='true'))
    
    return render_template('jobs/edit.html', job=job)

@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def jobs_delete(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('jobs_index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/matching', methods=['GET', 'POST'])
@login_required
def matching():
    """Job and CV matching page with multi-CV selection"""
    # Filter CVs and Jobs by current user or show all if admin
    if current_user.is_admin:
        cvs = CV.query.order_by(CV.created_at.desc()).all()
        jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).all()
    else:
        cvs = CV.query.filter(
            (CV.user_id == current_user.id) | (CV.user_id.is_(None))
        ).order_by(CV.created_at.desc()).all()
        jobs = Job.query.filter(
            ((Job.user_id == current_user.id) | (Job.user_id.is_(None))) & (Job.is_active == True)
        ).order_by(Job.created_at.desc()).all()

    selected_job = None
    selected_cv_ids = []
    match_results = []
    pass_threshold = 70
    criteria = ''

    # Support preselect via query param
    pre_job_id = request.args.get('job_id', type=int)
    if pre_job_id:
        selected_job = Job.query.get(pre_job_id)

    if request.method == 'POST':
        job_id = request.form.get('job_id', type=int)
        # read threshold and criteria
        try:
            pass_threshold = int(request.form.get('pass_threshold', pass_threshold))
        except (TypeError, ValueError):
            pass_threshold = 70
        criteria = (request.form.get('criteria') or '').strip()

        selected_cv_ids = request.form.getlist('cv_ids')
        selected_cv_ids = [int(cv_id) for cv_id in selected_cv_ids if cv_id.isdigit()]

        # If no CVs explicitly selected, default to all available CVs in scope
        if job_id and not selected_cv_ids:
            selected_cv_ids = [cv.id for cv in cvs]

        if job_id and selected_cv_ids:
            selected_job = Job.query.get_or_404(job_id)
            for cv_id in selected_cv_ids:
                cv = CV.query.get_or_404(cv_id)

                cv_text = f"""
                Name: {cv.name}
                Email: {cv.email}
                Phone: {cv.phone}
                Address: {cv.address}
                Education: {cv.education}
                Experience: {cv.experience}
                Skills: {cv.skills}
                """

                job_text = f"""
                Title: {selected_job.title}
                Company: {selected_job.company}
                Description: {selected_job.description}
                Requirements: {selected_job.requirements}
                Location: {selected_job.location}
                Employment Type: {selected_job.employment_type}
                Salary Min: {selected_job.salary_min}
                Salary Max: {selected_job.salary_max}
                """
                if criteria:
                    job_text += f"\nCustom Matching Criteria (must prioritize these):\n{criteria}\n"
                else:
                    job_text += f"\nDefault Matching Rubric (strictly follow):\n{DEFAULT_MATCHING_CRITERIA}\n"

                analysis = analyze_job_cv_match(cv_text, job_text)
                score = analysis.get('match_score', 0)
                strengths = analysis.get('strengths', [])
                weaknesses = analysis.get('weaknesses', [])
                recommendations = analysis.get('recommendations', [])

                match_results.append({
                    'cv': cv,
                    'match_score': score,
                    'pass': score >= pass_threshold,
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'recommendations': recommendations
                })

            # Sort results by score desc
            match_results.sort(key=lambda r: r['match_score'], reverse=True)

    return render_template(
        'matching.html',
        cvs=cvs,
        jobs=jobs,
        selected_job=selected_job,
        selected_cv_ids=selected_cv_ids,
        match_results=match_results,
        pass_threshold=pass_threshold,
        criteria=criteria
    )

@app.route('/api/match', methods=['POST'])
@login_required
def api_match():
    """API endpoint for matching CV and Job using OpenAI"""
    try:
        data = request.get_json()
        cv_id = data.get('cv_id')
        job_id = data.get('job_id')
        
        if not cv_id or not job_id:
            return jsonify({'error': 'CV ID and Job ID are required'}), 400
        
        cv = CV.query.get_or_404(cv_id)
        job = Job.query.get_or_404(job_id)
        
        # Prepare data for OpenAI analysis
        cv_text = f"""
        Name: {cv.name}
        Email: {cv.email}
        Phone: {cv.phone}
        Address: {cv.address}
        Education: {cv.education}
        Experience: {cv.experience}
        Skills: {cv.skills}
        """
        
        job_text = f"""
        Title: {job.title}
        Company: {job.company}
        Description: {job.description}
        Requirements: {job.requirements}
        Location: {job.location}
        Employment Type: {job.employment_type}
        """
        
        # Analyze with OpenAI
        match_result = analyze_job_cv_match(cv_text, job_text)
        
        return jsonify({
            'success': True,
            'match_score': match_result.get('match_score', 0),
            'analysis': match_result.get('analysis', ''),
            'strengths': match_result.get('strengths', []),
            'weaknesses': match_result.get('weaknesses', []),
            'recommendations': match_result.get('recommendations', [])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_job_cv_match(cv_text, job_text):
    """Analyze job and CV match using OpenAI"""
    try:
        # prefer Vietnamese output for strengths/weaknesses/recommendations
        prompt = f"""
        Phân tích mức độ phù hợp giữa CV và JD. Trả về đúng JSON, nội dung TIẾNG VIỆT:

        CV:
        {cv_text}

        JD:
        {job_text}

        Đầu ra JSON đúng cấu trúc:
        {{
            "match_score": 85,
            "analysis": "tóm tắt tổng quan bằng tiếng Việt",
            "strengths": ["điểm mạnh 1", "điểm mạnh 2"],
            "weaknesses": ["khoảng trống 1", "khoảng trống 2"],
            "recommendations": ["khuyến nghị 1", "khuyến nghị 2"]
        }}

        match_score trong khoảng 0-100.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Chỉ được trả về JSON hợp lệ, không thêm mô tả ngoài JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        data = json.loads(result)
        
        # Ensure proper data types
        processed_data = {
            'match_score': int(data.get('match_score', 0)),
            'analysis': str(data.get('analysis', '')),
            'strengths': data.get('strengths', []) if isinstance(data.get('strengths'), list) else [],
            'weaknesses': data.get('weaknesses', []) if isinstance(data.get('weaknesses'), list) else [],
            'recommendations': data.get('recommendations', []) if isinstance(data.get('recommendations'), list) else []
        }
        
        return processed_data
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {
            'match_score': 0,
            'analysis': 'Unable to analyze due to API error',
            'strengths': [],
            'weaknesses': ['API Error'],
            'recommendations': ['Please check OpenAI API configuration']
        }

@app.route('/api/analyze-cv-preview', methods=['POST'])
@login_required
def analyze_cv_preview():
    """Analyze CV text for preview without saving to database"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        # Use the same AI analysis function
        ai_data = analyze_cv_with_openai(text)
        
        return jsonify({
            'success': True,
            'data': {
                'name': ai_data.get('name', ''),
                'email': ai_data.get('email', ''),
                'phone': ai_data.get('phone', ''),
                'address': ai_data.get('address', ''),
                'education': ai_data.get('education', ''),
                'experience': ai_data.get('experience', ''),
                'skills': ai_data.get('skills', '')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export_data')
@login_required
def export_data():
    """Export all user data as JSON"""
    try:
        # Get user's data
        user_cvs = CV.query.filter_by(user_id=current_user.id).all()
        user_jobs = Job.query.filter_by(user_id=current_user.id).all()
        
        # Convert to dictionaries
        cvs_data = []
        for cv in user_cvs:
            cvs_data.append({
                'id': cv.id,
                'name': cv.name,
                'email': cv.email,
                'phone': cv.phone,
                'address': cv.address,
                'education': cv.education,
                'experience': cv.experience,
                'skills': cv.skills,
                'created_at': cv.created_at.isoformat(),
                'updated_at': cv.updated_at.isoformat()
            })
        
        jobs_data = []
        for job in user_jobs:
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'requirements': job.requirements,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'employment_type': job.employment_type,
                'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
                'is_active': job.is_active,
                'created_at': job.created_at.isoformat(),
                'updated_at': job.updated_at.isoformat()
            })
        
        export_data = {
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'is_admin': current_user.is_admin,
                'created_at': current_user.created_at.isoformat()
            },
            'cvs': cvs_data,
            'jobs': jobs_data,
            'exported_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create JSON response
        response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=jobfit_export_{current_user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/clear-flash', methods=['POST'])
def clear_flash():
    """Clear flash messages from session"""
    session.pop('_flashes', None)
    return jsonify({'status': 'success'})

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        settings.auto_extract = 'auto_extract' in request.form
        settings.email_notifications = 'email_notifications' in request.form
        settings.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=settings)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('password123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin/password123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

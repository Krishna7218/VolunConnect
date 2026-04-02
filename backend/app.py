from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import random
import re
import math
import mysql.connector
from ai_matchmaker import get_best_matches

app = Flask(__name__)
app.secret_key = "super_secret_hackathon_key" 

# ==========================================
# 🔌 MYSQL CONNECTION
# ==========================================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin123",
    database="login1" 
)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# ==========================================
# 📏 HAVERSINE FORMULA
# ==========================================
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==========================================
# 🔐 1. PURE LOGIN ROUTE 
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def home():
    cursor = db.cursor(dictionary=True) 
    
    cursor.execute("""
        (SELECT * FROM volunteers WHERE skills = 'IT Support' AND (exp >= 10 OR exp IN ('>10', '10+', '10-15')) LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Teaching' AND gender = 'female' AND (exp >= 10 OR exp IN ('>10', '10+', '10-15')) LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Healthcare' AND gender = 'female' AND (exp >= 10 OR exp IN ('>10', '10+', '10-15')) LIMIT 1)
        UNION ALL
        (SELECT * FROM volunteers WHERE skills = 'Event Management' AND (exp >= 10 OR exp IN ('>10', '10+', '10-15')) LIMIT 1)
    """)
    recommended_vols = cursor.fetchall()
    
    if not recommended_vols or len(recommended_vols) < 4:
        cursor.execute("SELECT * FROM volunteers LIMIT 4")
        recommended_vols = cursor.fetchall()

    error_msg = None # 🌟 NAYA: Error store karne ke liye variable

    if request.method == 'POST':
        email = request.form.get('Username')
        password = request.form.get('Password')

        if not email or not password:
            error_msg = "⚠️ All fields required!"
        else:
            cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
            user = cursor.fetchone()

            if user:
                if user['password'] == password:
                    session['user_email'] = email 
                    cursor.close()
                    return redirect(url_for('filter_page'))
                else:
                    error_msg = "❌ Wrong Password! Please try again." # 🌟 NAYA: Same page error
            else:
                error_msg = "❌ Account not found! Please Sign Up first." # 🌟 NAYA: Same page error

    cursor.close()
    
    # 🌟 NAYA: 'error' variable ko index.html mein bhej rahe hain
    return render_template("index.html", recommended_vols=recommended_vols, error=error_msg)

# ==========================================
# 📝 2. SIGN UP ROUTE
# ==========================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('FullName') 
        email = request.form.get('Username')
        password = request.form.get('Password')

        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username=%s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            return "<h3>⚠️ Email already registered! Please <a href='/'>Login</a>.</h3>"
            
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (email, password))
        db.commit()
        cursor.close()
        
        return redirect(url_for('home'))
        
    return render_template("signup.html")

# ==========================================
# 🚪 3. LOGOUT ROUTE 
# ==========================================
@app.route('/logout')
def logout():
    session.pop('user_email', None) 
    return redirect(url_for('home'))

# ==========================================
# 🗺️ 4. NGO DASHBOARD 
# ==========================================
@app.route('/filter')
def filter_page():
    user_email = session.get('user_email', 'Guest') 
    # 🌟 DATA AB JS FETCH KAREGA LIVE API SE, YAHAN SE DELETE KAR DIYA
    return render_template('filter.html', user_email=user_email)

# ==========================================
# 🧠 5. AI SMART SEARCH
# ==========================================
@app.route('/ai-search', methods=['GET', 'POST'])
def ai_search():
    user_email = session.get('user_email', 'Guest') 
    ngo_query = request.values.get('ai_query') 

    if not ngo_query:
        return redirect(url_for('filter_page'))

    cursor = db.cursor(dictionary=True)
    words = ngo_query.lower().replace(',', '').replace('.', '').split()
    target_city, target_lat, target_lng = None, None, None
    
    for word in words:
        if len(word) > 2:
            cursor.execute("SELECT city_name, lat, lng FROM cities WHERE LOWER(city_name) = %s LIMIT 1", (word,))
            result = cursor.fetchone()
            if result:
                target_city = result['city_name']
                target_lat = float(result['lat'])
                target_lng = float(result['lng'])
                break 
                
    cursor.execute("""
        SELECT v.*, c.lat, c.lng 
        FROM volunteers v
        LEFT JOIN cities c ON LOWER(v.locn) = LOWER(c.city_name)
    """)
    all_volunteers = cursor.fetchall()
    cursor.close()
    
    # 🌟 STRICT FIX: Agar user ne >10 manga hai, toh AI ko bewakoof mat banne do
    if '>10' in ngo_query.replace(' ', '') or '10+' in ngo_query.replace(' ', ''):
        strict_vols = []
        for v in all_volunteers:
            exp_val = str(v.get('exp', '0')).strip()
            # Sirf hardcore experienced logo ko hi aage badhne do
            if exp_val in ['>10', '10+', '10-15'] or (exp_val.isdigit() and int(exp_val) >= 10):
                strict_vols.append(v)
        if strict_vols:
            all_volunteers = strict_vols # List ko filter kar diya!

    skills_query = ngo_query.lower()
    if target_city:
        skills_query = skills_query.replace(target_city.lower(), '')
        
    ranked_results = get_best_matches(skills_query, all_volunteers)

    if len(ranked_results) == 0 and len(all_volunteers) > 0:
        ranked_results = all_volunteers

    final_results = []
    for vol in ranked_results:
        if target_lat and target_lng and vol.get('lat') and vol.get('lng'):
            dist = calculate_distance(target_lat, target_lng, float(vol['lat']), float(vol['lng']))
            vol['distance_km'] = round(dist, 1)
        else:
            vol['distance_km'] = 99999 
            
        final_results.append(vol)

    # 🌟 PURE FIX: Pehle Match Score, fir Distance
    if target_city:
        final_results = sorted(final_results, key=lambda k: (-k.get('match_score', 0), k.get('distance_km', 99999)))
    else:
        final_results = sorted(final_results, key=lambda k: -k.get('match_score', 0))

    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_results = len(final_results)
    total_pages = math.ceil(total_results / per_page) if total_results > 0 else 0
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_data = final_results[start_index:end_index]

    dummy_filters = {'skills': '', 'location': '', 'exp': '', 'gender': '', 'availability': '', 'work_type': ''}

    return render_template('result.html', volunteers=paginated_data, page=page, total_pages=total_pages, filters=dummy_filters, ai_search=True, ai_query=ngo_query, target_city=target_city, user_email=user_email)

# ==========================================
# 🚀 6. MANUAL SEARCH 
# ==========================================
@app.route('/search', methods=['GET', 'POST']) 
def search_volunteers():
    user_email = session.get('user_email', 'Guest') 
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        skills = request.form.get('skills')
        location = request.form.get('location')
        exp = request.form.get('exp')
        gender = request.form.get('gender')
        availability = request.form.get('availability')
        work_type = request.form.get('work_type')
    else:
        skills = request.args.get('skills')
        location = request.args.get('location')
        exp = request.args.get('exp')
        gender = request.args.get('gender')
        availability = request.args.get('availability')
        work_type = request.args.get('work_type')

    query = "SELECT * FROM volunteers WHERE 1=1"
    params = []

    if skills: 
        query += " AND skills = %s"
        params.append(skills)
    if location: 
        query += " AND locn = %s"
        params.append(location) 
    if exp: 
        query += " AND exp = %s"
        params.append(exp)
    if gender: 
        query += " AND gender = %s"
        params.append(gender)
    if availability: 
        query += " AND availability = %s"
        params.append(availability)
    if work_type: 
        query += " AND work_type = %s"
        params.append(work_type)

    cursor.execute(query, tuple(params))
    all_filtered_data = cursor.fetchall()
    cursor.close()

    page = request.args.get('page', 1, type=int)
    per_page = 20
    total_results = len(all_filtered_data)
    total_pages = math.ceil(total_results / per_page) if total_results > 0 else 0
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_data = all_filtered_data[start_index:end_index]

    current_filters = {'skills': skills or '', 'location': location or '', 'exp': exp or '', 'gender': gender or '', 'availability': availability or '', 'work_type': work_type or ''}

    return render_template('result.html', volunteers=paginated_data, page=page, total_pages=total_pages, filters=current_filters, user_email=user_email)

# ==========================================
# 👤 7. PROFILE DETAIL
# ==========================================
@app.route('/volunteer/<int:VolunteerId>')
def volunteer_detail(VolunteerId):
    user_email = session.get('user_email', 'Guest') 
    cursor = db.cursor(dictionary=True) 
    cursor.execute("SELECT * FROM volunteers WHERE VolunteerId = %s", (VolunteerId,))
    vol_data = cursor.fetchone()

    if not vol_data:
        return "Volunteer not found", 404

    cursor.execute("""
        SELECT skill_name FROM skills_mapping 
        WHERE category = %s AND experience_bracket = %s
    """, (vol_data['skills'], vol_data['exp']))
    
    skills_result = cursor.fetchall()
    assigned_skills = [row['skill_name'] for row in skills_result]
    
    if not assigned_skills:
        assigned_skills = ['General Volunteering']

    cursor.close()
    return render_template('detail.html', vol=vol_data, assigned_skills=assigned_skills, user_email=user_email)

# ==========================================
# 📡 8. LIVE HEATMAP API (Bina page refresh ke data dega)
# ==========================================
@app.route('/api/live-heatmap')
def live_heatmap():
    cursor = db.cursor(dictionary=True)
    # Database se 10 main cities uthao crisis center banane ke liye
    cursor.execute("SELECT city_name, lat, lng FROM cities WHERE lat IS NOT NULL LIMIT 15")
    cities = cursor.fetchall()
    cursor.close()

    hotspots = []
    critical_cities = []

    for city in cities:
        # Har city ke aas-paas 1 se 4 random aag (crises) lagao
        num_spots = random.randint(1, 4)
        max_intensity = 0

        for _ in range(num_spots):
            # Coordinates mein slight change taaki map pe faila hua dikhe
            jitter_lat = random.uniform(-0.08, 0.08)
            jitter_lng = random.uniform(-0.08, 0.08)
            intensity = random.uniform(0.2, 1.0) # Random khatra level

            hotspots.append([
                float(city['lat']) + jitter_lat,
                float(city['lng']) + jitter_lng,
                intensity
            ])

            if intensity > max_intensity:
                max_intensity = intensity

        # Agar intensity 0.85 se zyada hai, toh city ko RED alert mein daalo
        if max_intensity > 0.85:
            critical_cities.append(city['city_name'])

    # Unique cities only
    critical_cities = list(set(critical_cities))

    return jsonify({
        'hotspots': hotspots,
        'critical_cities': critical_cities
    })

# ==========================================
# 📞 8. SUPPORT PAGE ROUTE (WITH DB BACKEND)
# ==========================================
@app.route('/support', methods=['GET', 'POST'])
def support_page():
    user_email = session.get('user_email', 'Guest') 
    success_msg = None

    if request.method == 'POST':
        # 1. Form se data nikaalo
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        issue = request.form.get('issue')
        message = request.form.get('message')

        if fullname and email and issue and message:
            cursor = db.cursor()
            
            # 🌟 PRO HACK: Agar table nahi hai toh code khud bana dega!
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(255),
                    email VARCHAR(255),
                    issue VARCHAR(100),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Data ko database mein Insert karo
            cursor.execute("""
                INSERT INTO support_tickets (fullname, email, issue, message) 
                VALUES (%s, %s, %s, %s)
            """, (fullname, email, issue, message))
            
            db.commit()
            cursor.close()
            
            # 3. Success message set karo
            success_msg = "✅ Mission Accomplished! Your message has been beamed to our Command Center."

    return render_template('support.html', user_email=user_email, success_msg=success_msg)

if __name__ == '__main__':
    app.run(debug=True)
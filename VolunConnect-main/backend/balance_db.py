import mysql.connector
import random
import itertools

# 1. Database Connection
db = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="admin123", 
    database="login1"
)
cursor = db.cursor()

# 2. Table ko naye sire se banana (Purana data hat jayega)
cursor.execute("DROP TABLE IF EXISTS volunteers")
cursor.execute("""
CREATE TABLE volunteers (
    VolunteerId INT PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100),
    skills VARCHAR(50),
    exp VARCHAR(50),
    availability VARCHAR(50),
    work_type VARCHAR(50),
    rating VARCHAR(50),
    locn VARCHAR(50),
    gender VARCHAR(50)
)
""")

# 3. Filter Options
skills = ['IT Support', 'Teaching', 'Healthcare', 'Event Management']
locations = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Kolkata', 'Lucknow', 'Patna', 'Hyderabad', 'Dehradun', 'Bhopal', 'Agra']
exps = ['0-5', '5-10', '>10']
availabilities = ['Weekdays', 'Weekends', 'Flexible']
work_types = ['On-site', 'Remote']

# 4. Indian Names for Authentic Data
male_firsts = ['Aarav', 'Vihaan', 'Aditya', 'Arjun', 'Sai', 'Rohan', 'Amit', 'Rahul', 'Vikram', 'Karan', 'Rajesh', 'Sanjay', 'Deepak', 'Anil', 'Manoj', 'Akash', 'Pratham', 'Navneet', 'Asutosh', 'Digvijay', 'Arkadyuti', 'Ravi', 'Sunil']
female_firsts = ['Diya', 'Isha', 'Priya', 'Neha', 'Pooja', 'Anjali', 'Sneha', 'Kavya', 'Shruti', 'Swati', 'Riya', 'Kiran', 'Megha', 'Nisha', 'Rekha', 'Oishiki', 'Sinjini', 'Atrayee', 'Khusi', 'Prathiba', 'Nitu']
last_names = ['Sharma', 'Singh', 'Kumar', 'Patel', 'Gupta', 'Das', 'Dutta', 'Saha', 'Yadav', 'Bhandary', 'Jaiswal', 'Mor', 'Pawar', 'Nair', 'Koel', 'Reddy', 'Verma', 'Mishra', 'Pandey', 'Nath']

# 5. Har combination banayenge (Bina gender ke)
base_combinations = list(itertools.product(skills, locations, exps, availabilities, work_types))

data_to_insert = []
volunteer_id = 10001 # Nayi ID 10001 se shuru hogi

print("Generating 7,920 Indian Volunteer Profiles... Please wait.")

# Har ek filter combination ke andar ghus kar 10 log daalenge
for combo in base_combinations:
    skill, loc, exp, avail, work = combo
    
    # EXACT 3:2 RATIO: 6 Male generate karein
    for _ in range(6):
        fname = random.choice(male_firsts)
        lname = random.choice(last_names)
        fullname = f"{fname} {lname}"
        # Fake email generator (e.g. rahul.sharma45@gmail.com)
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10,999)}@gmail.com"
        
        data_to_insert.append((volunteer_id, fullname, email, skill, exp, avail, work, "", loc, "male"))
        volunteer_id += 1
        
    # EXACT 3:2 RATIO: 4 Female generate karein
    for _ in range(4):
        fname = random.choice(female_firsts)
        lname = random.choice(last_names)
        fullname = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}{random.randint(10,999)}@gmail.com"
        
        data_to_insert.append((volunteer_id, fullname, email, skill, exp, avail, work, "", loc, "female"))
        volunteer_id += 1

# Database mein daalne se pehle sabko mix (shuffle) kar denge
random.shuffle(data_to_insert)

# 6. Database mein ek sath daalna (Bulk Insert)
sql = """INSERT INTO volunteers 
         (VolunteerId, fullname, email, skills, exp, availability, work_type, rating, locn, gender) 
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

# 1000-1000 ke packets mein bhejenge taaki MySQL crash na ho
chunk_size = 1000
for i in range(0, len(data_to_insert), chunk_size):
    cursor.executemany(sql, data_to_insert[i:i+chunk_size])
    
db.commit()

print(f"✅ BINGO! {len(data_to_insert)} records successfully added.")
print("📊 Ratio Achieved: EXACTLY 60% Male & 40% Female.")
print("🔍 Search Guarantee: Any filter combination will now return EXACTLY 10 results!")

cursor.close()
db.close()
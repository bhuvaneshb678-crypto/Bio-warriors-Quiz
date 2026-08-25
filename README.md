# B Team Biology Quiz Portal v2

## Main features

- Registered User ID + password login
- Admin control panel
- 30 questions per day
- 25-minute timer with automatic submission
- Different randomized 30-question set for each student/day
- One server-enforced attempt per student per calendar day
- Automatic scoring
- Daily rank and overall leaderboard
- Student recent history
- Admin student management
- Admin question bank with categories and difficulty
- Enable/disable students and questions
- Results export to CSV
- SQLite database
- Mobile-friendly UI

## Start

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Admin login

User ID: `admin`
Password: `Admin@12345`

Change the admin password before real use.

## For classmates

Create one student account per person in Admin -> Students.

Example:
User ID: B001
Name: Student Name
Password: Bteam@123

## Important

The timer is enforced in the browser for user experience; the one-attempt rule is enforced by the server/database. For a high-stakes public competition, deploy behind HTTPS and use a production server/database.

from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import sqlite3, random, os, csv, io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quiz.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")
QUESTIONS_PER_DAY = 30
QUIZ_MINUTES = 25

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL, password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL,
        option_a TEXT NOT NULL, option_b TEXT NOT NULL, option_c TEXT NOT NULL,
        option_d TEXT NOT NULL, correct_answer TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Biology', explanation TEXT DEFAULT '',
        difficulty TEXT NOT NULL DEFAULT 'Medium', active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        quiz_date TEXT NOT NULL, score INTEGER NOT NULL, total INTEGER NOT NULL,
        seconds_taken INTEGER DEFAULT 0, submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, quiz_date), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS attempt_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL, selected_answer TEXT, is_correct INTEGER NOT NULL,
        FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
        FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
    );
    """)
    if not conn.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone():
        conn.execute("INSERT INTO users(user_id,name,password_hash,role) VALUES(?,?,?,?)",
                     ("admin","B Team Administrator",generate_password_hash("Admin@12345"),"admin"))
    if conn.execute("SELECT COUNT(*) c FROM questions").fetchone()["c"] == 0:
        seed_questions(conn)
    conn.commit(); conn.close()

def seed_questions(conn):
    # Reuse the first version's question bank if available in a fresh DB.
    qs = [
("The basic structural and functional unit of life is:","Tissue","Cell","Organ","Organelle","B","Cell Biology","Easy"),
("Which organelle is known as the powerhouse of the cell?","Nucleus","Golgi apparatus","Mitochondrion","Lysosome","C","Cell Biology","Easy"),
("DNA is primarily located in which cell structure in eukaryotes?","Ribosome","Nucleus","Cell wall","Vacuole","B","Molecular Biology","Easy"),
("Which nitrogenous base is found in RNA but not normally in DNA?","Thymine","Cytosine","Uracil","Guanine","C","Molecular Biology","Easy"),
("The process by which DNA makes an RNA copy is called:","Translation","Replication","Transcription","Mutation","C","Molecular Biology","Easy"),
("Translation occurs mainly on:","Ribosomes","Lysosomes","Centrosomes","Peroxisomes","A","Molecular Biology","Easy"),
("Which enzyme unwinds the DNA double helix during replication?","Ligase","Helicase","Amylase","Peptidase","B","Molecular Biology","Medium"),
("The monomers of proteins are:","Nucleotides","Fatty acids","Amino acids","Monosaccharides","C","Biochemistry","Easy"),
("Which carbohydrate is the main storage polysaccharide in plants?","Glycogen","Cellulose","Starch","Chitin","C","Biochemistry","Easy"),
("Which molecule is the main energy currency of cells?","DNA","ATP","RNA","NADPH","B","Biochemistry","Easy"),
("Enzymes generally function by:","Increasing activation energy","Decreasing activation energy","Changing products into substrates","Being consumed completely","B","Enzymology","Medium"),
("The site on an enzyme where a substrate binds is called the:","Allosteric gene","Active site","Peptide site","Promoter","B","Enzymology","Easy"),
("Michaelis-Menten kinetics relates enzyme velocity primarily to:","Substrate concentration","DNA length","Cell size","Oxygen pressure only","A","Enzymology","Medium"),
("The Km of an enzyme is the substrate concentration at which velocity is:","Zero","Half of Vmax","Equal to Vmax","Double Vmax","B","Enzymology","Medium"),
("Which vitamin is synthesized in skin in response to sunlight?","Vitamin A","Vitamin B12","Vitamin C","Vitamin D","D","Nutrition","Easy"),
("Hemoglobin is mainly responsible for transporting:","Glucose","Oxygen","DNA","Bile","B","Human Biology","Easy"),
("Which blood cells are primarily involved in immune defense?","Red blood cells","White blood cells","Platelets","Plasma cells only","B","Human Biology","Easy"),
("The functional unit of the kidney is the:","Neuron","Nephron","Alveolus","Sarcomere","B","Human Biology","Easy"),
("Gas exchange in human lungs mainly occurs in the:","Bronchi","Trachea","Alveoli","Diaphragm","C","Human Biology","Easy"),
("Which hormone lowers blood glucose concentration?","Glucagon","Insulin","Adrenaline","Thyroxine","B","Human Biology","Easy"),
("Photosynthesis mainly occurs in which organelle?","Mitochondrion","Chloroplast","Nucleus","Ribosome","B","Plant Biology","Easy"),
("The green pigment essential for photosynthesis is:","Melanin","Hemoglobin","Chlorophyll","Keratin","C","Plant Biology","Easy"),
("The Calvin cycle takes place in the:","Thylakoid lumen","Stroma","Nucleus","Cytoplasm","B","Plant Biology","Medium"),
("Which tissue transports water in plants?","Phloem","Xylem","Epidermis","Cambium only","B","Plant Biology","Easy"),
("Which tissue transports sugars in plants?","Xylem","Phloem","Cork","Collenchyma","B","Plant Biology","Easy"),
("The study of heredity and variation is called:","Ecology","Genetics","Anatomy","Taxonomy","B","Genetics","Easy"),
("A person with genotype Aa is described as:","Homozygous dominant","Homozygous recessive","Heterozygous","Hemizygous","C","Genetics","Easy"),
("The observable characteristics of an organism are its:","Genotype","Phenotype","Alleles","Genome only","B","Genetics","Easy"),
("Which molecule carries genetic information in most organisms?","ATP","DNA","Protein","Cellulose","B","Genetics","Easy"),
("A mutation is best described as a change in:","Cell temperature","Genetic material","Blood pressure","Tissue shape only","B","Genetics","Easy"),
("Bacteria are generally classified as:","Eukaryotes","Prokaryotes","Viruses","Multicellular fungi","B","Microbiology","Easy"),
("Which structure is present in bacteria but absent from typical animal cells?","Cell membrane","Ribosomes","Peptidoglycan cell wall","Cytoplasm","C","Microbiology","Medium"),
("Viruses are generally considered:","Free-living cells","Acellular infectious agents","Prokaryotic cells","Fungi","B","Microbiology","Easy"),
("Which microorganism is used in bread fermentation?","Yeast","Algae","Protozoan","Virus","A","Microbiology","Easy"),
("The Gram staining method differentiates bacteria mainly based on differences in their:","DNA sequence","Cell wall structure","Flagellar speed","Capsule color only","B","Microbiology","Medium"),
("An ecosystem includes:","Only animals","Only plants","Living organisms and their physical environment","Only microorganisms","C","Ecology","Easy"),
("The first trophic level in a food chain is usually occupied by:","Consumers","Decomposers","Producers","Predators","C","Ecology","Easy"),
("Organisms that break down dead organic matter are called:","Producers","Decomposers","Primary consumers","Parasites","B","Ecology","Easy"),
("Biodiversity refers to the variety of:","Only genes","Only ecosystems","Life at genetic, species and ecosystem levels","Only animals","C","Ecology","Medium"),
("PCR is commonly used to:","Digest proteins","Amplify DNA","Produce ATP","Measure blood pressure","B","Biotechnology","Easy"),
("The enzyme commonly used in PCR to synthesize DNA at high temperature is:","Taq polymerase","RNA polymerase","DNA ligase","Pepsin","A","Biotechnology","Easy"),
("Gel electrophoresis separates DNA fragments mainly according to:","Color","Size","Taste","Cell type","B","Biotechnology","Easy"),
("A plasmid is commonly used in molecular biology as a:","Protein hormone","Cloning vector","Lipid","Microscope","B","Biotechnology","Medium"),
("CRISPR-Cas9 is primarily associated with:","Gene editing","Protein digestion","Cell respiration","Blood clotting","A","Biotechnology","Medium"),
("Bioinformatics combines biology with:","Information technology and computational methods","Only geology","Only astronomy","Only chemistry","A","Bioinformatics","Easy"),
("A FASTA file commonly contains:","DNA/protein sequences","Only images","Patient bills","Audio files","A","Bioinformatics","Easy"),
("BLAST is widely used to:","Compare biological sequences","Measure pH","Count blood cells manually","Culture bacteria","A","Bioinformatics","Easy"),
("Phylogenetics studies:","Evolutionary relationships","Blood pressure","Photosynthesis rate only","Protein calories","A","Evolution","Easy"),
("Natural selection is strongly associated with:","Charles Darwin","Gregor Mendel only","Louis Pasteur","Robert Hooke","A","Evolution","Easy"),
("The smallest unit commonly considered in biological classification is:","Kingdom","Phylum","Species","Domain","C","Taxonomy","Easy"),
("Which level of protein structure is determined directly by amino acid sequence?","Primary","Secondary","Tertiary","Quaternary","A","Biochemistry","Medium"),
("Alpha helices and beta sheets are features of which protein structure?","Primary","Secondary","Tertiary","Quaternary","B","Biochemistry","Medium"),
("Lipids are generally:","Highly water-soluble polymers","Hydrophobic or largely nonpolar molecules","Nucleic acids","Proteins","B","Biochemistry","Easy"),
("The main component of most biological membranes is a:","Phospholipid bilayer","DNA sheet","Cellulose layer","Protein crystal only","A","Cell Biology","Easy"),
("Osmosis is the movement of:","Solute from high to low concentration","Water across a selectively permeable membrane","Proteins into the nucleus","ATP into mitochondria","B","Cell Biology","Easy"),
("Mitosis produces daughter cells that are generally:","Genetically very similar to the parent cell","Always haploid","Always genetically different","Without chromosomes","A","Cell Biology","Medium"),
("Meiosis is important for producing:","Gametes","Skin cells only","Red blood cells only","Bacterial spores only","A","Genetics","Easy"),
("Which molecule is the immediate product of glycolysis?","Pyruvate","DNA","Urea","Cholesterol","A","Biochemistry","Medium"),
("Most aerobic cellular respiration occurs in the:","Mitochondria","Nucleus","Golgi apparatus","Lysosome","A","Biochemistry","Easy"),
("The pH scale is used to describe:","Acidity or alkalinity","DNA length","Cell diameter","Protein sequence","A","Biochemistry","Easy"),
("Antibodies are mainly:","Lipids","Proteins","Carbohydrates","Nucleotides","B","Immunology","Easy"),
("Vaccination primarily works by stimulating:","Specific immune memory","Bone growth","Digestion","Photosynthesis","A","Immunology","Easy"),
("A pathogen is an organism or agent that can:","Cause disease","Always produce oxygen","Only digest cellulose","Prevent all mutations","A","Microbiology","Easy"),
("Stem cells are characterized by their ability to:","Self-renew and differentiate","Only produce antibodies","Never divide","Only carry RNA","A","Cell Biology","Medium"),
    ]
    conn.executemany("""INSERT INTO questions
    (question,option_a,option_b,option_c,option_d,correct_answer,category,difficulty)
    VALUES(?,?,?,?,?,?,?,?)""", qs)

def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if "user_pk" not in session: return redirect(url_for("login"))
        return f(*a,**kw)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        if "user_pk" not in session: return redirect(url_for("login"))
        if session.get("role")!="admin":
            flash("Administrator access required.","error"); return redirect(url_for("dashboard"))
        return f(*a,**kw)
    return w

def daily_questions(user_pk, today):
    conn=get_db()
    rows=conn.execute("SELECT * FROM questions WHERE active=1 ORDER BY id").fetchall()
    conn.close()
    if len(rows)<QUESTIONS_PER_DAY: return []
    # Different randomized set per student/day, stable during the day.
    rng=random.Random(f"{today}:{user_pk}:BTEAM")
    rows=list(rows); rng.shuffle(rows)
    return rows[:QUESTIONS_PER_DAY]

@app.route("/")
def index():
    if "user_pk" not in session: return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard" if session.get("role")=="admin" else "dashboard"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        uid=request.form.get("user_id","").strip(); pw=request.form.get("password","")
        conn=get_db(); u=conn.execute("SELECT * FROM users WHERE user_id=? AND active=1",(uid,)).fetchone(); conn.close()
        if u and check_password_hash(u["password_hash"],pw):
            session.clear(); session.update(user_pk=u["id"],user_id=u["user_id"],name=u["name"],role=u["role"])
            return redirect(url_for("admin_dashboard" if u["role"]=="admin" else "dashboard"))
        flash("Invalid User ID or Password.","error")
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role")=="admin": return redirect(url_for("admin_dashboard"))
    today=date.today().isoformat(); conn=get_db()
    attempt=conn.execute("SELECT * FROM attempts WHERE user_id=? AND quiz_date=?",(session["user_pk"],today)).fetchone()
    history=conn.execute("SELECT quiz_date,score,total,seconds_taken FROM attempts WHERE user_id=? ORDER BY quiz_date DESC LIMIT 10",(session["user_pk"],)).fetchall()
    rank=conn.execute("""SELECT 1+COUNT(*) r FROM attempts a
      WHERE a.quiz_date=? AND a.score>(SELECT score FROM attempts WHERE id=?)""",(today,attempt["id"] if attempt else -1)).fetchone()["r"] if attempt else None
    conn.close()
    return render_template("dashboard.html",attempt=attempt,history=history,today=today,rank=rank,quiz_minutes=QUIZ_MINUTES)

@app.route("/quiz")
@login_required
def quiz():
    if session.get("role")=="admin": return redirect(url_for("admin_dashboard"))
    today=date.today().isoformat(); conn=get_db()
    exists=conn.execute("SELECT id FROM attempts WHERE user_id=? AND quiz_date=?",(session["user_pk"],today)).fetchone()
    conn.close()
    if exists:
        flash("You have already completed today's quiz.","error"); return redirect(url_for("dashboard"))
    qs=daily_questions(session["user_pk"],today)
    if len(qs)<QUESTIONS_PER_DAY:
        flash(f"Admin needs at least {QUESTIONS_PER_DAY} active questions.","error"); return redirect(url_for("dashboard"))
    return render_template("quiz.html",questions=qs,today=today,quiz_minutes=QUIZ_MINUTES)

@app.route("/submit_quiz",methods=["POST"])
@login_required
def submit_quiz():
    if session.get("role")=="admin": return redirect(url_for("admin_dashboard"))
    today=date.today().isoformat(); conn=get_db()
    if conn.execute("SELECT id FROM attempts WHERE user_id=? AND quiz_date=?",(session["user_pk"],today)).fetchone():
        conn.close(); flash("Your quiz was already submitted.","error"); return redirect(url_for("dashboard"))
    qs=daily_questions(session["user_pk"],today)
    if len(qs)<QUESTIONS_PER_DAY:
        conn.close(); flash("Quiz is not configured correctly.","error"); return redirect(url_for("dashboard"))
    score=0; answers=[]
    for q in qs:
        ans=request.form.get(f"q_{q['id']}","")
        ok=int(ans==q["correct_answer"]); score+=ok; answers.append((q["id"],ans,ok))
    try:
        cur=conn.execute("INSERT INTO attempts(user_id,quiz_date,score,total,seconds_taken) VALUES(?,?,?,?,?)",
                          (session["user_pk"],today,score,QUESTIONS_PER_DAY,int(request.form.get("seconds_taken","0") or 0)))
        aid=cur.lastrowid
        conn.executemany("INSERT INTO attempt_answers(attempt_id,question_id,selected_answer,is_correct) VALUES(?,?,?,?)",
                         [(aid,q,a,ok) for q,a,ok in answers])
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback(); conn.close(); flash("Your quiz was already submitted.","error"); return redirect(url_for("dashboard"))
    conn.close()
    return render_template("result.html",score=score,total=QUESTIONS_PER_DAY,today=today,seconds=int(request.form.get("seconds_taken","0") or 0))

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn=get_db(); today=date.today().isoformat()
    stats={"users":conn.execute("SELECT COUNT(*) c FROM users WHERE role='student'").fetchone()["c"],
           "questions":conn.execute("SELECT COUNT(*) c FROM questions WHERE active=1").fetchone()["c"],
           "attempts_today":conn.execute("SELECT COUNT(*) c FROM attempts WHERE quiz_date=?",(today,)).fetchone()["c"]}
    scores=conn.execute("""SELECT u.user_id,u.name,COALESCE(SUM(a.score),0) total_score,
      COUNT(a.id) quizzes_taken,ROUND(COALESCE(AVG(a.score*100.0/a.total),0),1) average_percent
      FROM users u LEFT JOIN attempts a ON a.user_id=u.id
      WHERE u.role='student' GROUP BY u.id ORDER BY total_score DESC,average_percent DESC,u.name""").fetchall()
    conn.close(); return render_template("admin_dashboard.html",stats=stats,scores=scores,today=today)

@app.route("/admin/users",methods=["GET","POST"])
@admin_required
def admin_users():
    conn=get_db()
    if request.method=="POST":
        uid=request.form.get("user_id","").strip(); name=request.form.get("name","").strip(); pw=request.form.get("password","")
        try:
            if not uid or not name or not pw: raise ValueError
            conn.execute("INSERT INTO users(user_id,name,password_hash,role) VALUES(?,?,?,'student')",(uid,name,generate_password_hash(pw)))
            conn.commit(); flash("Student account created.","success")
        except (sqlite3.IntegrityError,ValueError): flash("Enter all fields and use a unique User ID.","error")
    users=conn.execute("SELECT id,user_id,name,active,created_at FROM users WHERE role='student' ORDER BY name").fetchall()
    conn.close(); return render_template("admin_users.html",users=users)

@app.route("/admin/users/<int:user_pk>/toggle",methods=["POST"])
@admin_required
def toggle_user(user_pk):
    conn=get_db(); conn.execute("UPDATE users SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=? AND role='student'",(user_pk,)); conn.commit(); conn.close()
    flash("Student status updated.","success"); return redirect(url_for("admin_users"))

@app.route("/admin/questions",methods=["GET","POST"])
@admin_required
def admin_questions():
    conn=get_db()
    if request.method=="POST":
        vals=(request.form.get("question","").strip(),request.form.get("option_a","").strip(),
              request.form.get("option_b","").strip(),request.form.get("option_c","").strip(),
              request.form.get("option_d","").strip(),request.form.get("correct_answer","").upper(),
              request.form.get("category","Biology").strip() or "Biology",
              request.form.get("difficulty","Medium"),request.form.get("explanation","").strip())
        if not all(vals[:6]) or vals[5] not in "ABCD": flash("Complete all required fields.","error")
        else:
            conn.execute("""INSERT INTO questions(question,option_a,option_b,option_c,option_d,correct_answer,category,difficulty,explanation)
            VALUES(?,?,?,?,?,?,?,?,?)""",vals); conn.commit(); flash("Question added.","success")
    questions=conn.execute("SELECT * FROM questions ORDER BY id DESC").fetchall(); conn.close()
    return render_template("admin_questions.html",questions=questions)

@app.route("/admin/questions/<int:question_id>/toggle",methods=["POST"])
@admin_required
def toggle_question(question_id):
    conn=get_db(); conn.execute("UPDATE questions SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?",(question_id,)); conn.commit(); conn.close()
    flash("Question status updated.","success"); return redirect(url_for("admin_questions"))

@app.route("/admin/results")
@admin_required
def admin_results():
    conn=get_db()
    results=conn.execute("""SELECT a.id,a.user_id,a.quiz_date,u.user_id student_id,u.name,a.score,a.total,a.seconds_taken,a.submitted_at
      FROM attempts a JOIN users u ON u.id=a.user_id ORDER BY a.quiz_date DESC,a.score DESC,a.seconds_taken ASC,u.name""").fetchall()
    conn.close(); return render_template("admin_results.html",results=results)

@app.route("/admin/results.csv")
@admin_required
def export_csv():
    conn=get_db(); rows=conn.execute("""SELECT a.quiz_date,u.user_id,u.name,a.score,a.total,a.seconds_taken,a.submitted_at
      FROM attempts a JOIN users u ON u.id=a.user_id ORDER BY a.quiz_date DESC,u.name""").fetchall(); conn.close()
    out=io.StringIO(); w=csv.writer(out); w.writerow(["Date","User ID","Name","Score","Total","Percentage","Seconds","Submitted At"])
    for r in rows: w.writerow([r["quiz_date"],r["user_id"],r["name"],r["score"],r["total"],round(r["score"]*100/r["total"],1),r["seconds_taken"],r["submitted_at"]])
    return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=b_team_results.csv"})

@app.route("/admin/reset/<int:user_pk>/<quiz_date>",methods=["POST"])
@admin_required
def reset_attempt(user_pk,quiz_date):
    conn=get_db(); conn.execute("DELETE FROM attempts WHERE user_id=? AND quiz_date=?",(user_pk,quiz_date)); conn.commit(); conn.close()
    flash("Attempt reset.","success"); return redirect(url_for("admin_results"))

if __name__=="__main__":
    init_db(); app.run(host="0.0.0.0",port=5000,debug=True)

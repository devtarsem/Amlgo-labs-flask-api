from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import sqlite3

app = Flask(__name__)
CORS(app)

@app.route('/suggestions', methods =["POST"])
def suggestions():
    data = request.get_json()
    
    df = pd.DataFrame(data)
    
    ### amount data cleaning
    if "amount" in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    else :
        df['amount' ]= 0
        
        
    ### catagory data cleaning
    
    if "category" in df.columns:
        df["category"] = df["category"].fillna("Other").astype(str).str.strip()
        df["category"] = df["category"].replace("", "Other")
    else:
        df["category"] = "Other"
        
    ### date data cleaning
    
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    else:
        df["Date"] = pd.NaT
        
    ### payment method data cleaning
    
    if "payment_method" in df.columns:
        df["payment_method"] = df["payment_method"].fillna("Other").astype(str).str.upper().str.strip()
    else:
        df["payment_method"] = "Other"
        
    
    ## insight generation
    total = float(df['amount'].sum())
    
    ## category wise
    
    by_catagory = df.groupby('category')['amount'].sum().to_dict()
    by_pays = df.groupby('payment_method')['amount'].sum().to_dict()
    
    suggestion = []
   
    if by_catagory:
        top_cat = max(by_catagory, key=by_catagory.get)
        top_value = by_catagory[top_cat]
        percentage = (top_value/total)*100
        suggestion.append( f"You're spending the most on {top_cat} — ₹{top_value:.2f} ({percentage:.1f}% of total). Consider reducing it by 10–15%.")
        if percentage >= 40:
            suggestion.append(
                f"Alert: {top_cat} takes up {percentage:.0f}% of your spending. High dependency risk!"
            )

    if by_pays:
        top_pay = max(by_pays, key=by_pays.get)
        pay_val = by_pays[top_pay]
        pct_pay = (pay_val / total) * 100
        if pct_pay >= 70:
            suggestion.append(
                f"Most payments are via {top_pay} ({pct_pay:.0f}%). Try diversifying payment methods."
            )
    
    return jsonify({
        "message": "Data received successfully",
        "your_data": suggestion
    }), 200


@app.route('/monthly-report', methods=["POST"])
def monthlyReport():
    data = request.get_json()
    user_id = data.get("user_id")
    month = data.get("month")
    total_spend = data.get("total_spend")
    print(data)

    conn = sqlite3.connect("report.db")
    cur = conn.cursor()

    # Correct table schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_reports (
            user_id TEXT NOT NULL,
            month TEXT NOT NULL,
            total_spend REAL NOT NULL
        )
    """)

    conn.commit()

    # Correct placeholders (3 values for 3 columns)
    cur.execute("""
        INSERT INTO monthly_reports (user_id, month, total_spend)
        VALUES (?, ?, ?)
    """, (user_id, month, total_spend))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Report saved successfully"}), 200


@app.route('/monthly-report/history', methods =["POST"])
def reportHistory():
    id = request.get_json()
    conn = sqlite3.connect("report.db")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT user_id, month, total_spent
        FROM monthly_reports
        WHERE user_id = ?
        ORDER BY month DESC
        
    """, (id))    
    rows = cur.fetchall()
    conn.close()
    
    reports = []
    for row in rows:
        reports.append({
            "user_id": row[0],
            "month": row[1],
            "total_spent": row[2]
        })
    print(reports)
    return jsonify({"status": "success", "reports": reports}), 200
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)
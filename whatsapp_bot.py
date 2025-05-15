import sqlite3
import os
import re
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import sqlparse

# Load environment variables
load_dotenv()

# Configure API keys
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)

# Database schema 
SCHEMA = {
    "table_name": "customers",
    "columns": {
        "customer_id": "INTEGER PRIMARY KEY",
        "customer_name": "TEXT",
        "age": "INTEGER",
        "gender": "TEXT",
        "position": "TEXT",
        "email": "TEXT",
        "contact": "TEXT",
        "country": "TEXT"
    }
}

# Global database connection
conn = sqlite3.connect('customers.db', check_same_thread=False)
cursor = conn.cursor()

def initialize_database():
    cursor.execute(f"DROP TABLE IF EXISTS {SCHEMA['table_name']}")
    columns_def = ", ".join([f"{name} {typ}" for name, typ in SCHEMA["columns"].items()])
    cursor.execute(f"CREATE TABLE {SCHEMA['table_name']} ({columns_def})")
    
    sample_data = [
        (1, 'John Doe', 35, 'Male', 'Manager', 'john@example.com', '+11234567890', 'USA'),
        (2, 'Jane Smith', 28, 'Female', 'Developer', 'jane@example.com', '+11234567891', 'USA'),
        (3, 'Robert Johnson', 42, 'Male', 'Director', 'robert@example.com', '+11234567892', 'USA'),
        (4, 'Emily Davis', 31, 'Female', 'Designer', 'emily@example.com', '+11234567893', 'USA'),
        (5, 'Michael Brown', 45, 'Male', 'CEO', 'michael@example.com', '+11234567894', 'USA'),
        (6, 'Sarah Wilson', 29, 'Female', 'Analyst', 'sarah@example.com', '+11234567895', 'USA'),
        (7, 'David Taylor', 38, 'Male', 'Engineer', 'david@example.com', '+11234567896', 'USA'),
        (8, 'Jessica Lee', 27, 'Female', 'Marketing', 'jessica@example.com', '+11234567897', 'USA'),
        (9, 'Daniel Martinez', 33, 'Male', 'Sales', 'daniel@example.com', '+11234567898', 'USA'),
        (10, 'Lisa Rodriguez', 40, 'Female', 'HR', 'lisa@example.com', '+11234567899', 'USA'),
        (11, 'Aarav Sharma', 32, 'Male', 'IT Manager', 'aarav@example.com', '+919876543210', 'India'),
        (12, 'Priya Patel', 26, 'Female', 'Software Engineer', 'priya@example.com', '+919876543211', 'India'),
        (13, 'Rahul Singh', 29, 'Male', 'Data Scientist', 'rahul@example.com', '+919876543212', 'India'),
        (14, 'Ananya Gupta', 24, 'Female', 'UX Designer', 'ananya@example.com', '+919876543213', 'India'),
        (15, 'Vikram Joshi', 41, 'Male', 'CTO', 'vikram@example.com', '+919876543214', 'India'),
        (16, 'Neha Reddy', 35, 'Female', 'Product Manager', 'neha@example.com', '+919876543215', 'India'),
        (17, 'Arjun Kumar', 30, 'Male', 'DevOps Engineer', 'arjun@example.com', '+919876543216', 'India'),
        (18, 'Divya Iyer', 27, 'Female', 'QA Engineer', 'divya@example.com', '+919876543217', 'India'),
        (19, 'Sanjay Mishra', 45, 'Male', 'Finance Head', 'sanjay@example.com', '+919876543218', 'India'),
        (20, 'Pooja Mehta', 31, 'Female', 'HR Manager', 'pooja@example.com', '+919876543219', 'India'),
        (21, 'Mohammed Ali', 39, 'Male', 'Sales Director', 'mohammed@example.com', '+971501234567', 'UAE'),
        (22, 'Emma Wilson', 33, 'Female', 'Marketing Head', 'emma@example.com', '+447911123456', 'UK'),
        (23, 'Carlos Gomez', 28, 'Male', 'Support Lead', 'carlos@example.com', '+34911234567', 'Spain'),
        (24, 'Yuki Tanaka', 25, 'Female', 'UI Developer', 'yuki@example.com', '+818012345678', 'Japan'),
        (25, 'Olivia Brown', 36, 'Female', 'Operations Manager', 'olivia@example.com', '+61234567890', 'Australia')
    ]
    cursor.executemany(
        f"INSERT INTO {SCHEMA['table_name']} VALUES ({','.join(['?']*len(SCHEMA['columns']))})",
        sample_data
    )
    conn.commit()
    print("Database initialized with 25 records")

def validate_sql_query(sql):
    try:
        sql_lower = sql.lower()
        valid_columns = set(SCHEMA["columns"].keys())
        valid_table = SCHEMA["table_name"].lower()
        
        parsed = sqlparse.parse(sql)[0]
        if not parsed or not hasattr(parsed, 'tokens'):
            return False, "Invalid SQL structure"

        table_found = False
        invalid_column = None
        for token in parsed.tokens:
            if isinstance(token, sqlparse.sql.Identifier):
                value = token.value.lower()
                if value == valid_table:
                    table_found = True
                elif value not in valid_columns and value != valid_table:
                    invalid_column = value
                    break

        if not table_found:
            return False, f"Invalid table name. Use '{SCHEMA['table_name']}'"
        if invalid_column:
            return False, f"Invalid column name: '{invalid_column}'"

        cursor.execute("EXPLAIN " + sql)
        return True, ""
    except sqlite3.Error as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}. Please try a simpler query."

def get_gemini_response(question):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    You are an SQL expert. Given this EXACT database schema:
    - Table: {SCHEMA['table_name']}
    - Columns: {', '.join(SCHEMA['columns'].keys())}

    Rules:
    1. Return ONLY the SQL query in plain text
    2. Use THESE EXACT column names: {', '.join(SCHEMA['columns'].keys())}
    3. Table name MUST be: {SCHEMA['table_name']}
    4. For name searches use: WHERE customer_name LIKE '%value%'
    5. Support complex queries including:
       - Aggregations (COUNT, AVG, MAX, MIN)
       - GROUP BY with HAVING
       - ORDER BY with correct syntax (e.g., ORDER BY age ASC or ORDER BY age DESC)
       - Multiple conditions with AND/OR
    6. If unsure, return: SELECT * FROM {SCHEMA['table_name']} LIMIT 5

    Examples:
    - "Average age of managers in USA": SELECT AVG(age) FROM customers WHERE position = 'Manager' AND country = 'USA'
    - "Top 3 oldest employees by age": SELECT customer_name, age FROM customers ORDER BY age DESC LIMIT 3
    - "Who is the youngest customer": SELECT customer_name, age FROM customers ORDER BY age ASC LIMIT 1
    - "Count of employees by position in India with age > 30": SELECT position, COUNT(*) as count FROM customers WHERE country = 'India' AND age > 30 GROUP BY position

    Question: {question}
    """
    response = model.generate_content(prompt)
    sql = response.text.strip()
    sql = re.sub(r'```(sql)?|```', '', sql).strip()
    return sql

def execute_query(sql):
    try:
        is_valid, error_msg = validate_sql_query(sql)
        if not is_valid:
            return error_msg

        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            return "No results found"
        
        result = f"Results ({len(rows)} rows):\n"
        for row in rows[:20]:  # Limit to 20 rows
            row_str = " | ".join(f"{col}: {val}" for col, val in zip(columns, row))
            result += row_str + "\n"
        if len(rows) > 20:
            result += f"...and {len(rows) - 20} more rows"
        return result
    except sqlite3.Error as err:
        return f"Database error: {str(err)}"

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()
    
    if not incoming_msg:
        msg.body("Try questions like:\n- Average age of managers in USA\n- Count employees by position in India\n- Top 3 oldest employees\n- Who is the youngest customer")
        return str(resp)
    
    try:
        sql = get_gemini_response(incoming_msg)
        print(f"Generated SQL: {sql}")  # Debug
        result = execute_query(sql)
        msg.body(result if len(result) < 1600 else result[:1500] + "...")
    except Exception as e:
        msg.body(f"Error: {str(e)}. Please try a simpler query or check your input.")
    
    return str(resp)

if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000)
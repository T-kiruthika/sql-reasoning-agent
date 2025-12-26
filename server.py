import os
import re
import json
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from langchain_community.utilities import SQLDatabase
import cohere
from urllib.parse import quote_plus
from langchain.memory import ConversationBufferWindowMemory
from sqlalchemy import create_engine, text
from decimal import Decimal

server_app = Flask(__name__)
server_app.config["SECRET_KEY"] = os.urandom(24)
server_app.config["SESSION_TYPE"] = "filesystem"
server_app.config["SESSION_PERMANENT"] = False
Session(server_app)

try:
    EMBEDDED_API_KEY = "paste your cohere key "

    co = cohere.Client(EMBEDDED_API_KEY)
    LLM_CONFIGURED = True
    print("[SUCCESS] Successfully connected to Cohere API.")
except Exception as e:
    print(f"[ERROR] Error configuring Cohere API: {e}.")
    co = None
    LLM_CONFIGURED = False

def get_llm_response(prompt_text):
    if not LLM_CONFIGURED:
        raise Exception("Cohere client is not initialized. Check console for errors.")
    response = co.chat(
        message=prompt_text,
        temperature=0.1
    )
    return response.text

session_memory = {}

@server_app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@server_app.route('/connect_db', methods=['POST'])
def connect_db():
    data = request.json
    db_type = data.get('db_type')
    username = data.get('username')
    password = data.get('password')
    host = data.get('host')
    port = data.get('port')
    db_name = data.get('db_name')

    if password:
        encoded_password = quote_plus(password)
    else:
        encoded_password = ''

    uri_map = {
        "postgresql": f"postgresql+psycopg2://{username}:{encoded_password}@{host}:{port}/{db_name}",
        "mysql": f"mysql+mysqlconnector://{username}:{encoded_password}@{host}:{port}/{db_name}",
        "sqlite": f"sqlite:///{db_name}",
    }
    db_uri = uri_map.get(db_type)

    if not db_uri:
        return jsonify({"error": "Unsupported database type."}), 400

    try:
        engine = create_engine(db_uri)
        with engine.connect() as connection:
            pass
        session['db_uri'] = db_uri
        session_memory[session.sid] = ConversationBufferWindowMemory(k=4, return_messages=True)
        return jsonify({"success": f"Successfully connected to {db_name}."})
    except Exception as e:
        return jsonify({"error": f"Connection failed. Please check credentials and database status. Error: {e}"}), 500

def get_sql_query_from_llm(user_question, db, chat_history, last_query, last_query_context=None):
    db_schema = db.get_table_info()
    db_dialect = db.dialect

    follow_up_instructions = ""
    if last_query_context:
        context_key = last_query_context.get('key')
        context_value = last_query_context.get('value')
        follow_up_instructions = f"""
CRITICAL: FOLLOW-UP QUESTION DETECTED WITH SPECIFIC CONTEXT.
The user's previous question identified a key piece of information: {context_key} = '{context_value}'.
The user is now asking a follow-up question about this specific category (e.g., "list them").
To ensure a correct, case-insensitive match, you MUST use the UPPER() function on both the column and the value in the WHERE clause.
Correct Query Example: SELECT emp_id, emp_name, {context_key} FROM employees WHERE UPPER({context_key}) = UPPER('{context_value}');
"""
    elif last_query:
        follow_up_instructions = f"""
CRITICAL: FOLLOW-UP QUESTION DETECTED
The user's previous SQL query was: {last_query}
You must analyze the user's new question in the context of this previous query.
Follow-up Logic (apply in this order):
1.  Request for More Details or Refining a Filter: If the user's question is a request for more details (e.g., "tell me more", "full details") OR adds a new filter to the previous results (e.g., "only the ones in department X"), you MUST preserve the original WHERE clause from the previous query.
2.  Filtering a Grouped List: If the previous query was a GROUP BY that returned a list of categories and the user now asks to see members of one category (e.g., "list the names in blood group b+"), generate a NEW SELECT statement with a case-insensitive WHERE clause.
3.  Aggregation of a List: If the previous query returned a simple list of items, and the user now asks to aggregate them (e.g., "count them"), you MUST wrap the previous query in a subquery.
"""

    starts_with_rule = """
4.  "Starts With" Queries: For questions asking for records that "start with" a letter (e.g., "list names that start with M"), generate a simple, case-insensitive LIKE or ILIKE query.
- PostgreSQL Example: SELECT emp_name FROM employees WHERE emp_name ILIKE 'M%';
- MySQL/SQLite Example: SELECT emp_name FROM employees WHERE emp_name LIKE 'M%';
"""

    grouping_rule = """
5.  Grouping and Counting: For "unique values and their counts" of a text column, you MUST use GROUP BY on the UPPER() version of the column to ensure case-insensitive counting. Alias the UPPER(column) back to the original column name for clarity.
- Correct Example: SELECT UPPER(blood_group) AS blood_group, COUNT(*) FROM employees GROUP BY UPPER(blood_group);
"""

    prompt = f"""
You are an expert-level SQL generation engine for a {db.dialect} database. Your only job is to generate a single, correct SQL query. You must follow all rules exactly.
{follow_up_instructions}
SQL GENERATION RULES:
1.  Comparative Questions: For questions that compare two values (e.g., "Is salary in DP002 higher than DP003?"), you MUST generate a single query that calculates both values in separate, clearly-named columns.
2.  List with Primary Key: For a general "list" of items (e.g., "list all employees"), you MUST select both the primary key column (identified by PRIMARY KEY (column_name) in the schema) AND the most important identifying column (e.g., emp_name).
3.  Full Details When Asked: If the user asks for "details", "information on", or "tell me about", then you MUST use SELECT *.
{starts_with_rule}
{grouping_rule}
6.  User-Defined Limits: If the user asks for a specific number of records (e.g., "list the first 100 employees"), you MUST include a LIMIT clause in your query.
7.  Standard SQL: For all other requests, generate appropriate, standard SQL.
Database Schema: {db_schema}
User's Question: "{user_question}"
CRITICAL FINAL INSTRUCTION: Your ONLY output must be a single SQL query wrapped in backticks like this: ```sql SELECT ... ```. DO NOT INCLUDE ANY OTHER TEXT OR EXPLANATIONS.
Your Output (must be only the single, correct SQL query in a sql ...  block):
"""
    if not LLM_CONFIGURED:
        raise Exception("LLM not initialized. Check your Cohere API key.")

    response_text = get_llm_response(prompt)
    return response_text.strip()

def generate_html_output(data):
    if not data: return ""
    headers = data[0].keys()
    pretty_headers = [h.replace('_', ' ').title() for h in headers]
    thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in pretty_headers) + "</tr></thead>"
    rows = []
    for row_data in data:
        row_values = [str(v) if v is not None else "" for v in row_data.values()]
        rows.append("<tr>" + "".join(f"<td>{v}</td>" for v in row_values) + "</tr>")
    tbody = "<tbody>" + "".join(rows) + "</tbody>"
    return f"<div class='table-container'><table>{thead}{tbody}</table></div>"

def generate_comparative_answer(data):
    if not data or len(data) != 1 or len(data[0]) != 2: return None
    first_row = data[0]
    keys = list(first_row.keys())
    values = list(first_row.values())
    if not all(isinstance(v, (int, float, Decimal)) for v in values): return None
    try:
        val1, val2 = float(values[0]), float(values[1])
        metric = keys[0].split('for')[0].replace('_', ' ')
        entity1_name, entity2_name = keys[0].split('for')[-1].upper(), keys[1].split('for')[-1].upper()
        if val1 > val2: answer_text = f"Yes, the {metric} for {entity1_name} is higher than for {entity2_name}."
        elif val2 > val1: answer_text = f"No, the {metric} for {entity1_name} is not higher than for {entity2_name}."
        else: answer_text = f"The {metric} is the same for both {entity1_name} and {entity2_name}."
        data_table_html = generate_html_output(data)
        return f"<p>{answer_text}</p>{data_table_html}"
    except (ValueError, IndexError, TypeError): return None

@server_app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message: return jsonify({"error": "No message provided."}), 400

    db_uri = session.get('db_uri')
    if not db_uri: return jsonify({"error": "Database not connected."}), 403

    memory = session_memory.get(session.sid)
    if memory is None: return jsonify({"error": "Session expired."}), 400

    try:
        engine = create_engine(db_uri)
        db = SQLDatabase(engine=engine)

        last_query_from_session = session.get('last_query')
        last_query_context = session.get('last_query_context')

        history_messages = memory.chat_memory.messages
        formatted_history = ""
        if len(history_messages) > 1:
            formatted_history = f"Previous User Question: {history_messages[-2].content}\nPrevious AI Response (contains SQL): {history_messages[-1].content}"

        llm_response = get_sql_query_from_llm(user_message, db, formatted_history, last_query_from_session, last_query_context)

        match = re.search(r"```sql\n(.*?)\n```", llm_response, re.DOTALL)
        sql_query = match.group(1).strip() if match else llm_response.replace("`", "").replace("sql", "").strip()

        session.pop('last_query_context', None)

        is_follow_up_aggregation = " as sub" in sql_query.lower() and last_query_from_session
        if not is_follow_up_aggregation:
            session['last_query'] = sql_query.strip().rstrip(';')
        else:
             session.pop('last_query', None)

        if not sql_query or "SELECT" not in sql_query.upper():
            return jsonify({"error": "I was unable to generate a valid SQL query."}), 500

        print(f"Executing Full SQL Query: {sql_query}")

        structured_results = []
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            keys = list(result.keys())
            fetched_rows = result.fetchall()
            
            if fetched_rows:
                for row in fetched_rows: structured_results.append(dict(zip(keys, row)))

            if len(structured_results) == 1 and len(keys) == 2:
                first_row = structured_results[0]
                values = list(first_row.values())
                is_string_val = isinstance(values[0], str) and isinstance(values[1], (int, float, Decimal))
                is_val_string = isinstance(values[1], str) and isinstance(values[0], (int, float, Decimal))

                if is_string_val or is_val_string:
                    category_key = keys[0] if is_string_val else keys[1]
                    category_value = values[0] if is_string_val else values[1]
                    session['last_query_context'] = {'key': category_key, 'value': category_value}
                    print(f"Context saved for follow-up: {session['last_query_context']}")

            user_message_lower = user_message.lower().strip()
            starts_with_match = re.search(r'(start|starts|starting) with ([a-zA-Z])', user_message_lower)
            if starts_with_match and structured_results:
                starting_letter = starts_with_match.group(2)
                print(f"Initial results for '{starting_letter}': {len(structured_results)}")
                
                filtered_results = []
                
                all_columns = list(structured_results[0].keys())
                column_to_check = next((col for col in all_columns if 'name' in col.lower()), all_columns[-1])
                print(f"Dynamically selected column for 'starts with' check: {column_to_check}")

                for row in structured_results:
                    name = row.get(column_to_check, "")
                    cleaned_name = re.sub(r'^(mr|ms|mrs|dr)\.?[ ]*|(([A-Z])\.\s*)+', '', name, flags=re.IGNORECASE).strip()
                    if cleaned_name.lower().startswith(starting_letter):
                        filtered_results.append(row)
                
                print(f"Final filtered results: {len(filtered_results)}")
                structured_results = filtered_results

        final_answer = ""
        if not structured_results:
            final_answer = "<p>I could not find any information for that query.</p>"
        else:
            comparative_answer = generate_comparative_answer(structured_results)
            if comparative_answer:
                final_answer = comparative_answer
            elif len(structured_results) == 1 and len(structured_results[0]) == 1:
                key_name = list(structured_results[0].keys())[0].replace("_", " ").title()
                value = list(structured_results[0].values())[0]
                final_answer = f"<p><strong>{key_name}:</strong> {value}</p>"
            else:
                total_rows = len(structured_results)
                summary_text = f"<p>Displaying **{total_rows}** matching records.</p>"
                output_html = generate_html_output(structured_results)
                final_answer = summary_text + output_html

        ai_message_for_memory = f"Generated SQL: `{sql_query}`"
        memory.chat_memory.add_user_message(user_message)
        memory.chat_memory.add_ai_message(ai_message_for_memory)
        session.modified = True
        return jsonify({'response': final_answer})

    except Exception as e:
        print(f"Chat Error Type: {type(e).__name__}")
        print(f"Chat Error Details: {e}")
        error_message = f"An error occurred on the server: {type(e).__name__}."
        if "syntax error" in str(e).lower() or "ProgrammingError" in type(e).__name__:
            error_message = "I tried to ask the database a question, but it didn't understand the grammar. Could you please rephrase your request?"
        elif "DatabaseError" in type(e).__name__:
            error_message = "I couldn't complete the request due to a database error."
        return jsonify({"error": error_message}), 500

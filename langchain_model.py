import os
import re
import sqlite3
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Initialize the LLaMA2 model with corrected settings
llama2_chat = ChatOllama(
    model="deepseek-r1:1.5b",
    num_ctx=512,  # Reduce context window
    repeat_penalty=1.1  # Prevent repetitive thinking
)

# Connect to the SQLite database (ensure the database and table exist)
db = SQLDatabase.from_uri("sqlite:///nba_roster.db",
                          sample_rows_in_table_info=0)


def get_schema(_):
    return db.get_table_info()


def clean_sql_query(raw_query: str) -> str:
    """Clean up the SQL query and ensure it's valid."""
    # Extract only the SQL query part
    query_pattern = r"(?i)(SELECT\s+.*?FROM\s+\S+.*?)(?=\s*;|$)"
    match = re.search(query_pattern, raw_query, re.IGNORECASE | re.DOTALL)

    if match:
        cleaned = match.group(1)
    else:
        # If no valid query found, default to a simple SELECT query
        cleaned = "SELECT * FROM nba_roster"

    # Clean up whitespace and ensure it ends with semicolon
    cleaned = cleaned.strip()
    if not cleaned.endswith(';'):
        cleaned += ';'

    return cleaned


# Define the SQL query prompt
template = """You are a SQL query generator. Output ONLY the SQL query, no explanations or thinking.
Table: nba_roster (NAME, TEAM, SALARY)
Question: {question}
SQL:"""

prompt = ChatPromptTemplate.from_messages([("human", template)])

# Define the response prompt template
response_template = """Based on the question and SQL results, provide a clear answer.
Question: {question}
SQL Results: {response}
Answer:"""

prompt_response = ChatPromptTemplate.from_messages(
    [("human", response_template)])

# Rest of the chain definitions
sql_response = (
    prompt
    | llama2_chat.bind(stop=[";"])
    | StrOutputParser()
    | clean_sql_query
)


def run_query(question):
    try:
        sql_query = sql_response.invoke({"question": question})
        print("\nGenerated SQL Query:", sql_query)

        # Execute the query and format results
        results = db.run(sql_query)

        # Connect directly to get column names
        conn = sqlite3.connect('nba_roster.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # Get column names
        columns = [description[0] for description in cursor.description]

        # Fetch all results
        rows = cursor.fetchall()

        print("\nQuery Results:")
        print("-" * 80)
        print("|".join(f" {col:15}" for col in columns))
        print("-" * 80)

        for row in rows:
            print("|".join(f" {str(value):15}" for value in row))

        conn.close()
        return results

    except Exception as e:
        print(f"Error executing query: {e}")
        return None


# Full chain with the defined prompt_response
full_chain = (
    RunnablePassthrough.assign(
        response=lambda x: run_query(x["question"])
    )
    | prompt_response
    | llama2_chat
)

# Example usage
if __name__ == "__main__":
    # Test queries
    test_questions = [
        "List all teams in the database",
        "Show me the total number of teams",
        "Display all unique team names"
    ]

    for question in test_questions:
        print("\n" + "="*80)
        print(f"Question: {question}")
        result = run_query(question)
        print("="*80)

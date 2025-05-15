# AI Chatbot for Delivering User Queries & Contact Details to CEO via WhatsApp
This project creates an intelligent WhatsApp-based chatbot using Twilio, Flask, and Google Gemini Pro. The chatbot accepts user queries or contact details through WhatsApp, generates structured responses or SQL queries (based on intent), and delivers formatted messages or insights directly to the CEO or backend team for action.

## Features
- Accepts user messages via WhatsApp
- Supports natural language queries (e.g., "Show youngest employee", "List managers in India")
- Uses Gemini Pro for intelligent SQL generation
- Validates and runs SQL queries against a sample customer database
- Sends concise, structured results back via WhatsApp

## Prerequisites
- Twilio Account with WhatsApp Sandbox activated
- Google AI Studio (API Key for Gemini)
- Ngrok (for local development)
- SQL

### Set Up Twilio WhatsApp Sandbox
- Sign up / log in to Twilio Console
- Navigate to Messaging → Try it Out → Send a WhatsApp message
- Activate your WhatsApp sandbox and follow the steps to join it
- Note the sandbox number and Webhook URL field

## Process Overview

- User Sends a Message via WhatsApp
The user sends a natural language question (e.g., "Top 3 oldest employees") through WhatsApp.

- Message Reaches Flask via Twilio Webhook
Twilio forwards the WhatsApp message to your Flask server at the /webhook endpoint.

- Gemini Generates SQL Query
The Flask app passes the user's question to Gemini Pro (Google Generative AI), which returns an appropriate SQL query.

- SQL Validation
The generated SQL is parsed and checked for:
Correct table name (customers)
Valid column names
Basic syntax correctness (via EXPLAIN in SQLite)

- Query Execution on SQLite
If valid, the SQL is run on the local SQLite database (customers.db), and results are fetched.

- Response Sent Back on WhatsApp
The result is formatted (max 20 rows) and sent back to the user via Twilio's WhatsApp API.

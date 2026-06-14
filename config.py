"""
config.py
Arquivo responsável pelas variáveis de ambiente, inicialização da IA
e conexão com serviços externos (Google Sheets).
"""
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from crewai import LLM

# Carrega as variáveis do arquivo .env
load_dotenv()

# Inicialização do Modelo Gemini via OpenRouter
gemini_llm = LLM(
    model="openrouter/google/gemini-2.5-flash", # Prefixo openrouter/ adicionado
    api_key=os.getenv("OPENROUTER_API_KEY"),    # Puxando a nova chave do .env
    temperature=0.3
)

# Configuração e Conexão com o Google Sheets
planilha_conectada = False
aba_notas = None
aba_financeiro = None

try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    # Lê as credenciais do arquivo baixado do Google Cloud
    credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # Abre a planilha pelo ID configurado no .env
    spreadsheet_id = str(os.getenv("SPREADSHEET_ID"))
    planilha = gc.open_by_key(spreadsheet_id)
    aba_notas = planilha.worksheet("Notas")
    aba_financeiro = planilha.worksheet("Financeiro")
    
    planilha_conectada = True
except Exception as e:
    print(f"Aviso: Não foi possível conectar ao Google Sheets. Erro: {e}")
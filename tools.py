"""
tools.py
Contém todas as ferramentas (@tool) separadas por domínio (Acadêmico, Financeiro e Comunicação).
Os agentes utilizam essas funções para executar ações reais.
"""
import os
import requests
from datetime import datetime
from fpdf import FPDF
from crewai.tools import tool

# Importa as abas conectadas do banco de dados
from config import aba_notas, aba_financeiro 

# ==========================================
# FERRAMENTAS ACADÊMICAS (SECRETÁRIO)
# ==========================================

@tool("cadastrar_aluno_notas")
def cadastrar_aluno_notas(dados: str) -> str:
    """Cadastra notas na planilha. Input: 'Nome, Turma, Nota Listening, Nota Speaking, Nota Reading'."""
    try:
        parts = [p.strip() for p in dados.split(',')]
        if aba_notas:
            aba_notas.append_row(parts)
            return f"Sucesso! Notas do aluno {parts[0]} cadastradas no Google Sheets."
        return "Erro: Banco de dados inativo."
    except Exception as e:
        return f"Erro ao cadastrar notas: {str(e)}"

@tool("gerar_boletim_pdf_banco")
def gerar_boletim_pdf_banco(nome_aluno: str) -> str:
    """Gera o boletim lendo as notas do Google Sheets. Input: Apenas o Nome do Aluno."""
    try:
        registros = aba_notas.get_all_records()
        aluno_dados = next((item for item in registros if str(item['Nome']).lower() == nome_aluno.lower()), None)
        
        if not aluno_dados:
            return f"Erro: Aluno '{nome_aluno}' não encontrado no banco de dados."
            
        nome, turma = aluno_dados['Nome'], aluno_dados['Turma']
        n_list, n_speak, n_read = float(aluno_dados['Listening']), float(aluno_dados['Speaking']), float(aluno_dados['Reading'])
        media = (n_list + n_speak + n_read) / 3
        status = "APROVADO(A)" if media >= 7.0 else "REPROVADO(A)"
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 20, f"Boletim Escolar - {nome}", ln=True, align='C')
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Turma: {turma}", ln=True)
        pdf.ln(10)
        
        pdf.set_fill_color(230, 230, 230)
        for materia, nota in [("Listening", n_list), ("Speaking", n_speak), ("Reading", n_read)]:
            pdf.cell(100, 10, materia, border=1)
            pdf.cell(50, 10, str(nota), border=1, ln=True)
            
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Média Final: {media:.2f}", ln=True)
        pdf.cell(0, 10, f"Resultado: {status}", ln=True)
        
        path = f"boletim_{nome.replace(' ', '_')}.pdf"
        pdf.output(path)
        return f"Sucesso! Boletim gerado e salvo em: {path}"
    except Exception as e:
        return f"Erro ao gerar boletim: {str(e)}"

# ==========================================
# FERRAMENTAS FINANCEIRAS
# ==========================================

@tool("cadastrar_financeiro")
def cadastrar_financeiro(dados: str) -> str:
    """Cadastra dados financeiros. Input: 'Nome, Valor Mensalidade, Dia Vencimento, Status'."""
    try:
        parts = [p.strip() for p in dados.split(',')]
        if aba_financeiro:
            aba_financeiro.append_row(parts)
            return f"Sucesso! Dados financeiros de {parts[0]} registrados."
        return "Erro: Banco de dados inativo."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool("atualizar_pagamento")
def atualizar_pagamento(dados: str) -> str:
    """Atualiza o status de pagamento. Input: 'Nome, Novo Status'."""
    try:
        nome, status = [p.strip() for p in dados.split(',')]
        celulas = aba_financeiro.findall(nome)
        if not celulas: return "Aluno não encontrado."
        
        linha = celulas[0].row
        aba_financeiro.update_cell(linha, 4, status) # Atualiza a 4ª coluna (Status)
        return f"Sucesso! Status de {nome} atualizado para {status}."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool("consultar_inadimplentes")
def consultar_inadimplentes(dummy: str) -> str:
    """Retorna uma lista de alunos com status 'Pendente'. Input pode ser vazio ' '."""
    try:
        registros = aba_financeiro.get_all_records()
        devedores = [str(r['Nome']) for r in registros if str(r['Status']).lower() == 'pendente']
        if not devedores: return "Nenhum aluno inadimplente."
        return "Alunos pendentes: " + ", ".join(devedores)
    except Exception as e:
        return f"Erro: {str(e)}"

@tool("gerar_recibo_pdf")
def gerar_recibo_pdf(nome_aluno: str) -> str:
    """Gera um PDF de recibo de pagamento."""
    try:
        registros = aba_financeiro.get_all_records()
        aluno = next((item for item in registros if str(item['Nome']).lower() == nome_aluno.lower()), None)
        if not aluno: return "Aluno não encontrado."
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 20, "RECIBO DE PAGAMENTO", ln=True, align='C')
        pdf.set_font("Helvetica", "", 14)
        pdf.ln(20)
        texto = f"Recebemos de {aluno['Nome']} a quantia de R$ {aluno['Valor']} referente à mensalidade do curso de Inglês."
        pdf.multi_cell(0, 10, texto)
        pdf.ln(20)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", align='R')
        
        path = f"recibo_{aluno['Nome'].replace(' ', '_')}.pdf"
        pdf.output(path)
        return f"Sucesso! Recibo gerado em: {path}"
    except Exception as e:
        return f"Erro: {str(e)}"

# ==========================================
# FERRAMENTAS DE COMUNICAÇÃO
# ==========================================

@tool("enviar_aviso_telegram")
def enviar_aviso_telegram(mensagem: str) -> str:
    """Envia uma mensagem de texto para o Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": mensagem})
        return "Aviso enviado ao Telegram!" if r.status_code == 200 else f"Erro no Telegram: {r.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"
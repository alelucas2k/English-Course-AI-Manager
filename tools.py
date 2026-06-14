"""
tools.py
Contém todas as ferramentas (@tool) separadas por domínio (Acadêmico, Financeiro e Comunicação).
Os agentes utilizam essas funções para executar ações no banco de dados (Google Sheets) e gerar documentos.
"""
import os
import json
import requests
from datetime import datetime
from fpdf import FPDF
from crewai.tools import tool

# Importa as abas conectadas do banco de dados
from config import aba_notas, aba_financeiro 

# ==========================================
# CLASSE BASE PARA PDFs PROFISSIONAIS
# ==========================================
class PDFEscolar(FPDF):
    def __init__(self, tipo_documento="DOCUMENTO OFICIAL"):
        super().__init__()
        self.tipo_documento = tipo_documento

    def header(self):
        # Faixa decorativa superior (Azul Marinho)
        self.set_fill_color(26, 54, 93) 
        self.rect(0, 0, 210, 35, "F")
        
        # Nome da Escola
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "ENGLISH COURSE ACADEMY", ln=True, align="L")
        
        # Subtítulo / Tipo de Documento
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(226, 232, 240)
        self.cell(0, 5, self.tipo_documento, ln=True, align="L")
        
        # Linha de espaçamento após o cabeçalho
        self.ln(20)

    def footer(self):
        # Posiciona a 1,5 cm do fim da página
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(113, 128, 150)
        
        # Linha divisória fina
        self.set_draw_color(226, 232, 240)
        self.line(10, self.get_y() - 2, 200, self.get_y() - 2)
        
        # Rodapé com paginação e data
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(100, 10, f"Gerado em {data_atual} | Sistema de Gestão ERP", align="L")
        self.cell(0, 10, f"Página {self.page_no()}", align="R")


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

@tool("cadastrar_multiplos_alunos_notas")
def cadastrar_multiplos_alunos_notas(dados_json: str) -> str:
    """
    Cadastra as notas de múltiplos alunos simultaneamente.
    Input OBRIGATÓRIO: Uma string contendo um JSON válido de lista de listas.
    Exemplo exato: '[["Carlos", "B1", 8.5, 9.0, 7.5], ["Ana", "A1", 9.5, 9.5, 10.0]]'
    """
    try:
        linhas = json.loads(dados_json)
        if aba_notas:
            aba_notas.append_rows(linhas)
            return f"Sucesso! {len(linhas)} alunos cadastrados academicamente em lote."
        return "Erro: Banco de dados inativo."
    except json.JSONDecodeError:
        return "Erro: O formato dos dados não é um JSON válido."
    except Exception as e:
        return f"Erro no processamento acadêmico em lote: {str(e)}"

@tool("atualizar_notas_aluno")
def atualizar_notas_aluno(dados: str) -> str:
    """
    Atualiza as notas de um aluno existente. 
    Input: 'Nome do Aluno, Nova Nota Listening, Nova Nota Speaking, Nova Nota Reading'.
    """
    try:
        partes = [p.strip() for p in dados.split(',')]
        if len(partes) != 4:
            return "Erro: Forneça o Nome e as 3 notas separadas por vírgula."
            
        nome, n_list, n_speak, n_read = partes
        
        if aba_notas:
            celula = aba_notas.find(nome)
            if celula:
                linha = celula.row
                aba_notas.update_cell(linha, 3, n_list)
                aba_notas.update_cell(linha, 4, n_speak)
                aba_notas.update_cell(linha, 5, n_read)
                return f"Sucesso! Notas do aluno '{nome}' atualizadas."
            return f"Aluno '{nome}' não encontrado nas Notas."
        return "Erro: Banco de dados inativo."
    except Exception as e:
        return f"Erro ao atualizar notas: {str(e)}"

@tool("remover_aluno_notas")
def remover_aluno_notas(nome_aluno: str) -> str:
    """Remove (Deleta) um aluno da base de dados acadêmica (Notas). Input: Nome do aluno."""
    try:
        if aba_notas:
            celula = aba_notas.find(nome_aluno)
            if celula:
                aba_notas.delete_rows(celula.row)
                return f"Sucesso! Aluno '{nome_aluno}' removido da planilha de Notas."
            return f"Aluno '{nome_aluno}' não encontrado nas Notas."
        return "Erro: Banco de dados inativo."
    except Exception as e:
        return f"Erro ao remover notas: {str(e)}"

@tool("consultar_notas_tela")
def consultar_notas_tela(nome_aluno: str) -> str:
    """Busca as notas de um aluno específico para mostrar na tela. Input: Nome do aluno."""
    try:
        registros = aba_notas.get_all_records()
        aluno = next((item for item in registros if str(item['Nome']).lower() == nome_aluno.lower()), None)
        if not aluno: 
            return "Aluno não encontrado no banco de notas."
        return str(aluno) 
    except Exception as e:
        return f"Erro na consulta: {str(e)}"

@tool("listar_todos_alunos")
def listar_todos_alunos(dummy: str) -> str:
    """Retorna a lista de todos os alunos cadastrados com suas respectivas turmas e notas. Input pode ser ' '."""
    try:
        registros = aba_notas.get_all_records()
        if not registros:
            return "Nenhum aluno cadastrado."
        
        # Agora a lista extrai todos os dados relevantes para a IA montar a tabela completa
        lista = [
            {
                "Nome": r.get("Nome", ""), 
                "Turma": r.get("Turma", ""),
                "Listening": r.get("Listening", ""),
                "Speaking": r.get("Speaking", ""),
                "Reading": r.get("Reading", "")
            } for r in registros
        ]
        return str(lista)
    except Exception as e:
        return f"Erro: {str(e)}"

@tool("gerar_boletim_pdf_banco")
def gerar_boletim_pdf_banco(nome_aluno: str) -> str:
    """Gera um boletim escolar profissional lendo as notas do banco. Input: Nome do Aluno."""
    try:
        registros = aba_notas.get_all_records()
        aluno_dados = next((item for item in registros if str(item['Nome']).lower() == nome_aluno.lower()), None)
        
        if not aluno_dados:
            return f"Erro: Aluno '{nome_aluno}' não encontrado no banco de dados."
            
        nome, turma = aluno_dados['Nome'], aluno_dados['Turma']
        n_list, n_speak, n_read = float(aluno_dados['Listening']), float(aluno_dados['Speaking']), float(aluno_dados['Reading'])
        media = (n_list + n_speak + n_read) / 3
        status = "APROVADO(A)" if media >= 7.0 else "REPROVADO(A)"
        
        pdf = PDFEscolar(tipo_documento="BOLETIM DE DESEMPENHO ACADÊMICO")
        pdf.add_page()
        pdf.set_text_color(45, 55, 72) 
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, f"Estudante: {nome.upper()}", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"Turma Ocupada: {turma}", ln=True)
        pdf.cell(0, 7, f"Período Letivo: {datetime.now().year}.1", ln=True)
        pdf.ln(8)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(237, 242, 247) 
        pdf.set_draw_color(203, 213, 224)
        
        pdf.cell(100, 10, " Habilidade Avaliada", border=1, fill=True)
        pdf.cell(50, 10, "Nota Obtida", border=1, fill=True, align="C", ln=True)
        
        pdf.set_font("Helvetica", "", 11)
        notas_itens = [("Análise de Escuta (Listening)", n_list), 
                       ("Expressão Oral (Speaking)", n_speak), 
                       ("Compreensão de Leitura (Reading)", n_read)]
        
        for habilidade, nota in notas_itens:
            pdf.cell(100, 10, f" {habilidade}", border=1)
            pdf.cell(50, 10, f"{nota:.1f}", border=1, align="C", ln=True)
            
        pdf.ln(6)
        
        pdf.set_fill_color(247, 250, 252)
        pdf.rect(10, pdf.get_y(), 150, 25, "F")
        pdf.rect(10, pdf.get_y(), 150, 25, "D")
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(150, 12, f"  Média Final: {media:.2f}", ln=True)
        
        if status == "APROVADO(A)":
            pdf.set_text_color(34, 139, 34)
        else:
            pdf.set_text_color(220, 20, 60) 
            
        pdf.cell(150, 8, f"  Situação: {status}", ln=True)
        
        path = f"boletim_{nome.replace(' ', '_').lower()}.pdf"
        pdf.output(path)
        return f"Sucesso! O Boletim profissional foi gerado e salvo em: {path}"
    except Exception as e:
        return f"Erro ao gerar boletim: {str(e)}"


# ==========================================
# FERRAMENTAS FINANCEIRAS (DIRETOR FINANCEIRO)
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

@tool("cadastrar_multiplos_financeiro")
def cadastrar_multiplos_financeiro(dados_json: str) -> str:
    """
    Cadastra os dados financeiros de múltiplos alunos simultaneamente.
    Input OBRIGATÓRIO: Uma string contendo um JSON válido de lista de listas.
    Exemplo exato: '[["Carlos", 150, 10, "Pago"], ["Ana", 160, 15, "Pendente"]]'
    """
    try:
        linhas = json.loads(dados_json)
        if aba_financeiro:
            aba_financeiro.append_rows(linhas)
            return f"Sucesso! {len(linhas)} registros financeiros criados em lote."
        return "Erro: Banco de dados inativo."
    except json.JSONDecodeError:
        return "Erro: O formato dos dados não é um JSON válido."
    except Exception as e:
        return f"Erro no processamento financeiro em lote: {str(e)}"

@tool("atualizar_pagamento")
def atualizar_pagamento(dados: str) -> str:
    """Atualiza o status de pagamento. Input: 'Nome, Novo Status'."""
    try:
        nome, status = [p.strip() for p in dados.split(',')]
        celulas = aba_financeiro.find(nome)
        if not celulas: return "Aluno não encontrado no financeiro."
        
        linha = celulas.row
        aba_financeiro.update_cell(linha, 4, status) 
        return f"Sucesso! Status de {nome} atualizado para {status}."
    except Exception as e:
        return f"Erro: {str(e)}"

@tool("remover_aluno_financeiro")
def remover_aluno_financeiro(nome_aluno: str) -> str:
    """Remove (Deleta) um aluno da base financeira. Input: Nome do aluno."""
    try:
        if aba_financeiro:
            celula = aba_financeiro.find(nome_aluno)
            if celula:
                aba_financeiro.delete_rows(celula.row)
                return f"Sucesso! Aluno '{nome_aluno}' removido do Financeiro."
            return f"Aluno '{nome_aluno}' não encontrado no Financeiro."
        return "Erro: Banco de dados inativo."
    except Exception as e:
        return f"Erro ao remover financeiro: {str(e)}"

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
    """Gera um PDF de recibo de pagamento profissional."""
    try:
        registros = aba_financeiro.get_all_records()
        aluno = next((item for item in registros if str(item.get('Nome', '')).lower() == nome_aluno.lower()), None)
        if not aluno: 
            return f"Aluno '{nome_aluno}' não encontrado no cadastro financeiro."
        
        # Extração segura para evitar o KeyError (tenta ler 'Dia Vencimento' ou 'Vencimento')
        valor = aluno.get('Valor', aluno.get('Valor Mensalidade', 0))
        dia_vencimento = aluno.get('Dia Vencimento', aluno.get('Vencimento', 'N/D'))
        status_pagamento = aluno.get('Status', 'N/D')
        nome_impressao = aluno.get('Nome', nome_aluno)
        
        pdf = PDFEscolar(tipo_documento="RECIBO DE QUITAÇÃO FINANCEIRA")
        pdf.add_page()
        pdf.set_text_color(45, 55, 72)
        
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(26, 54, 93)
        pdf.cell(0, 15, "COMPROVANTE DE PAGAMENTO", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_text_color(45, 55, 72)
        pdf.set_font("Helvetica", "", 12)
        
        texto_recibo = (
            f"Declaramos para os devidos fins que o estudante {str(nome_impressao).upper()} "
            f"efetuou o pagamento correspondente à mensalidade do curso de Língua Inglesa, "
            f"no valor total de R$ {float(valor):.2f}. O referido valor foi liquidado "
            f"em conformidade com os termos do contrato de prestação de serviços."
        )
        pdf.multi_cell(0, 8, texto_recibo)
        pdf.ln(15)
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(247, 250, 252)
        pdf.cell(60, 10, " Data de Vencimento", border=1, fill=True)
        pdf.cell(60, 10, " Valor Pago", border=1, fill=True)
        pdf.cell(60, 10, " Situação do Boleto", border=1, fill=True, ln=True)
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(60, 10, f" Dia {dia_vencimento}", border=1)
        pdf.cell(60, 10, f" R$ {float(valor):.2f}", border=1)
        pdf.cell(60, 10, f" {str(status_pagamento).upper()}", border=1, ln=True)
        
        pdf.ln(30)
        
        pdf.set_draw_color(160, 174, 192)
        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "Assinatura Eletrônica da Coordenação", ln=True, align="C")
        pdf.cell(0, 4, "English Course Academy ERP", ln=True, align="C")
        
        path = f"recibo_{nome_impressao.replace(' ', '_').lower()}.pdf"
        pdf.output(path)
        return f"Sucesso! Recibo financeiro oficial gerado em: {path}"
    except Exception as e:
        return f"Erro ao gerar recibo: {str(e)}"

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
    

@tool("enviar_documento_telegram")
def enviar_documento_telegram(dados: str) -> str:
    """
    Envia um arquivo PDF gerado para o grupo do Telegram.
    Input: O nome exato do arquivo gerado seguido de uma vírgula e uma mensagem opcional.
    Exemplo: 'boletim_Carlos_Souza.pdf, Segue o documento solicitado.' ou apenas 'recibo_Ana.pdf'
    """
    try:
        # Separa o nome do arquivo da mensagem (se houver)
        partes = dados.split(',', 1)
        caminho_arquivo = partes[0].strip()
        mensagem = partes[1].strip() if len(partes) > 1 else "Segue o documento anexado."
        
        # Verifica se o PDF realmente foi gerado e existe na pasta
        if not os.path.exists(caminho_arquivo):
            return f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado para envio."
            
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        
        # Faz o upload do arquivo via API
        with open(caminho_arquivo, 'rb') as arquivo:
            dados_post = {'chat_id': chat_id, 'caption': mensagem}
            arquivos_post = {'document': arquivo}
            r = requests.post(url, data=dados_post, files=arquivos_post)
            
        if r.status_code == 200:
            return f"Sucesso! Documento '{caminho_arquivo}' enviado ao Telegram com a mensagem."
        else:
            return f"Erro na API do Telegram ao enviar arquivo: {r.text}"
    except Exception as e:
        return f"Erro ao enviar documento: {str(e)}"
    

@tool("listar_todos_financeiro")
def listar_todos_financeiro(dummy: str) -> str:
    """Retorna a lista de todos os alunos cadastrados com seus respectivos status de pagamento e valores. Input pode ser ' '."""
    try:
        registros = aba_financeiro.get_all_records()
        if not registros:
            return "Nenhum registro financeiro encontrado."
        
        # Extrai os dados relevantes com segurança (usando get para evitar KeyError)
        lista = [
            {
                "Nome": r.get("Nome", ""), 
                "Valor": r.get("Valor", r.get("Valor Mensalidade", "")),
                "Vencimento": r.get("Dia Vencimento", r.get("Vencimento", "")),
                "Status": r.get("Status", "")
            } for r in registros
        ]
        return str(lista)
    except Exception as e:
        return f"Erro: {str(e)}"
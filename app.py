import os
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF
import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# 1. Configuração de Ambiente
load_dotenv()
st.set_page_config(page_title="English Course AI Manager", layout="wide", page_icon="🎓")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("ERRO: GEMINI_API_KEY não encontrada no .env")
    st.stop()

# 2. Inicialização do Modelo
gemini_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=api_key,
    temperature=0.5
)

# 3. Definição das Ferramentas (Tools)

@tool("gerar_certificado_pdf")
def gerar_certificado_pdf(dados: str) -> str:
    """Gera um certificado em PDF. O input deve ser uma string exata: 'Nome do Aluno, Documento, Turma'."""
    try:
        parts = [p.strip() for p in dados.split(',')]
        if len(parts) < 3:
            return "Erro: Formato inválido. Forneça os dados separados por vírgula: 'Nome, Documento, Turma'"
        
        nome, doc, turma = parts[0], parts[1], parts[2]
        
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_line_width(2)
        pdf.rect(10, 10, 277, 190)
        pdf.set_font("Helvetica", "B", 40)
        pdf.ln(40)
        pdf.cell(0, 20, "CERTIFICADO", ln=True, align='C')
        pdf.set_font("Helvetica", "", 20)
        pdf.ln(20)
        texto = f"Certificamos que {nome}, portador(a) do documento {doc}, concluiu com êxito o curso de Inglês da Turma {turma}."
        pdf.multi_cell(0, 10, texto, align='C')
        pdf.set_font("Helvetica", "I", 12)
        pdf.ln(30)
        pdf.cell(0, 10, f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y')}", align='C')
        
        path = f"certificado_{nome.replace(' ', '_')}.pdf"
        pdf.output(path)
        return f"Sucesso! Certificado gerado e salvo em: {path}"
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}"

@tool("gerar_boletim_pdf")
def gerar_boletim_pdf(dados_boletim: str) -> str:
    """Gera um boletim. O input deve ser uma string exata: 'Nome, Turma, Nota1, Nota2, Nota3'."""
    try:
        parts = [p.strip() for p in dados_boletim.split(',')]
        if len(parts) < 3:
            return "Erro: Faltam dados. Use: 'Nome, Turma, Notas'"
            
        nome, turma = parts[0], parts[1]
        notas_raw = parts[2:]
        
        notas_dict = {}
        for item in notas_raw:
            if ':' in item:
                k, v = item.split(':')
                notas_dict[k.strip()] = float(v.strip())
            else:
                return "Erro: O formato das notas deve ser Materia:Nota (ex: Inglês:8.5)"
        
        media = sum(notas_dict.values()) / len(notas_dict)
        status = "APROVADO(A)" if media >= 7.0 else "REPROVADO(A)"
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 20, f"Boletim Escolar - {nome}", ln=True, align='C')
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Turma: {turma}", ln=True)
        pdf.ln(10)
        
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(100, 10, "Disciplina", border=1, fill=True)
        pdf.cell(50, 10, "Nota", border=1, fill=True, ln=True)
        
        for m, n in notas_dict.items():
            pdf.cell(100, 10, m, border=1)
            pdf.cell(50, 10, str(n), border=1, ln=True)
        
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Média Final: {media:.2f}", ln=True)
        pdf.cell(0, 10, f"Resultado: {status}", ln=True)
        
        path = f"boletim_{nome.replace(' ', '_')}.pdf"
        pdf.output(path)
        return f"Sucesso! Boletim gerado e salvo em: {path}"
    except Exception as e:
        return f"Erro ao gerar boletim: {str(e)}"

@tool("enviar_aviso_telegram")
def enviar_aviso_telegram(mensagem: str) -> str:
    """Envia uma mensagem de texto para o grupo do Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return "Erro interno: Faltam as variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID no arquivo .env."
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": mensagem})
        if r.status_code == 200:
            return "Sucesso! Aviso enviado ao Telegram da turma."
        else:
            return f"Erro da API do Telegram: {r.text}"
    except Exception as e:
        return f"Erro de conexão com Telegram: {str(e)}"

# 4. Agentes
agente_secretario = Agent(
    role='Secretário Acadêmico',
    goal='Criar documentos oficiais em PDF (certificados e boletins) apenas quando os dados forem fornecidos.',
    backstory='Você é um secretário escolar focado. Você só gera um documento se receber as informações completas. Se a professora pedir um documento mas não fornecer os dados, você pede os dados educadamente em vez de inventá-los.',
    tools=[gerar_certificado_pdf, gerar_boletim_pdf],
    llm=gemini_llm,
    verbose=True,
    allow_delegation=False
)

agente_comunicacao = Agent(
    role='Coordenador de Comunicação',
    goal='Refinar textos e enviar mensagens ou avisos importantes para os alunos usando o Telegram.',
    backstory='Você é um comunicador nato. Garante que as mensagens enviadas sejam claras e profissionais.',
    tools=[enviar_aviso_telegram],
    llm=gemini_llm,
    verbose=True,
    allow_delegation=False
)

agente_atendimento = Agent(
    role='Assistente Virtual da Escola',
    goal='Responder a perguntas gerais da professora de forma amigável e educada.',
    backstory='Você é a interface de comunicação geral. Você sabe que o sistema pode gerar certificados, boletins e enviar avisos pelo Telegram. Se a professora fizer uma pergunta livre (ex: "que dia é hoje?", "quais suas funções?"), você responde naturalmente sem tentar usar ferramentas complexas.',
    llm=gemini_llm,
    verbose=True,
    allow_delegation=False
)

# 5. Interface Streamlit
st.title("🎓 English Course AI Manager")
st.caption("Conectado ao Gemini 2.5 Flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ex: Envie um aviso no Telegram informando que não haverá aula na sexta."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando e roteando o pedido..."):
            
            prompt_lower = prompt.lower()
            palavras_aviso = ["aviso", "telegram", "mensagem", "notificar", "avisar"]
            palavras_documento = ["certificado", "boletim", "pdf", "nota", "gerar", "documento"]
            
            # Roteamento Inteligente com 3 caminhos
            if any(palavra in prompt_lower for palavra in palavras_aviso):
                agente_responsavel = agente_comunicacao
                descricao_tarefa = f"A professora pediu para enviar um aviso: '{prompt}'. Reescreva o texto com um tom cordial (se necessário) e use a ferramenta enviar_aviso_telegram."
                
            elif any(palavra in prompt_lower for palavra in palavras_documento):
                agente_responsavel = agente_secretario
                descricao_tarefa = f"A professora pediu um documento: '{prompt}'. Verifique os dados fornecidos. Se estiverem completos, use a ferramenta de gerar certificado ou boletim. Se faltarem dados, responda avisando o que está faltando."
                
            else:
                # Caminho de fallback (bate-papo geral)
                agente_responsavel = agente_atendimento
                descricao_tarefa = f"A professora disse o seguinte: '{prompt}'. Responda à pergunta ou interação de forma natural e prestativa. Não tente invocar ferramentas."

            tarefa = Task(
                description=descricao_tarefa,
                expected_output="Sua resposta natural ou a confirmação da ação realizada.",
                agent=agente_responsavel
            )
            
            equipe = Crew(
                agents=[agente_responsavel],
                tasks=[tarefa],
                process=Process.sequential
            )
            
            try:
                resultado_obj = equipe.kickoff()
                resultado = str(resultado_obj)
                st.markdown(resultado)
                
                # Detecção de arquivo para criar botão de download
                pdf_match = re.findall(r'[\w-]+\.pdf', resultado)
                for pdf in set(pdf_match): 
                    if os.path.exists(pdf):
                        with open(pdf, "rb") as f:
                            st.download_button(f"📥 Baixar Documento Gerado", f, file_name=pdf)
                
                st.session_state.messages.append({"role": "assistant", "content": resultado})
            except Exception as ex:
                st.error(f"Erro durante a execução da Crew: {ex}")
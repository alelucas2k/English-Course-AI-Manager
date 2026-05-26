"""
app.py
Interface Streamlit e Orquestração Hierárquica da Crew.
"""
import os
import re
import streamlit as st
from crewai import Task, Crew, Process

# Importações dos módulos locais
from config import planilha_conectada, gemini_llm
from agents import (
    agente_secretario, agente_financeiro, 
    agente_comunicacao, agente_atendimento
)

st.set_page_config(page_title="English Course ERP Multi-Agent", layout="wide", page_icon="🎓")
st.title("🎓 English Course ERP Multi-Agent")
st.caption("Sprint 3: Arquitetura Hierárquica e Memória de Contexto")

if not planilha_conectada:
    st.warning("⚠️ A planilha não conectou. Verifique o credentials.json e o SPREADSHEET_ID.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Captura entrada do usuário
if prompt := st.chat_input("Ex: Cadastre o João, gere o boletim dele e mande um aviso no Telegram."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("O Agente Gerente está planejando e delegando tarefas para a equipe..."):
            
            # --- MEMÓRIA DE CONTEXTO ---
            # Pega as últimas 4 interações para que a IA lembre do assunto atual
            ultimas_mensagens = st.session_state.messages[-4:]
            contexto_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in ultimas_mensagens])

            # --- TAREFA ÚNICA PARA O GERENTE ---
            descricao_tarefa = f"""
            Histórico recente da conversa para contexto:
            {contexto_str}
            
            Nova solicitação do usuário: '{prompt}'
            
            Como Gerente, analise o que o usuário quer. Se for mais de uma ação, divida o problema em etapas.
            Delegue cada etapa para o agente mais capacitado da sua equipe. 
            Se a solicitação for apenas uma dúvida ou cumprimento, delegue para o Assistente Virtual.
            Nunca tente usar ferramentas diretamente, SEMPRE delegue para seus agentes subalternos.
            """

            # Em processos hierárquicos, não atribuímos um "agent" à Task. O Gerente pega para si.
            tarefa_principal = Task(
                description=descricao_tarefa,
                expected_output="A resposta final consolidada com as informações ou confirmações de ação geradas pela sua equipe.",
            )
            
            # --- ORQUESTRAÇÃO HIERÁRQUICA ---
            equipe = Crew(
                agents=[agente_secretario, agente_financeiro, agente_comunicacao, agente_atendimento],
                tasks=[tarefa_principal],
                process=Process.hierarchical,  # <-- A GRANDE MUDANÇA DA SPRINT 3
                manager_llm=gemini_llm         # O Gemini atua como o cérebro do Gerente
            )
            
            try:
                # O kickoff agora aciona o Gerente, que vai coordenar os outros 4 agentes
                resultado_obj = equipe.kickoff()
                resultado = str(resultado_obj)
                st.markdown(resultado)
                
                # Detecção de PDFs para liberar download
                pdf_match = re.findall(r'[\w-]+\.pdf', resultado)
                for pdf in set(pdf_match): 
                    if os.path.exists(pdf):
                        with open(pdf, "rb") as f:
                            st.download_button(f"📥 Baixar {pdf}", f, file_name=pdf)
                
                st.session_state.messages.append({"role": "assistant", "content": resultado})
            except Exception as ex:
                st.error(f"Erro durante a execução da Crew: {ex}")
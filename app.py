"""
app.py
Interface Streamlit, Orquestração Hierárquica da Crew e Dashboard de Gestão.
"""
import os
import re
import streamlit as st
from crewai import Task, Crew, Process

# Importações dos módulos locais
from config import planilha_conectada, aba_notas, aba_financeiro, gemini_llm
from agents import (
    agente_secretario, agente_financeiro, 
    agente_comunicacao, agente_atendimento
)

st.set_page_config(page_title="English Course ERP Multi-Agent", layout="wide", page_icon="🎓")

# ==========================================
# FUNÇÃO AUXILIAR: DASHBOARD LATERAL
# ==========================================
def obter_estatisticas():
    if not planilha_conectada:
        return 0, 0, 0.0
    
    try:
        dados_notas = aba_notas.get_all_records()
        dados_fin = aba_financeiro.get_all_records()
        
        total_alunos = len(dados_notas)
        
        pendentes = sum(1 for row in dados_fin if str(row.get('Status', '')).strip().lower() == 'pendente')
        
        media_geral = 0.0
        if total_alunos > 0:
            soma_todas_notas = 0
            for row in dados_notas:
                try:
                    m = (float(row.get('Listening', 0)) + float(row.get('Speaking', 0)) + float(row.get('Reading', 0))) / 3
                    soma_todas_notas += m
                except ValueError:
                    pass
            media_geral = soma_todas_notas / total_alunos
            
        return total_alunos, pendentes, media_geral
    except Exception:
        return 0, 0, 0.0
    

st.set_page_config(page_title="English Course ERP Multi-Agent", layout="wide", page_icon="🎓")

# ==========================================
# CUSTOMIZAÇÃO DE UI/UX (CSS INJETADO)
# ==========================================
st.markdown("""
    <style>
    /* Importa a fonte Inter do Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Aplica a nova fonte a todo o sistema */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Estiliza o Título Principal com Gradiente */
    h1 {
        background: -webkit-linear-gradient(45deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        padding-bottom: 10px;
    }

    /* Estiliza a Barra Lateral (Fundo e Borda) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161625 0%, #0D0D17 100%);
        border-right: 1px solid #2D2D44;
    }

    /* Transforma as Métricas em Cards Modernos */
    [data-testid="stMetric"] {
        background-color: #1E1E2F;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #3A3B50;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        margin-bottom: 10px;
    }
    
    /* Cor do texto do valor da métrica */
    [data-testid="stMetricValue"] {
        color: #FFFFFF;
        font-weight: 600;
    }

    /* Estiliza os Balões de Chat */
    .stChatMessage {
        background-color: #1E1E2F;
        border: 1px solid #2D2D44;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    /* Customiza o Botão de Nova Sessão */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #4F46E5;
        background-color: transparent;
        color: #4F46E5;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #4F46E5;
        color: white;
        border: 1px solid #4F46E5;
    }
    
    /* Suaviza a caixa de status amarela/verde */
    [data-testid="stStatusWidget"] {
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("📊 Visão Geral")
    
    if planilha_conectada:
        total_alunos, pendentes, media_geral = obter_estatisticas()
        
        st.metric(label="Total de Alunos Matriculados", value=total_alunos)
        st.metric(label="Mensalidades Pendentes", value=pendentes, delta=f"-{pendentes}" if pendentes > 0 else "OK", delta_color="inverse")
        st.metric(label="Média Geral da Escola", value=f"{media_geral:.1f}")
    else:
        st.warning("⚠️ Banco de Dados Desconectado.")
        
    st.divider()
    
    st.markdown("### Controle do Sistema")
    if st.button("🗑️ Limpar Memória / Nova Sessão", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# INTERFACE PRINCIPAL (CHAT)
# ==========================================
st.title("🎓 English Course ERP Multi-Agent")
st.caption("Sprint 4: Arquitetura Hierárquica, Dashboard e Tratamento de Resiliência")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Captura entrada do usuário
if prompt := st.chat_input("Ex: Verifique quem não pagou e mande um aviso no Telegram."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        resultado = None 
        
        with st.status("🧠 Agente Gerente iniciando orquestração...", expanded=True) as status:
            st.write("Lendo histórico da conversa e contexto...")
            
            ultimas_mensagens = st.session_state.messages[-4:]
            contexto_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in ultimas_mensagens])

            descricao_tarefa = f"""
            Histórico recente da conversa para contexto:
            {contexto_str}
            
            Nova solicitação do usuário: '{prompt}'
            
            Como Gerente, siga estas regras rígidas:
            1. REGRA DE LOTE (BATCH): Se o usuário solicitar o cadastro de MÚLTIPLOS alunos ao mesmo tempo, instrua expressamente seus agentes a usarem as ferramentas 'cadastrar_multiplos_alunos_notas' e 'cadastrar_multiplos_financeiro'.
            2. Analise o que o usuário quer. Se for mais de uma ação, divida o problema em etapas e delegue.
            3. Nunca tente usar ferramentas diretamente, SEMPRE delegue para seus agentes subalternos.
            4. REGRA DE FORMATAÇÃO VISUAL: Sempre que você for exibir dados de alunos ou notas retornadas pela sua equipe, organize esses dados em uma TABELA MARKDOWN elegante.
            5. REGRA DE ENVIO DE ARQUIVOS: Se o usuário pedir para gerar um documento e enviá-lo no Telegram, você deve PRIMEIRO delegar a geração do PDF ao setor responsável e, APÓS o PDF ser gerado, pegar o nome EXATO do arquivo e passá-lo ao Coordenador de Comunicação para fazer o envio.
            """

            tarefa_principal = Task(
                description=descricao_tarefa,
                expected_output="A resposta final consolidada com as informações ou confirmações de ação geradas pela sua equipe.",
            )
            
            st.write("Delegando tarefas para a equipe...")
            
            equipe = Crew(
                agents=[agente_secretario, agente_financeiro, agente_comunicacao, agente_atendimento],
                tasks=[tarefa_principal],
                process=Process.hierarchical,
                manager_llm=gemini_llm 
            )
            
            # ==========================================
            # TRATAMENTO DE ERROS E RESILIÊNCIA (NOVO)
            # ==========================================
            try:
                # Tenta executar a Crew
                resultado_obj = equipe.kickoff()
                resultado = str(resultado_obj)
                
                # Se der certo, fica verde e minimiza
                status.update(label="✅ Tarefas concluídas com sucesso!", state="complete", expanded=False)
                
            except Exception as ex:
                # Se a API cair ou der timeout, exibe o painel de diagnóstico
                status.update(label="❌ Sistema Indisponível ou Falha de Execução", state="error", expanded=True)
                st.error("⚠️ Não foi possível processar sua solicitação no momento.")
                st.info("Diagnóstico Técnico: Verifique sua conexão com a internet, a integridade da chave da API do OpenRouter (.env) ou possíveis limites de taxa (Rate Limit).")
                with st.expander("Ver detalhes técnicos do erro (Logs do Sistema)"):
                    st.code(str(ex))
                
        # ====================================================
        # RENDERIZAÇÃO DA RESPOSTA E ARQUIVOS NO CHAT
        # ====================================================
        if resultado:
            st.markdown(resultado) 
            
            # Detecção de PDFs para liberar download (garantindo lowercase na busca visual também)
            pdf_match = re.findall(r'[\w-]+\.pdf', resultado, flags=re.IGNORECASE)
            for pdf in set(pdf_match):
                # Tenta achar o arquivo localmente forçando minúsculas, caso a IA tenha escrito diferente no texto
                pdf_lower = pdf.lower() 
                if os.path.exists(pdf_lower):
                    with open(pdf_lower, "rb") as f:
                        st.download_button(f"📥 Baixar Documento ({pdf_lower})", f, file_name=pdf_lower)
                elif os.path.exists(pdf):
                    # Fallback de segurança caso o arquivo original tenha mantido a caixa alta
                    with open(pdf, "rb") as f:
                        st.download_button(f"📥 Baixar Documento ({pdf})", f, file_name=pdf)
            
            st.session_state.messages.append({"role": "assistant", "content": resultado})
            
            # Atualiza as métricas da sidebar
            palavras_gatilho = ["cadastre", "atualize", "nota", "mensalidade", "pago", "remova", "trancou"]
            if any(palavra in prompt.lower() for palavra in palavras_gatilho):
                st.rerun()
"""
agents.py
Define os papéis, objetivos e backstories de cada agente do sistema.
"""
from crewai import Agent

# Importa o modelo configurado
from config import gemini_llm

# Importa as ferramentas criadas
from tools import (
    cadastrar_aluno_notas, gerar_boletim_pdf_banco,
    cadastrar_financeiro, atualizar_pagamento, 
    consultar_inadimplentes, gerar_recibo_pdf,
    enviar_aviso_telegram
)

agente_secretario = Agent(
    role='Secretário Acadêmico',
    goal='Gerenciar matrículas, lançar notas na planilha e gerar boletins lendo os dados do banco.',
    backstory='Você é rigoroso com os dados acadêmicos. Sempre utiliza as ferramentas para ler ou escrever no banco de dados.',
    tools=[cadastrar_aluno_notas, gerar_boletim_pdf_banco],
    llm=gemini_llm, 
    verbose=True
)

agente_financeiro = Agent(
    role='Diretor Financeiro',
    goal='Gerenciar pagamentos, identificar inadimplentes, atualizar planilhas e gerar recibos.',
    backstory='Você cuida do caixa da escola. Verifica com precisão quem pagou e quem deve, extraindo dados da planilha.',
    tools=[cadastrar_financeiro, atualizar_pagamento, consultar_inadimplentes, gerar_recibo_pdf],
    llm=gemini_llm, 
    verbose=True
)

agente_comunicacao = Agent(
    role='Coordenador de Comunicação',
    goal='Refinar mensagens e notificar alunos via Telegram.',
    backstory='Você é a voz da escola. Se outro agente identificar inadimplentes, você formula uma mensagem educada de cobrança e envia no grupo.',
    tools=[enviar_aviso_telegram],
    llm=gemini_llm, 
    verbose=True
)

agente_atendimento = Agent(
    role='Assistente Virtual da Escola',
    goal='Responder a perguntas gerais de forma educada, sem tentar acessar banco de dados.',
    backstory='Você é a recepção. Responde perguntas cotidianas normalmente.',
    llm=gemini_llm, 
    verbose=True
)
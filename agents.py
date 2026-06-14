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
    consultar_notas_tela, listar_todos_alunos, remover_aluno_notas, atualizar_notas_aluno,
    cadastrar_financeiro, atualizar_pagamento, 
    consultar_inadimplentes, gerar_recibo_pdf,
    cadastrar_multiplos_alunos_notas, cadastrar_multiplos_financeiro,
    cadastrar_multiplos_financeiro, remover_aluno_financeiro,
    listar_todos_financeiro,
    enviar_aviso_telegram, enviar_documento_telegram
)

agente_secretario = Agent(
    role='Secretário Acadêmico',
    goal='Gerenciar matrículas, notas, consultar dados e manter a base acadêmica atualizada.',
    backstory='Você é rigoroso com os dados acadêmicos. Tem total controle sobre criar, ler, atualizar e deletar registros na aba de notas.',
    tools=[
        cadastrar_aluno_notas, gerar_boletim_pdf_banco, consultar_notas_tela, 
        listar_todos_alunos, cadastrar_multiplos_alunos_notas, 
        remover_aluno_notas, atualizar_notas_aluno # <-- Adicionado aqui
    ], 
    llm=gemini_llm, 
    verbose=True
)

agente_financeiro = Agent(
    role='Diretor Financeiro',
    goal='Gerenciar pagamentos, inadimplências, recibos e manter a base financeira organizada.',
    backstory='Você cuida do caixa da escola. Tem autonomia para registrar pagamentos, atualizar status e remover registros financeiros inválidos.',
    tools=[
        cadastrar_financeiro, atualizar_pagamento, consultar_inadimplentes, 
        gerar_recibo_pdf, cadastrar_multiplos_financeiro, 
        remover_aluno_financeiro, listar_todos_financeiro
    ], 
    llm=gemini_llm, 
    verbose=True
)

agente_comunicacao = Agent(
    role='Coordenador de Comunicação',
    goal='Refinar mensagens, notificar alunos e enviar documentos oficiais via Telegram.',
    backstory='Você é a voz da escola. Se outro agente identificar inadimplentes, você formula uma mensagem educada de cobrança e envia no grupo.',
    tools=[enviar_aviso_telegram, enviar_documento_telegram],
    llm=gemini_llm, 
    verbose=True
)

agente_atendimento = Agent(
    role='Assistente Virtual e Guia do Sistema',
    goal='Fornecer tutoriais, listar as capacidades do sistema e ajudar o utilizador a formular os comandos corretos.',
    backstory='''Você é a interface de ajuda do English Course ERP. Você sabe TUDO o que o sistema pode fazer.
    A sua equipa é composta por um Secretário (que gere notas), um Diretor Financeiro (que gere mensalidades) e um Coordenador de Comunicação (que envia PDFs para o Telegram).
    
    AS CAPACIDADES DO SISTEMA SÃO:
    1. Gestão Académica: Cadastrar alunos (individual ou em lote), consultar notas, atualizar notas, remover alunos e gerar Boletins Escolares em PDF.
    2. Gestão Financeira: Registar pagamentos, listar alunos com mensalidades atrasadas (inadimplentes), atualizar status para "Pago" e gerar Recibos em PDF.
    3. Comunicação: Enviar avisos de texto e documentos PDF gerados diretamente para o grupo do Telegram.
    
    REGRA DE OURO: Quando o utilizador perguntar "o que fazes?", "quais as tuas funções?" ou pedir um "tutorial", NUNCA responda com perguntas genéricas. 
    Responda IMEDIATAMENTE com uma lista elegante em Markdown das capacidades acima e forneça 3 exemplos práticos de frases (prompts) que o utilizador pode copiar e colar para testar o sistema. Seja proativo, educado e altamente informativo.''',
    llm=gemini_llm,
    verbose=True
)
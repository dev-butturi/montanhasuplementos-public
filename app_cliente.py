import streamlit as st
from supabase import create_client
import datetime


##
# Criar abas: Aba 1: Conheça os profissionais
# Criar abas: Aba 2: 
##


# --- 1. CONFIGURAÇÃO DA PÁGINA E CONEXÃO ---
st.set_page_config(page_title="Agendamento | Montanha Suplementos", page_icon="📅")

# Conexão com o Supabase Portal (Secrets)
URL_PORTAL = st.secrets["supabase_portal"]["url"]
KEY_PORTAL = st.secrets["supabase_portal"]["key"]
supabase_portal = create_client(URL_PORTAL, KEY_PORTAL)

# Mapeamento de Unidades
lojas_map = {
    "São João del-Rei": "SJDR",
    "BH - Jaraguá": "JARAGUA",
    "BH - Cidade Nova": "CENTRO",
    "Contagem": "CONTAGEM"
}

#st.page_link("https://google.com", label="Ir para Google", icon="🌐")


# --- 2. FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=600) # Cache de 10 minutos
def buscar_profissionais_portal():
    res = supabase_portal.table('profissionais_disponiveis').select('*').execute()
    return res.data if res.data else []

def extrair_horarios_validos(agenda_json, dia_semana, unidade_sigla):
    horarios = []
    regras = agenda_json.get('regras', [])
    
    for regra in regras:
        if dia_semana in regra.get('dias', []) and unidade_sigla in regra.get('unidades', []):
            try:
                h_inicio = int(regra['horario']['inicio'].split(':')[0])
                h_fim = int(regra['horario']['fim'].split(':')[0])
                
                for h in range(h_inicio, h_fim):
                    if 6 <= h <= 22:
                        horarios.append(f"{h:02d}:00")
            except Exception:
                continue
    
    return sorted(list(set(horarios)))

# --- 3. INTERFACE DO USUÁRIO ---

st.title("📅 Reserva de Avaliação Esportiva")
st.write("Selecione os detalhes abaixo para verificar a disponibilidade.")

# PASSO 1: FILTROS (REATIVOS)
st.markdown("### 1. Local e Serviço")
c1, c2, c3 = st.columns(3)

unidade_nome = c1.selectbox("Escolha a Unidade", list(lojas_map.keys()))
sigla_alvo = lojas_map[unidade_nome]

servico_alvo = c2.selectbox("Serviço Desejado", [
    "Avaliação Física + Bioimpedância", 
    "Nutricionista", 
    "Consultoria Esportiva"
])

data_alvo = c3.date_input("Data da Visita", min_value=datetime.date.today())
dia_semana_idx = data_alvo.weekday() + 1
if dia_semana_idx == 7: dia_semana_idx = 0 

# PROCESSAMENTO
todos_profs = buscar_profissionais_portal()
profs_validos = []

for p in todos_profs:
    profissoes = p.get('profissao', {})
    agenda = p.get('disponibilidade', {})
    
    pode_atender = False
    if servico_alvo == "Avaliação Física + Bioimpedância": pode_atender = True
    elif servico_alvo == "Nutricionista" and profissoes.get("Nutricionista"): pode_atender = True
    elif servico_alvo == "Consultoria Esportiva" and profissoes.get("Personal Trainer"): pode_atender = True
    
    if pode_atender:
        horarios_deste_prof = extrair_horarios_validos(agenda, dia_semana_idx, sigla_alvo)
        
        if horarios_deste_prof:
            profs_validos.append({
                "id": p['id'],
                "nome": p['nome'],
                "label": f"{p['nome']} ({', '.join([k for k, v in profissoes.items() if v])})",
                "horarios": horarios_deste_prof # MANTIVE 'horarios' PARA SIMPLIFICAR
            })

# PASSO 2: SELEÇÃO DE PROFISSIONAL (REATIVO - FORA DO FORM)
st.divider()
st.markdown("### 2. Especialista e Horário")
if profs_validos:
    dict_escolha = {p['label']: p['horarios'] for p in profs_validos} # CORRIGIDO AQUI
    
    col_p, col_h = st.columns(2)
    nome_escolhido = col_p.selectbox("Selecione o Especialista", list(dict_escolha.keys()))
    
    horas_disponiveis = dict_escolha[nome_escolhido]
    hora_final = col_h.selectbox("Horários Disponíveis", horas_disponiveis)
else:
    st.error("Nenhum profissional disponível para os critérios selecionados.")
    nome_escolhido = None
    hora_final = None

st.divider()
# PASSO 3: FORMULÁRIO DE DADOS PESSOAIS
with st.form("form_final_contato", border=False):
    st.markdown("### 3. Confirme seus Dados")
    c_nome, c_zap = st.columns(2)
    nome_cli = c_nome.text_input("Nome Completo")
    zap_cli = c_zap.text_input("WhatsApp")
    
    st.divider()
    submit = st.form_submit_button("Confirmar Agendamento", type="primary", use_container_width=True)

    if submit:
        if not nome_cli or not zap_cli or not hora_final:
            st.error("Por favor, preencha todos os campos antes de confirmar.")
        else:
            payload = {
                "nome_cliente": nome_cli,
                "whatsapp": zap_cli,
                "unidade": sigla_alvo,
                "data": str(data_alvo),
                "hora": hora_final,
                "profissional": nome_escolhido,
                "servico": servico_alvo,
                "status": "pendente"
            }
            try:
                supabase_portal.table("requisicoes_online").insert(payload).execute()
                st.balloons()
                st.success("Tudo pronto! Entraremos em contato em breve.")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
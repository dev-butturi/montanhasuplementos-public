import streamlit as st
from supabase import create_client
import datetime

st.markdown("""
    <style>
    /* Estilizando os botões primários para a cor da marca (ex: Laranja) */
    .stButton>button {
        border-radius: 20px;
    }
    .st-at { /* Cor de destaque */
        background-color: #FF4B4B;
    }
    /* Estilizando o container do Card */
    [data-testid="stMetricContainer"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

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

def filtrar_horarios_ocupados(horarios_livres, data, profissional, unidade):
    """
    Remove da lista de horários aqueles que já constam como ocupados 
    na tabela 'agendamentos_confirmados' do Portal.
    """
    try:
        # Busca apenas os horários para aquele dia, profissional e unidade
        resp = supabase_portal.table('agendamentos_confirmados')\
            .select('horario')\
            .eq('data_reserva', str(data))\
            .eq('profissional', profissional)\
            .eq('unidade', unidade)\
            .execute()
        
        if resp.data:
            # Extraímos os horários ocupados (HH:MM)
            ocupados = [ag['horario'][:5] for ag in resp.data]
            
            # Filtramos: só mantemos o que NÃO está na lista de ocupados
            return [h for h in horarios_livres if h not in ocupados]
    except Exception as e:
        print(f"Erro ao filtrar ocupados: {e}")
        
    return horarios_livres

# --- 3. INTERFACE DO USUÁRIO ---

# No topo do arquivo, após os imports
st.set_page_config(
    page_title="Agendamento | Montanha Suplementos", 
    page_icon="📅",
    layout="centered" # ou "wide" se preferir
)

# Inserindo a Logo
# Você pode usar um link direto da imagem ou um arquivo local
#st.image("https://seu-link-da-logo.com/logo.png", width=200) 

# No topo do arquivo
LOGO_URL = "SUA_URL_PUBLICA_DO_SUPABASE_AQUI"

st.columns(3)[1].imasge(LOGO_URL, width=200) # Centraliza usando colunas

st.title("📅 Reserva de Avaliação Esportiva")


tab_agendamento, tab_unidades = st.tabs(["🎯 Agendamento", "📍 Nossas Unidades"])


with tab_agendamento:
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
    # --- PASSO 2: SELEÇÃO DE PROFISSIONAL (REATIVO) ---
    st.divider()
    st.markdown("### 2. Especialista e Horário")

    if profs_validos:
        # Criamos um mapeamento do rótulo para os dados brutos do profissional
        # Isso facilita recuperar o 'nome' puro sem as especialidades entre parênteses
        mapa_profs = {p['label']: p for p in profs_validos}
        
        col_p, col_h = st.columns(2)
        
        label_escolhido = col_p.selectbox("Selecione o Especialista", list(mapa_profs.keys()))
        
        # Recuperamos o objeto do profissional selecionado
        prof_selecionado = mapa_profs[label_escolhido]
        
        # 1. Pegamos a lista bruta vinda das regras (JSON)
        horas_da_regra = prof_selecionado['horarios']
        
        # 2. AQUI ENTRA A MÁGICA: Filtramos os horários que já estão no banco
        with st.spinner("Verificando agenda..."):
            horas_disponiveis = filtrar_horarios_ocupados(
                horarios_livres=horas_da_regra,
                data=data_alvo,
                profissional=prof_selecionado['nome'], # Nome puro: "João Silva"
                unidade=sigla_alvo
            )
        
        # 3. Exibimos o selectbox apenas com o que sobrou
        if horas_disponiveis:
            hora_final = col_h.selectbox("Horários Disponíveis", horas_disponiveis)
        else:
            st.error("⚠️ Este profissional já está com a agenda lotada para este dia.")
            hora_final = None
            
    else:
        st.error("Nenhum profissional disponível para os critérios selecionados.")
        label_escolhido = None
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
                    "unidade_pretendida": sigla_alvo,
                    "data_pretendida": str(data_alvo),
                    "hora_pretendida": hora_final,
                    "profissional_pretendido": prof_selecionado['nome'],
                    "servico": servico_alvo,
                    "status": "pendente"
                }
                try:
                    supabase_portal.table("requisicoes_online").insert(payload).execute()
                    st.balloons()
                    st.success("Tudo pronto! Entraremos em contato em breve.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

with tab_unidades:
    st.subheader("Conheça nossas lojas e acompanhe no Instagram")
    
    # Dados das unidades (pode vir de um dict ou do banco)
    unidades = [
        {"nome": "São João del-Rei", "ig": "@montanha_sjdr", "link_ig": "https://instagram.com/montanha_sjdr", "wa": "5532999999999"},
        {"nome": "BH - Jaraguá", "ig": "@montanha_jaragua", "link_ig": "https://instagram.com/montanha_jaragua", "wa": "5531999999999"},
        {"nome": "BH - Cidade Nova", "ig": "@montanha_cidadenova", "link_ig": "https://instagram.com/montanha_cidadenova", "wa": "5531888888888"},
    ]

    # Criando os "Cards" em colunas
    cols = st.columns(2) # 2 cards por linha
    for i, uni in enumerate(unidades):
        with cols[i % 2]:
            with st.container(border=True): # Cria a borda do card
                st.markdown(f"### {uni['nome']}")
                st.write(f"📸 **Instagram:** {uni['ig']}")
                
                c_ig, c_wa = st.columns(2)
                c_ig.link_button("Ver Instagram", uni['link_ig'], use_container_width=True)
                c_wa.link_button("WhatsApp", f"https://wa.me/{uni['wa']}", use_container_width=True)
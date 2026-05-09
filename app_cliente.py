import streamlit as st
from supabase import create_client
import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS ---
st.set_page_config(
    page_title="Agendamento | Montanha Suplementos", 
    page_icon="📅",
    layout="centered"
)

# Conexão com o Supabase
URL_PORTAL = st.secrets["supabase_portal"]["url"]
KEY_PORTAL = st.secrets["supabase_portal"]["key"]
supabase_portal = create_client(URL_PORTAL, KEY_PORTAL)

# --- 2. BANCO DE DADOS LOCAL DAS UNIDADES (A GRANDE MUDANÇA) ---
# Aqui você concentra TUDO. Se inaugurar loja nova, é só adicionar aqui.
LOJAS_DB = {
    "São João del-Rei": {
        "sigla": "SJDR",
        "endereco": "Av. Leite de Castro, 1228 - Fábricas",
        "ig_link": "https://instagram.com/montanha_sjdr",
        "wa_link": "https://wa.me/5532984658118",
        "site_link": "https://www.montanhasuplementos.com.br"
    },
    "BH - Cidade Nova": {
        "sigla": "CENTRO",
        "endereco": "Rua Júlio Pereira da Silva, 10, Loja 1 - Cidade Nova",
        "ig_link": "https://instagram.com/montanha_jaragua",
        "wa_link": "https://wa.me/5531973658122",
        "site_link": "https://www.montanhasuplementos.com.br"
    },
    "BH - Jaraguá": {
        "sigla": "JARAGUA", # Mantive a sua sigla original
        "endereco": "Rua Izabel Bueno, 245, Loja 2 - Jaraguá",
        "ig_link": "https://instagram.com/montanhasuplementos_bh",
        "wa_link": "https://wa.me/5531982404318",
        "site_link": "https://www.montanhasuplementos.com.br"
    },
    "Contagem": {
        "sigla": "CONTAGEM",
        "endereco": "Av. José Faria da Rocha, 3126 - Eldorado",
        "ig_link": "https://instagram.com/montanhasuplementos_contagem",
        "wa_link": "https://wa.me/5531997862923",
        "site_link": "https://www.montanhasuplementos.com.br"
    }
}

# --- 3. CSS E COMPONENTES VISUAIS ---a
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background-color: #FFFFFF; color: #000000; }}
    div.stButton > button:first-child {{
        background-color: #E31F20; color: white; border-radius: 8px; border: none; font-weight: bold; transition: 0.3s;
    }}
    div.stButton > button:first-child:hover {{ background-color: #b3191a; color: white; }}
    .stSelectbox, .stDateInput, .stTextInput {{ background-color: #e7e6e7; border-radius: 5px; }}
    [data-testid="stExpander"], .st-emotion-cache-12w0qpk {{ background-color: #e7e6e7 !important; border: 1px solid #d1d1d1; }}
    h1, h2, h3 {{ color: #000000 !important; }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    """, unsafe_allow_html=True)

def botao_social(rede, link, texto):
    cor = "#833AB4" if rede == "instagram" else "#25D366"
    icone = "fa-brands fa-instagram" if rede == "instagram" else "fa-brands fa-whatsapp"
    html = f"""
    <a href="{link}" target="_blank" style="text-decoration: none;">
        <div style="display: flex; align-items: center; justify-content: center; background-color: {cor}; color: white; padding: 10px 20px; border-radius: 10px; margin: 5px 0; font-weight: bold; font-family: sans-serif;">
            <i class="{icone}" style="margin-right: 10px; font-size: 1.2rem;"></i> {texto}
        </div>
    </a>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE DADOS (Inalteradas) ---
@st.cache_data(ttl=600)
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
                    if 6 <= h <= 22: horarios.append(f"{h:02d}:00")
            except Exception: continue
    return sorted(list(set(horarios)))

def filtrar_horarios_ocupados(horarios_livres, data, profissional, unidade):
    try:
        resp = supabase_portal.table('agendamentos_confirmados').select('horario')\
            .eq('data_reserva', str(data)).eq('profissional', profissional).eq('unidade', unidade).execute()
        if resp.data:
            ocupados = [ag['horario'][:5] for ag in resp.data]
            return [h for h in horarios_livres if h not in ocupados]
    except Exception as e:
        print(f"Erro ao filtrar ocupados: {e}")
    return horarios_livres


# --- 5. LÓGICA DE CAPTURA DA URL (O PULO DO GATO) ---
params = st.query_params
slug_url = params.get("loja", "SJDR").upper() # Ex: link.com/?loja=SJDR

# Descobre qual é a loja selecionada baseada na URL
nome_loja_padrao = list(LOJAS_DB.keys())[0] # Padrão se a URL falhar
for nome, info in LOJAS_DB.items():
    if info["sigla"] == slug_url:
        nome_loja_padrao = nome
        break

dados_loja_padrao = LOJAS_DB[nome_loja_padrao]


# --- 6. INTERFACE PRINCIPAL ---
LOGO_URL = "https://lpixouzhhkswoeqlniof.supabase.co/storage/v1/object/public/midia/Logo_Vertical_Web_white.png"
st.columns(3)[1].image(LOGO_URL, use_container_width=True) 

tab_inicio, tab_agendamento, tab_unidades = st.tabs([":material/waving_hand: Bem-Vindo", ":material/add_task: Agendamento", ":material/pin_drop: Nossas Unidades"])

# --- ABA 1: LINKTREE (Dinâmico conforme a URL) ---
with tab_inicio:
    # Títulos centralizados com HTML
    st.markdown(f"<h2 style='text-align: center;'>Bem-vindo à Montanha {nome_loja_padrao}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; margin-top: -10px;'>📍 {dados_loja_padrao['endereco']}</p>", unsafe_allow_html=True)

    #st.info("👆 Para marcar uma avaliação com especialistas, clique na aba **':material/add_task: Agendamento'** logo acima 👆")
    st.markdown("""
    <div style="
        background-color: #e7e6e7; 
        padding: 15px; 
        border-radius: 8px; 
        text-align: center; 
        color: #000000; 
        border-left: 5px solid #E31F20;
        border-right: 5px solid #E31F20;
        margin: 10px 0px;
    ">
        Clique na aba <<<strong> Agendamento </strong>>>  logo acima para marcar uma avaliação com especialistas.
    </div>
""", unsafe_allow_html=True)
    
    st.divider()
    botao_social("whatsapp", dados_loja_padrao["wa_link"], "Falar com Consultor")
    botao_social("instagram", dados_loja_padrao["ig_link"], "Acompanhar Novidades no Insta")
    st.link_button("🛒 Compre Suplementos On-Line", dados_loja_padrao["site_link"], use_container_width=True)

# --- ABA 2: AGENDAMENTO ---
with tab_agendamento:
    st.write("## Agendamento de Especialistas")
    st.markdown("### 1. Local e Serviço")
    c1, c2, c3 = st.columns(3)

    # O Selectbox já vem pré-selecionado de acordo com a URL!
    index_padrao = list(LOJAS_DB.keys()).index(nome_loja_padrao)
    unidade_nome_selecionada = c1.selectbox("Escolha a Unidade", list(LOJAS_DB.keys()), index=index_padrao)
    
    # Extrai a sigla da unidade selecionada no selectbox
    sigla_alvo = LOJAS_DB[unidade_nome_selecionada]["sigla"]

    servico_alvo = c2.selectbox("Serviço Desejado", ["Avaliação Física + Bioimpedância", "Nutricionista", "Consultoria Esportiva"])
    data_alvo = c3.date_input("Data da Visita", min_value=datetime.date.today())
    dia_semana_idx = data_alvo.weekday() + 1
    if dia_semana_idx == 7: dia_semana_idx = 0 

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
                    "horarios": horarios_deste_prof
                })

    st.divider()
    st.markdown("### 2. Especialista e Horário")

    if profs_validos:
        mapa_profs = {p['label']: p for p in profs_validos}
        col_p, col_h = st.columns(2)
        label_escolhido = col_p.selectbox("Selecione o Especialista", list(mapa_profs.keys()))
        prof_selecionado = mapa_profs[label_escolhido]
        horas_da_regra = prof_selecionado['horarios']
        
        with st.spinner("Verificando agenda..."):
            horas_disponiveis = filtrar_horarios_ocupados(
                horarios_livres=horas_da_regra,
                data=data_alvo,
                profissional=prof_selecionado['nome'],
                unidade=sigla_alvo
            )
        
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

# --- ABA 3: NOSSAS UNIDADES (Gerada automaticamente) ---
with tab_unidades:
    st.write("Conheça toda a nossa rede:")
    
    # O loop lê o dicionário e cria os cards sem precisar de código repetido!
    for nome_unidade, info_unidade in LOJAS_DB.items():
        with st.container():
            st.markdown(f"""
                <div style="background-color: #e7e6e7; padding: 20px; border-radius: 10px; border-left: 5px solid #E31F20; margin-bottom: 10px;">
                    <h4 style="margin: 0;">{nome_unidade}</h4>
                    <p style="color: #666; margin: 5px 0;">{info_unidade['endereco']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Centraliza os botões do card
            col_espaco_esq, c1, c2, col_espaco_dir = st.columns([0.5, 2, 2, 0.5])
            with c1:
                botao_social("instagram", info_unidade['ig_link'], "Instagram")
            with c2:
                botao_social("whatsapp", info_unidade['wa_link'], "WhatsApp")
            st.write("") # Espaçamento entre cards

import streamlit as st
from supabase import create_client
import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA, CONEXÃO E ESTILOS ---
st.set_page_config(
    page_title="Pré-Agendamento | Montanha Suplementos", 
    page_icon="📅",
    layout="centered" # ou "wide" se preferir
)

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

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown(f"""
    <style>
    /* 1. Forçar fundo branco e esconder o menu de troca de tema */
    [data-testid="stAppViewContainer"] {{
        background-color: #FFFFFF;
        color: #000000;
    }}
    
    /* 2. Estilizar os botões primários (Vermelho Montanha) */
    div.stButton > button:first-child {{
        background-color: #E31F20;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #b3191a;
        color: white;
    }}

    /* 3. Estilizar campos de seleção e input (Cinza Suave) */
    .stSelectbox, .stDateInput, .stTextInput {{
        background-color: #e7e6e7;
        border-radius: 5px;
    }}

    /* 4. Estilizar os Cards de Unidades e Containers */
    [data-testid="stExpander"], .st-emotion-cache-12w0qpk {{
        background-color: #e7e6e7 !important;
        border: 1px solid #d1d1d1;
    }}

    /* 5. Ajustar títulos para Preto */
    h1, h2, h3 {{
        color: #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


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

st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

def botao_social(rede, link, texto):
    cor = "#833AB4" if rede == "instagram" else "#25D366"
    icone = "fa-brands fa-instagram" if rede == "instagram" else "fa-brands fa-whatsapp"
    
    html = f"""
    <a href="{link}" target="_blank" style="text-decoration: none;">
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: {cor};
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            margin: 5px 0;
            font-weight: bold;
            font-family: sans-serif;
        ">
            <i class="{icone}" style="margin-right: 10px; font-size: 1.2rem;"></i>
            {texto}
        </div>
    </a>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 3. INTERFACE DO USUÁRIO ---
LOGO_URL = "https://lpixouzhhkswoeqlniof.supabase.co/storage/v1/object/public/midia/Logo_Vertical_Web_white.png"

st.columns(3)[1].image(LOGO_URL, width=200) # Centraliza usando colunas
# vermelho E31F20
# cinza e7e6e7

tab_inicio, tab_agendamento, tab_unidades = st.tabs(["Bem-Vindo", ":material/calendar_check: Agendamento", ":material/pin_drop: Nossas Unidades"])

unidade_nome = 'SJDR'
loja_endereco = 'Av. Leite de Castro, 1228 - Fábricas - São João del-Rei - MG'
with tab_inicio:
    # 1. Foto da Fachada ou Logo da Unidade
    st.title(f"Bem-vindo à Montanha {unidade_nome}")
    st.caption(f"📍 {loja_endereco}")

    if st.button("🎯 Agendar Avaliação Agora", use_container_width=True, type="primary"):
        # Lógica para mudar para a aba de agendamento (ou apenas rolar a página)
        pass
        
    botao_social("whatsapp", "https://wa.me/...", "Falar com Consultor")
    
    botao_social("instagram", "https://insta...", "Acompanhar Novidades")
    
    st.link_button("Compre On-Line", "https://...", use_container_width=True)
    
    st.markdown("---")
  

with tab_agendamento:
    st.write("## Agendamento de Especialistas ")
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
    with st.container():
        st.markdown(f"""
            <div style="background-color: #e7e6e7; padding: 20px; border-radius: 10px; border-left: 5px solid #E31F20;">
                <h5 style="margin:-5px;">São João del-Rei</h4>
                <p style="color: #666; margin: 5px 0;">Av. Leite de Castro 1228, Fábricas</p>
            </div>
        """, unsafe_allow_html=True)
        c12, c1, c2, c22 = st.columns(4)
        with c1:
            botao_social("instagram", "https://instagram.com/perfil", "Siga")
        with c2:
            botao_social("whatsapp", "https://wa.me/5532...", "Chame")
import streamlit as st
from supabase import create_client
import datetime

# Defs
def carregar_profissionais():
    res = supabase_portal.table('profissionais_disponiveis').select('nome, profissao').execute()
    if res.data:
        # Criamos uma lista formatada: "Dr. João (Nutricionista)"
        return [f"{p['nome']} ({p['profissao']})" for p in res.data]
    return ["Selecione um profissional"]

# Conexão com o Supabase EXTERNO (Portal)
URL_PORTAL = st.secrets["supabase_portal"]["url"]
KEY_PORTAL = st.secrets["supabase_portal"]["key"]
supabase_portal = create_client(URL_PORTAL, KEY_PORTAL)

st.set_page_config(page_title="Agendamento | Montanha Suplementos", page_icon="📅")

st.title("Reserva de Avaliação Esportiva")
st.write("Escolha a unidade e o horário de sua preferência.")

# Lista de lojas (Para o cliente saber onde está marcando)
lojas = {
    "São João del-Rei": 1,
    "BH - Cidade Nova": 2,
    "BH - Jaraguá": 3,
    "Contagem": 4
}

with st.form("form_requisicao"):
    nome = st.text_input("Seu Nome Completo *")
    whatsapp = st.text_input("WhatsApp para contato *")
    unidade = st.selectbox("Unidade Montanha Suplementos", list(lojas.keys()))
    
    col1, col2 = st.columns(2)
    data = col1.date_input("Data desejada", min_value=datetime.date.today())
    hora = col2.time_input("Horário")
    
    servicos_disponiveis = [
    "Nutricionista", 
    "Avaliação Física + Bioimpedância", 
    "Consultoria Esportiva"
    ]
    
    servico_selecionado = st.selectbox("Serviço Desejado *", servicos_disponiveis)
    
    lista_profissionais = carregar_profissionais()
    profissional = st.selectbox("Profissional", ["Qualquer Profissional"] + lista_profissionais)
    
    submit = st.form_submit_button("Solicitar Agendamento", type="primary", use_container_width=True)
    
    if submit:
        if not nome or not whatsapp:
            st.error("Por favor, preencha nome e WhatsApp.")
        else:
            nova_req = {
                "nome_cliente": nome,
                "whatsapp": whatsapp,
                "id_loja_pretendida": lojas[unidade],
                "data_pretendida": str(data),
                "hora_pretendida": str(hora),
                "profissional_pretendido": profissional,
                "servico": servico_selecionado
            }
            supabase_portal.table("requisicoes_online").insert(nova_req).execute()
            st.success("✅ Solicitação enviada! Aguarde nosso contato via WhatsApp para confirmação.")
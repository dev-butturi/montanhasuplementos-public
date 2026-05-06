import streamlit as st
from supabase import create_client
import datetime

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
    
    nutri = st.selectbox("Profissional (Opcional)", ["Qualquer Profissional", "Dr. João Silva", "Dra. Maria Nutri"])
    
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
                "nutri_pretendido": nutri,
                "servico": servico_selecionado, # Novo campo
                "status": "pendente"
            }
            supabase_portal.table("requisicoes_online").insert(nova_req).execute()
            st.success("✅ Solicitação enviada! Aguarde nosso contato via WhatsApp para confirmação.")
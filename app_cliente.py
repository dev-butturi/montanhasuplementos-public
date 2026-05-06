import streamlit as st
from supabase import create_client
import datetime

# Conexão com o Supabase EXTERNO (Portal)
URL_PORTAL = "SUA_URL_SUPABASE_PORTAL"
KEY_PORTAL = "SUA_KEY_SUPABASE_PORTAL"
supabase_portal = create_client(URL_PORTAL, KEY_PORTAL)

st.set_page_config(page_title="Agendamento | Montanha Suplementos", page_icon="📅")

st.title("Reserva de Avaliação Esportiva")
st.write("Escolha a unidade e o horário de sua preferência.")

# Lista de lojas (Para o cliente saber onde está marcando)
lojas = {
    "Loja Matriz - Centro": 1,
    "Loja Shopping": 2,
    "Loja Sul": 3
}

with st.form("form_requisicao"):
    nome = st.text_input("Seu Nome Completo *")
    whatsapp = st.text_input("WhatsApp para contato *")
    unidade = st.selectbox("Unidade Montanha Suplementos", list(lojas.keys()))
    
    col1, col2 = st.columns(2)
    data = col1.date_input("Data desejada", min_value=datetime.date.today())
    hora = col2.time_input("Horário")
    
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
                "status": "pendente"
            }
            supabase_portal.table("requisicoes_online").insert(nova_req).execute()
            st.success("✅ Solicitação enviada! Aguarde nosso contato via WhatsApp para confirmação.")
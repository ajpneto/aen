from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ========================
# CONFIGURAÇÕES DO NEGÓCIO
# ========================
EMPRESA = {
    "nome": "AENTECH",
    "slogan": "Assistência Técnica Especializada em Celulares e Tablets",
    "cidade": "Ourinhos - SP",
    "whatsapp": "5541984512660",
    "whatsapp_display": "(41) 98451-2660",
    "email": "contato@fazhoje.com",
    "endereco": "Ourinhos - SP",
    "horario": "Seg a Sáb — 09h às 19h",
    "garantia_dias": 90,
}

SERVICOS = [
    {
        "icone": "fa-mobile-screen-button",
        "titulo": "Troca de Tela",
        "descricao": "Substituição de telas quebradas, com rachaduras, manchas ou falhas no toque (display e touch).",
        "msg_whats": "Olá AENTECH! Preciso trocar a tela do meu celular.",
    },
    {
        "icone": "fa-battery-full",
        "titulo": "Troca de Bateria",
        "descricao": "Substituição de baterias viciadas, com baixa autonomia ou inchadas.",
        "msg_whats": "Olá AENTECH! Preciso trocar a bateria do meu celular.",
    },
    {
        "icone": "fa-plug-circle-bolt",
        "titulo": "Reparo no Conector de Carga",
        "descricao": "Conserto ou troca da porta USB/Lightning quando o aparelho não carrega ou apresenta mau contato.",
        "msg_whats": "Olá AENTECH! Meu celular não está carregando direito.",
    },
    {
        "icone": "fa-microchip",
        "titulo": "Reparos em Componentes",
        "descricao": "Troca de câmeras (frontal e traseira), alto-falantes, microfones, botões de ligar/volume e leitores biométricos.",
        "msg_whats": "Olá AENTECH! Preciso de reparo em um componente do meu celular.",
    },
    {
        "icone": "fa-laptop-code",
        "titulo": "Manutenção de Software",
        "descricao": "Restauração do sistema operacional, remoção de vírus, desbloqueios e recuperação de dados.",
        "msg_whats": "Olá AENTECH! Preciso de manutenção de software no meu celular.",
    },
    {
        "icone": "fa-droplet",
        "titulo": "Desoxidação",
        "descricao": "Limpeza química interna de aparelhos que sofreram danos por contato com líquidos.",
        "msg_whats": "Olá AENTECH! Meu celular molhou, preciso de desoxidação.",
    },
]

PASSOS = [
    {
        "numero": "01",
        "icone": "fa-clipboard-list",
        "titulo": "Ordem de Serviço (OS)",
        "descricao": "Registramos os dados do cliente, identificação do aparelho (modelo, cor e IMEI) e a descrição detalhada do defeito e das condições físicas do celular.",
    },
    {
        "numero": "02",
        "icone": "fa-magnifying-glass-chart",
        "titulo": "Orçamento e Diagnóstico",
        "descricao": "O técnico testa os componentes e define o valor do conserto e o prazo de entrega antes de iniciar o reparo. Sem surpresas!",
    },
    {
        "numero": "03",
        "icone": "fa-circle-check",
        "titulo": "Execução e Garantia",
        "descricao": "Após a aprovação, realizamos a troca de peças ou o reparo na placa e entregamos o aparelho com garantia por escrito pelo serviço prestado.",
    },
]

DEPOIMENTOS = [
    {
        "nome": "Mariana Silva",
        "texto": "Levei meu iPhone com a tela trincada e em 1 hora estava pronto. Atendimento excelente e preço justo!",
        "nota": 5,
    },
    {
        "nome": "Carlos Eduardo",
        "texto": "Meu Samsung tinha parado de carregar. Diagnóstico rápido e conserto no mesmo dia. Recomendo demais!",
        "nota": 5,
    },
    {
        "nome": "Juliana Prado",
        "texto": "Meu celular caiu na água e achei que tinha perdido. A AENTECH desoxidou e salvou tudo!",
        "nota": 5,
    },
]

FAQ = [
    {
        "pergunta": "Quanto tempo demora o conserto?",
        "resposta": "A maioria dos reparos (tela, bateria, conector de carga) é concluída em até 1 hora. Casos mais complexos, como reparo em placa, podem levar de 24h a 72h. O prazo exato é informado no orçamento.",
    },
    {
        "pergunta": "Vocês usam peças originais?",
        "resposta": "Trabalhamos com peças originais e compatíveis de alta qualidade. Você escolhe a melhor opção para o seu bolso durante o orçamento — sempre com transparência.",
    },
    {
        "pergunta": "Quanto custa o diagnóstico?",
        "resposta": "O diagnóstico é GRATUITO. Só cobramos pelo reparo após sua aprovação do orçamento.",
    },
    {
        "pergunta": "Vocês dão garantia?",
        "resposta": f"Sim! Todos os serviços têm {EMPRESA['garantia_dias']} dias de garantia por escrito. Se o problema voltar, consertamos novamente sem custo.",
    },
    {
        "pergunta": "Atendem qual marca?",
        "resposta": "Atendemos todas as marcas: Apple, Samsung, Xiaomi, Motorola, LG, Realme, Asus e outras.",
    },
]

MARCAS = ["Apple", "Samsung", "Xiaomi", "Motorola", "LG", "Realme", "Asus", "Nokia"]


@app.context_processor
def inject_globals():
    return {
        "empresa": EMPRESA,
        "marcas": MARCAS,
        "ano_atual": 2025,
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        servicos=SERVICOS,
        passos=PASSOS,
        depoimentos=DEPOIMENTOS,
        faq=FAQ,
    )


@app.route("/contato", methods=["POST"])
def contato():
    """Recebe formulário de contato (opcional)."""
    data = request.get_json() or request.form.to_dict()
    nome = data.get("nome", "").strip()
    telefone = data.get("telefone", "").strip()
    mensagem = data.get("mensagem", "").strip()

    if not nome or not telefone:
        return jsonify({"ok": False, "erro": "Nome e telefone são obrigatórios."}), 400

    # Aqui você pode integrar com e-mail, banco de dados ou CRM.
    print(f"[NOVO CONTATO] {nome} | {telefone} | {mensagem}")

    return jsonify({"ok": True, "msg": "Recebemos seu contato! Em breve responderemos."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

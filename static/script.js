document.getElementById("btn-filtrar").addEventListener("click", function () {
    let casa = document.getElementById("filtro-casa").value;
    let esporte = document.getElementById("filtro-esporte").value;

    fetch("/filtrar", {
        method: "POST",
        body: JSON.stringify({ casa: casa, esporte: esporte }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        let container = document.getElementById("apostas-container");
        container.innerHTML = "";
        function sportIcon(esporte) {
            const name = (esporte || '').toLowerCase();
            if (name.includes('futebol') || name.includes('football')) return '⚽';
            if (name.includes('tênis') || name.includes('tenis') || name.includes('tennis')) return '🎾';
            if (name.includes('basquete') || name.includes('basketball')) return '🏀';
            if (name.includes('cavalo') || name.includes('horse racing')) return '🏇';
            if (name.includes('rugby')) return '🏉';
            if (name.includes('beisebol') || name.includes('baseball')) return '⚾';
            if (name.includes('volei') || name.includes('volleyball')) return '🏐';
            if (name.includes('hockey') || name.includes('hóquei')) return '🏒';
            if (name.includes('cricket')) return '🏏';
            if (name.includes('formula') || name.includes('f1')) return '🏎️';
            if (name.includes('motogp') || name.includes('moto')) return '🏍️';
            return '🏅';
        }

        data.forEach(aposta => {
            container.innerHTML += `
                <div class="card">
                    <h2>${aposta.evento}</h2>
                    <p><strong>🏠 Casa:</strong> ${aposta.casa}</p>
                    <p><strong>⏳ Tempo:</strong> ${aposta.tempo}</p>
                    <p><span class="sport-icon" title="${aposta.esporte}">${sportIcon(aposta.esporte)}</span></p>
                    <p><strong>🎯 Mercado:</strong> ${aposta.mercado}</p>
                    <p><strong>💰 Lucro:</strong> ${aposta.lucro}</p>
                    <p><strong>📈 Chance:</strong> ${aposta.chance}</p>
                </div>
            `;
        });
    });
});
document.getElementById("btn-filtrar").addEventListener("click", async () => {
    const filtroCasa = document.getElementById("filtro-casa").value.trim();
    const filtroEsporte = document.getElementById("filtro-esporte").value.trim();
    
    try {
        const response = await fetch("http://localhost:5000/filtrar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ casa: filtroCasa, esporte: filtroEsporte })
        });
        
        const data = await response.json();
        console.log("Apostas filtradas recebidas:", data); // DEBUG
        atualizarListaApostas(data);
    } catch (error) {
        console.error("Erro ao filtrar:", error);
        document.getElementById("surebetsList").innerHTML = "Erro ao filtrar surebets.";
    }
});
function atualizarListaApostas(apostas) {
    const betsList = document.getElementById("surebetsList");
    betsList.innerHTML = ""; // Limpa a lista antes de adicionar os novos resultados
    
    if (apostas.length === 0) {
        betsList.innerHTML = "<li>Nenhuma aposta encontrada.</li>";
        return;
    }

    apostas.forEach(bet => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${bet.casa}</strong> - ${bet.evento} - 💰 Lucro: ${bet.lucro}`;
        betsList.appendChild(li);
    });
}
function atualizarListaApostas(apostas) {
    const betsList = document.getElementById("surebetsList");
    betsList.innerHTML = ""; // Limpa a lista

    if (apostas.length === 0) {
        betsList.innerHTML = "<li>Nenhuma aposta encontrada.</li>";
        return;
    }

    apostas.forEach(bet => {
        const li = document.createElement("li");
        li.innerHTML = `
            <strong>${bet.evento}</strong> - ${bet.mercado} <br>
            📢 <strong>${bet.sinal}</strong> <br>
            💰 Lucro: ${bet.lucro} <br>
            🔗 <a href="${bet.link}" target="_blank" class="btn-link">Apostar na ${bet.casa}</a>
        `;
        betsList.appendChild(li);
    });
}

const socket = io("http://localhost:5000");

socket.on("notificacao_surebet", (data) => {
    data.melhores.forEach(sinal => {
        mostrarNotificacao(`📢 Nova Surebet Encontrada! ${sinal}`);
    });

    // Opcional: toca um som de alerta
    const audio = new Audio("/static/alert.mp3");
    audio.play();
});

function mostrarNotificacao(mensagem) {
    const notificacao = document.createElement("div");
    notificacao.className = "notificacao";
    notificacao.textContent = mensagem;

    document.body.appendChild(notificacao);

    setTimeout(() => {
        notificacao.remove();
    }, 5000);  // A notificação desaparece após 5 segundos
}

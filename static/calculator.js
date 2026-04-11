document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM carregado! Verificando botão...");

  const botao = document.getElementById("btn-calcular");

  if (botao) {
      console.log("✅ Botão de calcular encontrado!");
      botao.addEventListener("click", (event) => {
          event.preventDefault();
          console.log("✅ O botão foi clicado!");
          calcularSurebet();
      });
  } else {
      console.error("❌ Botão de calcular NÃO encontrado!");
  }
});

function calcularSurebet() {
  const odds = document.getElementById("odds").value.split(",").map(Number);
  const stake = parseFloat(document.getElementById("stake").value);

  fetch("http://localhost:5000/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ odds, stake })
  })
  .then(response => response.json())
  .then(result => {
    document.getElementById("resultado").innerHTML = result.surebet
    ? `🎯 Apostas: ${result.stakes.join(" | ")} <br> 💰 Lucro: ${result.profit.toFixed(2)}`
    : result.message;
  
  })
  .catch(error => {
      console.error("Erro ao conectar com o servidor:", error);
      document.getElementById("resultado").innerHTML = "Erro ao conectar com o servidor.";
  });
}

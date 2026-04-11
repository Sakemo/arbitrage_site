# 🟢 SureBet Dashboard - Console Logs Guide

## Overview
O dashboard agora fornece **logs detalhados no console do navegador** para rastrear a origem dos dados (Betfair API vs Placeholder).

---

## 🎯 Como Usar

1. **Abra o Flask App:**
   ```bash
   python app.py
   ```

2. **Acesse a Dashboard:**
   - URL: `http://localhost:5000/` ou `http://localhost:5000/home`

3. **Abra o Developer Console:**
   - **Windows/Linux:** `F12` ou `Ctrl + Shift + I`
   - **macOS:** `Cmd + Option + I`
   - Selecione a aba **Console**

---

## 📊 O Que Você Verá

### 1️⃣ **Inicialização da Dashboard**
```
========================================
🟢 SureBet Dashboard Loaded - Ready to Display Data
========================================
[INIT] Loading filter options from /api/filters...
```

### 2️⃣ **Carregamento de Filtros**
```
[FILTER OPTIONS] Loading: 4 bookmakers | 3 sports | Profit range: 1% - 3%
  📊 Bookmakers: Betano, Stake, Superbet, Sportingbet
  ⚽ Sports: Football, Tennis, Basketball
```

### 3️⃣ **Requisição de Dados (Fetch)**
```
[FETCH] Page 1 | Filters: bookmaker=&sport=&date=&min_profit=&sort=profit_desc&page=1...
```

### 4️⃣ **Resposta com Dados Carregados**
```
[SCRAPING DATA] Loaded 7 opportunities ➤ 🟢 7x BETFAIR API | 🔵 0x PLACEHOLDER
[DATA DETAILS]
  🟢 [1] Man United vs Liverpool (Premier League) | Profit: 1.5% | Bookmakers: Betano, Stake, Superbet | Odds: 2.10 | 2.05 | 2.15
  🟢 [2] Real Madrid vs Barcelona (La Liga) | Profit: 2.1% | Bookmakers: Betano, Stake, Superbet | Odds: 1.95 | 1.98 | 2.05
  🔵 [3] Test Event (Placeholder) | Profit: 1.2% | Bookmakers: Betano, Stake | Odds: 1.80 | 1.85
```

### 5️⃣ **Renderização das Oportunidades**
```
  Rendering [1] 🟢 BETFAIR API | Man United vs Liverpool | League: Premier League | Profit: 1.5% | Bookmakers: Betano, Stake, Superbet
  Rendering [2] 🟢 BETFAIR API | Real Madrid vs Barcelona | League: La Liga | Profit: 2.1% | Bookmakers: Betano, Stake, Superbet
  Rendering [3] 🔵 PLACEHOLDER | Test Event | League: Test | Profit: 1.2% | Bookmakers: Betano, Stake
```

### 6️⃣ **Resumo Final**
```
[DISPLAY SUMMARY] Rendered 7 cards: 7x 🟢 BETFAIR API + 0x 🔵 PLACEHOLDER
```

---

## 🎨 Códigos de Cor dos Logs

| Cor | Significado | Exemplo |
|-----|-----------|---------|
| 🟢 Verde | **BETFAIR API** | Dados reais da API Betfair |
| 🔵 Azul | **PLACEHOLDER** | Dados de teste/placeholder |
| 🟠 Laranja | **Filtros** | Filtros aplicados (`[FILTER OPTIONS]`) |
| 🟣 Roxo | **Fetch** | Requisição HTTP (`[FETCH]`) |
| 🟡 Verde Claro | **Scraping** | Dados carregados (`[SCRAPING DATA]`) |
| 🔴 Vermelho | **Erro** | Erros na requisição (`❌ Error fetching...`) |

---

## 🔍 O Que Procurar

### ✅ **Funcionamento Correto - Placeholder Normal**
```
[SCRAPING DATA] Loaded 7 opportunities ➤ 🔵 7x PLACEHOLDER
```
- Significa que todos os dados vêm do banco de dados local (teste)
- Esperado quando Betfair API não está respondendo ou está desabilitada

### ✅ **Funcionamento Correto - Betfair API Ativo**
```
[SCRAPING DATA] Loaded 7 opportunities ➤ 🟢 7x BETFAIR API
```
- Significa que os dados estão vindo da API Betfair em tempo real
- Este é o modo de produção desejado

### ⚠️ **Modo Misto (Ambos)**
```
[SCRAPING DATA] Loaded 10 opportunities ➤ 🟢 5x BETFAIR API | 🔵 5x PLACEHOLDER
```
- Significa que alguns dados são da Betfair, outros são placeholder
- Normal se a Betfair API retorna menos oportunidades que o esperado

### ❌ **Problema - Nenhum Dado**
```
[SCRAPING DATA] Loaded 0 opportunities
[DISPLAY SUMMARY] Rendered 0 cards: 0x 🟢 BETFAIR API + 0x 🔵 PLACEHOLDER
Nenhuma aposta encontrada.
```
- Verifique se há filtros muito restritivos
- Verifique a conexão com o banco de dados

---

## 📋 Fluxo Completo de Logs (Startup)

```
========================================
🟢 SureBet Dashboard Loaded - Ready to Display Data
========================================
[INIT] Loading filter options from /api/filters...

[FILTER OPTIONS] Loading: 4 bookmakers | 3 sports | Profit range: 1% - 3%
  📊 Bookmakers: Betano, Stake, Superbet, Sportingbet
  ⚽ Sports: Football, Tennis, Basketball

[FETCH] Page 1 | Filters: bookmaker=&sport=&date=&min_profit=&sort=profit_desc&page=1&per_page=20

[SCRAPING DATA] Loaded 7 opportunities ➤ 🟢 7x BETFAIR API
[DATA DETAILS]
  🟢 [1] Man United vs Liverpool (Premier League) | Profit: 1.5% | ...
  🟢 [2] Real Madrid vs Barcelona (La Liga) | Profit: 2.1% | ...

  Rendering [1] 🟢 BETFAIR API | Man United vs Liverpool | League: Premier League | Profit: 1.5% | ...
  Rendering [2] 🟢 BETFAIR API | Real Madrid vs Barcelona | League: La Liga | Profit: 2.1% | ...

[DISPLAY SUMMARY] Rendered 7 cards: 7x 🟢 BETFAIR API + 0x 🔵 PLACEHOLDER
```

---

## 🔧 Aplicando Filtros

Quando você seleciona filtros:

```
[FILTERS] Applied: Bookmakers=[Betano, Stake] | Sports=[Football] | MinProfit=2% | Sort=profit_desc

[FETCH] Page 1 | Filters: bookmaker=Betano&bookmaker=Stake&sport=Football&...

[SCRAPING DATA] Loaded 3 opportunities ➤ 🟢 3x BETFAIR API
  🟢 [1] Event 1 | Profit: 2.3% | ...
  🟢 [2] Event 2 | Profit: 2.5% | ...
  🟢 [3] Event 3 | Profit: 2.1% | ...

[DISPLAY SUMMARY] Rendered 3 cards: 3x 🟢 BETFAIR API + 0x 🔵 PLACEHOLDER
```

---

## 🐛 Troubleshooting

### **Logs não aparecem?**
1. Recarregue a página (`F5` ou `Ctrl + R`)
2. Verifique se o console está aberto (`F12`)
3. Procure por erros (em vermelho) que possam estar ocultando os logs

### **Todos os dados como PLACEHOLDER?**
1. Betfair API pode estar desabilitada ou com credenciais inválidas
2. Verifique o arquivo `credentials.json`
3. Verifique se `get_scraped_betfair_data()` está sendo chamado em `modules/scrap.py`

### **Nenhum dado aparece?**
1. Verifique se `/api/opportunities` retorna dados
2. Abra `http://localhost:5000/api/opportunities` no navegador
3. Verifique o console do navegador para ver mensagens de erro

---

## 📱 Exemplo Visual

```
┌─────────────────────────────────────────┐
│ Console (DevTools)                      │
├─────────────────────────────────────────┤
│ ========================================  │
│ 🟢 SureBet Dashboard Loaded             │
│ ========================================  │
│                                         │
│ [INIT] Loading filter options...        │
│                                         │
│ [FILTER OPTIONS] Loading:               │
│   📊 Bookmakers: Betano, Stake...       │
│   ⚽ Sports: Football, Tennis...        │
│                                         │
│ [FETCH] Page 1 | Filters: ...           │
│                                         │
│ [SCRAPING DATA] Loaded 7 opportunities │
│ 🟢 7x BETFAIR API                       │
│ [DATA DETAILS]                          │
│   🟢 [1] Man Utd vs Liverpool...        │
│   🟢 [2] Real Madrid vs Barcelona...    │
│                                         │
│ [DISPLAY SUMMARY] Rendered 7 cards     │
│   7x 🟢 BETFAIR API                     │
└─────────────────────────────────────────┘
```

---

## 💡 Dicas

- **Salve os logs:** Você pode clicar com botão direito e "Save as..." para salvar os logs
- **Filtros de console:** Use o campo de busca para filtrar por `[SCRAPING]`, `[FETCH]`, etc.
- **Exporte logs:** Copie tudo do console e cole em um arquivo de texto para análise
- **Linha do tempo:** Os logs aparecem em ordem cronológica - útil para rastrear performance

---

## 📞 Suporte

Se tiver problemas:
1. Abra o console do navegador (`F12`)
2. Copie o conteúdo dos logs
3. Procure por mensagens de erro (em vermelho)
4. Verifique se as seguintes URLs retornam dados:
   - `http://localhost:5000/api/filters`
   - `http://localhost:5000/api/opportunities`

---

**Última atualização:** 2024
**Versão da Dashboard:** v2.0 com Console Logs Detalhados

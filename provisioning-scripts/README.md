# 🌐 Automação e Provisionamento de Ativos – Projeto 1: Migração e Melhorias de TI

Este diretório centraliza a camada de **automação e provisionamento de rede** desenvolvida para operacionalizar a transição da infraestrutura legada para a nova topologia física e lógica de redes da empresa.

Os scripts em Python contidos aqui utilizam a biblioteca **Netmiko** e o mecanismo de parsing **TextFSM** para aplicar configurações seguras, padronizadas e em lote nos switches Cisco (camadas de **Distribuição** e **Acesso**).

---

## 📌 Integração com a Migração Global

Estes scripts são os executores práticos das diretrizes descritas no **[README principal do projeto](file:///home/eliezerpires/InfrastructureTImigration-and-Improve/README.md)**. O uso destas ferramentas é mapeado diretamente nas seguintes fases da migração:

| Script | Função Principal | Camada da Rede | Fase da Migração Relacionada |
| :--- | :--- | :--- | :--- |
| **`scriptSW_STP.py`** | Configuração inteligente de **Rapid-STP** e prioridade de VLANs. | Distribuição e Acesso | **Fase 4.2 (Distribuição):** Eleição do Switch Root Bridge para evitar loops de Layer 2. |
| **`scriptSW_IPVlan.py`** | Padronização de Hostname, gateway padrão e IP de Gerência (SVI Vlan 200). | Acesso | **Fase 4.3 (Acesso):** Comissionamento e conformidade de nomenclatura de novos switches. |

---

## ⚙️ Detalhamento Arquitetural dos Scripts

### 1. Inteligência de STP e Prevenção de Loops (`scriptSW_STP.py`)
Este script automatiza o provisionamento do **Rapid Spanning Tree (Rapid-STP)** e ajusta as prioridades do Spanning-Tree para cada VLAN de acordo com a função do switch:
* **Switches de Distribuição (Root Bridges):** Configura uma prioridade de STP baixa (`priority 12288` ou personalizada) para assegurar que o tráfego da camada 2 convirja prioritariamente através deles.
* **Switches de Acesso:** Configura uma prioridade mais alta (`priority 24576` ou personalizada).
* **Mecanismo de Segurança L2:** Antes de aplicar qualquer alteração, o script conecta-se ao switch e executa `show vlan brief`. Ele realiza o parsing dos dados e só executa a configuração de prioridade se a VLAN estiver ativa no dispositivo, mitigando contaminações e erros de STP no domínio de broadcast.

### 2. Padronização e Endereçamento de Acesso (`scriptSW_IPVlan.py`)
Automatiza o comissionamento de novos switches de acesso conforme o plano de melhorias lógicas da rede:
* **Padronização de Nomenclatura:** Altera o hostname do dispositivo seguindo rigorosamente o padrão corporativo:
  $$\text{Hostname} = \text{\{localizacao\}}.\text{\{rack\}}.\text{\{novo\_ID\_switch\}}$$
* **Endereçamento de Gerência (VLAN 200):** Configura a interface lógica `Vlan 200` com a descrição oficial e calcula o IP final de gerência de forma dinâmica a partir do identificador numérico extraído do switch (ex: `192.168.236.X` com máscara `/25`).
* **Provisionamento de Gateway:** Atualiza a rota de gerenciamento apontando o `ip default-gateway` para o endereço do switch CORE (`192.168.236.199`).

---

## 🛠️ Requisitos Técnicos e Configuração de Ambiente

### 1. Instalação de Dependências do Python
Para garantir que as conexões SSH/Telnet e o processamento de texto das CLI do Cisco IOS funcionem perfeitamente, instale as bibliotecas necessárias:

```bash
pip install netmiko textfsm
```

### 2. Configurações Prévias nos Ativos (Cisco IOS)
Certifique-se de que todos os switches estejam preparados para conexões SSH seguras:
```cisco
ip ssh version 2
line vty 0 15
 transport input ssh
```

---

## 🚀 Guia de Execução Passo a Passo

### A. Executando o Script de Spanning Tree (STP)
Para configurar ou alterar prioridades de STP por VLAN em lote:
```bash
python3 scriptSW_STP.py
```
**Fluxo Interativo do Terminal:**
1. **Tipo de switch:** Digite `d` para switches de Distribuição ou `a` para switches de Acesso.
2. **Usuário:** Insira seu usuário de gerência de rede.
3. **Senha:** Digite a sua senha (o terminal ocultará os caracteres por segurança).
4. **VLAN ID:** Informe o número da VLAN desejada (ex: `100`).
5. **Prioridade:** Informe a prioridade STP (ex: `12288` ou `24576`).

### B. Executando o Script de Padronização e Endereçamento
Para switches de acesso que estão sendo migrados ou ativados:
```bash
python3 scriptSW_IPVlan.py
```
**Fluxo Interativo do Terminal:**
1. **ID do Switch:** O novo identificador numérico/nome do ativo (ex: `SWA201`).
2. **Localização:** Nome do local/prédio onde o switch está instalado (ex: `PredioA`).
3. **Rack:** Identificador do rack físico (ex: `Rack01`).
4. **Usuário / Senha:** Suas credenciais administrativas da rede.

---

## ⚠️ Alertas Importantes de Transição

> [!WARNING]
> **Definição de Inventário e Faixas de IPs:** 
> Os endereços IPs configurados nas listas `swsditributions` e `swsaccess` dentro dos scripts representam o endereçamento **anterior** à migração (faixa `192.168.236.X`).
> 
> Uma vez concluídas as reconfigurações físicas e a ativação do novo CORE Cisco C9200L, estas listas **devem ser atualizadas nos scripts** com o novo bloco de gerenciamento da **VLAN 200** (`192.168.36.128 - 255`, com gateway em `192.168.36.199`).

---

## 💡 Próximas Etapas e Recomendações de Evolução

1. **Desacoplamento do Inventário:** Como melhoria futura na maturidade do código de redes, recomenda-se mover as listas estáticas de switches de dentro do código Python para arquivos externos em formato `YAML` ou `JSON` (integrando com ferramentas de inventário dinâmico como Ansible ou API do NetBox).
2. **Ambiente de Validação:** Sempre realize a homologação de novas prioridades de STP em ambiente controlado de laboratório ou durante janelas de manutenção estritas de madrugada para evitar quedas no tráfego produtivo.
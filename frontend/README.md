# Frontend - Sistema de Matching de Licitações

Este é o frontend React do Sistema de Matching de Licitações, que consome as APIs do backend Python para buscar e gerenciar licitações.

## 🚀 Funcionalidades

- **Buscar Novas Licitações**: Inicia o processo de busca de novas licitações do PNCP
- **Reavaliar Licitações**: Executa reavaliação das licitações existentes no banco
- **Visualizar Licitações**: Lista todas as licitações armazenadas no banco de dados
- **Visualizar Empresas**: Lista todas as empresas cadastradas no sistema
- **Status em Tempo Real**: Acompanha o status dos processos em execução

## 🛠️ Tecnologias Utilizadas

- **React 18** com TypeScript
- **Tailwind CSS** para estilização
- **shadcn/ui** para componentes de interface
- **Lucide React** para ícones
- **Fetch API** para comunicação com o backend

## 📦 Instalação

```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm start
```

O frontend será executado em `http://localhost:3000` e se comunicará com a API Flask em `http://localhost:5000`.

## 🔧 Configuração

A URL base da API está configurada em `src/App.tsx`:

```typescript
const API_BASE_URL = 'http://localhost:5000/api';
```

Certifique-se de que o backend Flask esteja rodando na porta 5000.

## 📱 Como Usar

1. **Iniciar o Backend**: Certifique-se de que a API Flask está rodando
2. **Abrir o Frontend**: Acesse `http://localhost:3000`
3. **Buscar Licitações**: Clique em "Buscar Novas Licitações" para buscar do PNCP
4. **Reavaliar**: Clique em "Reavaliar Licitações" para reprocessar matches
5. **Visualizar Dados**: Use as abas para ver licitações e empresas

## 🎨 Interface

- **Cards de Status**: Mostram o status atual dos processos
- **Botões de Ação**: Para executar as funções principais
- **Abas**: Para alternar entre visualização de licitações e empresas
- **Polling**: Atualização automática do status durante execução

## 🔍 Endpoints Consumidos

- `GET /api/bids` - Buscar licitações
- `GET /api/companies` - Buscar empresas
- `POST /api/search-new-bids` - Buscar novas licitações
- `POST /api/reevaluate-bids` - Reavaliar licitações
- `GET /api/status` - Status dos processos

## 🚦 Status dos Processos

O frontend monitora automaticamente o status dos processos em background:

- 🔵 **Executando**: Processo em andamento
- 🟢 **Sucesso**: Processo concluído com sucesso
- 🔴 **Erro**: Processo falhou
- ⚪ **Parado**: Processo não executado

## 📝 Estrutura do Projeto

```
src/
├── components/
│   └── ui/           # Componentes shadcn/ui
├── lib/
│   └── utils.ts      # Utilitários
├── App.tsx           # Componente principal
├── index.tsx         # Ponto de entrada
└── index.css         # Estilos globais
```

## 🤝 Contribuição

Para contribuir com o projeto:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

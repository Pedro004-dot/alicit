---
description: 
globs: 
alwaysApply: true
---
/**
 * roo.config.ts
 * 
 * Este arquivo define as regras, convenções e arquitetura que devem ser seguidas
 * durante o desenvolvimento do sistema RAG para análise de documentos de licitação
 * via WhatsApp.
 * 
 * Última atualização: Incorpora o modelo de dados refinado com estrutura hierárquica
 * de Licitações, Documentos, Anexos e estratégia otimizada para FAISS.
 */

const cursorRules = 
  /**
   * VISÃO GERAL DO PROJETO
   * 
   * Sistema: RAG (Retrieval Augmented Generation) para análise de documentos de licitações
   * Canal: WhatsApp via Evolution API
   * Stack: Node.js, TypeScript, Express, Prisma, PostgreSQL, FAISS, LangChain
   * 
   * O sistema permite que usuários enviem documentos de licitação via WhatsApp,
   * extraia automaticamente dados estruturados importantes, e responda a perguntas
   * específicas sobre o conteúdo dos documentos através de RAG.
   * 
   * Uma licitação pode conter múltiplos documentos e anexos, todos indexados
   * de forma unificada para consultas semânticas eficientes.
   */
  
  /**
   * ESTRUTURA DE DIRETÓRIOS
   */
  directoryStructure: {
    src: {
      config: 'Configurações da aplicação',
      controllers: 'Manipuladores de requisições HTTP',
      services: {
        core: 'Serviços principais do domínio (users, bids, documents)',
        rag: 'Serviços relacionados ao processamento RAG',
        whatsapp: 'Serviços de integração com WhatsApp',
        ai: 'Serviços de interação com LLMs e embeddings'
      },
      repositories: 'Camada de acesso a dados com Prisma',
      routes: 'Definição de rotas da API',
      middlewares: 'Middlewares da aplicação',
      utils: 'Funções utilitárias',
      types: 'Definições de tipos TypeScript',
      lib: {
        langchain: 'Componentes customizados do LangChain',
        whatsapp: 'Integrações com WhatsApp via Evolution API',
        vectorstore: 'Implementações e utilitários para FAISS',
        llm: 'Configurações de modelos LLM (OpenAI, Google Gemini)'
      }
    },
    prisma: 'Schema do Prisma e migrações',
    tests: 'Testes automatizados',
    storage: {
      documents: 'Armazenamento de documentos originais',
      indices: {
        bids: 'Índices FAISS organizados por licitação'
      }
    }
  },
  
  /**
   * CONVENÇÕES DE CÓDIGO
   */
  codingConventions: {
    general: [
      'Usar TypeScript para todo o código',
      'Seguir padrões ESLint/Prettier configurados',
      'Documentar funções e classes com JSDoc',
      'Utilizar async/await para operações assíncronas (evitar callbacks)',
      'Aplicar princípios SOLID',
      'Utilizar injeção de dependência quando apropriado'
    ],
    
    naming: {
      files: 'kebab-case para nomes de arquivos (bid-service.ts)',
      classes: 'PascalCase para classes (BidProcessor)',
      interfaces: 'PascalCase com prefixo I (IBid)',
      types: 'PascalCase (BidMetadata)',
      functions: 'camelCase para funções e métodos (processBid)',
      variables: 'camelCase para variáveis (userBid)',
      constants: 'SNAKE_CASE_MAIÚSCULO para constantes globais (MAX_CHUNK_SIZE)',
      database: {
        tables: 'snake_case para tabelas (bid_documents)',
        columns: 'snake_case para colunas (document_id)'
      }
    },
    
    structure: {
      imports: 'Agrupar imports: externos, internos, tipos, relativos',
      exports: 'Usar exports nomeados ao invés de default exports',
      maxLineLength: 100,
      indentation: 2
    }
  },
  
  /**
   * ARQUITETURA E PADRÕES
   */
  architecture: {
    pattern: 'Arquitetura em camadas com separação clara de responsabilidades',
    
    layers: {
      routes: {
        responsibility: 'Definir endpoints e direcionar para controllers',
        naming: '*-routes.ts',
        location: 'src/routes/',
        rules: [
          'Não deve conter lógica de negócio',
          'Validar input com middleware dedicado (Zod, Joi, etc)',
          'Agrupar rotas por domínio/funcionalidade'
        ]
      },
      
      controllers: {
        responsibility: 'Processar requests, invocar services, formatar responses',
        naming: '*-controller.ts',
        location: 'src/controllers/',
        rules: [
          'Métodos devem ser curtos (máx. 15-20 linhas)',
          'Apenas orquestração, sem regras de negócio',
          'Validação básica de parâmetros',
          'Tratamento de erros consistente',
          'Retornar respostas com status HTTP apropriados'
        ]
      },
      
      services: {
        responsibility: 'Implementar regras de negócio e lógica da aplicação',
        naming: '*-service.ts',
        location: 'src/services/',
        rules: [
          'Regras de negócio devem estar isoladas em services',
          'Services devem ser testáveis independentemente',
          'Evitar dependências diretas de frameworks',
          'Injetar dependências (repositories, outros services)',
          'Organizar por domínio/funcionalidade',
          'Usar interfaces para abstração'
        ],
        domainServices: [
          'UserService: Gestão de usuários e contexto ativo',
          'BidService: Operações com licitações',
          'DocumentService: Processamento de documentos principais',
          'AttachmentService: Gerenciamento de anexos',
          'RagService: Core do sistema de RAG',
          'WhatsAppService: Interação com Evolution API',
          'VectorIndexService: Gerenciamento de índices FAISS'
        ]
      },
      
      repositories: {
        responsibility: 'Abstrair acesso a dados e operações com Prisma',
        naming: '*-repository.ts',
        location: 'src/repositories/',
        rules: [
          'Encapsular todas as queries do Prisma',
          'Métodos devem representar operações de domínio',
          'Implementar interfaces definidas em src/types',
          'Manipular erros específicos de banco de dados',
          'Sem lógica de negócio, apenas CRUD e queries'
        ]
      }
    },
    
    patterns: {
      dependency_injection: 'Usar injeção de dependência para facilitar testes',
      error_handling: 'Implementar classes de erro específicas e middleware global',
      validation: 'Validar inputs com schemas (Zod)',
      rate_limiting: 'Implementar rate limiting para proteger APIs'
    }
  },
  
  /**
   * TECNOLOGIAS E IMPLEMENTAÇÕES ESPECÍFICAS
   */
  technologies: {
    database: {
      technology: 'PostgreSQL',
      orm: 'Prisma',
      rules: [
        'Schema deve ser versionado no repositório',
        'Migrações devem ser geradas via Prisma',
        'Usar enums para valores constantes',
        'Implementar soft delete quando apropriado',
        'Adicionar índices para campos frequentemente consultados',
        'Usar UUID para chaves primárias',
        'Validar dados antes de inserir/atualizar',
        'Manter relacionamentos claros entre Bid, Document e Attachment'
      ]
    },
    
    rag: {
      framework: 'LangChain',
      vectorStore: 'FAISS',
      embeddings: 'OpenAI Embeddings (text-embedding-large)',
      llm: 'Google Gemini (gemini-1.0-pro)',
      rules: [
        'Criar um índice FAISS por licitação (agrupando todos documentos e anexos)',
        'Manter mapeamento entre vectorId e documentChunks no banco de dados',
        'Implementar filtragem por documento/anexo específico em runtime',
        'Componentizar pipelines de RAG para testabilidade',
        'Implementar estratégias de chunking semântico',
        'Persistir índices FAISS em disco organizado por licitação',
        'Aplicar reranking para resultados de busca',
        'Implementar retrieval com MMR (Maximum Marginal Relevance)',
        'Manter metadados detalhados junto aos chunks',
        'Otimizar uso de tokens nos prompts',
        'Implementar atualização incremental de índices FAISS quando novos documentos são adicionados',
        'Implementar fallbacks para falhas de API externa'
      ]
    },
    
    whatsapp: {
      technology: 'Evolution API',
      rules: [
        'Abstrair comunicação com Evolution API em classe dedicada',
        'Implementar retry para mensagens falhas',
        'Validar mídia recebida antes de processamento',
        'Limitar tamanho máximo de documentos',
        'Implementar queue para processamento assíncrono',
        'Manter metadados de conversas para contexto',
        'Detectar intenção de trocar contexto entre licitações'
      ]
    },
    
    security: {
      rules: [
        'Não expor credenciais em código',
        'Usar variáveis de ambiente para configurações sensíveis',
        'Validar e sanitizar todos os inputs',
        'Implementar rate limiting',
        'Registrar tentativas de acesso inválidas',
        'Implementar autenticação por número WhatsApp',
        'Sanitizar conteúdo de documentos antes de processamento'
      ]
    }
  },
  
  /**
   * TRATAMENTO DE ERROS
   */
  errorHandling: {
    strategy: 'Utilizar classes de erro personalizadas + middleware global',
    rules: [
      'Criar hierarquia de erros (BaseError -> tipos específicos)',
      'Mapear erros para códigos HTTP apropriados',
      'Logar detalhes de erros para depuração',
      'Retornar mensagens de erro amigáveis aos usuários',
      'Capturar erros assíncronos com try/catch ou middleware'
    ],
    errorTypes: [
      'ValidationError', 'DocumentProcessingError', 'NotFoundError', 
      'DatabaseError', 'WhatsAppError', 'LLMError', 'RagError', 'FaissError'
    ]
  },
  
  /**
   * LOGGING E MONITORAMENTO
   */
  logging: {
    library: 'winston/pino',
    rules: [
      'Estruturar logs em formato JSON',
      'Incluir contexto em todos os logs (requestId, userId, etc)',
      'Definir níveis de log adequados (error, warn, info, debug)',
      'Evitar logging de dados sensíveis',
      'Implementar correlationId para rastreamento de requests'
    ],
    metrics: [
      'Tempo de processamento de documentos',
      'Tempo de resposta para consultas RAG',
      'Taxa de sucesso de extração de metadados',
      'Qualidade das respostas (via feedback usuário)',
      'Uso de recursos (memória, CPU, tokens)',
      'Tamanho dos índices FAISS',
      'Número de chunks por licitação'
    ]
  },
  
  /**
   * TESTES
   */
  testing: {
    frameworks: ['Jest', 'Supertest'],
    types: [
      'Testes unitários para services e utils',
      'Testes de integração para repositories e APIs',
      'Testes e2e para fluxos completos'
    ],
    rules: [
      'Mínimo de 70% de cobertura de código',
      'Usar mocks para dependências externas',
      'Testar casos de erro e exceções',
      'Implementar factories para criação de objetos de teste',
      'Separar testes por tipo e domínio',
      'Testar diferentes cenários de consulta FAISS'
    ]
  },
  
  /**
   * MODELOS DE DADOS PRINCIPAIS - ATUALIZADOS
   */
  dataModels: {
    user: {
      fields: [
        'id: UUID (PK)',
        'phone_number: String (unique)',
        'name: String?',
        'active_bid_id: UUID? (FK)',
        'created_at: DateTime',
        'updated_at: DateTime'
      ]
    },
    
    bid: {
      fields: [
        'id: UUID (PK)',
        'user_id: UUID (FK)',
        'title: String',
        'bid_number: String?',
        'bid_type: BidType (enum)',
        'status: BidStatus (enum)',
        'metadata: JSON',
        'created_at: DateTime',
        'updated_at: DateTime'
      ]
    },
    
    document: {
      fields: [
        'id: UUID (PK)',
        'bid_id: UUID (FK)',
        'title: String',
        'file_name: String',
        'file_path: String',
        'file_type: String',
        'is_main_document: Boolean',
        'processing_status: ProcessingStatus (enum)',
        'metadata: JSON',
        'created_at: DateTime',
        'updated_at: DateTime'
      ]
    },
    
    attachment: {
      fields: [
        'id: UUID (PK)',
        'document_id: UUID (FK)',
        'title: String',
        'file_name: String',
        'file_path: String',
        'file_type: String',
        'processing_status: ProcessingStatus (enum)',
        'metadata: JSON',
        'created_at: DateTime',
        'updated_at: DateTime'
      ]
    },
    
    documentChunk: {
      fields: [
        'id: UUID (PK)',
        'document_id: UUID? (FK)',
        'attachment_id: UUID? (FK)',
        'content: Text',
        'order: Integer',
        'metadata: JSON',
        'vector_id: String?', // Referência à posição no índice FAISS da licitação
        'created_at: DateTime'
      ]
    },
    
    vectorIndex: {
      fields: [
        'id: UUID (PK)',
        'bid_id: UUID (FK, unique)',
        'index_path: String',
        'dimensions: Integer',
        'vector_count: Integer',
        'last_updated: DateTime',
        'created_at: DateTime'
      ]
    },
    
    conversation: {
      fields: [
        'id: UUID (PK)',
        'user_id: UUID (FK)',
        'active_bid_id: UUID?',
        'start_time: DateTime',
        'last_activity: DateTime',
        'created_at: DateTime',
        'updated_at: DateTime'
      ]
    },
    
    message: {
      fields: [
        'id: UUID (PK)',
        'conversation_id: UUID (FK)',
        'direction: MessageDirection (enum)',
        'content: Text',
        'bid_context_id: UUID?',
        'document_context_id: UUID?',
        'relevant_chunks: UUID[]',
        'timestamp: DateTime',
        'created_at: DateTime'
      ]
    }
  },
  
  /**
   * ENUMS
   */
  enums: {
    bidType: [
      'CONCORRENCIA',
      'TOMADA_DE_PRECOS',
      'CONVITE',
      'CONCURSO',
      'LEILAO',
      'PREGAO_ELETRONICO',
      'PREGAO_PRESENCIAL',
      'RDC',
      'OUTROS'
    ],
    
    bidStatus: [
      'ABERTA',
      'EM_ANDAMENTO',
      'SUSPENSA',
      'HOMOLOGADA',
      'REVOGADA',
      'ANULADA',
      'FRACASSADA',
      'DESERTA'
    ],
    
    processingStatus: [
      'PENDING',
      'PROCESSING',
      'PROCESSED',
      'FAILED'
    ],
    
    messageDirection: [
      'INBOUND',
      'OUTBOUND'
    ]
  },
  
  /**
   * FAISS E RAG - ESTRATÉGIAS E PADRÕES
   */
  faissStrategies: {
    indexStructure: 'Um índice FAISS por licitação, englobando todos os documentos e anexos relacionados',
    documentFiltering: 'Filtragem por documento específico implementada em runtime via metadados',
    
    storagePattern: {
      path: './storage/indices/bids/{bidId}.faiss',
      metadataPath: './storage/indices/bids/{bidId}.metadata.json'
    },
    
    vectorIdMapping: {
      description: 'Mapeamento entre posição no índice FAISS e ID do chunk no banco de dados',
      implementation: 'Armazenar vectorId no DocumentChunk e usar para recuperar metadados após busca'
    },
    
    updateStrategies: [
      'Atualização incremental ao adicionar novos documentos/anexos a uma licitação',
      'Reconstrução completa do índice quando necessário',
      'Atualização de metadados sem reindexação quando possível'
    ],
    
    searchStrategies: {
      standard: 'Busca semântica padrão em toda a licitação',
      documentSpecific: 'Busca semântica com filtro para documento específico',
      hybrid: 'Combinação de busca semântica e por palavras-chave para melhores resultados',
      mmr: 'Maximum Marginal Relevance para diversidade de resultados'
    }
  },
  
  /**
   * PERFORMANCE
   */
  performance: {
    rules: [
      'Processar documentos de forma assíncrona',
      'Implementar cache para consultas frequentes',
      'Otimizar carregamento de índices FAISS',
      'Implementar precarregamento de índices frequentemente acessados',
      'Limitar tamanho máximo de contexto para LLM',
      'Implementar paginação para resultados grandes',
      'Usar pools de conexão para banco de dados',
      'Otimizar prompts para reduzir uso de tokens',
      'Armazenar e reutilizar embeddings quando possível'
    ]
  },
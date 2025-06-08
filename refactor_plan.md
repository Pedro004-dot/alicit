# 🔧 PLANO DE REFATORAÇÃO OBRIGATÓRIA

## FASE 1: Separação de Responsabilidades (CRÍTICO)

### 1.1 Estrutura de Diretórios
```
src/
├── controllers/           # Endpoints HTTP apenas
│   ├── bid_controller.py
│   ├── company_controller.py
│   ├── match_controller.py
│   └── analysis_controller.py
├── services/             # Lógica de negócio
│   ├── bid_service.py
│   ├── company_service.py
│   ├── match_service.py
│   └── analysis_service.py
├── repositories/         # Acesso a dados
│   ├── bid_repository.py
│   ├── company_repository.py
│   └── match_repository.py
├── models/              # Entidades do domínio
│   ├── bid.py
│   ├── company.py
│   └── match.py
├── middleware/          # Middlewares
│   ├── auth.py
│   ├── rate_limiter.py
│   └── error_handler.py
└── config/             # Configurações
    ├── database.py
    ├── settings.py
    └── logging.py
```

### 1.2 Exemplo de Controller Refatorado
```python
# controllers/bid_controller.py
from flask import Blueprint, request, jsonify
from services.bid_service import BidService
from middleware.error_handler import handle_errors

bid_bp = Blueprint('bids', __name__)

@bid_bp.route('/', methods=['GET'])
@handle_errors
def get_bids():
    """Endpoint limpo - apenas orquestração"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    filters = request.args.to_dict()
    
    service = BidService()
    result = service.get_bids_paginated(page, limit, filters)
    
    return jsonify({
        'success': True,
        'data': result.data,
        'pagination': result.pagination
    })
```

### 1.3 Service Layer
```python
# services/bid_service.py
from typing import List, Dict, Any
from repositories.bid_repository import BidRepository
from models.bid import Bid

class BidService:
    def __init__(self):
        self.repository = BidRepository()
    
    def get_bids_paginated(self, page: int, limit: int, filters: Dict[str, Any]):
        """Lógica de negócio isolada"""
        # Validações
        if page < 1 or limit < 1 or limit > 100:
            raise ValueError("Parâmetros de paginação inválidos")
        
        # Lógica específica
        bids = self.repository.find_with_filters(filters, page, limit)
        total = self.repository.count_with_filters(filters)
        
        return PaginatedResult(
            data=[bid.to_dict() for bid in bids],
            pagination=Pagination(page, limit, total)
        )
```

## FASE 2: Padrões de Concorrência (CRÍTICO)

### 2.1 Task Queue com Celery
```python
# tasks/analysis_tasks.py
from celery import Celery
from services.analysis_service import AnalysisService

celery_app = Celery('bid_analysis')

@celery_app.task(bind=True)
def process_bid_analysis(self, licitacao_id: str):
    """Task assíncrona segura"""
    try:
        service = AnalysisService()
        result = service.analyze_bid(licitacao_id)
        return {'success': True, 'result': result}
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        raise
```

### 2.2 Connection Pool
```python
# config/database.py
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(
            DATABASE_URL,
            poolclass=pool.QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

## FASE 3: Observabilidade e Monitoramento

### 3.1 Health Checks Robustos
```python
# middleware/health.py
class HealthChecker:
    def check_database(self) -> bool:
        """Verifica conexão com banco"""
        try:
            with DatabaseManager().get_session() as session:
                session.execute("SELECT 1")
            return True
        except:
            return False
    
    def check_celery(self) -> bool:
        """Verifica workers do Celery"""
        # Implementar verificação
        pass
```

### 3.2 Métricas de Performance
```python
# middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')
```

## CRONOGRAMA DE IMPLEMENTAÇÃO

### Semana 1-2: Separação de Camadas
- [ ] Criar estrutura de diretórios
- [ ] Refatorar endpoints principais
- [ ] Implementar services e repositories
- [ ] Testes unitários básicos

### Semana 3-4: Concorrência
- [ ] Implementar Celery para tarefas pesadas
- [ ] Connection pooling
- [ ] Cache Redis
- [ ] Rate limiting

### Semana 5-6: Observabilidade
- [ ] Health checks
- [ ] Métricas Prometheus
- [ ] Logging estruturado
- [ ] Alertas básicos

## CRITÉRIOS DE SUCESSO

### Performance
- [ ] Tempo de resposta < 200ms para endpoints simples
- [ ] Throughput > 1000 req/min
- [ ] Zero vazamentos de conexão

### Código
- [ ] Cobertura de testes > 80%
- [ ] Complexidade ciclomática < 5 por função
- [ ] Zero duplicação de código

### Operacional
- [ ] Health checks funcionais
- [ ] Métricas sendo coletadas
- [ ] Logs estruturados 
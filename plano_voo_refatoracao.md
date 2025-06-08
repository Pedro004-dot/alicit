# 🛫 PLANO DE VOO DETALHADO - REFATORAÇÃO SISTEMA RAG LICITAÇÕES

## 📊 ANÁLISE ATUAL DA ARQUITETURA

### Estado Descoberto:
- **src/api.py**: 1451 linhas - MONÓLITO CRÍTICO
- **src/matching/**: 4 arquivos (1,939 linhas total) - MELHOR ESTRUTURADA 
- **src/analysis/**: 3 arquivos (625 linhas total) - BOA SEPARAÇÃO
- **src/core/**: 2 arquivos (1,400 linhas total) - PROCESSAMENTO PESADO

### ✅ Pontos Positivos Encontrados:
1. **Módulos `matching`, `analysis`, `core` já têm boa separação**
2. **Abstrações existentes**: `BaseTextVectorizer` (POO aplicada)
3. **Estrutura de pacotes** com `__init__.py` bem organizados
4. **Separação de responsabilidades** nos módulos especializados

### ❌ Problemas Críticos:
1. **`api.py` concentra TUDO** - 24 endpoints em arquivo único
2. **Zero abstrações** em `api.py` - código 100% procedural
3. **Threading manual perigoso** - race conditions garantidas
4. **Duplicação massiva** - padrão de conexão/cursor repetido 20+ vezes
5. **Estado global compartilhado** - `process_status` concorrente
6. **Acoplamento direto** - API fala diretamente com banco

---

## 🎯 ESTRATÉGIA GERAL DE REFATORAÇÃO

### Fase 1: **CIRURGIA IMEDIATA** (Semana 1-2)
- Quebrar o monólito `api.py` sem quebrar funcionalidade
- Implementar camadas de abstração mínimas
- Eliminar race conditions críticas

### Fase 2: **ARQUITETURA SÓLIDA** (Semana 3-4)  
- Implementar padrões arquiteturais robustos
- Task queue para concorrência segura
- Connection pooling adequado

### Fase 3: **OBSERVABILIDADE** (Semana 5-6)
- Monitoramento e métricas
- Health checks robustos
- Logging estruturado

---

## 🔬 REFATORAÇÃO MÓDULO POR MÓDULO

### 📁 **MÓDULO 1: Extração de `api.py`**

#### **1.1 Controllers (Endpoints HTTP)**
```python
# controllers/base_controller.py
from abc import ABC
from flask import jsonify
from typing import Dict, Any

class BaseController(ABC):
    """Base para todos os controllers com padrões comuns"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = None, **kwargs) -> Dict:
        response = {'success': True}
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        response.update(kwargs)
        return jsonify(response)
    
    @staticmethod
    def error_response(error: str, status_code: int = 400) -> tuple:
        return jsonify({
            'success': False,
            'error': error
        }), status_code
```

```python
# controllers/bid_controller.py
from flask import Blueprint, request
from services.bid_service import BidService
from middleware.error_handler import handle_errors
from .base_controller import BaseController

bid_bp = Blueprint('bids', __name__)

class BidController(BaseController):
    def __init__(self):
        self.service = BidService()
    
    @handle_errors
    def get_bids(self):
        """GET /api/bids - Listar licitações"""
        filters = {
            'uf': request.args.get('uf'),
            'status': request.args.get('status'),
            'modalidade_id': request.args.get('modalidade_id')
        }
        
        result = self.service.get_bids_paginated(
            page=int(request.args.get('page', 1)),
            limit=min(int(request.args.get('limit', 20)), 100),
            filters={k: v for k, v in filters.items() if v}
        )
        
        return self.success_response(
            data=result.data,
            pagination=result.pagination,
            total=result.total
        )
    
    @handle_errors 
    def get_bid_detail(self, pncp_id: str):
        """GET /api/bids/<pncp_id> - Detalhes da licitação"""
        bid = self.service.get_bid_by_pncp_id(pncp_id)
        
        if not bid:
            return self.error_response('Licitação não encontrada', 404)
            
        return self.success_response(
            data=bid,
            message=f'Licitação {pncp_id} encontrada'
        )

# Registrar rotas
controller = BidController()
bid_bp.route('/', methods=['GET'])(controller.get_bids)
bid_bp.route('/<pncp_id>', methods=['GET'])(controller.get_bid_detail)
```

```python
# controllers/company_controller.py  
from flask import Blueprint, request
from services.company_service import CompanyService
from middleware.error_handler import handle_errors
from .base_controller import BaseController

company_bp = Blueprint('companies', __name__)

class CompanyController(BaseController):
    def __init__(self):
        self.service = CompanyService()
    
    @handle_errors
    def get_companies(self):
        """GET /api/companies - Listar empresas"""
        companies = self.service.get_all_companies()
        return self.success_response(
            data=companies,
            total=len(companies)
        )
    
    @handle_errors
    def create_company(self):
        """POST /api/companies - Criar empresa"""
        data = request.get_json()
        
        # Validação delegada ao service
        company_id = self.service.create_company(data)
        
        return self.success_response(
            data={'id': company_id},
            message='Empresa criada com sucesso'
        ), 201

# Registrar rotas
controller = CompanyController()
company_bp.route('/', methods=['GET'])(controller.get_companies) 
company_bp.route('/', methods=['POST'])(controller.create_company)
```

```python
# controllers/analysis_controller.py
from flask import Blueprint, request
from services.analysis_service import AnalysisService  
from tasks.analysis_tasks import process_bid_analysis_task
from middleware.error_handler import handle_errors
from .base_controller import BaseController

analysis_bp = Blueprint('analysis', __name__)

class AnalysisController(BaseController):
    def __init__(self):
        self.service = AnalysisService()
    
    @handle_errors
    def iniciar_analise(self, licitacao_id: str):
        """POST /api/licitacoes/<id>/iniciar-analise"""
        # Validar se licitação existe
        if not self.service.licitacao_exists(licitacao_id):
            return self.error_response('Licitação não encontrada', 404)
        
        # Enviar para task queue (Celery)
        task = process_bid_analysis_task.delay(licitacao_id)
        
        return self.success_response(
            data={'task_id': task.id},
            message='Análise iniciada em background'
        ), 202
    
    @handle_errors
    def get_checklist(self, licitacao_id: str):
        """GET /api/licitacoes/<id>/checklist"""
        checklist = self.service.get_checklist(licitacao_id)
        
        if checklist is None:
            return self.success_response(
                status='not_found',
                message='Checklist não encontrado'
            )
        
        return self.success_response(
            data=checklist,
            status='ready'
        )

# Registrar rotas
controller = AnalysisController()  
analysis_bp.route('/<licitacao_id>/iniciar-analise', methods=['POST'])(controller.iniciar_analise)
analysis_bp.route('/<licitacao_id>/checklist', methods=['GET'])(controller.get_checklist)
```

#### **1.2 Services (Lógica de Negócio)**
```python
# services/base_service.py
from abc import ABC
from typing import TypeVar, Generic
from repositories.base_repository import BaseRepository

T = TypeVar('T')

class BaseService(ABC, Generic[T]):
    """Service base com operações comuns"""
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
        
    def validate_pagination(self, page: int, limit: int) -> tuple[int, int]:
        """Validação padrão de paginação"""
        page = max(1, page)
        limit = min(max(1, limit), 100)  # Máximo 100 por página
        return page, limit
```

```python
# services/bid_service.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from repositories.bid_repository import BidRepository
from models.bid import Bid
from .base_service import BaseService

@dataclass
class PaginatedResult:
    data: List[Dict]
    pagination: Dict[str, Any]
    total: int

class BidService(BaseService[Bid]):
    def __init__(self):
        super().__init__(BidRepository())
    
    def get_bids_paginated(self, page: int, limit: int, filters: Dict[str, Any]) -> PaginatedResult:
        """Buscar licitações com paginação e filtros"""
        page, limit = self.validate_pagination(page, limit)
        
        # Validar filtros
        valid_filters = self._validate_filters(filters)
        
        # Buscar dados
        bids = self.repository.find_with_filters(valid_filters, page, limit)
        total = self.repository.count_with_filters(valid_filters)
        
        # Calcular paginação
        total_pages = (total + limit - 1) // limit
        
        return PaginatedResult(
            data=[bid.to_dict() for bid in bids],
            pagination={
                'current_page': page,
                'per_page': limit,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            total=total
        )
    
    def get_bid_by_pncp_id(self, pncp_id: str) -> Optional[Dict]:
        """Buscar licitação por PNCP ID"""
        bid = self.repository.find_by_pncp_id(pncp_id)
        return bid.to_dict() if bid else None
    
    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e sanitizar filtros"""
        valid_filters = {}
        
        if filters.get('uf'):
            uf = filters['uf'].upper()
            if len(uf) == 2 and uf.isalpha():
                valid_filters['uf'] = uf
        
        if filters.get('status'):
            # Validar contra enum de status
            valid_filters['status'] = filters['status']
            
        return valid_filters
```

```python
# services/company_service.py
from typing import List, Dict, Any
from repositories.company_repository import CompanyRepository
from models.company import Company
from .base_service import BaseService
from exceptions.validation_error import ValidationError

class CompanyService(BaseService[Company]):
    def __init__(self):
        super().__init__(CompanyRepository())
    
    def get_all_companies(self) -> List[Dict]:
        """Buscar todas as empresas"""
        companies = self.repository.find_all()
        return [company.to_dict() for company in companies]
    
    def create_company(self, data: Dict[str, Any]) -> str:
        """Criar nova empresa"""
        # Validação
        self._validate_company_data(data)
        
        # Criar modelo
        company = Company.from_dict(data)
        
        # Salvar
        return self.repository.save(company)
    
    def _validate_company_data(self, data: Dict[str, Any]) -> None:
        """Validar dados da empresa"""
        required_fields = ['nome_fantasia', 'razao_social', 'descricao_servicos_produtos']
        
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f'Campo obrigatório ausente: {field}')
        
        # Validar CNPJ se fornecido
        cnpj = data.get('cnpj')
        if cnpj and not self._is_valid_cnpj(cnpj):
            raise ValidationError('CNPJ inválido')
    
    def _is_valid_cnpj(self, cnpj: str) -> bool:
        """Validar formato CNPJ"""
        # Implementar validação real de CNPJ
        return len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14
```

#### **1.3 Repositories (Acesso a Dados)**
```python
# repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from contextlib import contextmanager
from config.database import DatabaseManager

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Repository base com operações CRUD padrão"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    @contextmanager
    def get_session(self):
        """Context manager para sessões de banco"""
        with self.db_manager.get_session() as session:
            yield session
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        pass
    
    @abstractmethod
    def save(self, entity: T) -> str:
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        pass
```

```python
# repositories/bid_repository.py
from typing import List, Optional, Dict, Any
from psycopg2.extras import RealDictCursor
from models.bid import Bid
from .base_repository import BaseRepository

class BidRepository(BaseRepository[Bid]):
    
    def find_by_id(self, id: str) -> Optional[Bid]:
        """Buscar licitação por ID"""
        with self.get_session() as session:
            cursor = session.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM licitacoes WHERE id = %s", (id,))
            row = cursor.fetchone()
            return Bid.from_dict(dict(row)) if row else None
    
    def find_by_pncp_id(self, pncp_id: str) -> Optional[Bid]:
        """Buscar licitação por PNCP ID"""
        with self.get_session() as session:
            cursor = session.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM licitacoes WHERE pncp_id = %s", (pncp_id,))
            row = cursor.fetchone()
            return Bid.from_dict(dict(row)) if row else None
    
    def find_with_filters(self, filters: Dict[str, Any], page: int, limit: int) -> List[Bid]:
        """Buscar licitações com filtros e paginação"""
        offset = (page - 1) * limit
        
        where_conditions = []
        params = []
        
        for key, value in filters.items():
            where_conditions.append(f"{key} = %s")
            params.append(value)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM licitacoes 
            {where_clause}
            ORDER BY data_publicacao DESC, created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        with self.get_session() as session:
            cursor = session.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Bid.from_dict(dict(row)) for row in rows]
    
    def count_with_filters(self, filters: Dict[str, Any]) -> int:
        """Contar licitações com filtros"""
        where_conditions = []
        params = []
        
        for key, value in filters.items():
            where_conditions.append(f"{key} = %s")
            params.append(value)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"SELECT COUNT(*) FROM licitacoes {where_clause}"
        
        with self.get_session() as session:
            cursor = session.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    
    def find_all(self) -> List[Bid]:
        """Buscar todas as licitações"""
        with self.get_session() as session:
            cursor = session.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM licitacoes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [Bid.from_dict(dict(row)) for row in rows]
    
    def save(self, bid: Bid) -> str:
        """Salvar licitação"""
        # Implementar INSERT/UPDATE
        pass
    
    def delete(self, id: str) -> bool:
        """Deletar licitação"""
        # Implementar DELETE
        pass
```

#### **1.4 Models (Entidades do Domínio)**
```python
# models/base_model.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
import uuid

class BaseModel(ABC):
    """Model base com funcionalidades comuns"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
    
    @classmethod
    @abstractmethod  
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        pass
```

```python
# models/bid.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
from .base_model import BaseModel

@dataclass
class Bid(BaseModel):
    """Modelo para licitação"""
    pncp_id: str
    objeto_compra: str
    valor_total_estimado: Optional[float] = None
    uf: Optional[str] = None
    status: Optional[str] = None
    data_publicacao: Optional[date] = None
    modalidade_compra: str = 'Pregão Eletrônico'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'pncp_id': self.pncp_id,
            'objeto_compra': self.objeto_compra,
            'valor_total_estimado': float(self.valor_total_estimado) if self.valor_total_estimado else 0,
            'uf': self.uf or '',
            'status': self.status or '',
            'data_publicacao': self.data_publicacao.isoformat() if self.data_publicacao else '',
            'modalidade_compra': self.modalidade_compra,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bid':
        bid = cls(
            pncp_id=data['pncp_id'],
            objeto_compra=data['objeto_compra']
        )
        bid.id = data.get('id', bid.id)
        bid.valor_total_estimado = data.get('valor_total_estimado')
        bid.uf = data.get('uf')
        bid.status = data.get('status')
        
        # Parse de data
        if data.get('data_publicacao'):
            if isinstance(data['data_publicacao'], str):
                bid.data_publicacao = datetime.fromisoformat(data['data_publicacao']).date()
            else:
                bid.data_publicacao = data['data_publicacao']
        
        return bid
```

### 📁 **MÓDULO 2: Concorrência Segura**

#### **2.1 Task Queue com Celery**
```python
# tasks/celery_app.py
from celery import Celery
import os

# Configuração do Celery
celery_app = Celery(
    'bid_analysis',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'tasks.analysis_tasks',
        'tasks.matching_tasks'
    ]
)

# Configurações
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_routes={
        'tasks.analysis_tasks.*': {'queue': 'analysis'},
        'tasks.matching_tasks.*': {'queue': 'matching'}
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True
)
```

```python
# tasks/analysis_tasks.py
from celery import Task
from tasks.celery_app import celery_app
from services.analysis_service import AnalysisService
from config.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    """Task base com conexão de banco"""
    _db_manager = None
    
    @property
    def db_manager(self):
        if self._db_manager is None:
            self._db_manager = DatabaseManager()
        return self._db_manager

@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_bid_analysis_task(self, licitacao_id: str):
    """Task para análise de licitação"""
    try:
        logger.info(f"Iniciando análise da licitação: {licitacao_id}")
        
        # Usar connection manager para garantir cleanup
        with self.db_manager.get_session() as session:
            service = AnalysisService(session)
            result = service.analyze_bid_sync(licitacao_id)
        
        logger.info(f"Análise concluída para: {licitacao_id}")
        return {
            'success': True,
            'result': result,
            'licitacao_id': licitacao_id
        }
        
    except Exception as exc:
        logger.error(f"Erro na análise da licitação {licitacao_id}: {exc}")
        
        # Retry com exponential backoff
        countdown = 2 ** self.request.retries * 60  # 1min, 2min, 4min
        
        raise self.retry(
            countdown=countdown,
            exc=exc,
            max_retries=3
        )

@celery_app.task(bind=True, base=DatabaseTask)
def search_new_bids_task(self, config: dict):
    """Task para busca de novas licitações"""
    try:
        from services.matching_service import MatchingService
        
        with self.db_manager.get_session() as session:
            service = MatchingService(session)
            result = service.search_new_bids(config)
        
        return {
            'success': True,
            'result': result,
            'config_used': config
        }
        
    except Exception as exc:
        logger.error(f"Erro na busca de licitações: {exc}")
        raise
```

#### **2.2 Database Connection Manager**
```python
# config/database.py
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de conexões com pool"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._create_pool()
    
    def _create_pool(self):
        """Criar pool de conexões"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'licitacoes'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                port=os.getenv('DB_PORT', 5432)
            )
            logger.info("✅ Pool de conexões criado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar pool de conexões: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões"""
        connection = None
        try:
            connection = self._pool.getconn()
            connection.autocommit = False
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Erro na conexão: {e}")
            raise
        finally:
            if connection:
                self._pool.putconn(connection)
    
    @contextmanager  
    def get_session(self):
        """Context manager compatível com services"""
        with self.get_connection() as conn:
            yield conn
    
    def close_all_connections(self):
        """Fechar todas as conexões"""
        if self._pool:
            self._pool.closeall()
            logger.info("Todas as conexões fechadas")
```

### 📁 **MÓDULO 3: Middleware e Utilidades**

#### **3.1 Error Handler**
```python
# middleware/error_handler.py
from functools import wraps
from flask import jsonify
import logging
from exceptions.base_exception import BaseAppException
from exceptions.validation_error import ValidationError

logger = logging.getLogger(__name__)

def handle_errors(f):
    """Decorator para tratamento global de erros"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Erro de validação: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'type': 'validation_error'
            }), 400
        except BaseAppException as e:
            logger.error(f"Erro da aplicação: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'type': e.__class__.__name__
            }), e.status_code
        except Exception as e:
            logger.error(f"Erro interno: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'type': 'internal_error'
            }), 500
    
    return decorated_function
```

#### **3.2 Rate Limiter**
```python
# middleware/rate_limiter.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import os

# Configurar Redis para rate limiting
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=1
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1",
    default_limits=["1000 per hour", "100 per minute"]
)

# Decorators específicos
def rate_limit_heavy():
    """Para operações pesadas (análise, busca)"""
    return limiter.limit("10 per minute")

def rate_limit_standard():
    """Para operações padrão"""
    return limiter.limit("100 per minute")
```

---

## 🔄 **MIGRAÇÃO GRADUAL**

### **Semana 1: Refatoração Crítica**

#### **Dia 1-2: Estrutura Base**
```bash
# Criar nova estrutura
mkdir -p src/{controllers,services,repositories,models,middleware,config,tasks,exceptions}

# Implementar bases
touch src/controllers/base_controller.py
touch src/services/base_service.py  
touch src/repositories/base_repository.py
touch src/models/base_model.py
```

#### **Dia 3-4: Migração de Endpoints**
1. **BidController** - 6 endpoints de licitações
2. **CompanyController** - 4 endpoints de empresas  
3. **MatchController** - 2 endpoints de matches
4. **AnalysisController** - 3 endpoints de análise

#### **Dia 5-7: Services e Repositories**
1. Implementar services com validações
2. Criar repositories com connection pooling
3. Testar migração gradual

### **Semana 2: Concorrência**

#### **Dia 1-3: Celery Setup**
```bash
# Instalar dependências
pip install celery[redis] redis

# Configurar workers
celery -A tasks.celery_app worker --loglevel=info --queues=analysis,matching
celery -A tasks.celery_app flower  # Monitor web
```

#### **Dia 4-7: Migração de Threading**
1. Substituir `threading.Thread` por `@celery.task`
2. Implementar retry policies
3. Monitoramento de tasks

### **Semana 3: Testing e Observabilidade**

#### **Testes Unitários**
```python
# tests/test_bid_service.py
import pytest
from services.bid_service import BidService
from repositories.bid_repository import BidRepository
from unittest.mock import Mock

class TestBidService:
    
    def test_get_bids_paginated_valid_params(self):
        # Mock repository
        mock_repo = Mock(spec=BidRepository)
        mock_repo.find_with_filters.return_value = []
        mock_repo.count_with_filters.return_value = 0
        
        service = BidService()
        service.repository = mock_repo
        
        result = service.get_bids_paginated(1, 20, {})
        
        assert result.data == []
        assert result.total == 0
        assert result.pagination['current_page'] == 1
```

#### **Health Checks**
```python
# middleware/health.py
from flask import Blueprint, jsonify
from config.database import DatabaseManager
from tasks.celery_app import celery_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check completo"""
    checks = {
        'database': _check_database(),
        'celery': _check_celery(),
        'redis': _check_redis()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code

def _check_database() -> bool:
    try:
        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except:
        return False
```

---

## 📊 **MÉTRICAS DE SUCESSO**

### **Antes vs Depois**

| Métrica | ANTES | DEPOIS |
|---------|-------|--------|
| **Linhas por arquivo** | 1,451 | < 200 |
| **Complexity Score** | >10 | < 5 |
| **Cobertura de Testes** | 0% | >80% |
| **Tempo de Response** | >1s | <200ms |
| **Concurrent Users** | ~10 | >100 |
| **Memory Leaks** | Sim | Zero |
| **Race Conditions** | Múltiplas | Zero |

### **Validação Técnica**
```python
# scripts/validate_refactor.py
def validate_architecture():
    """Script para validar arquitetura pós-refatoração"""
    
    # 1. Nenhum arquivo > 300 linhas
    # 2. Todos os endpoints têm @handle_errors
    # 3. Nenhum threading.Thread manual
    # 4. Connection pooling ativo
    # 5. Tasks funcionais no Celery
    
    return all_checks_passed
```

---

## 🎯 **CRONOGRAMA EXECUTIVO**

### **Sprint 1 (Semana 1-2): CIRURGIA**
- ✅ Quebrar monólito `api.py`
- ✅ Implementar camadas Controller/Service/Repository
- ✅ Connection pooling
- ✅ Task queue básico

### **Sprint 2 (Semana 3-4): ROBUSTEZ**  
- ✅ Testes unitários (>80% cobertura)
- ✅ Error handling robusto
- ✅ Rate limiting
- ✅ Health checks

### **Sprint 3 (Semana 5-6): OBSERVABILIDADE**
- ✅ Métricas Prometheus
- ✅ Logging estruturado  
- ✅ Dashboard monitoring
- ✅ Alertas automáticos

**ENTREGA**: Sistema escalável, testável e observável.
**CAPACIDADE**: 1000+ usuários simultâneos.
**MANUTENIBILIDADE**: Features independentes e deploying seguro. 
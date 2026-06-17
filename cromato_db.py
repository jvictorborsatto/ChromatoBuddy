import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class KnowledgeDatabase:
    def __init__(self, db_path="knowledge_base.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de chunks com estrutura completa
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                sinonimos TEXT,
                conteudo TEXT NOT NULL,
                tipo TEXT,
                tags TEXT,
                referencias TEXT,
                versao TEXT,
                autores TEXT,
                data_criacao TEXT,
                data_atualizacao TEXT,
                aprovado INTEGER DEFAULT 0,
                aprovado_por TEXT,
                observacoes TEXT,
                fonte TEXT
            )
        ''')
        
        # Tabela de versões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS versoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versao TEXT UNIQUE,
                data_criacao TEXT,
                descricao TEXT,
                usuario TEXT,
                chunks_adicionados INTEGER
            )
        ''')
        
        # Tabela de tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                tag TEXT PRIMARY KEY,
                contador INTEGER DEFAULT 0,
                descricao TEXT,
                exemplos TEXT
            )
        ''')
        
        # Tabela de tipos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tipos (
                tipo TEXT PRIMARY KEY,
                descricao TEXT,
                campos_obrigatorios TEXT
            )
        ''')
        
        # Insere tipos padrão
        tipos_padrao = [
            ('fundamento', 'Conceito fundamental da cromatografia', 'titulo,conteudo'),
            ('problema', 'Problema comum em cromatografia', 'titulo,conteudo'),
            ('solucao', 'Solução para problemas cromatográficos', 'titulo,conteudo'),
            ('conceito', 'Conceito técnico ou teórico', 'titulo,conteudo'),
            ('aplicacao', 'Aplicação prática', 'titulo,conteudo'),
            ('instrumentacao', 'Instrumentação e equipamentos', 'titulo,conteudo'),
            ('metodo', 'Método analítico', 'titulo,conteudo'),
            ('referencia', 'Referência bibliográfica', 'titulo,conteudo')
        ]
        
        for tipo, desc, campos in tipos_padrao:
            cursor.execute('INSERT OR IGNORE INTO tipos (tipo, descricao, campos_obrigatorios) VALUES (?, ?, ?)',
                          (tipo, desc, campos))
        
        conn.commit()
        conn.close()
    
    def adicionar_chunk(self, chunk: Dict) -> str:
        """Adiciona ou atualiza um chunk"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        chunk_id = chunk.get('id', f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        tags_json = json.dumps(chunk.get('tags', []))
        refs_json = json.dumps(chunk.get('referencias', []))
        autores_json = json.dumps(chunk.get('autores', []))
        
        cursor.execute('''
            INSERT OR REPLACE INTO chunks 
            (id, titulo, sinonimos, conteudo, tipo, tags, referencias, versao, autores, 
             data_criacao, data_atualizacao, aprovado, aprovado_por, observacoes, fonte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            chunk_id,
            chunk.get('titulo', ''),
            chunk.get('sinonimos', ''),
            chunk.get('conteudo', ''),
            chunk.get('tipo', ''),
            tags_json,
            refs_json,
            chunk.get('versao', '1.0'),
            autores_json,
            chunk.get('data_criacao', datetime.now().isoformat()),
            datetime.now().isoformat(),
            chunk.get('aprovado', 0),
            chunk.get('aprovado_por', ''),
            chunk.get('observacoes', ''),
            chunk.get('fonte', '')
        ))
        
        # Atualiza tags
        for tag in chunk.get('tags', []):
            cursor.execute('INSERT OR IGNORE INTO tags (tag) VALUES (?)', (tag,))
            cursor.execute('UPDATE tags SET contador = contador + 1 WHERE tag = ?', (tag,))
        
        conn.commit()
        conn.close()
        return chunk_id
    
    def get_chunks(self, filtro: Dict = None) -> List[Dict]:
        """Busca chunks com filtros"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verifica colunas existentes
        cursor.execute("PRAGMA table_info(chunks)")
        colunas = [col['name'] for col in cursor.fetchall()]
        
        query = "SELECT * FROM chunks"
        params = []
        
        if filtro:
            conditions = []
            if 'tag' in filtro:
                conditions.append("tags LIKE ?")
                params.append(f'%"{filtro["tag"]}"%')
            if 'tipo' in filtro and 'tipo' in colunas:
                conditions.append("tipo = ?")
                params.append(filtro["tipo"])
            if 'busca' in filtro:
                if 'titulo' in colunas:
                    conditions.append("(titulo LIKE ? OR conteudo LIKE ? OR sinonimos LIKE ?)")
                    params.extend([f'%{filtro["busca"]}%'] * 3)
                else:
                    conditions.append("conteudo LIKE ?")
                    params.append(f'%{filtro["busca"]}%')
            if 'aprovado' in filtro and 'aprovado' in colunas:
                conditions.append("aprovado = ?")
                params.append(filtro["aprovado"])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY data_criacao DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        chunks = []
        for row in results:
            chunk = dict(row)
            # Converte JSON com segurança
            if 'tags' in chunk and chunk['tags']:
                try:
                    chunk['tags'] = json.loads(chunk['tags'])
                except:
                    chunk['tags'] = []
            else:
                chunk['tags'] = []
            
            if 'referencias' in chunk and chunk['referencias']:
                try:
                    chunk['referencias'] = json.loads(chunk['referencias'])
                except:
                    chunk['referencias'] = []
            else:
                chunk['referencias'] = []
            
            if 'autores' in chunk and chunk['autores']:
                try:
                    chunk['autores'] = json.loads(chunk['autores'])
                except:
                    chunk['autores'] = []
            else:
                chunk['autores'] = []
            
            chunks.append(chunk)
        
        return chunks
    
    def get_tipos(self) -> List[Dict]:
        """Retorna os tipos disponíveis"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tipos ORDER BY tipo")
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def get_tag_cloud(self) -> Dict[str, int]:
        """Retorna nuvem de tags"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tag, contador FROM tags ORDER BY contador DESC")
        results = cursor.fetchall()
        conn.close()
        return {tag: contador for tag, contador in results}
    
    def criar_versao(self, descricao: str, usuario: str = "sistema"):
        """Cria uma nova versão"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT versao FROM versoes ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        if last:
            major, minor = last[0].split('.')
            nova_versao = f"{major}.{int(minor) + 1}"
        else:
            nova_versao = "1.0"
        
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO versoes (versao, data_criacao, descricao, usuario, chunks_adicionados)
            VALUES (?, ?, ?, ?, ?)
        ''', (nova_versao, datetime.now().isoformat(), descricao, usuario, total_chunks))
        
        conn.commit()
        conn.close()
        return nova_versao
    
    def exportar_json(self, caminho="knowledge-base.json", apenas_aprovados=True):
        """Exporta chunks para JSON no formato do Cromato Buddy"""
        filtro = {'aprovado': 1} if apenas_aprovados else {}
        chunks = self.get_chunks(filtro)
        
        # Busca versão atual
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT versao FROM versoes ORDER BY id DESC LIMIT 1")
        versao = cursor.fetchone()
        conn.close()
        
        dados = {
            "versao": versao[0] if versao else "1.0",
            "data_geracao": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "id": c['id'],
                    "titulo": c['titulo'],
                    "conteudo": c['conteudo'],
                    "sinonimos": c['sinonimos'],
                    "tipo": c['tipo'],
                    "tags": c['tags'],
                    "referencias": c['referencias'],
                    "autores": c['autores'],
                    "versao": c['versao'],
                    "fonte": c['fonte']
                }
                for c in chunks
            ]
        }
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return len(chunks)
    
    def validar_chunk(self, chunk: Dict) -> Dict:
        """Valida um chunk e retorna erros se houver"""
        erros = []
        avisos = []
        
        # Campos obrigatórios
        if not chunk.get('titulo', '').strip():
            erros.append("Título é obrigatório")
        if not chunk.get('conteudo', '').strip():
            erros.append("Conteúdo é obrigatório")
        if not chunk.get('tipo', '').strip():
            erros.append("Tipo é obrigatório")
        
        # Verifica se o tipo existe
        if chunk.get('tipo'):
            tipos = self.get_tipos()
            tipos_list = [t['tipo'] for t in tipos]
            if chunk['tipo'] not in tipos_list:
                avisos.append(f"Tipo '{chunk['tipo']}' não está na lista padrão")
        
        # Verifica tags
        if not chunk.get('tags', []):
            avisos.append("Nenhuma tag definida. Adicione pelo menos uma tag.")
        
        # Verifica referências
        if chunk.get('referencias', []):
            for ref in chunk['referencias']:
                if len(ref) < 10:
                    avisos.append(f"Referência muito curta: '{ref}'")
        
        # Verifica autores
        if not chunk.get('autores', []):
            avisos.append("Nenhum autor definido. Adicione pelo menos um autor.")
        
        return {
            'valido': len(erros) == 0,
            'erros': erros,
            'avisos': avisos
        }
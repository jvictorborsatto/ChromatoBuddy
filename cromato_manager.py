import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import json
from datetime import datetime
import os
import sys
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cromato_db import KnowledgeDatabase

class CromatoManagerV2:
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Cromato Buddy Manager v2.0 - Formulário Estruturado")
        self.root.geometry("1300x750")
        
        self.db = KnowledgeDatabase()
        self.chunk_atual = None
        self.guia_aberto = None
        
        self.setup_ui()
        self.carregar_chunks()
        self.carregar_tags()
        self.carregar_tipos()
    
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="📥 Importar DOCX", command=self.importar_docx)
        file_menu.add_command(label="📤 Exportar JSON", command=self.exportar_json)
        file_menu.add_command(label="📋 Guia de Tags", command=self.mostrar_guia_tags)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Frame principal com PanedWindow
        main_panel = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== PAINEL ESQUERDO - LISTA =====
        left_frame = tk.Frame(main_panel)
        main_panel.add(left_frame, width=350)
        
        # Filtros
        filter_frame = tk.LabelFrame(left_frame, text="🔍 Filtros", padx=5, pady=5)
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, sticky=tk.W)
        self.search_entry = tk.Entry(filter_frame, width=25)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.carregar_chunks())
        
        tk.Label(filter_frame, text="Tipo:").grid(row=1, column=0, sticky=tk.W)
        self.tipo_combo = ttk.Combobox(filter_frame, width=23)
        self.tipo_combo.grid(row=1, column=1, padx=5, pady=2)
        self.tipo_combo.bind('<<ComboboxSelected>>', lambda e: self.carregar_chunks())
        
        tk.Label(filter_frame, text="Tag:").grid(row=2, column=0, sticky=tk.W)
        self.tag_combo = ttk.Combobox(filter_frame, width=23)
        self.tag_combo.grid(row=2, column=1, padx=5, pady=2)
        self.tag_combo.bind('<<ComboboxSelected>>', lambda e: self.carregar_chunks())
        
        # Lista de chunks
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chunk_list = tk.Listbox(list_frame, font=("Arial", 9))
        self.chunk_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chunk_list.bind('<<ListboxSelect>>', self.on_chunk_selected)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chunk_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.chunk_list.yview)
        
        # Botões rápidos
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="➕ Novo Chunk", command=self.novo_chunk).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Excluir", command=self.excluir_chunk, bg="#ff6b6b").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📋 Duplicar", command=self.duplicar_chunk).pack(side=tk.LEFT, padx=2)
        
        # ===== PAINEL DIREITO - FORMULÁRIO =====
        right_frame = tk.Frame(main_panel)
        main_panel.add(right_frame, width=600)
        
        # Barra de status do chunk
        status_frame = tk.Frame(right_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.id_label = tk.Label(status_frame, text="ID: ---", font=("Arial", 9, "bold"))
        self.id_label.pack(side=tk.LEFT, padx=5)
        
        self.versao_label = tk.Label(status_frame, text="Versão: ---")
        self.versao_label.pack(side=tk.LEFT, padx=15)
        
        self.aprovado_var = tk.IntVar(value=0)
        tk.Checkbutton(status_frame, text="✅ Aprovado", variable=self.aprovado_var, 
                      command=self.salvar_chunk).pack(side=tk.LEFT, padx=10)
        
        self.fonte_label = tk.Label(status_frame, text="Fonte: ---")
        self.fonte_label.pack(side=tk.LEFT, padx=15)
        
        # Notebook para organização
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ===== ABA 1: DADOS PRINCIPAIS =====
        tab1 = tk.Frame(notebook)
        notebook.add(tab1, text="📝 Dados")
        
        # Título
        tk.Label(tab1, text="📌 Título:*", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.titulo_entry = tk.Entry(tab1, width=60, font=("Arial", 10))
        self.titulo_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.titulo_entry.bind('<KeyRelease>', lambda e: self.salvar_chunk())
        
        # Sinônimos
        tk.Label(tab1, text="🔗 Sinônimos:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.sinonimos_entry = tk.Entry(tab1, width=60)
        self.sinonimos_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.sinonimos_entry.bind('<KeyRelease>', lambda e: self.salvar_chunk())
        
        # Tipo
        tk.Label(tab1, text="📂 Tipo:*").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.tipo_combo_form = ttk.Combobox(tab1, width=30)
        self.tipo_combo_form.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.tipo_combo_form.bind('<<ComboboxSelected>>', lambda e: self.salvar_chunk())
        
        # Tags
        tk.Label(tab1, text="🏷️ Tags (separadas por vírgula):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.tags_entry = tk.Entry(tab1, width=60)
        self.tags_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.tags_entry.bind('<KeyRelease>', lambda e: self.salvar_chunk())
        
        # Conteúdo
        tk.Label(tab1, text="📄 Conteúdo:*", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.conteudo_text = scrolledtext.ScrolledText(tab1, height=12, wrap=tk.WORD, font=("Arial", 10))
        self.conteudo_text.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.conteudo_text.bind('<KeyRelease>', lambda e: self.salvar_chunk())
        
        # Observações
        tk.Label(tab1, text="📌 Observações:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.obs_text = scrolledtext.ScrolledText(tab1, height=3, wrap=tk.WORD)
        self.obs_text.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.obs_text.bind('<KeyRelease>', lambda e: self.salvar_chunk())
        
        tab1.grid_rowconfigure(4, weight=1)
        tab1.grid_columnconfigure(1, weight=1)
        
        # ===== ABA 2: AUTORES E REFERÊNCIAS =====
        tab2 = tk.Frame(notebook)
        notebook.add(tab2, text="✍️ Autores e Referências")

        tab2.grid_rowconfigure(2, weight=3)
        tab2.grid_rowconfigure(0, weight=0)
        tab2.grid_rowconfigure(1, weight=0)
        tab2.grid_rowconfigure(3, weight=0)
        tab2.grid_columnconfigure(0, weight=0)
        tab2.grid_columnconfigure(1, weight=1)

        tk.Label(tab2, text="✍️ Autores do Chunk (quem escreveu, separados por vírgula):", 
                font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.autores_entry = tk.Entry(tab2, width=60, font=("Arial", 10))
        self.autores_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.autores_entry.bind('<KeyRelease>', lambda e: self.salvar_chunk())

        ttk.Separator(tab2, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        tk.Label(tab2, text="📖 Referências Citadas (ABNT, uma por linha):", 
                font=("Arial", 9, "bold")).grid(row=2, column=0, columnspan=1, sticky=tk.W, padx=5, pady=5)

        ref_frame = tk.Frame(tab2, bd=2, relief=tk.SUNKEN, bg="white")
        ref_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        ref_frame.grid_rowconfigure(0, weight=1)
        ref_frame.grid_columnconfigure(0, weight=1)

        self.refs_text = scrolledtext.ScrolledText(
            ref_frame, 
            height=15,
            wrap=tk.WORD,
            font=("Arial", 10),
            bd=0
        )
        self.refs_text.grid(row=0, column=0, sticky="nsew")
        self.refs_text.bind('<KeyRelease>', lambda e: self.salvar_chunk())

        tk.Label(tab2, 
                text="📌 Autores = quem escreveu este chunk | Referências = fontes citadas no conteúdo",
                font=("Arial", 8, "italic"), fg="#666").grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # ===== ABA 3: VALIDAÇÃO =====
        tab3 = tk.Frame(notebook)
        notebook.add(tab3, text="✅ Validação")
        
        self.validacao_text = scrolledtext.ScrolledText(tab3, height=15, wrap=tk.WORD, font=("Arial", 10))
        self.validacao_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.validacao_text.config(state=tk.DISABLED)
        
        tk.Button(tab3, text="🔍 Validar Chunk", command=self.validar_chunk_atual, bg="#4ecdc4").pack(pady=10)
        
        # ===== BOTÕES =====
        btn_frame2 = tk.Frame(right_frame)
        btn_frame2.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame2, text="💾 Salvar Chunk", command=self.salvar_chunk, bg="#4ecdc4", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame2, text="🔍 Validar", command=self.validar_chunk_atual).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame2, text="📋 Gerar JSON", command=self.exportar_json).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        total = len(self.db.get_chunks())
        self.status_bar.config(text=f"✅ Pronto! {total} chunks no banco de dados.")
    
    def carregar_chunks(self):
        """Carrega chunks na lista"""
        self.chunk_list.delete(0, tk.END)
        
        filtro = {}
        busca = self.search_entry.get().strip()
        if busca:
            filtro['busca'] = busca
        
        tipo = self.tipo_combo.get()
        if tipo and tipo != "Todos":
            filtro['tipo'] = tipo
        
        tag = self.tag_combo.get()
        if tag and tag != "Todas":
            filtro['tag'] = tag
        
        chunks = self.db.get_chunks(filtro)
        
        if not hasattr(self.chunk_list, 'item_data'):
            self.chunk_list.item_data = {}
        
        for idx, chunk in enumerate(chunks):
            label = f"{chunk['titulo'][:30]}"
            if chunk.get('tipo'):
                label += f" [{chunk['tipo']}]"
            if chunk.get('aprovado', 0):
                label = "✅ " + label
            else:
                label = "⏳ " + label
            self.chunk_list.insert(tk.END, label)
            self.chunk_list.item_data[idx] = chunk['id']
    
    def carregar_tags(self):
        """Carrega tags nos combobox"""
        tags = self.db.get_tag_cloud()
        self.tag_combo['values'] = ["Todas"] + list(tags.keys())
        if not self.tag_combo.get():
            self.tag_combo.set("Todas")
    
    def carregar_tipos(self):
        """Carrega tipos nos combobox"""
        tipos = self.db.get_tipos()
        tipos_list = [t['tipo'] for t in tipos]
        self.tipo_combo['values'] = ["Todos"] + tipos_list
        self.tipo_combo_form['values'] = tipos_list
        if not self.tipo_combo.get():
            self.tipo_combo.set("Todos")
    
    def on_chunk_selected(self, event):
        """Carrega chunk selecionado"""
        selection = self.chunk_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        chunk_id = getattr(self.chunk_list, 'item_data', {}).get(index)
        
        if not chunk_id:
            return
        
        chunks = self.db.get_chunks()
        chunk = next((c for c in chunks if c['id'] == chunk_id), None)
        if not chunk:
            return
        
        self.chunk_atual = chunk
        
        self.id_label.config(text=f"ID: {chunk['id']}")
        self.versao_label.config(text=f"Versão: {chunk.get('versao', '1.0')}")
        self.fonte_label.config(text=f"Fonte: {chunk.get('fonte', '---')}")
        
        self.titulo_entry.delete(0, tk.END)
        self.titulo_entry.insert(0, chunk.get('titulo', ''))
        
        self.sinonimos_entry.delete(0, tk.END)
        self.sinonimos_entry.insert(0, chunk.get('sinonimos', ''))
        
        if chunk.get('tipo'):
            self.tipo_combo_form.set(chunk['tipo'])
        
        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, ', '.join(chunk.get('tags', [])))
        
        self.conteudo_text.delete(1.0, tk.END)
        self.conteudo_text.insert(tk.END, chunk.get('conteudo', ''))
        
        self.autores_entry.delete(0, tk.END)
        self.autores_entry.insert(0, ', '.join(chunk.get('autores', [])))
        
        self.refs_text.delete(1.0, tk.END)
        self.refs_text.insert(tk.END, '\n'.join(chunk.get('referencias', [])))
        
        self.aprovado_var.set(chunk.get('aprovado', 0))
        
        self.obs_text.delete(1.0, tk.END)
        self.obs_text.insert(tk.END, chunk.get('observacoes', ''))
    
    def novo_chunk(self):
        """Cria um novo chunk em branco"""
        self.chunk_atual = {
            'id': f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'titulo': '',
            'sinonimos': '',
            'conteudo': '',
            'tipo': '',
            'tags': [],
            'referencias': [],
            'autores': [],
            'versao': '1.0',
            'aprovado': 0,
            'aprovado_por': '',
            'observacoes': '',
            'fonte': ''
        }
        
        self.id_label.config(text="ID: NOVO")
        self.versao_label.config(text="Versão: 1.0")
        self.fonte_label.config(text="Fonte: ---")
        self.titulo_entry.delete(0, tk.END)
        self.sinonimos_entry.delete(0, tk.END)
        self.tipo_combo_form.set('')
        self.tags_entry.delete(0, tk.END)
        self.conteudo_text.delete(1.0, tk.END)
        self.autores_entry.delete(0, tk.END)
        self.refs_text.delete(1.0, tk.END)
        self.aprovado_var.set(0)
        self.obs_text.delete(1.0, tk.END)
        
        self.status_bar.config(text="📝 Novo chunk criado. Preencha os campos e salve.")
    
    def salvar_chunk(self, event=None):
        """Salva o chunk atual"""
        if not self.chunk_atual:
            return
        
        self.chunk_atual['titulo'] = self.titulo_entry.get().strip()
        self.chunk_atual['sinonimos'] = self.sinonimos_entry.get().strip()
        self.chunk_atual['tipo'] = self.tipo_combo_form.get().strip()
        self.chunk_atual['tags'] = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]
        self.chunk_atual['conteudo'] = self.conteudo_text.get(1.0, tk.END).strip()
        self.chunk_atual['autores'] = [a.strip() for a in self.autores_entry.get().split(',') if a.strip()]
        self.chunk_atual['referencias'] = [r.strip() for r in self.refs_text.get(1.0, tk.END).split('\n') if r.strip()]
        self.chunk_atual['aprovado'] = self.aprovado_var.get()
        self.chunk_atual['observacoes'] = self.obs_text.get(1.0, tk.END).strip()
        
        if not self.chunk_atual['titulo'] or not self.chunk_atual['conteudo']:
            self.status_bar.config(text="⚠️ Título e Conteúdo são obrigatórios!")
            return
        
        validacao = self.db.validar_chunk(self.chunk_atual)
        if not validacao['valido']:
            msg = "❌ Erros encontrados:\n" + "\n".join(validacao['erros'])
            if validacao['avisos']:
                msg += "\n\n⚠️ Avisos:\n" + "\n".join(validacao['avisos'])
            if not messagebox.askyesno("Validação", msg + "\n\nDeseja salvar mesmo assim?"):
                return
        
        self.db.adicionar_chunk(self.chunk_atual)
        self.carregar_chunks()
        self.carregar_tags()
        self.status_bar.config(text=f"✅ Chunk '{self.chunk_atual['titulo']}' salvo em {datetime.now().strftime('%H:%M:%S')}")
        
        self.mostrar_validacao(validacao)
    
    def validar_chunk_atual(self):
        """Valida o chunk atual e mostra resultados"""
        if not self.chunk_atual:
            return
        
        chunk = self.chunk_atual.copy()
        chunk['titulo'] = self.titulo_entry.get().strip()
        chunk['conteudo'] = self.conteudo_text.get(1.0, tk.END).strip()
        chunk['tipo'] = self.tipo_combo_form.get().strip()
        chunk['tags'] = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]
        chunk['referencias'] = [r.strip() for r in self.refs_text.get(1.0, tk.END).split('\n') if r.strip()]
        chunk['autores'] = [a.strip() for a in self.autores_entry.get().split(',') if a.strip()]
        
        validacao = self.db.validar_chunk(chunk)
        self.mostrar_validacao(validacao)
    
    def mostrar_validacao(self, validacao):
        """Mostra validação na aba 3"""
        self.validacao_text.config(state=tk.NORMAL)
        self.validacao_text.delete(1.0, tk.END)
        
        if validacao['valido']:
            self.validacao_text.insert(tk.END, "✅ CHUNK VÁLIDO!\n\n", "valid")
        else:
            self.validacao_text.insert(tk.END, "❌ CHUNK INVÁLIDO!\n\n", "invalid")
        
        if validacao['erros']:
            self.validacao_text.insert(tk.END, "🔴 ERROS:\n", "error")
            for erro in validacao['erros']:
                self.validacao_text.insert(tk.END, f"  • {erro}\n", "error")
            self.validacao_text.insert(tk.END, "\n")
        
        if validacao['avisos']:
            self.validacao_text.insert(tk.END, "🟡 AVISOS:\n", "warning")
            for aviso in validacao['avisos']:
                self.validacao_text.insert(tk.END, f"  • {aviso}\n", "warning")
            self.validacao_text.insert(tk.END, "\n")
        
        self.validacao_text.tag_config("valid", foreground="green", font=("Arial", 12, "bold"))
        self.validacao_text.tag_config("invalid", foreground="red", font=("Arial", 12, "bold"))
        self.validacao_text.tag_config("error", foreground="red")
        self.validacao_text.tag_config("warning", foreground="orange")
        
        self.validacao_text.config(state=tk.DISABLED)
    
    def excluir_chunk(self):
        """Exclui o chunk atual"""
        if not self.chunk_atual:
            return
        
        if messagebox.askyesno("Confirmar", f"Excluir chunk '{self.chunk_atual.get('titulo', '')}'?"):
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE id = ?", (self.chunk_atual['id'],))
            conn.commit()
            conn.close()
            self.chunk_atual = None
            self.carregar_chunks()
            self.status_bar.config(text="🗑️ Chunk excluído")
    
    def duplicar_chunk(self):
        """Duplica o chunk atual"""
        if not self.chunk_atual:
            return
        
        chunk = self.chunk_atual.copy()
        chunk['id'] = f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        chunk['data_criacao'] = datetime.now().isoformat()
        chunk['aprovado'] = 0
        chunk['titulo'] = chunk.get('titulo', '') + " (cópia)"
        
        self.db.adicionar_chunk(chunk)
        self.carregar_chunks()
        self.status_bar.config(text=f"📋 Chunk duplicado como {chunk['id']}")
    
    def importar_docx(self):
        """Importa arquivo DOCX com extração inteligente de chunks JSON"""
        try:
            import mammoth
        except ImportError:
            messagebox.showerror("Erro", "Biblioteca 'mammoth' não instalada.\nExecute: pip install mammoth")
            return
        
        arquivos = filedialog.askopenfilenames(
            title="Selecionar arquivos DOCX",
            filetypes=[("Documentos Word", "*.docx"), ("Todos os arquivos", "*.*")]
        )
        
        if not arquivos:
            return
        
        total_chunks = 0
        for arquivo in arquivos:
            self.status_bar.config(text=f"⏳ Processando {os.path.basename(arquivo)}...")
            self.root.update()
            
            try:
                with open(arquivo, "rb") as f:
                    result = mammoth.extract_raw_text(f)
                    texto = result.value
                
                # Extrai chunks JSON do texto
                chunks = self._extrair_chunks_json(texto, os.path.basename(arquivo))
                
                for chunk in chunks:
                    # Garante ID único
                    if not chunk.get('id'):
                        chunk['id'] = f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}_{total_chunks}"
                    
                    # Marca como aprovado por importação automática
                    chunk['aprovado'] = chunk.get('aprovado', 1)
                    chunk['aprovado_por'] = chunk.get('aprovado_por', 'importacao_automatica')
                    chunk['fonte'] = chunk.get('fonte', os.path.basename(arquivo))
                    
                    # Verifica campos obrigatórios
                    if not chunk.get('titulo') or not chunk.get('conteudo'):
                        print(f"⚠️ Chunk ignorado (sem título ou conteúdo): {chunk.get('titulo', '')}")
                        continue
                    
                    self.db.adicionar_chunk(chunk)
                    total_chunks += 1
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar {arquivo}:\n{str(e)}")
                import traceback
                traceback.print_exc()
        
        self.carregar_chunks()
        self.carregar_tags()
        self.status_bar.config(text=f"✅ Importados {total_chunks} chunks de {len(arquivos)} arquivos")
        messagebox.showinfo("Importação", f"✅ {total_chunks} chunks importados com sucesso!")
    
    def _extrair_chunks_json(self, texto, fonte):
        """
        Extrai chunks do formato JSON presente no texto do DOCX.
        O formato esperado é:
        
        ## CHUNK N
        {
            "titulo": "...",
            "tipo": "...",
            "tags": [...],
            "conteudo": "...",
            "referencias": [...]
        }
        """
        chunks = []
        
        # Padrão para encontrar blocos JSON completos
        # Busca por "## CHUNK" seguido de número, depois um bloco JSON
        padrao_chunk = r'##\s*CHUNK\s*\d+\s*\n*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
        
        # Também tenta encontrar JSONs que podem estar em linhas separadas
        matches = re.findall(padrao_chunk, texto, re.DOTALL)
        
        if matches:
            for json_str in matches:
                try:
                    chunk_data = json.loads(json_str.strip())
                    # Garante campos obrigatórios
                    if 'conteudo' in chunk_data and 'titulo' in chunk_data:
                        # Processa o conteúdo - pode estar como string ou lista
                        if isinstance(chunk_data['conteudo'], list):
                            chunk_data['conteudo'] = '\n'.join(chunk_data['conteudo'])
                        
                        # Verifica se referencias é lista
                        if 'referencias' in chunk_data and isinstance(chunk_data['referencias'], str):
                            # Se for string, converte para lista
                            chunk_data['referencias'] = [r.strip() for r in chunk_data['referencias'].split('\n') if r.strip()]
                        elif 'referencias' not in chunk_data:
                            chunk_data['referencias'] = []
                        
                        # Verifica se tags é lista
                        if 'tags' in chunk_data and isinstance(chunk_data['tags'], str):
                            chunk_data['tags'] = [t.strip() for t in chunk_data['tags'].split(',') if t.strip()]
                        elif 'tags' not in chunk_data:
                            chunk_data['tags'] = []
                        
                        # Verifica tipo
                        if not chunk_data.get('tipo'):
                            chunk_data['tipo'] = 'fundamento'
                        
                        # Autores (se houver)
                        if 'autores' not in chunk_data:
                            chunk_data['autores'] = []
                        elif isinstance(chunk_data['autores'], str):
                            chunk_data['autores'] = [a.strip() for a in chunk_data['autores'].split(',') if a.strip()]
                        
                        chunk_data['fonte'] = fonte
                        
                        # Verifica se o chunk já tem um ID válido
                        if not chunk_data.get('id'):
                            chunk_data['id'] = f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(chunks)}"
                        
                        chunks.append(chunk_data)
                        print(f"✅ Chunk extraído: {chunk_data['titulo'][:50]}...")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Erro ao decodificar JSON: {e}")
                    # Tenta uma abordagem mais flexível
                    chunk = self._parse_chunk_fallback(json_str, fonte)
                    if chunk:
                        chunks.append(chunk)
        else:
            # Se não encontrou chunks no formato esperado, tenta o parser alternativo
            print("⚠️ Nenhum chunk JSON encontrado. Tentando parser alternativo...")
            chunks = self._processar_texto_alternativo(texto, fonte)
        
        return chunks
    
    def _parse_chunk_fallback(self, texto, fonte):
        """
        Parser alternativo para chunks que não estão em JSON válido
        """
        try:
            chunk = {
                'titulo': '',
                'conteudo': '',
                'tipo': 'fundamento',
                'tags': [],
                'referencias': [],
                'autores': [],
                'fonte': fonte,
                'versao': '1.0',
                'aprovado': 1,
                'aprovado_por': 'importacao_automatica'
            }
            
            # Tenta extrair título
            match_titulo = re.search(r'"titulo"\s*:\s*"([^"]+)"', texto)
            if match_titulo:
                chunk['titulo'] = match_titulo.group(1)
            
            # Tenta extrair tipo
            match_tipo = re.search(r'"tipo"\s*:\s*"([^"]+)"', texto)
            if match_tipo:
                chunk['tipo'] = match_tipo.group(1)
            
            # Tenta extrair tags
            match_tags = re.search(r'"tags"\s*:\s*\[([^\]]+)\]', texto)
            if match_tags:
                tags_str = match_tags.group(1)
                chunk['tags'] = [t.strip().strip('"\'') for t in tags_str.split(',') if t.strip()]
            
            # Tenta extrair conteúdo
            match_conteudo = re.search(r'"conteudo"\s*:\s*"((?:[^"\\]|\\.)*)"', texto, re.DOTALL)
            if match_conteudo:
                chunk['conteudo'] = match_conteudo.group(1).replace('\\"', '"').replace('\\n', '\n')
            
            # Tenta extrair referências
            match_refs = re.search(r'"referencias"\s*:\s*\[([^\]]+)\]', texto, re.DOTALL)
            if match_refs:
                refs_str = match_refs.group(1)
                chunk['referencias'] = [r.strip().strip('"\'') for r in refs_str.split(',') if r.strip()]
            
            if chunk['titulo'] and chunk['conteudo']:
                chunk['id'] = f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                return chunk
            
        except Exception as e:
            print(f"⚠️ Erro no parser alternativo: {e}")
        
        return None
    
    def _processar_texto_alternativo(self, texto, fonte):
        """
        Processa texto que pode ter chunks em formato alternativo
        (como o que aparece no arquivo BASE DE CONHECIMENTO.docx)
        """
        chunks = []
        
        # Divide por "## CHUNK"
        partes = re.split(r'##\s*CHUNK\s*\d+', texto)
        
        for parte in partes:
            parte = parte.strip()
            if not parte:
                continue
            
            # Tenta encontrar um JSON dentro da parte
            try:
                # Procura por { ... } que contenha "titulo" e "conteudo"
                padrao_json = r'\{[^{}]*"titulo"[^{}]*"conteudo"[^{}]*\}'
                match = re.search(padrao_json, parte, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    chunk_data = json.loads(json_str)
                    
                    # Garante campos
                    if 'titulo' in chunk_data and 'conteudo' in chunk_data:
                        chunk_data['fonte'] = fonte
                        if not chunk_data.get('tipo'):
                            chunk_data['tipo'] = 'fundamento'
                        if not chunk_data.get('tags'):
                            chunk_data['tags'] = []
                        if not chunk_data.get('referencias'):
                            chunk_data['referencias'] = []
                        if not chunk_data.get('autores'):
                            chunk_data['autores'] = []
                        
                        # Ajusta IDs
                        chunk_data['id'] = f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(chunks)}"
                        chunks.append(chunk_data)
                        continue
            except:
                pass
            
            # Se não encontrou JSON, tenta extrair manualmente
            chunk = self._extrair_chunk_manual(parte, fonte, len(chunks))
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _extrair_chunk_manual(self, texto, fonte, idx):
        """Extrai chunk manualmente de texto não estruturado"""
        chunk = {
            'titulo': '',
            'conteudo': '',
            'tipo': 'fundamento',
            'tags': [],
            'referencias': [],
            'autores': [],
            'fonte': fonte,
            'versao': '1.0',
            'aprovado': 1,
            'aprovado_por': 'importacao_automatica',
            'id': f"chunk_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}"
        }
        
        linhas = texto.split('\n')
        conteudo_parts = []
        
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            
            # Tenta identificar título (linhas curtas que parecem títulos)
            if not chunk['titulo']:
                # Verifica se a linha parece um título
                if len(linha) < 80 and not linha.startswith('"') and not linha.endswith('"'):
                    # Verifica se não é uma referência
                    if not re.match(r'^[A-Z]{2,}', linha):
                        chunk['titulo'] = linha
                        continue
            
            # Tenta identificar referências (ABNT style)
            if re.match(r'^[A-Z]{2,}', linha) and ',' in linha and '(' in linha:
                chunk['referencias'].append(linha)
                continue
            
            # Se não for título nem referência, é conteúdo
            if linha:
                conteudo_parts.append(linha)
        
        chunk['conteudo'] = '\n'.join(conteudo_parts)
        
        # Se não encontrou título, tenta extrair do início do conteúdo
        if not chunk['titulo'] and conteudo_parts:
            first_line = conteudo_parts[0]
            if len(first_line) < 80:
                chunk['titulo'] = first_line
                chunk['conteudo'] = '\n'.join(conteudo_parts[1:])
        
        # Determina tipo baseado no conteúdo
        if chunk['conteudo']:
            if 'problema' in chunk['conteudo'].lower() or 'troubleshooting' in chunk['conteudo'].lower():
                chunk['tipo'] = 'problema'
            elif 'solução' in chunk['conteudo'].lower() or 'solução' in chunk['conteudo'].lower():
                chunk['tipo'] = 'solucao'
            elif 'conceito' in chunk['conteudo'].lower() or 'fundamento' in chunk['conteudo'].lower():
                chunk['tipo'] = 'fundamento'
            elif 'aplicação' in chunk['conteudo'].lower() or 'aplicacao' in chunk['conteudo'].lower():
                chunk['tipo'] = 'aplicacao'
        
        # Extrai tags do conteúdo
        tags_comuns = ['cromatografia', 'lc-ms', 'gc-ms', 'spe', 'spme', 'hplc', 'capillary_lc', 
                      'temperatura', 'gradiente', 'colunas', 'empacotamento', 'validacao']
        chunk['tags'] = [tag for tag in tags_comuns if tag in chunk['conteudo'].lower()]
        
        if chunk['titulo'] and chunk['conteudo']:
            return chunk
        
        return None
    
    def exportar_json(self):
        """Exporta JSON para o Cromato Buddy"""
        caminho = filedialog.asksaveasfilename(
            title="Salvar JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not caminho:
            return
        
        total = self.db.exportar_json(caminho)
        self.status_bar.config(text=f"📤 Exportados {total} chunks para {caminho}")
        messagebox.showinfo("Exportação", f"✅ {total} chunks exportados para:\n{caminho}")
    
    def mostrar_guia_tags(self):
        """Mostra guia de tags"""
        if self.guia_aberto and self.guia_aberto.winfo_exists():
            self.guia_aberto.lift()
            return
        
        guia = tk.Toplevel(self.root)
        guia.title("📋 Guia de Tags - Cromato Buddy")
        guia.geometry("700x600")
        self.guia_aberto = guia
        
        text = scrolledtext.ScrolledText(guia, wrap=tk.WORD, font=("Arial", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        conteudo = """
📋 GUIA DE TAGS - CROMATO BUDDY

Este guia ajuda a padronizar a criação de chunks para a base de conhecimento.

---

🏷️ TAGS RECOMENDADAS (gerais):

• cromatografia
• química analítica
• separações
• lc-ms
• gc
• spme
• hplc
• uplc
• fundamentos
• instrumentação
• métodos
• validação

---

🏷️ TAGS POR TIPO DE CONTEÚDO:

🔹 FUNDAMENTOS:
  - equilibrio_particao
  - retencao
  - seletividade
  - resolucao
  - eficiencia
  - tempo_morto
  - fator_retencao
  - volume_morto
  - capacidade_pico
  - eluicao

🔹 VAN DEEMTER:
  - termo_a
  - termo_b
  - termo_c
  - difusao_longitudinal
  - transferencia_massa
  - velocidade_linear
  - hetp
  - n_pratos_teoricos
  - dispersao_extracoluna
  - band_broadening

🔹 TEMPERATURA:
  - temperatura
  - viscosidade
  - difusao
  - vanthoff
  - gradiente_radial
  - gradiente_axial
  - aquecimento_resistivo
  - peltier
  - controle_pid
  - sensores_rtd
  - termopares

🔹 LC CAPILAR:
  - capillary_lc
  - micro_lc
  - nano_lc
  - peeksil
  - silica_fundida
  - conexoes_capilares
  - volumes_extracolunares
  - colunas_estreitas
  - baixa_vazao

🔹 PARTÍCULAS E COLUNAS:
  - fpp
  - spp
  - core_shell
  - monolitos
  - colunas_empacotadas
  - tubulares_abertas
  - frit_metalico
  - frit_fibra_vidro
  - empacotamento
  - permeabilidade

🔹 IT-SPME:
  - it-spme
  - column_switching
  - breakthrough
  - loading
  - washing
  - elution
  - forward_flush
  - back_flush
  - direct_it-spme
  - sorvente

🔹 GRAFENO:
  - grafeno
  - oxido_grafeno
  - sigo
  - sigo-c18ec
  - interacao_pi-pi
  - endcapping
  - adsorcao
  - dessorcao
  - area_superficial
  - funcionalizacao

🔹 LC-MS:
  - esi
  - apci
  - ionizacao
  - supressao_ionica
  - sensibilidade
  - mrm
  - sim
  - full_scan
  - fragmentacao
  - interface_lc-ms

🔹 TROUBLESHOOTING:
  - contrapressao
  - recuperacao
  - picos_assimetricos
  - baixa_resolucao
  - supressao_ionica
  - breakthrough
  - ruido
  - variacao_retencao
  - entupimento
  - perda_eficiencia

---

📌 COMO USAR:

1. Escolha a tag principal que descreve o conteúdo
2. Adicione tags secundárias para contexto
3. Use hífens para separar palavras compostas
4. Mantenha consistência (ex: sempre "lc-ms", não "lcms")

Exemplo de chunk bem formatado:
{
  "titulo": "Supressão Iônica em LC-MS",
  "tipo": "problema",
  "tags": ["supressao_ionica", "lc-ms", "troubleshooting", "matriz"],
  "conteudo": "Explicação detalhada...",
  "referencias": ["SNYDER, L. R...", "DOLAN, J. W..."]
}

---

📖 REFERÊNCIAS NO FORMATO ABNT:

• LIVRO: SOBRENOME, Nome. Título. Edição. Cidade: Editora, Ano.
• ARTIGO: SOBRENOME, Nome. Título do artigo. Nome do Periódico, volume, páginas, Ano.
• TESE: SOBRENOME, Nome. Título. Ano. Tese (Doutorado) - Universidade, Cidade.

Exemplos:
SNYDER, L. R.; KIRKLAND, J. J.; DOLAN, J. W. Introduction to Modern Liquid Chromatography. 3rd ed. New York: Wiley, 2010.
LANÇAS, F. M. Cromatografia Líquida Moderna. Campinas: Editora Unicamp, 2009.
"""
        
        text.insert(tk.END, conteudo)
        text.config(state=tk.DISABLED)


# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = CromatoManagerV2(root)
    root.mainloop()
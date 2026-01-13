# 🔄 Scripts de Migração - V1.x → V2.0

Scripts para migração do banco de dados de INTEGER para UUID com ORM SQLAlchemy.

## 📋 Ordem de Execução

Execute os scripts **nesta ordem exata**:

### 1️⃣ Backup do Banco Atual

```bash
python scripts/migration/backup_banco_atual.py
```

**O que faz:**
- Cria cópia do banco atual em `backups/`
- Exporta dados em JSON para segurança
- Verifica integridade do backup

**Resultado:**
- `backups/sistema_questoes_backup_YYYYMMDD_HHMMSS.db`
- `backups/sistema_questoes_backup_YYYYMMDD_HHMMSS.json`

---

### 2️⃣ Criar Novo Schema

```bash
python scripts/migration/criar_novo_schema.py
```

**O que faz:**
- Cria todas as tabelas do novo schema (UUID)
- Popula dados iniciais (tipos, dificuldades, fontes)
- Não toca no banco antigo

**Resultado:**
- `data/sistema_questoes_v2.db` (novo banco vazio com schema)

---

### 3️⃣ Migrar Dados

```bash
python scripts/migration/migrar_dados.py
```

**O que faz:**
- Migra todos os dados do banco antigo para o novo
- Converte IDs INTEGER para UUIDs
- Gera códigos legíveis (Q-2026-0001, etc.)
- Deduplica imagens por hash MD5
- Unifica tabelas de resposta
- Mantém todos os relacionamentos

**Resultado:**
- `data/sistema_questoes_v2.db` (banco novo populado)

---

## 📊 Estrutura de Migração

### Etapas do Script de Migração

1. **Preparação**
   - Conecta aos dois bancos
   - Cria mapas de conversão (ID antigo → UUID novo)

2. **Migração de Dados Base**
   - Dificuldades (FACIL, MEDIO, DIFICIL)
   - Tags (hierarquia completa)
   - Tipos de Questão (OBJETIVA, DISCURSIVA)
   - Fontes (extraídas do banco antigo)
   - Anos de Referência (extraídos do banco antigo)

3. **Migração de Imagens**
   - Centraliza imagens em tabela única
   - Deduplica por hash MD5
   - Mapeia referências antigas para UUIDs

4. **Migração de Questões**
   - Gera códigos legíveis (Q-AAAA-NNNN)
   - Converte todos os campos
   - Mapeia relacionamentos

5. **Migração de Alternativas**
   - Converte para UUIDs
   - Mantém ordem e dados

6. **Migração de Respostas (UNIFICADAS)**
   - Une resposta_objetiva, resposta_discursiva e resolucao_questao
   - Uma única tabela `resposta_questao`

7. **Migração de Relacionamentos**
   - questao_tag (N:N)
   - lista_questao (N:N com ordem)
   - questao_versao (N:N)

8. **Validação**
   - Verifica contagens
   - Compara com banco antigo
   - Exibe estatísticas

---

## 🔍 Verificação dos Resultados

### Comparar Contagens

```bash
# Banco antigo
sqlite3 data/sistema_questoes.db "SELECT COUNT(*) FROM questao WHERE ativo = 1;"

# Banco novo
sqlite3 data/sistema_questoes_v2.db "SELECT COUNT(*) FROM questao WHERE ativo = 1;"
```

### Verificar Códigos Gerados

```bash
sqlite3 data/sistema_questoes_v2.db "SELECT codigo, titulo FROM questao LIMIT 10;"
```

Deve exibir códigos como: `Q-2026-0001`, `Q-2026-0002`, etc.

### Verificar Deduplicação de Imagens

```bash
sqlite3 data/sistema_questoes_v2.db "SELECT COUNT(*), COUNT(DISTINCT hash_md5) FROM imagem;"
```

Se os números forem diferentes, houve deduplicação!

### Verificar Relacionamentos

```bash
# Questões com tags
sqlite3 data/sistema_questoes_v2.db "SELECT COUNT(*) FROM questao_tag;"

# Questões em listas
sqlite3 data/sistema_questoes_v2.db "SELECT COUNT(*) FROM lista_questao;"
```

---

## 🚨 Em Caso de Erro

### Rollback

Se algo der errado durante a migração:

1. **Remova o banco novo:**
   ```bash
   rm data/sistema_questoes_v2.db
   ```

2. **Restaure do backup:**
   ```bash
   # Encontre o backup mais recente
   ls -lt backups/

   # Restaure (se necessário)
   cp backups/sistema_questoes_backup_YYYYMMDD_HHMMSS.db data/sistema_questoes.db
   ```

3. **Corrija o problema e tente novamente**

### Logs e Debug

Para ver mais detalhes durante a execução, modifique o `echo=True` no script:

```python
engine = create_engine(f'sqlite:///{db_novo}', echo=True)  # Ver SQL gerado
```

---

## 📝 Estrutura do Novo Banco

### Tabelas Principais

- `questao` - Questões (com UUIDs e códigos legíveis)
- `alternativa` - Alternativas de questões objetivas
- `resposta_questao` - **Respostas unificadas** (objetivas + discursivas)
- `imagem` - **Tabela centralizada de imagens** (com hash MD5)
- `lista` - Listas de questões
- `tag` - Tags hierárquicas

### Tabelas de Relacionamento

- `questao_tag` - N:N entre questões e tags
- `lista_questao` - N:N entre listas e questões (com ordem)
- `questao_versao` - Relaciona versões de questões

### Tabelas de Referência

- `tipo_questao` - OBJETIVA, DISCURSIVA
- `fonte_questao` - ENEM, FUVEST, AUTORAL, etc.
- `ano_referencia` - 2024, 2025, etc.
- `dificuldade` - FACIL, MEDIO, DIFICIL

---

## ✅ Checklist de Migração

- [ ] Backup do banco atual criado
- [ ] Backup verificado (tamanhos conferem)
- [ ] Novo schema criado
- [ ] Dados iniciais populados no novo schema
- [ ] Migração executada sem erros
- [ ] Contagens verificadas (antigo vs novo)
- [ ] Códigos legíveis gerados corretamente
- [ ] Imagens deduplicadas
- [ ] Relacionamentos preservados
- [ ] Testes básicos realizados

---

## 🎯 Próximos Passos

Após a migração bem-sucedida:

1. **Fase 3:** Criar Repositories com ORM
2. **Fase 4:** Atualizar Services e Controllers
3. **Fase 5:** Atualizar Views e Forms
4. **Fase 6:** Testes completos
5. **Fase 7:** Deploy em produção

---

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. Verifique os logs de erro
2. Consulte o documento `ARQUITETURA_UUID_ORM.md`
3. Verifique se todos os requisitos estão instalados:
   ```bash
   pip list | grep -E "sqlalchemy|pillow"
   ```

---

**Última atualização:** 2026-01-13
**Versão:** 2.0.0

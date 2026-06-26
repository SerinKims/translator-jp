PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS translation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_language TEXT NOT NULL DEFAULT 'ja',
    target_language TEXT NOT NULL DEFAULT 'ko',

    source_site TEXT NOT NULL DEFAULT 'manual'
        CHECK (source_site IN ('manual', 'pixiv')),

    source_url TEXT,
    source_title TEXT,
    source_author TEXT,
    source_work_id TEXT,
    source_fetched_at DATETIME,

    original_text TEXT NOT NULL,
    translated_text TEXT,

    model_name TEXT NOT NULL DEFAULT 'gemma4:26b-a4b-it-q4_K_M',
    prompt_version TEXT NOT NULL DEFAULT 'translate_ja_ko_v1',
    ollama_think TEXT,
    ollama_options_json TEXT,

    style TEXT NOT NULL DEFAULT 'webnovel',
    honorific_policy TEXT NOT NULL DEFAULT 'preserve',
    preserve_names INTEGER NOT NULL DEFAULT 1,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'fetched',
            'pending_translation',
            'running',
            'completed',
            'partial_failed',
            'failed',
            'cancelled'
        )),

    total_chunks INTEGER NOT NULL DEFAULT 0,
    completed_chunks INTEGER NOT NULL DEFAULT 0,
    failed_chunks INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,
    elapsed_ms INTEGER,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    job_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,

    source_text TEXT NOT NULL,
    translated_text TEXT,

    context_before TEXT,
    context_after TEXT,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),

    retry_count INTEGER NOT NULL DEFAULT 0,

    prompt_used TEXT,
    raw_model_response TEXT,

    elapsed_ms INTEGER,
    error_message TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES translation_jobs(id) ON DELETE CASCADE,

    UNIQUE (job_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS glossary_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    description TEXT,

    is_active INTEGER NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS glossary_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    glossary_set_id INTEGER,

    source_lang TEXT NOT NULL DEFAULT 'ja',
    target_lang TEXT NOT NULL DEFAULT 'ko',
    source_term TEXT NOT NULL,
    target_term TEXT NOT NULL,

    term_type TEXT NOT NULL DEFAULT 'common',
    description TEXT,
    aliases TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    is_required INTEGER NOT NULL DEFAULT 1,

    is_case_sensitive INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (glossary_set_id) REFERENCES glossary_sets(id) ON DELETE CASCADE,

    UNIQUE (glossary_set_id, source_lang, target_lang, source_term)
);

CREATE TABLE IF NOT EXISTS translation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_hash TEXT NOT NULL UNIQUE,

    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,

    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    style TEXT NOT NULL,
    honorific_policy TEXT NOT NULL DEFAULT 'preserve',
    preserve_names INTEGER NOT NULL DEFAULT 1,

    glossary_hash TEXT,

    hit_count INTEGER NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    job_id INTEGER,
    chunk_id INTEGER,

    source_text TEXT NOT NULL,
    model_translation TEXT NOT NULL,
    user_corrected_translation TEXT,

    rating INTEGER CHECK (rating BETWEEN 1 AND 5),

    feedback_type TEXT,
    comment TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES translation_jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (chunk_id) REFERENCES translation_chunks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    version_name TEXT NOT NULL UNIQUE,
    task_type TEXT NOT NULL DEFAULT 'translation',

    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,

    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    run_name TEXT,

    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    dataset_name TEXT NOT NULL,

    total_cases INTEGER NOT NULL DEFAULT 0,
    passed_cases INTEGER NOT NULL DEFAULT 0,
    failed_cases INTEGER NOT NULL DEFAULT 0,

    avg_elapsed_ms INTEGER,

    no_japanese_left_score REAL,
    paragraph_match_score REAL,
    glossary_preserve_score REAL,
    dialogue_style_score REAL,
    no_empty_translation_score REAL,

    report_json TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eval_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    eval_run_id INTEGER NOT NULL,

    case_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    expected_translation TEXT,
    actual_translation TEXT,

    passed INTEGER NOT NULL DEFAULT 0,
    score REAL,

    fail_reason TEXT,
    elapsed_ms INTEGER,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (eval_run_id) REFERENCES eval_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    default_style TEXT NOT NULL DEFAULT 'webnovel',
    default_honorific_policy TEXT NOT NULL DEFAULT 'preserve',
    default_preserve_names INTEGER NOT NULL DEFAULT 1,

    default_model_name TEXT NOT NULL DEFAULT 'gemma4:26b-a4b-it-q4_K_M',
    default_prompt_version TEXT NOT NULL DEFAULT 'translate_ja_ko_v1',

    auto_use_glossary INTEGER NOT NULL DEFAULT 1,
    auto_cache_enabled INTEGER NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_status
ON translation_jobs(status);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_created_at
ON translation_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_model_prompt
ON translation_jobs(model_name, prompt_version);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_source_site
ON translation_jobs(source_site);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_source_work_id
ON translation_jobs(source_work_id);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_source_url
ON translation_jobs(source_url);

CREATE INDEX IF NOT EXISTS idx_translation_jobs_source_site_work_id
ON translation_jobs(source_site, source_work_id);

CREATE INDEX IF NOT EXISTS idx_translation_chunks_job_id
ON translation_chunks(job_id);

CREATE INDEX IF NOT EXISTS idx_translation_chunks_status
ON translation_chunks(status);

CREATE INDEX IF NOT EXISTS idx_glossary_terms_source_term
ON glossary_terms(source_term);

CREATE INDEX IF NOT EXISTS idx_glossary_terms_lang
ON glossary_terms(source_lang, target_lang);

CREATE INDEX IF NOT EXISTS idx_glossary_terms_active
ON glossary_terms(is_active);

CREATE INDEX IF NOT EXISTS idx_translation_cache_source_hash
ON translation_cache(source_hash);

CREATE INDEX IF NOT EXISTS idx_translation_feedback_type
ON translation_feedback(feedback_type);

CREATE INDEX IF NOT EXISTS idx_eval_runs_prompt_version
ON eval_runs(prompt_version);

CREATE INDEX IF NOT EXISTS idx_eval_results_eval_run_id
ON eval_results(eval_run_id);

CREATE TRIGGER IF NOT EXISTS trg_translation_jobs_updated_at
AFTER UPDATE ON translation_jobs
FOR EACH ROW
BEGIN
    UPDATE translation_jobs
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_translation_chunks_updated_at
AFTER UPDATE ON translation_chunks
FOR EACH ROW
BEGIN
    UPDATE translation_chunks
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_glossary_sets_updated_at
AFTER UPDATE ON glossary_sets
FOR EACH ROW
BEGIN
    UPDATE glossary_sets
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_glossary_terms_updated_at
AFTER UPDATE ON glossary_terms
FOR EACH ROW
BEGIN
    UPDATE glossary_terms
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_translation_cache_updated_at
AFTER UPDATE ON translation_cache
FOR EACH ROW
BEGIN
    UPDATE translation_cache
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_user_settings_updated_at
AFTER UPDATE ON user_settings
FOR EACH ROW
BEGIN
    UPDATE user_settings
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

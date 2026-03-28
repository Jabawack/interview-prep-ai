-- 002: Job postings
CREATE TABLE job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    url TEXT,
    raw_content TEXT,
    parsed_data JSONB NOT NULL DEFAULT '{}',
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_range TEXT,
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(company, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(location, '')), 'C')
    ) STORED,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_postings_search ON job_postings USING GIN(search_vector);
CREATE INDEX idx_job_postings_user ON job_postings(user_id, created_at DESC);
CREATE INDEX idx_job_postings_company ON job_postings(company);

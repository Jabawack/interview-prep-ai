-- 004: Interview prep + diagrams
CREATE TABLE interview_prep (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    job_posting_id UUID REFERENCES job_postings(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('questions', 'salary', 'system_design', 'mock_interview', 'general')),
    content JSONB NOT NULL DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE diagrams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_prep_id UUID REFERENCES interview_prep(id) ON DELETE CASCADE,
    excalidraw_json JSONB NOT NULL DEFAULT '{}',
    title TEXT NOT NULL,
    diagram_type TEXT NOT NULL CHECK (diagram_type IN ('architecture', 'entity', 'api_flow', 'component', 'sequence')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_interview_prep_conversation ON interview_prep(conversation_id);
CREATE INDEX idx_diagrams_prep ON diagrams(interview_prep_id);

-- 003: Company profiles
CREATE TABLE company_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    industry TEXT,
    interview_rounds JSONB NOT NULL DEFAULT '[]',
    common_questions JSONB NOT NULL DEFAULT '[]',
    glassdoor_rating NUMERIC(2,1),
    culture_notes TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_company_profiles_name ON company_profiles(lower(name));

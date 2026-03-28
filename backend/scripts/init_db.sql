-- Enable pgvector extension for CLIP embedding storage and similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for fuzzy text search on wardrobe items
CREATE EXTENSION IF NOT EXISTS pg_trgm;

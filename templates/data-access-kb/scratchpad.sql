-- list all records
SELECT * FROM sema4ai.my_kb;

-- list all records with id filters
SELECT * FROM sema4ai.my_kb WHERE id in ('1', '2');

-- list all records with metadata filters
SELECT * FROM sema4ai.my_kb WHERE category = 'ai';

-- delete records with ids
DELETE FROM sema4ai.my_kb WHERE id in ('1', '2');

-- bsaic search
SELECT * 
FROM sema4ai.my_kb 
WHERE content = 'how to get insights from data'
and relevance >= 0.5
LIMIT 1;

-- search with metadata filters
SELECT * 
FROM sema4ai.my_kb 
WHERE content = 'what can I do with AI'
and relevance >= 0.5
and category = 'ai'
LIMIT 1;

-- search with id filters
SELECT * 
FROM sema4ai.my_kb 
WHERE content = 'what can I do with AI'
and relevance >= 0.5
and id in ('1', '2')
LIMIT 1;

-- list metadata columns
SELECT metadata_columns
FROM information_schema.knowledge_bases
WHERE name = 'my_kb';

-- insert records
INSERT INTO sema4ai.my_kb (id, content, src, category) 
VALUES 
('1', 'AI enables machines to mimic human intelligence, such as learning, reasoning, problem-solving, and language understanding.', 'src_1', 'ai'),
('2', 'Machine learning is a subset of AI that focuses on training algorithms to learn patterns from data without being explicitly programmed.', 'src_2', 'ml'),
('3', 'Generative AI, like ChatGPT or image generators, creates new content such as text, images, code, or music based on patterns learned from data.', 'src_3', 'ai');

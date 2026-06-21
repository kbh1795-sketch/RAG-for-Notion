from datetime import datetime, timezone
from math import exp
from unittest import TestCase

from src.persona_chat import PersonaChatEngine
from src.retriever import TimeWeightedRetriever, combine_scores, keyword_relevance_score
from src.time_decay import recency_weight


class CoreTests(TestCase):
    def test_recency_falls_back_and_decays(self):
        now = datetime(2026, 6, 12, tzinfo=timezone.utc)
        self.assertAlmostEqual(recency_weight(created_time='2026-06-02T00:00:00+00:00', now=now, half_life_days=10), exp(-1), places=6)

    def test_score_combination(self):
        self.assertAlmostEqual(combine_scores(0.8, 0.4, alpha=0.7, beta=0.3), 0.68)

    def test_recent_note_ranks_higher(self):
        now = datetime(2026, 6, 12, tzinfo=timezone.utc)
        old = {'id':'old','title':'Planning idea','content':'Planning should use urgency and idea priority.','created_time':'2024-01-01T00:00:00+00:00','last_edited_time':'2024-01-01T00:00:00+00:00','source':'notion','url':'old'}
        recent = {'id':'recent','title':'Planning idea update','content':'Planning should use freshness and idea priority.','created_time':'2026-06-01T00:00:00+00:00','last_edited_time':'2026-06-11T00:00:00+00:00','source':'notion','url':'recent'}
        result = TimeWeightedRetriever([old, recent], now=now).search('planning idea priority', top_k=2)
        self.assertEqual(result[0].document['id'], 'recent')

    def test_persona_extracts_sources(self):
        doc = {'id':'recent','title':'Recent planning update','content':'Fresh notes should have stronger influence than stale urgency-only rules.','created_time':'2026-06-01T00:00:00+00:00','last_edited_time':'2026-06-11T00:00:00+00:00','source':'notion','url':'recent'}
        reply = PersonaChatEngine([doc], prefer_openai=False).chat('fresh planning')
        self.assertEqual(reply.mode, 'extractive')
        self.assertEqual(reply.sources[0]['title'], 'Recent planning update')

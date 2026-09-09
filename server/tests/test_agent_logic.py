from __future__ import annotations

import unittest

from app.agent_logic import buildAgentAnswer, buildAgentContext, classifyIntent, getLocalStats


class AgentLogicTest(unittest.TestCase):
    def answer(self, question: str, year: int = 2024, layer: str = "ndvi") -> str:
        intent = classifyIntent(question)
        context = buildAgentContext(intent, question, year, layer)
        stats = getLocalStats(question, year, layer)
        return buildAgentAnswer(intent, question, context, stats)

    def test_concept_explain_resilience(self):
        answer = self.answer("什么是生态韧性？")
        self.assertIn("生态韧性", answer)
        self.assertIn("扰动", answer)
        self.assertNotIn("我已从项目本地数据统计中读取到以下结果", answer)
        self.assertNotIn("NDVI统计结果", answer)

    def test_ndvi_median_stats(self):
        answer = self.answer("2024年NDVI中位数是多少？")
        self.assertEqual(classifyIntent("2024年NDVI中位数是多少？"), "stats_query")
        self.assertIn("0.5052", answer)
        self.assertIn("中位数", answer)
        self.assertIn("NDVI", answer)

    def test_p90_explanation(self):
        answer = self.answer("P90是什么意思？")
        self.assertEqual(classifyIntent("P90是什么意思？"), "stats_query")
        self.assertIn("P90", answer)
        self.assertIn("90%", answer)
        self.assertIn("当前系统加载", answer)

    def test_governance_advice(self):
        answer = self.answer("洪水风险高的地方怎么治理？", layer="four_dim_fri")
        self.assertEqual(classifyIntent("洪水风险高的地方怎么治理？"), "governance_advice")
        self.assertIn("FRI", answer)
        self.assertIn("治理", answer)
        self.assertIn("生态缓冲", answer)
        self.assertNotIn("NDVI统计结果", answer)

    def test_teaching_guidance(self):
        answer = self.answer("学生如何分析ER和FRI？", layer="four_dim_er")
        self.assertEqual(classifyIntent("学生如何分析ER和FRI？"), "teaching_guidance")
        self.assertIn("学生", answer)
        self.assertIn("ER", answer)
        self.assertIn("FRI", answer)
        self.assertIn("证据", answer)


if __name__ == "__main__":
    unittest.main()

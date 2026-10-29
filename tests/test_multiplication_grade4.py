"""检查题型约束、随机复现与实际 PDF 中的题号和答案。"""

from pathlib import Path
import random
import re
import tempfile
import unittest

import pymupdf

from multiplication_grade4 import generate_problems, write_pdf


class MultiplicationTests(unittest.TestCase):
    def test_problem_constraints_across_seeds(self):
        for seed in range(200):
            with self.subTest(seed=seed):
                oral, written = generate_problems(random.Random(seed))
                self.assertEqual(len(set(oral + written)), 20)
                for group in (oral, written):
                    self.assertEqual(len(group), 10)
                    self.assertTrue(all(10 <= b <= 99 for _, b in group))
                self.assertTrue(all(100 <= a <= 999 for a, _ in oral))
                self.assertEqual(sum(100 <= a <= 999 for a, _ in written), 5)
                self.assertEqual(sum(1000 <= a <= 9999 for a, _ in written), 5)
                self.assertTrue(all(a % 10 == b % 10 == 0 for a, b in oral))

    def test_seed_reproduces_questions(self):
        self.assertEqual(generate_problems(random.Random(42)),
                         generate_problems(random.Random(42)))
        self.assertNotEqual(generate_problems(random.Random(42)),
                            generate_problems(random.Random(43)))

    def test_printed_questions_and_answers(self):
        oral, written = generate_problems(random.Random(42))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "试卷" / "练习.pdf"
            write_pdf(output, oral, written)
            with pymupdf.open(output) as document:
                self.assertEqual(len(document), 2)
                for page in document:
                    self.assertAlmostEqual(page.rect.width * 25.4 / 72, 210, places=2)
                    self.assertAlmostEqual(page.rect.height * 25.4 / 72, 297, places=2)
                    for block in page.get_text("dict")["blocks"]:
                        if block["type"] != 0:
                            continue
                        for line in block["lines"]:
                            for span in line["spans"]:
                                self.assertTrue(page.rect.contains(pymupdf.Rect(span["bbox"])))
                questions = document[0].get_text()
                answers = document[1].get_text()
                self.assertNotIn("参考答案", questions)
                for removed in ("多位数乘两位数练习", "四年级上册", "姓名", "班级", "日期"):
                    self.assertNotIn(removed, questions)
                self.assertTrue(document[0].get_text(sort=True).startswith("一、口算"))
                self.assertIn("参考答案", answers)
                pattern = r"(\d+)\.\s+(\d+)\s*×\s*(\d+)\s*=\s*(\d+)"
                printed_answers = re.findall(pattern, answers)
                expected = [(str(i), str(a), str(b), str(a * b))
                            for i, (a, b) in enumerate(oral + written, 1)]
                self.assertEqual(printed_answers, expected)
                printed_questions = re.findall(r"(\d+)\.\s+(\d+)\s*×\s*(\d+)\s*=", questions)
                self.assertEqual(printed_questions, [entry[:3] for entry in expected])


if __name__ == "__main__":
    unittest.main()

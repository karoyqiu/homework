"""检查题型约束、随机复现与实际 PDF 中的题号和答案。"""

from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest

import pymupdf

from multiplication_grade4 import generate_problems, write_pdf


class MultiplicationTests(unittest.TestCase):
    def test_problem_constraints_across_seeds(self):
        oral_orders = set()
        written_orders = set()
        oral_factors = set()
        for seed in range(200):
            with self.subTest(seed=seed):
                oral, written = generate_problems(random.Random(seed))
                self.assertEqual(len({tuple(sorted(problem)) for problem in oral + written}), 20)
                self.assertTrue(all(a != 1 and b != 1 for a, b in oral + written))
                for group in (oral, written):
                    self.assertEqual(len(group), 10)
                for a, b in oral:
                    oral_orders.add(len(str(a).replace("0", "")))
                    oral_factors.update((a, b))
                    if len(str(a).replace("0", "")) == 1:
                        a, b = b, a
                    self.assertTrue(10 <= a <= 9999)
                    self.assertTrue(2 <= b <= 999)
                    self.assertEqual(len(str(a).replace("0", "")), 2)
                    self.assertEqual(len(str(b).replace("0", "")), 1)
                written_orders.update(len(str(a)) for a, _ in written)
                normalized = [sorted(problem) for problem in written]
                self.assertTrue(all(10 <= a <= 99 and 10 <= b <= 999
                                    for a, b in normalized))
                self.assertEqual(sum(100 <= b <= 999 for _, b in normalized), 8)
                self.assertEqual(sum(10 <= b <= 99 for _, b in normalized), 2)
        self.assertEqual(oral_orders, {1, 2})
        self.assertEqual(written_orders, {2, 3})
        self.assertTrue({10, 100, 101}.issubset(oral_factors))

    def test_seed_reproduces_questions(self):
        self.assertEqual(generate_problems(random.Random(42)),
                         generate_problems(random.Random(42)))
        self.assertNotEqual(generate_problems(random.Random(42)),
                            generate_problems(random.Random(43)))

    def test_printed_questions_and_answers(self):
        oral, written = generate_problems(random.Random(42))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "试卷" / "练习.pdf"
            write_pdf(output, [(oral, written)])
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

    def test_multiple_copies_from_cli(self):
        script = Path(__file__).resolve().parents[1] / "multiplication_grade4.py"
        with tempfile.TemporaryDirectory() as directory:
            texts = []
            for run in range(2):
                output = Path(directory) / f"batch{run}.pdf"
                subprocess.run([sys.executable, str(script), "--copies", "3",
                                "--seed", "42", "--output", str(output)],
                               check=True, capture_output=True)
                with pymupdf.open(output) as document:
                    self.assertEqual(len(document), 6)
                    batch = [page.get_text() for page in document]
                    texts.append(batch)
                    rng = random.Random(42)
                    for index in range(3):
                        oral, written = generate_problems(rng)
                        questions, answers = batch[index], batch[index + 3]
                        self.assertNotIn("参考答案", questions)
                        self.assertIn("参考答案", answers)
                        self.assertTrue(document[index].get_text(sort=True).startswith("一、口算"))
                        for page_index in (index, index + 3):
                            page = document[page_index]
                            self.assertIn(f"第 {index + 1} 份", batch[page_index])
                            self.assertIn(f"第 {page_index + 1} 页", batch[page_index])
                            self.assertAlmostEqual(page.rect.width * 25.4 / 72, 210, places=2)
                            self.assertAlmostEqual(page.rect.height * 25.4 / 72, 297, places=2)
                            for word in page.get_text("words"):
                                self.assertTrue(page.rect.contains(pymupdf.Rect(word[:4])))
                        expected = [(str(i), str(a), str(b), str(a * b))
                                    for i, (a, b) in enumerate(oral + written, 1)]
                        self.assertEqual(re.findall(r"(\d+)\.\s+(\d+)\s*×\s*(\d+)\s*=", questions),
                                         [entry[:3] for entry in expected])
                        self.assertEqual(re.findall(r"(\d+)\.\s+(\d+)\s*×\s*(\d+)\s*=\s*(\d+)", answers),
                                         expected)
                    self.assertEqual(len(set(batch[:3])), 3)
            self.assertEqual(texts[0], texts[1])

    def test_invalid_copies_rejected(self):
        script = Path(__file__).resolve().parents[1] / "multiplication_grade4.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.pdf"
            for value in ("0", "-1", "1.5", "abc"):
                with self.subTest(value=value):
                    result = subprocess.run(
                        [sys.executable, str(script), "--copies", value,
                         "--output", str(output)], capture_output=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(b"--copies", result.stderr)
                    self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

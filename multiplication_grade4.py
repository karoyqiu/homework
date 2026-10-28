"""生成四年级上册多位数乘两位数练习及答案，输出 A4 PDF。"""

import argparse
from pathlib import Path
import random

import pymupdf


Problem = tuple[int, int]
MM = 72 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = 210 * MM, 297 * MM
FONT = pymupdf.Font("cjk")


def generate_problems(rng: random.Random) -> tuple[list[Problem], list[Problem]]:
    """两组各含五道三位数和五道四位数题，全卷不重复。"""
    used: set[Problem] = set()
    groups: list[list[Problem]] = []
    for oral in (True, False):
        problems: list[Problem] = []
        for digits in (3, 4):
            lower, upper = 10 ** (digits - 1), 10**digits - 1
            selected = 0
            while selected < 5:
                if oral:
                    problem = (rng.randint(lower // 10, upper // 10) * 10,
                               rng.randint(1, 9) * 10)
                else:
                    problem = (rng.randint(lower, upper), rng.randint(10, 99))
                if problem in used:
                    continue
                used.add(problem)
                problems.append(problem)
                selected += 1
        rng.shuffle(problems)
        groups.append(problems)
    return groups[0], groups[1]


def text(page: pymupdf.Page, x: float, y: float, value: str,
         size: float = 13) -> None:
    page.insert_text((x, y), value, fontname="worksheet", fontsize=size)


def new_page(document: pymupdf.Document, title: str, number: int) -> pymupdf.Page:
    page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    page.insert_font(fontname="worksheet", fontbuffer=FONT.buffer)
    title_x = (PAGE_WIDTH - FONT.text_length(title, fontsize=19)) / 2
    text(page, title_x, 45, title, 19)
    text(page, 42, 69, "四年级上册 · 多位数乘两位数", 11)
    text(page, PAGE_WIDTH / 2 - 25, PAGE_HEIGHT - 23, f"第 {number} 页", 10)
    return page


def write_pdf(output: Path, oral: list[Problem], written: list[Problem]) -> None:
    """一页题目、一页答案；竖式计算区域采用两列五行。"""
    output.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        document.set_metadata({"title": "多位数乘两位数练习", "author": "homework"})
        page = new_page(document, "多位数乘两位数练习", 1)
        text(page, 42, 96, "姓名：____________    班级：____________    日期：____________", 11)
        text(page, 42, 125, "一、口算（共 10 题，直接写出得数）", 14)
        for index, (left, right) in enumerate(oral):
            row, column = divmod(index, 2)
            text(page, 42 + column * 263, 152 + row * 25,
                 f"{index + 1}.  {left} × {right} = ________")

        text(page, 42, 287, "二、竖式计算（共 10 题，请在下方空白处列竖式）", 14)
        for index, (left, right) in enumerate(written):
            row, column = divmod(index, 2)
            text(page, 42 + column * 263, 316 + row * 98,
                 f"{index + 11}.  {left} × {right} =")

        page = new_page(document, "参考答案", 2)
        text(page, 42, 111, "一、口算", 14)
        for index, (left, right) in enumerate(oral):
            row, column = divmod(index, 2)
            text(page, 42 + column * 263, 143 + row * 31,
                 f"{index + 1}.  {left} × {right} = {left * right}")

        text(page, 42, 330, "二、竖式计算", 14)
        for index, (left, right) in enumerate(written):
            row, column = divmod(index, 2)
            text(page, 42 + column * 263, 362 + row * 31,
                 f"{index + 11}.  {left} × {right} = {left * right}")
        document.subset_fonts()
        document.save(str(output), garbage=4, deflate=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("output/multiplication_grade4.pdf"),
                        help="输出 PDF 路径（默认：output/multiplication_grade4.pdf）")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子；相同种子生成相同题目（默认：每次随机）")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".pdf":
        parser.error("--output 必须是以 .pdf 结尾的文件路径")
    oral, written = generate_problems(random.Random(args.seed))
    write_pdf(args.output, oral, written)
    print(f"已生成：{args.output.resolve()}")


if __name__ == "__main__":
    main()

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
    """口算均为三位数乘两位数；竖式各含五道三位数和四位数题。全卷不重复。"""
    used: set[Problem] = set()
    groups: list[list[Problem]] = []
    for oral in (True, False):
        problems: list[Problem] = []
        for digits, count in (((3, 10),) if oral else ((3, 5), (4, 5))):
            lower, upper = 10 ** (digits - 1), 10**digits - 1
            selected = 0
            while selected < count:
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


def new_page(document: pymupdf.Document, title: str | None, number: int,
             copy_number: int | None = None) -> pymupdf.Page:
    page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    page.insert_font(fontname="worksheet", fontbuffer=FONT.buffer)
    if title:
        title_x = (PAGE_WIDTH - FONT.text_length(title, fontsize=19)) / 2
        text(page, title_x, 45, title, 19)
        text(page, 42, 69, "四年级上册 · 多位数乘两位数", 11)
    text(page, PAGE_WIDTH / 2 - 25, PAGE_HEIGHT - 23, f"第 {number} 页", 10)
    if copy_number is not None:
        text(page, 42, PAGE_HEIGHT - 23, f"第 {copy_number} 份", 10)
    return page


def write_pdf(output: Path,
              worksheets: list[tuple[list[Problem], list[Problem]]]) -> None:
    """各份题目在前、对应答案在后，每份各占一页。"""
    if not worksheets:
        raise ValueError("至少需要一份试卷")
    output.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        document.set_metadata({"title": "多位数乘两位数练习", "author": "homework"})
        for copy_number, (oral, written) in enumerate(worksheets, 1):
            label = copy_number if len(worksheets) > 1 else None
            page = new_page(document, None, copy_number, label)
            text(page, 42, 45, "一、口算（共 10 题，直接写出得数）", 14)
            for index, (left, right) in enumerate(oral):
                row, column = divmod(index, 2)
                text(page, 42 + column * 263, 72 + row * 25,
                     f"{index + 1}.  {left} × {right} = ________")

            text(page, 42, 207, "二、竖式计算（共 10 题，请在下方空白处列竖式）", 14)
            for index, (left, right) in enumerate(written):
                row, column = divmod(index, 2)
                text(page, 42 + column * 263, 236 + row * 98,
                     f"{index + 11}.  {left} × {right} =")

        for copy_number, (oral, written) in enumerate(worksheets, 1):
            label = copy_number if len(worksheets) > 1 else None
            page = new_page(document, "参考答案", len(worksheets) + copy_number, label)
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
    parser.add_argument("--copies", type=int, default=1,
                        help="生成份数，须为正整数；各份题目在前、答案在后（默认：1）")
    args = parser.parse_args()
    if args.copies < 1:
        parser.error("--copies 必须是正整数")
    if args.output.suffix.lower() != ".pdf":
        parser.error("--output 必须是以 .pdf 结尾的文件路径")
    rng = random.Random(args.seed)
    worksheets = [generate_problems(rng) for _ in range(args.copies)]
    write_pdf(args.output, worksheets)
    print(f"已生成：{args.output.resolve()}")


if __name__ == "__main__":
    main()

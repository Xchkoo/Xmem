import { describe, expect, it } from "vitest";
import { toPlainTextFromMarkdown } from "../../src/utils/markdown";

describe("toPlainTextFromMarkdown", () => {
  it("会移除常见 markdown 语法并保留可读文本", () => {
    const md = [
      "# 标题",
      "",
      "> 引用",
      "",
      "- *斜体* 与 **加粗**",
      "",
      "链接: [Google](https://google.com)",
      "",
      "图片: ![alt](https://img)",
      "",
      "行内代码: `const x = 1`",
      "",
      "```ts",
      "console.log('x')",
      "```",
    ].join("\n");

    const text = toPlainTextFromMarkdown(md);
    expect(text).toContain("标题");
    expect(text).toContain("引用");
    expect(text).toContain("斜体 与 加粗");
    expect(text).toContain("链接: Google");
    expect(text).toContain("行内代码: const x = 1");
    expect(text).not.toContain("http");
    expect(text).not.toContain("```");
    expect(text).not.toContain("console.log");
  });
});


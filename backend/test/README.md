# 测试说明

## 运行测试

### 安装测试依赖

```bash
cd backend
uv sync
```

### 运行所有测试

```bash
uv run pytest
```

### 运行 OCR 测试

```bash
uv run pytest test/test_ocr.py -v
```

### 运行特定测试类

```bash
uv run pytest test/test_ocr.py::TestOCRLocal -v
```

### 运行特定测试方法

```bash
uv run pytest test/test_ocr.py::TestOCRLocal::test_extract_text_from_image_local_with_valid_image -v
```

## 测试覆盖率

生成测试覆盖率报告：

```bash
uv run pytest --cov=app --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试图片准备

1. 将测试图片放在 `backend/test/img/` 目录中
2. 支持的格式：`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.gif`
3. 建议准备包含文本的图片用于测试

## 前置要求

### 本地 OCR 测试

- 安装 Tesseract OCR：
  - Windows: 下载安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim`
  - macOS: `brew install tesseract tesseract-lang`

- 配置环境变量（可选）：
  ```env
  TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```

### 远程 OCR 测试

- 配置远程 OCR API（待实现）：
  ```env
  OCR_PROVIDER=remote
  OCR_API_URL=https://your-ocr-api.com
  OCR_API_KEY=your-api-key
  ```

## 测试结构

- `test_ocr.py` - OCR 功能测试
- `conftest.py` - Pytest 配置和共享 fixtures
- `img/` - 测试图片目录

## 注意事项

- 如果 Tesseract 未安装或配置错误，相关测试会被跳过
- 如果测试图片不存在，相关测试会被跳过
- 测试不会修改实际的生产数据


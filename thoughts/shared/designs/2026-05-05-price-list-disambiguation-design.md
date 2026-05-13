# Price List Disambiguation — Design Document

**Date:** 2026-05-05  
**Status:** Draft  
**Bug ID:** LLM mixes service names and prices across adjacent bullet items  
**Target file:** `backend/agents/response_agent.py` — `_format_context()` method  
**Scope:** Context formatting only; no changes to search, chunking, or prompts

---

## 1. Problem Statement

### 1.1 The Bug

When the LLM receives a markdown bullet list of priced services, it treats the list as a flat "bag of tokens" and cross-contaminates service names with prices from different rows.

**Concrete example:**

```
## Отдельные услуги

- Фактическое присоединение кабеля...: **6 000 руб.**
- Фактическое присоединение ответвления...: **8 000 руб.**
- Выезд бригады ООО «Башкирэнерго» для допуска персонала...: **5 000 руб.**
- Монтаж ответвления...: **200 руб.**
- Выезд бригады для оказания услуг: **6 000 руб.**
```

**User asks:** "Стоимость услуги «Выезд бригады ООО «Башкирэнерго» для оказания услуг»?"

**Model answer:** "6 000 рублей" — mixing "Выезд бригады ООО «Башкирэнерго»" (from item 3, which costs 5 000) with "для оказания услуг: 6 000 руб." (from item 5).

**Correct answer:** There is no service called "Выезд бригады ООО «Башкирэнерго» для оказания услуг". The user conflated two different services. Item 3 costs 5 000 руб. (допуск персонала), item 5 costs 6 000 руб. (оказание услуг without ООО).

### 1.2 Root Cause

Markdown bullet lists lack explicit structural boundaries between items. The LLM's attention mechanism treats adjacent list items as continuous text, making it easy to associate a service name from one item with a price from another.

### 1.3 Why This Matters

This is a **hallucination with real operational consequences**. A customer who receives the wrong price for a service may file incorrect applications, dispute bills, or lose trust in the system. The Башкирэнерго domain is safety-critical: wrong procedure advice has real-world impact.

---

## 2. Solution Overview

Reformat detected price lists from bullet format into markdown tables **before** they reach the LLM. Tables enforce a strict row-column structure that makes cross-contamination nearly impossible.

**Before (bug-prone):**
```markdown
- Фактическое присоединение кабеля...: **6 000 руб.**
- Выезд бригады ООО «Башкирэнерго» для допуска персонала...: **5 000 руб.**
- Выезд бригады для оказания услуг: **6 000 руб.**
```

**After (safe):**
```markdown
⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.

| Услуга | Стоимость |
|---|---|
| Фактическое присоединение кабеля... | 6 000 руб. |
| Выезд бригады ООО «Башкирэнерго» для допуска персонала... | 5 000 руб. |
| Выезд бригады для оказания услуг | 6 000 руб. |
```

Each table row is a self-contained unit. The LLM cannot accidentally merge cells across rows.

---

## 3. Detection Algorithm

### 3.1 When to Trigger Reformatting

The reformatting triggers **only** when a chunk's content contains a markdown bullet list that qualifies as a "price list". A price list is defined conservatively:

**A chunk qualifies for reformatting when ALL of the following are true:**

1. **Has a bullet list block**: The content contains 2+ consecutive lines starting with `- ` (dash-space) that form a contiguous block (no intervening non-bullet lines).
2. **Contains multiple price patterns**: At least 2 bullet items in the block match the price pattern `\*\*\d[\d\s]*руб\.?\*\*` (bold number ending in "руб.").
3. **Price pattern is at the end of items**: The price appears at or near the end of the bullet text (after a colon, dash, or as the final bold element). This distinguishes a price list from a paragraph that happens to mention prices.

**Why "at least 2 prices"?** A single price in a list is not a price list — it's just a list that mentions a price. The bug only manifests when there are multiple prices the LLM could cross-contaminate.

### 3.2 Price Pattern Regex

```python
PRICE_PATTERN = re.compile(
    r'\*\*'                    # opening bold
    r'(\d[\d\s]*)'             # digits with optional spaces (e.g., "6 000", "200")
    r'\s*руб\.?'               # "руб" or "руб."
    r'\*\*'                    # closing bold
)
```

This matches:
- `**6 000 руб.**` ✓
- `**200 руб.**` ✓
- `**15 000 руб**` ✓
- `**1 500 000 руб.**` ✓

This does NOT match:
- `6 000 руб.` (not bold) — we only reformat lists where prices are bolded, which is the pattern in our knowledge base
- `**6 000**` (missing "руб") — not a price, just a number

### 3.3 Detection Pseudocode

```python
def _is_price_list(content: str) -> bool:
    """
    Returns True if content contains a bullet list block that qualifies
    as a price list (2+ items with bold prices at the end).
    """
    lines = content.split('\n')
    
    # Find contiguous bullet blocks
    bullet_blocks = _extract_bullet_blocks(lines)
    
    for block in bullet_blocks:
        if len(block) < 2:
            continue
        
        price_count = 0
        for item_text in block:
            # Strip the leading "- " and check if price is at the end
            stripped = item_text.lstrip('- ').strip()
            match = PRICE_PATTERN.search(stripped)
            if match and _price_at_end(stripped, match):
                price_count += 1
        
        if price_count >= 2:
            return True
    
    return False
```

### 3.4 `_price_at_end()` Heuristic

A price is "at the end" of a bullet item if:
- The price match ends within the last 30% of the item's text length, OR
- The item follows the pattern `...: **X руб.**` (colon before price), OR
- The item follows the pattern `... — **X руб.**` (em-dash before price)

This prevents false positives where a price appears mid-sentence (e.g., "В 2023 году было подключено **5 000 руб.** клиентов, что больше...").

---

## 4. Parsing Logic

### 4.1 Extracting Bullet Blocks

A "bullet block" is a maximal sequence of consecutive lines where each line either:
- Starts with `- ` (a bullet item), or
- Is a continuation line (indented, part of a multi-line bullet item)

```python
def _extract_bullet_blocks(lines: list[str]) -> list[list[str]]:
    """
    Group consecutive bullet lines into blocks.
    A block ends when a non-bullet, non-continuation line is encountered.
    """
    blocks = []
    current_block = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            current_block.append(stripped)
        elif current_block and (stripped == '' or _is_continuation(line)):
            # Empty line or continuation within a bullet block
            # End the current block
            if stripped == '':
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                # Append continuation to last item
                current_block[-1] += ' ' + stripped
        else:
            if current_block:
                blocks.append(current_block)
                current_block = []
    
    if current_block:
        blocks.append(current_block)
    
    return blocks
```

### 4.2 Splitting a Bullet Item into Service Name and Price

Each bullet item follows one of these patterns:

| Pattern | Example | Parsing Rule |
|---------|---------|-------------|
| `Service: **Price**` | `- Монтаж ответвления: **200 руб.**` | Split on last `: ` before price |
| `Service — **Price**` | `- Услуга — **5 000 руб.**` | Split on last ` — ` before price |
| `Service **Price**` | `- Выезд бригады **6 000 руб.**` | Split on price match boundary |

```python
def _parse_bullet_item(item: str) -> tuple[str, str] | None:
    """
    Parse a bullet item into (service_name, price_text).
    Returns None if the item doesn't contain a price.
    
    Input: "- Монтаж ответвления: **200 руб.**"
    Output: ("Монтаж ответвления", "200 руб.")
    """
    # Remove leading "- "
    text = item.lstrip('- ').strip()
    
    # Find the price pattern
    match = PRICE_PATTERN.search(text)
    if not match:
        return None
    
    # Verify price is at the end
    if not _price_at_end(text, match):
        return None
    
    price_text = match.group(1).strip() + ' руб.'
    # Remove the bold price from the text to get the service name
    service_name = text[:match.start()].strip()
    
    # Clean up separators at the end of service name
    service_name = service_name.rstrip(':').rstrip('—').rstrip('-').strip()
    
    if not service_name:
        return None
    
    return (service_name, price_text)
```

### 4.3 Handling Multi-line Bullet Items

Some bullet items span multiple lines:

```markdown
- Фактическое присоединение кабеля 
  кабельного типа напряжением до 1 кВ: **6 000 руб.**
```

**Strategy:** Pre-process multi-line items by joining continuation lines (indented lines following a bullet) into the parent bullet item before parsing. This is handled in `_extract_bullet_blocks()` above — continuation lines are appended to the last bullet item.

### 4.4 Handling Nested Bullets

Nested bullets (sub-lists) are common:

```markdown
- Услуги по подключению:
  - Подключение до 15 кВт: **5 000 руб.**
  - Подключение от 15 до 150 кВт: **15 000 руб.**
```

**Strategy:** 
- Only reformat the **innermost** bullet level that contains prices.
- If a parent bullet has no price but its children do, treat the parent as a section header and reformat the children as a table.
- If both parent and children have prices, reformat the entire block as a single table (flattened).

For the initial implementation, we handle the **simple case**: a flat bullet list with prices. Nested lists are left as-is (conservative approach). The detection algorithm only triggers on flat lists.

### 4.5 Handling Items Without Prices

A bullet list may contain items without prices mixed with priced items:

```markdown
## Отдельные услуги

- Фактическое присоединение кабеля: **6 000 руб.**
- Примечание: стоимость может варьироваться
- Выезд бригады: **5 000 руб.**
```

**Strategy:** Items without prices are included in the table with "—" (em-dash) in the Стоимость column. This preserves the complete list while making the structure explicit.

---

## 5. Table Generation Logic

### 5.1 Transformation Pipeline

```
Input: chunk content (string)
  │
  ├─ 1. Detect if content contains a price list
  │     └─ If NO → return content unchanged
  │
  ├─ 2. Extract bullet blocks from content
  │
  ├─ 3. For each bullet block that is a price list:
  │     ├─ Parse each item into (service_name, price_text) or (service_name, "—")
  │     ├─ Generate markdown table
  │     └─ Replace original bullet block with table + disambiguation note
  │
  └─ 4. Return transformed content
```

### 5.2 Table Format

```markdown
⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.

| Услуга | Стоимость |
|---|---|
| Фактическое присоединение кабеля... | 6 000 руб. |
| Фактическое присоединение ответвления... | 8 000 руб. |
| Выезд бригады ООО «Башкирэнерго» для допуска персонала... | 5 000 руб. |
| Монтаж ответвления... | 200 руб. |
| Выезд бригады для оказания услуг | 6 000 руб. |
```

### 5.3 Disambiguation Note

The note is placed **immediately before** the table, not at the top of the chunk. This ensures the LLM reads it right before processing the price data.

**Text:** `⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.`

**Rationale for the note:**
- "отдельные услуги" — emphasizes each row is a separate service
- "точными ценами" — emphasizes prices are exact, not approximate
- "Не смешивай название услуги из одной строки с ценой из другой" — explicit instruction against the exact bug pattern

### 5.4 Section Header Preservation

If the bullet list has a preceding header (e.g., `## Отдельные услуги`), it is preserved above the disambiguation note:

```markdown
## Отдельные услуги

⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.

| Услуга | Стоимость |
|---|---|
| ... | ... |
```

### 5.5 Multiple Price Lists in One Chunk

A chunk may contain multiple price list blocks separated by other content. Each block is detected and reformatted independently.

---

## 6. Integration Point: `_format_context()`

### 6.1 Current Code (lines 262-281)

```python
def _format_context(self, results: List[SearchResult]) -> str:
    """Форматирование контекста из результатов поиска."""
    if not results:
        return "Контекст: информация не найдена."

    parts = []
    for i, result in enumerate(results[:10], 1):
        # Исправляем LaTeX формулы в контенте источника
        fixed_content = fix_latex_in_text(result.content)
        
        part = (
            f"[src_{i}]\n"
            f"Файл: {result.filename}\n"
            f"Раздел: {result.breadcrumbs}\n"
            f"Категория: {result.category if result.category else 'не указана'}\n"
            f"Текст:\n{fixed_content}\n"
        )
        parts.append(part)

    return "\n---\n".join(parts)
```

### 6.2 Proposed Change

Add a single processing step between `fix_latex_in_text()` and the string formatting. The new function `_disambiguate_price_lists()` is called on `fixed_content` before it goes into the `part` string.

```python
def _format_context(self, results: List[SearchResult]) -> str:
    """Форматирование контекста из результатов поиска."""
    if not results:
        return "Контекст: информация не найдена."

    parts = []
    for i, result in enumerate(results[:10], 1):
        # Исправляем LaTeX формулы в контенте источника
        fixed_content = fix_latex_in_text(result.content)
        
        # NEW: Reformat price lists into tables to prevent cross-contamination
        fixed_content = _disambiguate_price_lists(fixed_content)
        
        part = (
            f"[src_{i}]\n"
            f"Файл: {result.filename}\n"
            f"Раздел: {result.breadcrumbs}\n"
            f"Категория: {result.category if result.category else 'не указана'}\n"
            f"Текст:\n{fixed_content}\n"
        )
        parts.append(part)

    return "\n---\n".join(parts)
```

### 6.3 Why This Location

1. **After `fix_latex_in_text()`** — LaTeX fixes happen first; price list disambiguation operates on the already-fixed text.
2. **Before string formatting** — The transformation happens on the content string, before it's wrapped in the `[src_N]` envelope. This keeps the transformation pure (string → string) and testable.
3. **Per-result, not per-context** — Each search result is processed independently. This is correct because each result is a separate chunk from Qdrant.

### 6.4 New Module Location

The price list disambiguation logic will live in a new module:

**File:** `backend/agents/price_list_formatter.py`

This keeps the logic isolated, testable, and separate from the response agent. The `_format_context()` method imports and calls the single public function `_disambiguate_price_lists()`.

---

## 7. Detailed Algorithm

### 7.1 Main Function: `_disambiguate_price_lists(content: str) -> str`

```python
def _disambiguate_price_lists(content: str) -> str:
    """
    Detect price lists in markdown content and reformat them
    as tables to prevent LLM cross-contamination of service
    names and prices.
    
    Conservative: only reformats bullet lists that contain
    2+ items with bold prices at the end.
    
    Args:
        content: Raw markdown content from a search result chunk
        
    Returns:
        Content with price lists reformatted as tables,
        or original content if no price lists detected
    """
    if not content:
        return content
    
    lines = content.split('\n')
    bullet_blocks = _extract_bullet_blocks(lines)
    
    # Check if any block qualifies as a price list
    has_price_list = False
    for block in bullet_blocks:
        if _is_block_price_list(block):
            has_price_list = True
            break
    
    if not has_price_list:
        return content
    
    # Transform each qualifying block
    result_lines = lines.copy()
    for block in bullet_blocks:
        if not _is_block_price_list(block):
            continue
        
        # Find the line range of this block in the original content
        block_start, block_end = _find_block_range(lines, block)
        if block_start is None:
            continue
        
        # Parse items into (service, price) pairs
        table_rows = []
        for item in block:
            parsed = _parse_bullet_item(item)
            if parsed:
                table_rows.append(parsed)
            else:
                # Item without price — include with dash
                service = item.lstrip('- ').strip()
                # Remove trailing colon/dash if present
                service = service.rstrip(':').rstrip('—').rstrip('-').strip()
                if service:
                    table_rows.append((service, '—'))
        
        if len(table_rows) < 2:
            continue  # Don't create a 1-row table
        
        # Generate table markdown
        table_md = _generate_price_table(table_rows)
        
        # Check for preceding header to insert note after it
        header_line = _find_preceding_header(lines, block_start)
        
        # Build replacement text
        replacement = _build_replacement(table_md, header_line)
        
        # Replace in result_lines
        # (This requires careful index management — see implementation notes)
        result_lines = _replace_block(result_lines, block_start, block_end, replacement)
    
    return '\n'.join(result_lines)
```

### 7.2 Block Detection: `_is_block_price_list(block: list[str]) -> bool`

```python
def _is_block_price_list(block: list[str]) -> bool:
    """
    Returns True if a bullet block qualifies as a price list.
    A price list has 2+ items with bold prices at the end.
    """
    if len(block) < 2:
        return False
    
    price_count = 0
    for item in block:
        text = item.lstrip('- ').strip()
        match = PRICE_PATTERN.search(text)
        if match and _price_at_end(text, match):
            price_count += 1
    
    return price_count >= 2
```

### 7.3 Price-at-End Check: `_price_at_end(text: str, match: re.Match) -> bool`

```python
def _price_at_end(text: str, match: re.Match) -> bool:
    """
    Returns True if the price pattern appears at or near the end
    of the text, indicating it's a price tag rather than a
    number mentioned mid-sentence.
    """
    # Price must end within the last 30% of the text
    price_end = match.end()
    text_len = len(text)
    
    if text_len == 0:
        return False
    
    # Allow price to be in the last 30% of the text
    threshold = int(text_len * 0.7)
    return price_end >= threshold
```

### 7.4 Table Generation: `_generate_price_table(rows: list[tuple[str, str]]) -> str`

```python
def _generate_price_table(rows: list[tuple[str, str]]) -> str:
    """
    Generate a markdown table from (service, price) pairs.
    
    Args:
        rows: List of (service_name, price_text) tuples
        
    Returns:
        Markdown table string
    """
    lines = []
    lines.append('| Услуга | Стоимость |')
    lines.append('|---|---|')
    for service, price in rows:
        # Escape pipe characters in service names
        service_escaped = service.replace('|', '\\|')
        lines.append(f'| {service_escaped} | {price} |')
    return '\n'.join(lines)
```

### 7.5 Replacement Builder: `_build_replacement(table_md: str, header_line: str | None) -> str`

```python
DISAMBIGUATION_NOTE = (
    "⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. "
    "Не смешивай название услуги из одной строки с ценой из другой."
)

def _build_replacement(table_md: str, header_line: str | None) -> str:
    """
    Build the replacement text: note + table, optionally with
    a preceding header preserved.
    """
    parts = []
    if header_line:
        parts.append(header_line)
        parts.append('')  # blank line after header
    parts.append(DISAMBIGUATION_NOTE)
    parts.append('')
    parts.append(table_md)
    return '\n'.join(parts)
```

---

## 8. Edge Cases

| Edge Case | Behavior | Rationale |
|-----------|----------|-----------|
| **Single-price list** (1 item with price) | NOT reformatted | A single price cannot be cross-contaminated; table format adds no value |
| **No prices in list** | NOT reformatted | Not a price list |
| **Price mid-sentence** ("В **5 000 руб.** обойдётся...") | NOT detected as price-at-end | The `_price_at_end()` heuristic rejects it |
| **Mixed list** (some items with prices, some without) | Reformatted; items without prices get "—" in Стоимость column | Preserves completeness while enforcing structure |
| **Nested bullets** (sub-lists) | Only the innermost level with prices is reformatted | Conservative: don't flatten structure the LLM might need |
| **Multiple price lists in one chunk** | Each is reformatted independently | Correct — each block is processed separately |
| **Price with decimal** ("**5 000,50 руб.**") | Supported by regex | The pattern `\d[\d\s]*` handles spaces in numbers |
| **Price without bold** ("5 000 руб.") | NOT detected | Only bold prices are reformatted; this matches our knowledge base format |
| **Empty content** | Returns empty string unchanged | No processing needed |
| **Content with no bullet lists** | Returns content unchanged | Conservative: only transform what we detect |
| **Table already present** | No transformation (bullet detection won't trigger) | Tables are already safe |
| **Pipe character in service name** | Escaped as `\|` in table | Prevents markdown table breakage |
| **Very long service names** | Included as-is in table | No truncation — accuracy over formatting |
| **Multi-line bullet items** | Continuation lines joined to parent item | Handled in `_extract_bullet_blocks()` |

---

## 9. Test Cases

### 9.1 Primary Bug Case — Before/After

**Input (the exact bug scenario):**
```markdown
## Отдельные услуги

- Фактическое присоединение кабеля кабельного типа напряжением до 1 кВ: **6 000 руб.**
- Фактическое присоединение ответвления от воздушной линии напряжением до 1 кВ: **8 000 руб.**
- Выезд бригады ООО «Башкирэнерго» для допуска персонала: **5 000 руб.**
- Монтаж ответвления от воздушной линии: **200 руб.**
- Выезд бригады для оказания услуг: **6 000 руб.**
```

**Expected output:**
```markdown
## Отдельные услуги

⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.

| Услуга | Стоимость |
|---|---|
| Фактическое присоединение кабеля кабельного типа напряжением до 1 кВ | 6 000 руб. |
| Фактическое присоединение ответвления от воздушной линии напряжением до 1 кВ | 8 000 руб. |
| Выезд бригады ООО «Башкирэнерго» для допуска персонала | 5 000 руб. |
| Монтаж ответвления от воздушной линии | 200 руб. |
| Выезд бригады для оказания услуг | 6 000 руб. |
```

**Why this fixes the bug:** The LLM now sees each service-price pair as a table row. The disambiguation note explicitly warns against cross-row contamination. The service "Выезд бригады ООО «Башкирэнерго» для допуска персонала" is unambiguously paired with "5 000 руб." in the same row, making it impossible to accidentally combine with "6 000 руб." from a different row.

### 9.2 No Price List — Pass Through

**Input:**
```markdown
## Процесс подключения

Для подключения необходимо:
- Подать заявку через личный кабинет
- Предоставить документы
- Дождаться технических условий
```

**Expected output:** Unchanged (no prices detected).

### 9.3 Single Price — No Table

**Input:**
```markdown
Стоимость подключения:
- Плата за подключение: **15 000 руб.**
```

**Expected output:** Unchanged (only 1 price, below threshold of 2).

### 9.4 Mixed List — Items Without Prices

**Input:**
```markdown
## Услуги

- Консультация бесплатная
- Подключение до 15 кВт: **5 000 руб.**
- Подключение от 15 до 150 кВт: **15 000 руб.**
```

**Expected output:**
```markdown
## Услуги

⚠️ Внимание: ниже перечислены отдельные услуги с точными ценами. Не смешивай название услуги из одной строки с ценой из другой.

| Услуга | Стоимость |
|---|---|
| Консультация бесплатная | — |
| Подключение до 15 кВт | 5 000 руб. |
| Подключение от 15 до 150 кВт | 15 000 руб. |
```

### 9.5 Price Mid-Sentence — Not Detected

**Input:**
```markdown
В 2023 году было подключено **5 000 руб.** клиентов, что больше показателя прошлого года.
```

**Expected output:** Unchanged (no bullet list, no price-at-end pattern).

### 9.6 Multiple Price Lists in One Chunk

**Input:**
```markdown
## Услуги подключения

- Подключение до 15 кВт: **5 000 руб.**
- Подключение от 15 до 150 кВт: **15 000 руб.**

Некоторые дополнительные услуги:

- Выезд бригады: **6 000 руб.**
- Монтаж: **200 руб.**
```

**Expected output:** Both bullet blocks are independently detected and reformatted into separate tables, each with its own disambiguation note.

### 9.7 Empty Content

**Input:** `""`

**Expected output:** `""`

### 9.8 Already a Table — No Transformation

**Input:**
```markdown
| Услуга | Стоимость |
|---|---|
| Подключение | 5 000 руб. |
```

**Expected output:** Unchanged (no bullet list detected).

---

## 10. File Structure

### 10.1 New File: `backend/agents/price_list_formatter.py`

Contains all price list disambiguation logic:
- `PRICE_PATTERN` — compiled regex for bold price detection
- `_disambiguate_price_lists(content: str) -> str` — main entry point
- `_extract_bullet_blocks(lines: list[str]) -> list[list[str]]` — block extraction
- `_is_block_price_list(block: list[str]) -> bool` — detection
- `_price_at_end(text: str, match: re.Match) -> bool` — position heuristic
- `_parse_bullet_item(item: str) -> tuple[str, str] | None` — item parsing
- `_generate_price_table(rows: list[tuple[str, str]]) -> str` — table generation
- `_build_replacement(table_md: str, header_line: str | None) -> str` — replacement builder
- `_find_block_range(lines: list[str], block: list[str]) -> tuple[int, int]` — line range finder
- `_find_preceding_header(lines: list[str], block_start: int) -> str | None` — header detection
- `_replace_block(lines: list[str], start: int, end: int, replacement: str) -> list[str]` — line replacement
- `DISAMBIGUATION_NOTE` — constant for the warning text

### 10.2 Modified File: `backend/agents/response_agent.py`

Single change in `_format_context()`:
- Add import: `from agents.price_list_formatter import _disambiguate_price_lists`
- Add line after `fix_latex_in_text()`: `fixed_content = _disambiguate_price_lists(fixed_content)`

### 10.3 New Test File: `backend/tests/test_price_list_formatter.py`

Comprehensive unit tests covering all edge cases from Section 9.

---

## 11. Performance Considerations

| Concern | Assessment |
|---------|------------|
| **Regex performance** | `PRICE_PATTERN` is a simple regex applied per line. O(n) where n is content length. Negligible. |
| **Memory** | No large data structures. Lines are split and joined — O(n) memory where n is content size. |
| **Latency** | Processing is synchronous and runs per-chunk (max 10 chunks). Expected <1ms per chunk. |
| **False positives** | Conservative detection (2+ prices, price-at-end, bold-only) minimizes false positives. |
| **False negatives** | Only bullet lists with bold prices are reformatted. Other formats (numbered lists, plain text) are not affected. This is acceptable — the bug manifests specifically in bullet lists. |

---

## 12. Rollout Plan

### Phase 1: Implementation (this PR)
- Create `backend/agents/price_list_formatter.py` with all logic
- Add import and call in `response_agent.py`
- Add comprehensive unit tests in `backend/tests/test_price_list_formatter.py`
- Add test for `_format_context()` integration in existing `test_agent.py`

### Phase 2: Validation
- Run existing benchmark (`api_benchmarks/`) with the new formatter
- Compare `hallucination_risk` scores before/after
- Specifically test queries about service prices from the benchmark dataset

### Phase 3: Monitoring
- Add logging in `_disambiguate_price_lists()` to track how often reformatting triggers
- Monitor for any unexpected transformations (false positives)

---

## 13. Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| **Prompt engineering** (add instruction to system prompt) | Prompts are frozen per project constraints. Even if not frozen, LLMs still struggle with structural boundaries in context — a prompt can't reliably prevent cross-contamination. |
| **Chunking-level fix** (reformat during ingestion) | Would require re-ingesting all data. The fix belongs at the presentation layer because the same chunk might need different formatting for different use cases. |
| **XML/JSON wrapping** (wrap each item in `<item>` tags) | Adds more tokens than a table. Tables are a native markdown construct that LLMs handle well. |
| **Numbered list** (replace `- ` with `1. `) | Doesn't solve the core problem — LLMs still treat numbered lists as a bag of tokens. The issue is the lack of row-column structure, not the bullet style. |
| **Separator lines** (add `---` between items) | Increases token count significantly for long lists. Tables are more compact and provide stronger structural guarantees. |
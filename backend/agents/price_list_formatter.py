"""
Price List Disambiguation Formatter

Reformats markdown bullet lists containing priced services into markdown tables
to prevent LLM cross-contamination of service names and prices.

Conservative: only reformats bullet lists with 2+ items containing bold prices at the end.
"""
import re

class BulletBlock(list):
    """A list of bullet items that also carries the original line range."""
    def __init__(self, items, start_index, end_index):
        super().__init__(items)
        self.start_index = start_index
        self.end_index = end_index


# Compiled regex for bold price detection: **\d[\d\s]*\s*руб\.?\*\*
PRICE_PATTERN = re.compile(
    r'\*\*'                    # opening bold
    r'(\d+(?:\s+\d+)*)'       # digits with optional spaces (e.g., "6 000", "200")
    r'\s*руб\.?'              # "руб" or "руб."
    r'\*\*'                    # closing bold
)

DISAMBIGUATION_NOTE = (
    "\u26a0\ufe0f Внимание: ниже перечислены отдельные услуги с точными ценами. "
    "Не смешивай название услуги из одной строки с ценой из другой."
)


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
    has_price_list = any(_is_block_price_list(block) for block in bullet_blocks)
    
    if not has_price_list:
        return content
    
    # Transform each qualifying block
    result_lines = list(lines)  # make a mutable copy
    
    # Process blocks in reverse order to preserve line indices
    blocks_with_ranges = []
    for block in bullet_blocks:
        if _is_block_price_list(block):
            blocks_with_ranges.append((block.start_index, block.end_index, block))
    
    # Process from bottom to top to avoid index shifting
    for block_start, block_end, block in reversed(blocks_with_ranges):
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
        result_lines[block_start:block_end + 1] = replacement.split('\n')
    
    return '\n'.join(result_lines)


def _extract_bullet_blocks(lines: list) -> list:
    """
    Group consecutive bullet lines into blocks.
    Each block is a BulletBlock (list subclass) containing joined bullet items
    plus start_index/end_index tracking the original line range.
    A block ends when a non-bullet, non-continuation line is encountered.
    """
    blocks = []
    current_block = []
    current_start = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('- '):
            # New bullet item
            if not current_block:
                current_start = i
            current_block.append(line)
        elif current_block and _is_continuation(line):
            # Continuation line (indented text belonging to previous bullet)
            current_block[-1] = current_block[-1] + ' ' + stripped
        else:
            # End of block
            if current_block:
                blocks.append(BulletBlock(current_block, current_start, i - 1))
                current_block = []
                current_start = None
    
    if current_block:
        blocks.append(BulletBlock(current_block, current_start, len(lines) - 1))
    
    return blocks


def _is_continuation(line: str) -> bool:
    """
    Returns True if the line is a continuation of a bullet item
    (indented but not starting with '- ').
    """
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith('- '):
        return False
    # Check if the original line is indented (starts with spaces)
    return len(line) - len(line.lstrip(' ')) >= 2


def _is_block_price_list(block: list) -> bool:
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


def _price_at_end(text: str, match: re.Match) -> bool:
    """
    Returns True if the price pattern appears at or near the end
    of the text, indicating it's a price tag rather than a
    number mentioned mid-sentence.
    
    Uses 30% threshold: price must end within the last 30% of the text.
    """
    price_end = match.end()
    text_len = len(text)
    
    if text_len == 0:
        return False
    
    # Allow price to be in the last 30% of the text
    threshold = int(text_len * 0.7)
    return price_end >= threshold


def _parse_bullet_item(item: str) -> tuple | None:
    """
    Parse a bullet item into (service_name, price_text).
    Returns None if the item doesn't contain a price at the end.
    
    Input: "- Монтаж ответвления: **200 руб.**"
    Output: ("Монтаж ответвления", "200 руб.")
    """
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


def _generate_price_table(rows: list) -> str:
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


def _build_replacement(table_md: str, header_line: str | None) -> str:
    """
    Build the replacement text: note + table, optionally with
    a preceding header preserved.
    """
    parts = []
    if header_line is not None and header_line.strip():
        parts.append(header_line)
        parts.append('')  # blank line after header
    parts.append(DISAMBIGUATION_NOTE)
    parts.append('')
    parts.append(table_md)
    return '\n'.join(parts)


def _find_block_range(lines: list, block: list) -> tuple:
    """
    Find the line range (start, end inclusive) of a bullet block
    within the original lines list.
    
    Returns (start_index, end_index) or (None, None) if not found.
    """
    if not block:
        return (None, None)
    
    # Find the first item of the block in lines
    first_item_stripped = block[0].strip()
    for i, line in enumerate(lines):
        if line.strip() == first_item_stripped:
            return (i, i + len(block) - 1)
    
    return (None, None)


def _find_preceding_header(lines: list, block_start: int) -> str | None:
    """
    Find a markdown header immediately preceding a bullet block.
    Looks for lines starting with '#' within 3 lines above the block.
    
    Returns the header line string, or None if no header found.
    """
    # Search upward from block_start for a header
    for i in range(block_start - 1, max(block_start - 4, -1), -1):
        if i < 0:
            break
        line = lines[i].strip()
        if line.startswith('#'):
            return lines[i]
        if line:  # Non-empty, non-header line blocks upward search
            return None
    return None

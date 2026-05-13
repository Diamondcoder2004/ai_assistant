"""
Tests for price_list_formatter.py — Price List Disambiguation

Covers all test cases from design document sections 9.1-9.8
plus additional edge cases.
"""
import pytest
from agents.price_list_formatter import (
    _disambiguate_price_lists,
    _extract_bullet_blocks,
    _is_block_price_list,
    _price_at_end,
    _parse_bullet_item,
    _generate_price_table,
    _build_replacement,
    _find_preceding_header,
    PRICE_PATTERN,
    DISAMBIGUATION_NOTE,
)
import re


class TestPricePattern:
    """Tests for PRICE_PATTERN regex."""
    
    def test_matches_simple_price(self):
        match = PRICE_PATTERN.search('**200 руб.**')
        assert match is not None
        assert match.group(1) == '200'
    
    def test_matches_price_with_spaces(self):
        match = PRICE_PATTERN.search('**6 000 руб.**')
        assert match is not None
        assert match.group(1) == '6 000'
    
    def test_matches_price_without_dot(self):
        match = PRICE_PATTERN.search('**15 000 руб**')
        assert match is not None
        assert match.group(1) == '15 000'
    
    def test_matches_large_price(self):
        match = PRICE_PATTERN.search('**1 500 000 руб.**')
        assert match is not None
        assert match.group(1) == '1 500 000'
    
    def test_does_not_match_non_bold(self):
        match = PRICE_PATTERN.search('6 000 руб.')
        assert match is None
    
    def test_does_not_match_missing_rub(self):
        match = PRICE_PATTERN.search('**6 000**')
        assert match is None


class TestPriceAtEnd:
    """Tests for _price_at_end() heuristic."""
    
    def test_price_at_end_of_text(self):
        text = 'Монтаж ответвления: **200 руб.**'
        match = PRICE_PATTERN.search(text)
        assert _price_at_end(text, match) is True
    
    def test_price_near_end_of_long_text(self):
        text = 'Фактическое присоединение кабеля кабельного типа напряжением до 1 кВ: **6 000 руб.**'
        match = PRICE_PATTERN.search(text)
        assert _price_at_end(text, match) is True
    
    def test_price_mid_sentence_not_at_end(self):
        text = 'В **5 000 руб.** обойдётся подключение'
        # Move price to beginning so it fails the 30% test
        match = PRICE_PATTERN.search(text)
        # Price is at position 2, ends at ~13, text is ~35 chars
        # 13 < 35*0.7 = 24.5, so it should return False
        assert _price_at_end(text, match) is False
    
    def test_empty_text(self):
        match = PRICE_PATTERN.search('')
        assert match is None


class TestParseBulletItem:
    """Tests for _parse_bullet_item()."""
    
    def test_parse_colon_separator(self):
        result = _parse_bullet_item('- Монтаж ответвления: **200 руб.**')
        assert result == ('Монтаж ответвления', '200 руб.')
    
    def test_parse_em_dash_separator(self):
        result = _parse_bullet_item('- Услуга — **5 000 руб.**')
        assert result == ('Услуга', '5 000 руб.')
    
    def test_parse_no_separator(self):
        result = _parse_bullet_item('- Выезд бригады **6 000 руб.**')
        assert result == ('Выезд бригады', '6 000 руб.')
    
    def test_parse_no_price(self):
        result = _parse_bullet_item('- Консультация бесплатная')
        assert result is None
    
    def test_parse_price_mid_text(self):
        result = _parse_bullet_item('- В **5 000 руб.** обойдётся услуга')
        assert result is None  # Price not at end


class TestGeneratePriceTable:
    """Tests for _generate_price_table()."""
    
    def test_generates_basic_table(self):
        rows = [('Услуга A', '100 руб.'), ('Услуга B', '200 руб.')]
        table = _generate_price_table(rows)
        assert '| Услуга | Стоимость |' in table
        assert '|---|---|' in table
        assert '| Услуга A | 100 руб. |' in table
        assert '| Услуга B | 200 руб. |' in table
    
    def test_escapes_pipe_characters(self):
        rows = [('Услуга с | символом', '100 руб.')]
        table = _generate_price_table(rows)
        assert '| Услуга с \\| символом | 100 руб. |' in table


class TestExtractBulletBlocks:
    """Tests for _extract_bullet_blocks()."""
    
    def test_extracts_simple_block(self):
        lines = ['- Item 1', '- Item 2', '- Item 3', '', 'Normal text']
        blocks = _extract_bullet_blocks(lines)
        assert len(blocks) == 1
        assert len(blocks[0]) == 3
    
    def test_extracts_multiple_blocks(self):
        lines = [
            '- Block 1A',
            '- Block 1B',
            '',
            'Normal text',
            '- Block 2A',
            '- Block 2B',
        ]
        blocks = _extract_bullet_blocks(lines)
        assert len(blocks) == 2
    
    def test_extracts_with_continuation_lines(self):
        lines = [
            '- Item 1',
            '  continuation of item 1',
            '- Item 2',
            '  continuation of item 2',
        ]
        blocks = _extract_bullet_blocks(lines)
        assert len(blocks) == 1
        # Continuations should be joined to previous items
        assert 'continuation of item 1' in blocks[0][0]
        assert 'continuation of item 2' in blocks[0][1]
    
    def test_no_bullet_blocks(self):
        lines = ['Just', 'some', 'normal', 'text']
        blocks = _extract_bullet_blocks(lines)
        assert len(blocks) == 0


class TestIsBlockPriceList:
    """Tests for _is_block_price_list()."""
    
    def test_two_prices_returns_true(self):
        block = [
            '- Услуга A: **100 руб.**',
            '- Услуга B: **200 руб.**',
        ]
        assert _is_block_price_list(block) is True
    
    def test_single_price_returns_false(self):
        block = ['- Услуга A: **100 руб.**']
        assert _is_block_price_list(block) is False
    
    def test_no_prices_returns_false(self):
        block = ['- Item A', '- Item B', '- Item C']
        assert _is_block_price_list(block) is False
    
    def test_one_price_one_without_returns_false(self):
        block = [
            '- Услуга A: **100 руб.**',
            '- Просто услуга',
        ]
        assert _is_block_price_list(block) is False
    
    def test_empty_block_returns_false(self):
        assert _is_block_price_list([]) is False


class TestBuildReplacement:
    """Tests for _build_replacement()."""
    
    def test_with_header(self):
        table_md = '| Услуга | Стоимость |\n|---|---|\n| A | 100 |'
        result = _build_replacement(table_md, '## Отдельные услуги')
        lines = result.split('\n')
        assert lines[0] == '## Отдельные услуги'
        assert lines[1] == ''
        assert lines[2] == DISAMBIGUATION_NOTE
        assert lines[3] == ''
    
    def test_without_header(self):
        table_md = '| Услуга | Стоимость |\n|---|---|\n| A | 100 |'
        result = _build_replacement(table_md, None)
        lines = result.split('\n')
        assert lines[0] == DISAMBIGUATION_NOTE
        assert lines[1] == ''


class TestFindPrecedingHeader:
    """Tests for _find_preceding_header()."""
    
    def test_finds_header_immediately_before(self):
        lines = ['## Услуги', '', '- Item 1: **100 руб.**', '- Item 2: **200 руб.**']
        header = _find_preceding_header(lines, 2)
        assert header == '## Услуги'
    
    def test_no_header_before_block(self):
        lines = ['Some text', '- Item 1: **100 руб.**', '- Item 2: **200 руб.**']
        header = _find_preceding_header(lines, 1)
        assert header is None
    
    def test_header_too_far_away(self):
        lines = ['## Услуги', '', 'Some text', '', '- Item 1: **100 руб.**', '- Item 2: **200 руб.**']
        header = _find_preceding_header(lines, 4)
        assert header is None  # Non-empty line between header and block


class TestDisambiguatePriceLists:
    """Integration tests for _disambiguate_price_lists() covering design doc test cases 9.1-9.8."""
    
    # Test 9.1: Primary Bug Case
    def test_9_1_primary_bug_case(self):
        """The exact bug scenario from the design doc."""
        input_text = """## Отдельные услуги

- Фактическое присоединение кабеля кабельного типа напряжением до 1 кВ: **6 000 руб.**
- Фактическое присоединение ответвления от воздушной линии напряжением до 1 кВ: **8 000 руб.**
- Выезд бригады ООО «Башкирэнерго» для допуска персонала: **5 000 руб.**
- Монтаж ответвления от воздушной линии: **200 руб.**
- Выезд бригады для оказания услуг: **6 000 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        
        # Header is preserved
        assert '## Отдельные услуги' in result
        # Disambiguation note is present
        assert DISAMBIGUATION_NOTE in result
        # Table format is used
        assert '| Услуга | Стоимость |' in result
        assert '|---|---|' in result
        # Each service-price pair is in a separate row
        assert '| Фактическое присоединение кабеля кабельного типа напряжением до 1 кВ | 6 000 руб. |' in result
        assert '| Выезд бригады ООО «Башкирэнерго» для допуска персонала | 5 000 руб. |' in result
        assert '| Выезд бригады для оказания услуг | 6 000 руб. |' in result
        # Original bullet format is gone
        assert '- Фактическое присоединение кабеля' not in result
        assert '- Выезд бригады ООО' not in result
    
    # Test 9.2: No Price List — Pass Through
    def test_9_2_no_price_list_passthrough(self):
        """Content without prices should be unchanged."""
        input_text = """## Процесс подключения

Для подключения необходимо:
- Подать заявку через личный кабинет
- Предоставить документы
- Дождаться технических условий"""
        
        result = _disambiguate_price_lists(input_text)
        assert result == input_text
    
    # Test 9.3: Single Price — No Table
    def test_9_3_single_price_no_table(self):
        """Single price below threshold should not trigger reformatting."""
        input_text = """Стоимость подключения:
- Плата за подключение: **15 000 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        assert result == input_text
    
    # Test 9.4: Mixed List — Items Without Prices
    def test_9_4_mixed_list_without_prices(self):
        """Mixed list where some items lack prices gets dashes."""
        input_text = """## Услуги

- Консультация бесплатная
- Подключение до 15 кВт: **5 000 руб.**
- Подключение от 15 до 150 кВт: **15 000 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        
        assert '| Услуга | Стоимость |' in result
        assert '| Консультация бесплатная | — |' in result
        assert '| Подключение до 15 кВт | 5 000 руб. |' in result
        assert '| Подключение от 15 до 150 кВт | 15 000 руб. |' in result
        assert DISAMBIGUATION_NOTE in result
    
    # Test 9.5: Price Mid-Sentence — Not Detected
    def test_9_5_price_mid_sentence_not_detected(self):
        """Price in middle of sentence should not be reformatted."""
        input_text = 'В 2023 году было подключено **5 000 руб.** клиентов, что больше показателя прошлого года.'
        result = _disambiguate_price_lists(input_text)
        assert result == input_text
    
    # Test 9.6: Multiple Price Lists in One Chunk
    def test_9_6_multiple_price_lists(self):
        """Two separate price list blocks should both be reformatted."""
        input_text = """## Услуги подключения

- Подключение до 15 кВт: **5 000 руб.**
- Подключение от 15 до 150 кВт: **15 000 руб.**

Некоторые дополнительные услуги:

- Выезд бригады: **6 000 руб.**
- Монтаж: **200 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        
        # Two tables should exist
        assert result.count('| Услуга | Стоимость |') == 2
        # Two disambiguation notes
        assert result.count(DISAMBIGUATION_NOTE) == 2
        # Both headers preserved
        assert '## Услуги подключения' in result
        # First table items
        assert '| Подключение до 15 кВт | 5 000 руб. |' in result
        assert '| Подключение от 15 до 150 кВт | 15 000 руб. |' in result
        # Second table items
        assert '| Выезд бригады | 6 000 руб. |' in result
        assert '| Монтаж | 200 руб. |' in result
        # Original bullets are gone
        assert '- Подключение до 15 кВт:' not in result
        assert '- Выезд бригады:' not in result
    
    # Test 9.7: Empty Content
    def test_9_7_empty_content(self):
        """Empty string should return empty string."""
        result = _disambiguate_price_lists('')
        assert result == ''
    
    # Test 9.8: Already a Table — No Transformation
    def test_9_8_already_a_table(self):
        """Content that is already a table should not be transformed."""
        input_text = """| Услуга | Стоимость |
|---|---|
| Подключение | 5 000 руб. |"""
        
        result = _disambiguate_price_lists(input_text)
        assert result == input_text
    
    # Additional edge case: None content
    def test_none_content(self):
        """None should be returned as None."""
        result = _disambiguate_price_lists(None)
        assert result is None
    
    # Additional: Price without dot suffix
    def test_price_without_dot(self):
        """Price format 'руб' without dot should work."""
        input_text = """- Услуга A: **5 000 руб**
- Услуга B: **10 000 руб**"""
        
        result = _disambiguate_price_lists(input_text)
        assert '| Услуга A | 5 000 руб. |' in result
        assert '| Услуга B | 10 000 руб. |' in result
    
    # Additional: Multi-line bullet items
    def test_multiline_bullet_items(self):
        """Multi-line bullet items with continuations should be handled."""
        input_text = """- Фактическое присоединение кабеля
  кабельного типа: **6 000 руб.**
- Монтаж ответвления: **200 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        assert '| Услуга | Стоимость |' in result
        assert 'Фактическое присоединение кабеля кабельного типа' in result
        assert '200 руб.' in result
    
    # Additional: Pipe character in service name
    def test_pipe_character_escaped(self):
        """Pipe characters in service names should be escaped."""
        input_text = """- Услуга с | символом: **100 руб.**
- Другая услуга: **200 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        assert '| Услуга с \\| символом | 100 руб. |' in result
    
    # Additional: dash separator (not em-dash)
    def test_dash_separator(self):
        """Items separated by dash should work."""
        input_text = """- Услуга A - **100 руб.**
- Услуга B - **200 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        assert '| Услуга A | 100 руб. |' in result
        assert '| Услуга B | 200 руб. |' in result
    
    # Additional: Content with no bullet lists at all
    def test_no_bullet_lists(self):
        """Content with no bullet lists should pass through unchanged."""
        input_text = 'Just some regular paragraph text without any bullets.'
        result = _disambiguate_price_lists(input_text)
        assert result == input_text
    
    # Additional: Multiple header levels
    def test_h3_header_preserved(self):
        """H3 headers preceding price lists should be preserved."""
        input_text = """### Дополнительные услуги

- Услуга A: **100 руб.**
- Услуга B: **200 руб.**"""
        
        result = _disambiguate_price_lists(input_text)
        assert '### Дополнительные услуги' in result
        assert DISAMBIGUATION_NOTE in result
        assert '| Услуга A | 100 руб. |' in result
    
    # Additional: Non-bullet list with prices should not be reformatted
    def test_non_bullet_list_with_prices(self):
        """Non-bullet lists (e.g., paragraphs with prices) should not be reformatted."""
        input_text = 'Услуга A стоит **100 руб.**, а услуга B стоит **200 руб.**'
        result = _disambiguate_price_lists(input_text)
        assert result == input_text  # No bullet list detected

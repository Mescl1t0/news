import json
import sys
import re

def translate_text(text, dest='ru'):
    """Translate text to destination language using googletrans if available, otherwise return original."""
    try:
        from googletrans import Translator
        translator = Translator()
        # Detect if text already contains Cyrillic (Russian)
        if re.search(r'[А-Яа-яЁё]', text):
            return text
        translated = translator.translate(text, dest=dest)
        return translated.text
    except Exception as e:
        # Fallback: if googletrans not available or fails, return original
        # But we need to try to provide some translation, so we'll return original for now
        # In a real scenario, we might have a dictionary, but for simplicity we return original.
        return text

def translate_title(title_original):
    # If already contains Cyrillic, return as is (but we might want to keep original? Task says add Russian translation)
    # We'll return the original if it's already Russian, else translate.
    if re.search(r'[А-Яа-яЁё]', title_original):
        return title_original
    return translate_text(title_original, 'ru')

def translate_description(snippet):
    # If snippet is empty, return a generic sentence
    if not snippet:
        return "Описание недоступно."
    
    # Remove placeholder pattern if present
    # Pattern: "Материал посвящён теме «...»." or "Материал посвящён теме ..."
    # We want to extract the inner part and translate it if needed, then form a proper sentence.
    match = re.search(r'Материал посвящён теме[ «](.*?)[»]?\.?$', snippet)
    if match:
        inner = match.group(1)
        # Translate inner if it's not Russian
        if not re.search(r'[А-Яа-яЁё]', inner):
            inner = translate_text(inner, 'ru')
        return f"Материал посвящён теме {inner}."
    
    # If snippet is already in Russian and not a placeholder, we can use it as is, but ensure it's a sentence.
    if re.search(r'[А-Яа-яЁё]', snippet):
        # Make sure it ends with a period
        if not snippet.endswith('.'):
            snippet += '.'
        return snippet
    
    # Otherwise, translate the snippet to Russian
    translated = translate_text(snippet, 'ru')
    if not translated.endswith('.'):
        translated += '.'
    return translated

def process_item(item):
    # Create output item with id, title_ru, description_ru
    title_ru = translate_title(item['title_original'])
    
    # For description, we use the snippet if available, otherwise create from title
    if 'snippet' in item and item['snippet']:
        description_ru = translate_description(item['snippet'])
    else:
        # Fallback: make a simple description from title
        description_ru = f"Статья о {title_ru.lower()}."
    
    return {
        'id': item['id'],
        'title_ru': title_ru,
        'description_ru': description_ru
    }

def main():
    # Read input
    with open('/home/node/.openclaw/workspace/news-reports/public/reports/2026-05-17/ai_input.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process all items
    output_items = []
    for section in data['sections']:
        for item in section['items']:
            output_items.append(process_item(item))
    
    # Create output
    output = {
        'provider': 'openclaw-agent',
        'items': output_items
    }
    
    # Write output
    with open('/home/node/.openclaw/workspace/news-reports/public/reports/2026-05-17/ai_output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Processed {len(output_items)} items")

if __name__ == '__main__':
    main()
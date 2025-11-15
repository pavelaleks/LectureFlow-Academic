"""
Скрипт для экспорта данных курсов и лекций для переноса на другой компьютер.

Использование:
    python scripts/export_data.py export --output backup_folder/
    python scripts/export_data.py import --source backup_folder/
"""
import argparse
import shutil
import json
from pathlib import Path
import sys

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config


def export_data(output_dir: Path):
    """
    Экспортировать все данные курсов и лекций в указанную папку.
    
    Args:
        output_dir: Папка для сохранения данных
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем структуру папок
    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    print(f"📦 Экспорт данных в {output_dir}")
    
    # Копируем courses.json
    if config.COURSES_JSON.exists():
        shutil.copy2(config.COURSES_JSON, data_dir / "courses.json")
        print(f"✅ Скопирован {config.COURSES_JSON}")
    else:
        print(f"⚠️  Файл {config.COURSES_JSON} не найден")
    
    # Копируем course_contexts
    if config.COURSE_CONTEXTS_DIR.exists() and any(config.COURSE_CONTEXTS_DIR.iterdir()):
        contexts_dest = data_dir / "course_contexts"
        if contexts_dest.exists():
            shutil.rmtree(contexts_dest)
        shutil.copytree(config.COURSE_CONTEXTS_DIR, contexts_dest)
        print(f"✅ Скопирована папка {config.COURSE_CONTEXTS_DIR}")
    else:
        print(f"⚠️  Папка {config.COURSE_CONTEXTS_DIR} пуста или не существует")
    
    # Копируем uploads
    if config.UPLOADS_DIR.exists() and any(config.UPLOADS_DIR.iterdir()):
        uploads_dest = data_dir / "uploads"
        if uploads_dest.exists():
            shutil.rmtree(uploads_dest)
        shutil.copytree(config.UPLOADS_DIR, uploads_dest)
        print(f"✅ Скопирована папка {config.UPLOADS_DIR}")
    else:
        print(f"⚠️  Папка {config.UPLOADS_DIR} пуста или не существует")
    
    # Копируем outputs
    if config.OUTPUTS_DIR.exists() and any(config.OUTPUTS_DIR.iterdir()):
        if outputs_dir.exists():
            shutil.rmtree(outputs_dir)
        shutil.copytree(config.OUTPUTS_DIR, outputs_dir)
        print(f"✅ Скопирована папка {config.OUTPUTS_DIR}")
    else:
        print(f"⚠️  Папка {config.OUTPUTS_DIR} пуста или не существует")
    
    # Создаем файл README с инструкциями
    readme_path = output_dir / "README.txt"
    readme_content = """BACKUP DATA FOR LECTUREFLOW ACADEMIC
==========================================

Эта папка содержит резервную копию всех данных курсов и лекций.

Для восстановления данных на другом компьютере:
1. Склонируйте проект: git clone <repository_url>
2. Настройте проект согласно инструкциям в README.md
3. Запустите скрипт импорта:
   python scripts/export_data.py import --source .

Или скопируйте папки вручную:
- data/ -> <project_root>/data/
- outputs/ -> <project_root>/outputs/

После копирования перезапустите Streamlit приложение.
"""
    readme_path.write_text(readme_content, encoding='utf-8')
    
    print(f"\n✅ Экспорт завершен! Данные сохранены в {output_dir}")
    print(f"📁 Структура резервной копии:")
    print(f"   {output_dir}/")
    print(f"   ├── data/")
    print(f"   │   ├── courses.json")
    print(f"   │   ├── course_contexts/")
    print(f"   │   └── uploads/")
    print(f"   └── outputs/")


def import_data(source_dir: Path):
    """
    Импортировать данные из указанной папки.
    
    Args:
        source_dir: Папка с резервной копией данных
    """
    source_dir = Path(source_dir)
    
    if not source_dir.exists():
        print(f"❌ Ошибка: папка {source_dir} не существует")
        return
    
    print(f"📥 Импорт данных из {source_dir}")
    
    data_dir = source_dir / "data"
    outputs_dir = source_dir / "outputs"
    
    # Проверяем наличие данных
    if not data_dir.exists() and not outputs_dir.exists():
        print(f"❌ Ошибка: в папке {source_dir} не найдены папки data/ или outputs/")
        return
    
    # Восстанавливаем courses.json
    courses_source = data_dir / "courses.json"
    if courses_source.exists():
        if config.COURSES_JSON.exists():
            backup_path = config.COURSES_JSON.with_suffix('.json.backup')
            shutil.copy2(config.COURSES_JSON, backup_path)
            print(f"💾 Создана резервная копия существующего файла: {backup_path}")
        
        shutil.copy2(courses_source, config.COURSES_JSON)
        print(f"✅ Восстановлен {config.COURSES_JSON}")
    else:
        print(f"⚠️  Файл {courses_source} не найден")
    
    # Восстанавливаем course_contexts
    contexts_source = data_dir / "course_contexts"
    if contexts_source.exists() and any(contexts_source.iterdir()):
        if config.COURSE_CONTEXTS_DIR.exists():
            # Создаем резервную копию существующей папки
            backup_path = config.COURSE_CONTEXTS_DIR.with_name(config.COURSE_CONTEXTS_DIR.name + '_backup')
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(config.COURSE_CONTEXTS_DIR, backup_path)
            print(f"💾 Создана резервная копия существующей папки: {backup_path}")
        
        # Удаляем существующую папку и копируем новую
        if config.COURSE_CONTEXTS_DIR.exists():
            shutil.rmtree(config.COURSE_CONTEXTS_DIR)
        shutil.copytree(contexts_source, config.COURSE_CONTEXTS_DIR)
        print(f"✅ Восстановлена папка {config.COURSE_CONTEXTS_DIR}")
    else:
        print(f"⚠️  Папка {contexts_source} пуста или не существует")
    
    # Восстанавливаем uploads
    uploads_source = data_dir / "uploads"
    if uploads_source.exists() and any(uploads_source.iterdir()):
        if config.UPLOADS_DIR.exists():
            # Создаем резервную копию существующей папки
            backup_path = config.UPLOADS_DIR.with_name(config.UPLOADS_DIR.name + '_backup')
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(config.UPLOADS_DIR, backup_path)
            print(f"💾 Создана резервная копия существующей папки: {backup_path}")
        
        # Удаляем существующую папку и копируем новую
        if config.UPLOADS_DIR.exists():
            shutil.rmtree(config.UPLOADS_DIR)
        shutil.copytree(uploads_source, config.UPLOADS_DIR)
        print(f"✅ Восстановлена папка {config.UPLOADS_DIR}")
    else:
        print(f"⚠️  Папка {uploads_source} пуста или не существует")
    
    # Восстанавливаем outputs
    if outputs_dir.exists() and any(outputs_dir.iterdir()):
        if config.OUTPUTS_DIR.exists():
            # Создаем резервную копию существующей папки
            backup_path = config.OUTPUTS_DIR.with_name(config.OUTPUTS_DIR.name + '_backup')
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(config.OUTPUTS_DIR, backup_path)
            print(f"💾 Создана резервная копия существующей папки: {backup_path}")
        
        # Удаляем существующую папку и копируем новую
        if config.OUTPUTS_DIR.exists():
            shutil.rmtree(config.OUTPUTS_DIR)
        shutil.copytree(outputs_dir, config.OUTPUTS_DIR)
        print(f"✅ Восстановлена папка {config.OUTPUTS_DIR}")
    else:
        print(f"⚠️  Папка {outputs_dir} пуста или не существует")
    
    print(f"\n✅ Импорт завершен!")
    print(f"⚠️  ВАЖНО: Перезапустите Streamlit приложение для применения изменений")


def main():
    parser = argparse.ArgumentParser(
        description="Экспорт и импорт данных LectureFlow Academic"
    )
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда export
    export_parser = subparsers.add_parser('export', help='Экспортировать данные')
    export_parser.add_argument(
        '--output',
        type=str,
        default='backup',
        help='Папка для сохранения резервной копии (по умолчанию: backup)'
    )
    
    # Команда import
    import_parser = subparsers.add_parser('import', help='Импортировать данные')
    import_parser.add_argument(
        '--source',
        type=str,
        required=True,
        help='Папка с резервной копией данных'
    )
    
    args = parser.parse_args()
    
    if args.command == 'export':
        export_data(Path(args.output))
    elif args.command == 'import':
        import_data(Path(args.source))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()


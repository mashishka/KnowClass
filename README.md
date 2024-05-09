
# Окружение
* предполагается работа в vscode
* рекомендуемые расширения в .vscode/extensions.json
* используем mypy и black
* предполагается работа в venv, зависимости в requirements.txt, те, что только для разработке в requirements-dev.txt
* тесты на pytest, в директории test

# Возможные улучшения работы с бд:
    * свойство количества для факторов, их значений, примеров, значений результата
    * изменяемое имя результата
    * триггеры на проверку того, что в positions лежат правильные id при update
    * разные типы в text?
    * функция проверки наличия значения (has_value)
    * триггер на factor_id для example value (вместо ручного способа)
    * триггеры на изменение позиции (вместо ручного способа)
    * проверка наличия триггеров при загрузке
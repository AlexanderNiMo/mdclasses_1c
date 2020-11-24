
# Метаданные конфигурации 1с

Может использоваться для анализа иерархической выгрузки в xml из конфигуратора.

Текущие возможности:

- Чтение списка объектов из xml и их основных свойств
- Чтение модулей и их структуры (области, подпрограммы, область переменных, препроцессоры, описание инструкций расширений подпрограмм)
- Чтение основных свойств форм и их модулей

Использование:

        import mdclasses
        
        conf = mdclasses.read_configuration('xml_dump_path')
        
        for obj in conf.conf_objects:
            obj.read_modules()   
            obj.read_forms()
            
            # Поиск процедуры/функции в модуле
            main_func = obj.modules[0].find_sub_program('Имя процедуры')
            
        # Поиск объекта в конфигурации
        
        conf.get_object('Справочник1', mdclasses.ObjectType.CATALOG)
        
Установка:

    pip install mdclasses
        

